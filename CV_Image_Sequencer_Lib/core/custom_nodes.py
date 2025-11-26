from typing import Any, Optional, override
import random
import numpy as np
import cv2 as cv

from ..utils.source_manager import SourceManager
from .types import ColorImage, Float, GrayScaleImage, Int, MorphologyTypes, ThresholdType, Contours, String  # Add Contours
from .nodes import Node, Graph

class IDXNode(Node):
    def __init__(self, graph: Graph):
        super().__init__(graph, [], [("Idx", Int)])

    @override
    def compute_function(self, inputs):
        idx = random.randint(0, 100)
        print(idx)
        return [idx]


class SourceNode(Node):
    def __init__(self, graph: Graph, source_manager: SourceManager, n_frames: int = 1,
                 grayscale_mode: bool = False):

        if grayscale_mode:
            super().__init__(graph, [("Offset", Int)], [*[("Image", GrayScaleImage) for _ in
                                                 range(n_frames)]])
        else:
            super().__init__(graph, [("Offset", Int)], [*[("Image", ColorImage) for _ in
                                                 range(n_frames)]])

        self.n_frames = n_frames
        self.grayscale_mode = grayscale_mode
        self.source_manager = source_manager

        self.name = "SourceNode"

        self.min_values = [Int(value=0)]
        self.max_values = [Int(value=self.source_manager.get_number_of_frames())]
        self.default_values = [Int(value=0)]

    @override
    def compute_function(self, inputs):
        offset = inputs[0].value
        frames = self.source_manager.get_next_n_frames(self.n_frames, offset, self.grayscale_mode)
        if frames is None:
            if self.grayscale_mode:
                frames = [GrayScaleImage(None) for _ in range(self.n_frames)]
            else:
                frames = [ColorImage(None) for _ in range(self.n_frames)]
        # frames.append(offset)
        return frames

    @override
    def to_dict(self):
        d = super().to_dict()
        d["params"] = {"n_frames": self.n_frames, "grayscale_mode": self.grayscale_mode}
        return d


class ABSDiffNode(Node):
    def __init__(self, graph: Graph):
        super().__init__(graph, [("Image 1", GrayScaleImage), ("Image 2", GrayScaleImage)],
                         [("Result Image", GrayScaleImage)])
        self.name = "AbsDiffNode"

    @override
    def compute_function(self, inputs: list[Optional[GrayScaleImage]]):
        if inputs[0] is None or inputs[1] is None:
            return [GrayScaleImage(value=None)]
        img1 = inputs[0].value
        img2 = inputs[1].value
        if img1 is None or img2 is None:
            return [GrayScaleImage(value=None)]
        img = cv.absdiff(img1, img2)
        return [GrayScaleImage(value=img)]


class ThresholdNode(Node):
    def __init__(self, graph: Graph):
        super().__init__(graph, [("Image 1", GrayScaleImage), ("Threshold value", Float),
                                 ("New value", Int), ("Type", ThresholdType)],
                         [("Result Image", GrayScaleImage), ("Threshold value", Float), ("Type", ThresholdType)])
        self.name = "ThresholdNode"

        self.min_values[1] = Float(value=0)
        self.min_values[2] = Int(value=0)
        self.max_values[1] = Float(value=255)
        self.max_values[2] = Int(value=255)

        self.default_values[1] = Float(value=10)
        self.default_values[2] = Int(value=255)
        self.default_values[3] = ThresholdType(value="Binary")

    @override
    def compute_function(self, inputs: list):
        if inputs[0] is None:
            return [GrayScaleImage(value=None), Float(value=0), inputs[3]]
        img1 = inputs[0].value
        if img1 is None:
            return [GrayScaleImage(value=None), Float(value=0), inputs[3]]

        t, img = cv.threshold(img1, inputs[1].value, inputs[2].value, ThresholdType.options[inputs[3].value])
        return [GrayScaleImage(value=img), Float(value=t), inputs[3]]


class InvertNode(Node):
    def __init__(self, graph: Graph):
        super().__init__(graph, [("Image 1", GrayScaleImage)],
                         [("Result Image", GrayScaleImage)])
        self.name = "InvertNode"

    @override
    def compute_function(self, inputs: list[Optional[GrayScaleImage]]):
        if inputs[0] is None:
            return [GrayScaleImage(value=None)]
        img1 = inputs[0].value
        if img1 is None:
            return [GrayScaleImage(value=None)]
        img = cv.bitwise_not(img1)
        return [GrayScaleImage(value=img)]

class MinNode(Node):
    def __init__(self, graph: Graph):
        super().__init__(graph, [("Image 1", GrayScaleImage), ("Image 2", GrayScaleImage)],
                         [("Result Image", GrayScaleImage)])
        self.name = "MinNode"

    @override
    def compute_function(self, inputs: list[Optional[GrayScaleImage]]):
        if inputs[0] is None or inputs[1] is None:
            return [GrayScaleImage(value=None)]
        img1 = inputs[0].value
        img2 = inputs[1].value
        if img1 is None or img2 is None:
            return [GrayScaleImage(value=None)]
        img = np.min([img1, img2], axis=0)
        return [GrayScaleImage(value=img)]


class MaxNode(Node):
    def __init__(self, graph: Graph):
        super().__init__(graph, [("Image 1", GrayScaleImage), ("Image 2", GrayScaleImage)],
                         [("Result Image", GrayScaleImage)])
        self.name = "MaxNode"

    @override
    def compute_function(self, inputs: list[Optional[GrayScaleImage]]):
        if inputs[0] is None or inputs[1] is None:
            return [GrayScaleImage(value=None)]
        img1 = inputs[0].value
        img2 = inputs[1].value
        if img1 is None or img2 is None:
            return [GrayScaleImage(value=None)]
        img = np.max([img1, img2], axis=0)
        return [GrayScaleImage(value=img)]


class ClampedDiffNode(Node):
    def __init__(self, graph: Graph):
        super().__init__(graph,
                         parameter_template=[
                             ("Image 1", GrayScaleImage),
                             ("Image 2", GrayScaleImage),
                             ("Cutoff", Int)
                         ],
                         result_template=[
                             ("Result Image", GrayScaleImage)
                         ])

        self.min_values[2] = Int(0)
        self.max_values[2] = Int(255)
        self.default_values[2] = Int(0)

        self.name = "ClampedDiff"

    @override
    def compute_function(self, inputs: list):
        if inputs[0] is None or inputs[1] is None:
            return [GrayScaleImage(value=None)]
        img1 = inputs[0].value
        img2 = inputs[1].value
        if img1 is None or img2 is None:
            return [GrayScaleImage(value=None)]
        res = img1.astype(np.int32) - img2.astype(np.int32)
        res[res < inputs[2].value] = 0
        res = res.astype(np.uint8)
        return [GrayScaleImage(value=res)]


class SplitChannelNode(Node):
    def __init__(self, graph: Graph):
        super().__init__(graph, [("Image", ColorImage)],
                         [("Channel 1", GrayScaleImage), ("Channel 2", GrayScaleImage),
                          ("Channel 3", GrayScaleImage)])
        self.name = "SplitChannelsNode"

    @override
    def compute_function(self, inputs: list):
        if inputs[0] is None:
            return [GrayScaleImage(value=None), GrayScaleImage(value=None), GrayScaleImage(value=None)]
        img1 = inputs[0].value
        if img1 is None:
            return [GrayScaleImage(value=None), GrayScaleImage(value=None), GrayScaleImage(value=None)]

        ch1, ch2, ch3 = cv.split(img1)
        return [GrayScaleImage(value=ch1), GrayScaleImage(ch2), GrayScaleImage(ch3)]


class RegionOfInterestNode(Node):
    def __init__(self, graph: Graph):
        super().__init__(graph, [("Image", GrayScaleImage), ("x", Int), ("y", Int),
                                 ("width", Int), ("height", Int)],
                         [("Result Image", GrayScaleImage)])
        self.name = "RegionOfInterestNode"

        self.default_values[1] = Int(0)
        self.default_values[2] = Int(0)
        self.default_values[3] = Int(-1)
        self.default_values[4] = Int(-1)

    @override
    def compute_function(self, inputs: list):
        if inputs[0] is None:
            return [GrayScaleImage(value=None)]
        img = inputs[0].value
        if img is None:
            return [GrayScaleImage(value=None)]

        x = inputs[1].value
        y = inputs[2].value
        width = inputs[3].value
        height = inputs[4].value 

        if width <= 0:
            width = img.shape[1] - x
        if height <= 0:
            height = img.shape[0] - y

        res = img[y:y+height, x:x+width]
        return [GrayScaleImage(value=res)]


class ErodeNode(Node):
    def __init__(self, graph: Graph):
        super().__init__(graph, [("Image", GrayScaleImage), ("kernelSize", Int),
                                 ("iterations", Int)],
                         [("Result Image", GrayScaleImage)])
        self.name = "ErodeNode"

        self.min_values[1] = Int(0)
        self.min_values[2] = Int(0)

        self.default_values[1] = Int(3)
        self.default_values[2] = Int(1)

    @override
    def compute_function(self, inputs: list):
        if inputs[0] is None:
            return [GrayScaleImage(value=None)]
        img = inputs[0].value
        if img is None:
            return [GrayScaleImage(value=None)]

        kernel = np.ones((inputs[1].value, inputs[1].value))
        res = cv.erode(img, kernel, iterations=inputs[2].value)
        return [GrayScaleImage(value=res)]

class DilateNode(Node):
    def __init__(self, graph: Graph):
        super().__init__(graph, [("Image", GrayScaleImage), ("kernelSize", Int),
                                 ("iterations", Int)],
                         [("Result Image", GrayScaleImage)])
        self.name = "DilateNode"

        self.min_values[1] = Int(0)
        self.min_values[2] = Int(0)

        self.default_values[1] = Int(3)
        self.default_values[2] = Int(1)

    @override
    def compute_function(self, inputs: list):
        if inputs[0] is None:
            return [GrayScaleImage(value=None)]
        img = inputs[0].value
        if img is None:
            return [GrayScaleImage(value=None)]

        kernel = np.ones((inputs[1].value, inputs[1].value))
        res = cv.dilate(img, kernel, iterations=inputs[2].value)
        return [GrayScaleImage(value=res)]


class PixelwiseAnd(Node):
    def __init__(self, graph: Graph):
        super().__init__(graph,
                         parameter_template=[
                             ("Image 1", GrayScaleImage),
                             ("Image 2", GrayScaleImage),
                         ],
                         result_template=[
                             ("Result Image", GrayScaleImage)
                         ])

        self.name = "PixelwiseAnd"

    @override
    def compute_function(self, inputs: list):
        if inputs[0] is None or inputs[1] is None:
            return [GrayScaleImage(value=None)]
        img1 = inputs[0].value
        img2 = inputs[1].value
        if img1 is None or img2 is None:
            return [GrayScaleImage(value=None)]
        res = cv.bitwise_and(img1, img2)
        return [GrayScaleImage(value=res)]

class MorphologyOperationNode(Node):
    def __init__(self, graph: Graph):
        super().__init__(graph, [("Image", GrayScaleImage), ("operation", MorphologyTypes), ("kernelSize", Int),
                                 ("iterations", Int)],
                         [("Result Image", GrayScaleImage)])
        self.name = "MorphologyOperationNode"

        self.min_values[2] = Int(0)
        self.min_values[3] = Int(0)

        self.default_values[2] = Int(3)
        self.default_values[3] = Int(1)
        self.default_values[1] = MorphologyTypes("Close")

    @override
    def compute_function(self, inputs: list):
        if inputs[0] is None:
            return [GrayScaleImage(value=None)]
        img = inputs[0].value
        if img is None:
            return [GrayScaleImage(value=None)]

        kernel = np.ones((inputs[2].value, inputs[2].value))
        res = cv.morphologyEx(img, MorphologyTypes.options[inputs[1].value], kernel, iterations=inputs[3].value)
        return [GrayScaleImage(value=res)]

class FindContoursNode(Node):
    def __init__(self, graph: Graph):
        super().__init__(graph, 
                         parameter_template=[
                             ("Input Image", GrayScaleImage),
                             ("Draw On Image", GrayScaleImage),
                             ("Mode", Int),
                             ("Method", Int),
                             ("Draw Color R", Int),
                             ("Draw Color G", Int),
                             ("Draw Color B", Int),
                             ("Thickness", Int)
                         ],
                         result_template=[
                             ("Result Image", ColorImage),
                             ("Contour Count", Int),
                             ("Contours", Contours)  # Changed from list to Contours
                         ])
        
        self.name = "FindContoursNode"
        
        # Set default values
        self.default_values[2] = Int(cv.RETR_EXTERNAL)
        self.default_values[3] = Int(cv.CHAIN_APPROX_SIMPLE)
        self.default_values[4] = Int(0)    # Red = 0
        self.default_values[5] = Int(255)  # Green = 255
        self.default_values[6] = Int(0)    # Blue = 0
        self.default_values[7] = Int(2)    # Thickness
        
        # Set min/max values for colors
        self.min_values[4] = Int(0)
        self.max_values[4] = Int(255)
        self.min_values[5] = Int(0)
        self.max_values[5] = Int(255)
        self.min_values[6] = Int(0)
        self.max_values[6] = Int(255)
        self.min_values[7] = Int(-1)  # -1 means filled
        self.max_values[7] = Int(50)

    @override
    def compute_function(self, inputs: list):
        if inputs[0] is None:
            return [ColorImage(value=None), Int(0), Contours(value=[])]  # Changed
        
        img = inputs[0].value
        if img is None:
            return [ColorImage(value=None), Int(0), Contours(value=[])]  # Changed
        
        # Determine which image to draw on
        if inputs[1] is not None and inputs[1].value is not None:
            draw_img = inputs[1].value
        else:
            draw_img = img
        
        # Find contours on the input image
        contours, _ = cv.findContours(img, inputs[2].value, inputs[3].value)
        
        # Convert draw image to color if it's grayscale
        if len(draw_img.shape) == 2:
            result_img = cv.cvtColor(draw_img, cv.COLOR_GRAY2BGR)
        else:
            result_img = draw_img.copy()
        
        # Create BGR color tuple from RGB inputs (OpenCV uses BGR)
        color = (inputs[6].value, inputs[5].value, inputs[4].value)  # BGR order
        
        # Draw contours
        cv.drawContours(result_img, contours, -1, color, inputs[7].value)
        
        return [ColorImage(value=result_img), Int(len(contours)), Contours(value=contours)]  # Changed


class SaveContourCropsNode(Node):
    def __init__(self, graph: Graph):
        super().__init__(graph, 
                         parameter_template=[
                             ("Input Image", GrayScaleImage),
                             ("Contours", Contours),
                             ("Padding", Int),
                             ("Min Area", Int)
                         ],
                         result_template=[
                             ("Saved Count", Int),
                             ("Output Directory", String),  # Add this - the directory path
                             ("Status", String)
                         ])
        
        self.name = "SaveContourCropsNode"
        
        # These are now internal attributes, not socket inputs
        self.output_directory = "./contour_crops"
        self.filename_prefix = "crop"
        
        # Set default values
        self.default_values[2] = Int(value=5)  # Padding
        self.default_values[3] = Int(value=100)  # Min Area
        
        # Set min/max values
        self.min_values[2] = Int(value=0)
        self.max_values[2] = Int(value=100)
        self.min_values[3] = Int(value=0)
        self.max_values[3] = Int(value=10000)

    def clear_output_directory(self):
        """Remove all files from the output directory"""
        import os
        import glob
        
        if not os.path.exists(self.output_directory):
            print(f"Directory {self.output_directory} does not exist, nothing to clear")
            return
        
        # Remove all image files
        patterns = ['*.png', '*.jpg', '*.jpeg', '*.tif', '*.tiff']
        removed_count = 0
        
        for pattern in patterns:
            files = glob.glob(os.path.join(self.output_directory, pattern))
            for file in files:
                try:
                    os.remove(file)
                    removed_count += 1
                except Exception as e:
                    print(f"Failed to remove {file}: {e}")
        
        print(f"Cleared {removed_count} files from {self.output_directory}")
        return removed_count

    @override
    def compute_function(self, inputs: list):
        if inputs[0] is None or inputs[1] is None:
            return [Int(value=0), String(value=""), String(value="Error: Missing inputs")]
        
        img = inputs[0].value
        contours = inputs[1].value
        
        if img is None or not contours:
            return [Int(value=0), String(value=""), String(value="Error: Invalid inputs")]
        
        padding = inputs[2].value
        min_area = inputs[3].value
        
        # Create output directory if it doesn't exist
        import os
        os.makedirs(self.output_directory, exist_ok=True)
        
        # Clear directory before saving new crops
        self.clear_output_directory()
        
        saved_count = 0
        for i, contour in enumerate(contours):
            # Filter by area
            area = cv.contourArea(contour)
            if area < min_area:
                continue
            
            # Get bounding box
            x, y, w, h = cv.boundingRect(contour)
            
            # Add padding
            x = max(0, x - padding)
            y = max(0, y - padding)
            w = min(img.shape[1] - x, w + 2 * padding)
            h = min(img.shape[0] - y, h + 2 * padding)
            
            # Crop image
            crop = img[y:y+h, x:x+w]
            
            # Save crop
            filename = f"{self.filename_prefix}_{saved_count:04d}.png"
            filepath = os.path.join(self.output_directory, filename)
            cv.imwrite(filepath, crop)
            
            saved_count += 1
        
        status = f"Saved {saved_count} crops to {self.output_directory}"
        return [Int(value=saved_count), String(value=self.output_directory), String(value=status)]  # Changed return

class ClassificationNode(Node):
    def __init__(self, graph: Graph):
        super().__init__(graph, 
                         parameter_template=[
                             ("Original Image", GrayScaleImage),
                             ("Crops Directory", String),
                             ("Entropy Threshold", Float),
                             ("Temperature", Float),
                             ("Batch Size", Int)
                         ],
                         result_template=[
                             ("Annotated Image", ColorImage),
                             ("Classification Count", Int),
                             ("Status", String)
                         ])
        
        self.name = "ClassificationNode"
        
        # Internal attributes for model path
        self.model_path = "./model"
        self.output_csv = "./classifications.csv"
        self.binary_mode = False
        self.font_scale = 2  # Changed from 0.6 to 1.2 (double the size)
        self.font_thickness = 4  # Changed from 2 to 3 (thicker text)
        self.size_bar = False  # Remove scale bar from images
        
        # Set default values
        self.default_values[1] = String(value="./contour_crops")
        self.default_values[2] = Float(value=1.0)
        self.default_values[3] = Float(value=1.5)
        self.default_values[4] = Int(value=64)
        
        # Set min/max values
        self.min_values[2] = Float(value=0.0)
        self.max_values[2] = Float(value=5.0)
        self.min_values[3] = Float(value=0.1)
        self.max_values[3] = Float(value=3.0)
        self.min_values[4] = Int(value=1)
        self.max_values[4] = Int(value=256)

    def resize_to_larger_edge(self, image, target_size):
        """Resize image so larger edge equals target_size"""
        from PIL import Image
        import torchvision.transforms.functional as F
        
        original_width, original_height = image.size
        larger_edge = max(original_width, original_height)
        scale_factor = target_size / larger_edge
        
        new_width = int(original_width * scale_factor)
        new_height = int(original_height * scale_factor)
        
        try:
            resized_image = F.resize(image, (new_height, new_width))
        except ValueError:
            print(f"Skipping: image size: {image.size}, new height: {new_height}, new width: {new_width}")
            return None
        return resized_image

    def custom_image_processor(self, image, target_size=(224, 224), padding_color=255):
        """Custom preprocessing matching your training routine"""
        from PIL import Image
        import torchvision.transforms as transforms
        
        if image.mode != 'RGB':
            image = image.convert('RGB')

        if self.size_bar:
            # Remove scale bar by cropping bottom 50 pixels
            width, height = image.size
            image = image.crop((0, 0, width, height - 50))
        
        # Resize the image
        resized_image = self.resize_to_larger_edge(image, 224)
        if resized_image is None:
            return None

        # Calculate padding
        new_width, new_height = resized_image.size
        padding_left = (target_size[0] - new_width) // 2
        padding_right = target_size[0] - new_width - padding_left
        padding_top = (target_size[1] - new_height) // 2
        padding_bottom = target_size[1] - new_height - padding_top

        # Apply padding
        padding = (padding_left, padding_top, padding_right, padding_bottom)
        pad_transform = transforms.Pad(padding, fill=padding_color)
        padded_image = pad_transform(resized_image)

        # Apply transformations
        transform_chain = transforms.Compose([
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5])
        ])
        
        return transform_chain(padded_image)

    @override
    def compute_function(self, inputs: list):
        print("=" * 80)
        print("ClassificationNode.compute_function called!")
        
        if inputs[0] is None:
            print("ERROR: Missing image")
            return [ColorImage(value=None), Int(value=0), String(value="Error: Missing image")]
        
        original_img = inputs[0].value
        crop_dir = inputs[1].value
        entropy_threshold = inputs[2].value
        temperature = inputs[3].value
        batch_size = inputs[4].value
        
        print(f"Original image shape: {original_img.shape if original_img is not None else 'None'}")
        print(f"Crop directory: {crop_dir}")
        
        if original_img is None:
            return [ColorImage(value=None), Int(value=0), String(value="Error: Invalid image")]
        
        # Convert grayscale to color if needed
        if len(original_img.shape) == 2:
            original_img = cv.cvtColor(original_img, cv.COLOR_GRAY2BGR)
        
        import os
        from pathlib import Path
        
        print(f"Checking crop directory: {crop_dir}")
        print(f"  Exists: {os.path.exists(crop_dir)}")
        if os.path.exists(crop_dir):
            files = list(Path(crop_dir).glob("*.png")) + list(Path(crop_dir).glob("*.jpg"))
            print(f"  Number of files: {len(files)}")
        
        print(f"Checking model path: {self.model_path}")
        print(f"  Exists: {os.path.exists(self.model_path)}")
        
        if not os.path.exists(crop_dir):
            return [ColorImage(value=None), Int(value=0), String(value=f"Error: Directory {crop_dir} not found")]
        
        if not os.path.exists(self.model_path):
            return [ColorImage(value=None), Int(value=0), String(value=f"Error: Model path {self.model_path} not found")]
        
        try:
            # Import required libraries
            import torch
            from transformers import ViTForImageClassification
            from torch.utils.data import Dataset, DataLoader
            from PIL import Image
            import pandas as pd
            
            # Custom dataset using your preprocessing
            class ImageFolderDataset(Dataset):
                def __init__(self, image_dir, processor_func):
                    self.image_dir = Path(image_dir)
                    self.image_files = sorted(list(self.image_dir.glob("*.png")) + \
                                             list(self.image_dir.glob("*.jpg")) + \
                                             list(self.image_dir.glob("*.jpeg")))
                    self.processor_func = processor_func
                
                def __len__(self):
                    return len(self.image_files)
                
                def __getitem__(self, idx):
                    img_path = self.image_files[idx]
                    image = Image.open(img_path)
                    
                    # Use custom processor
                    pixel_values = self.processor_func(image)
                    
                    if pixel_values is None:
                        # Return a dummy tensor if processing failed
                        pixel_values = torch.zeros((3, 224, 224))
                    
                    return {
                        'pixel_values': pixel_values,
                        'label': img_path.name,
                        'index': idx,
                        'path': str(img_path)
                    }
            
            print("Loading model...")
            vit = ViTForImageClassification.from_pretrained(self.model_path)
            
            # Use MPS on Mac if available, otherwise CPU
            if torch.backends.mps.is_available():
                device = torch.device("mps")
                print("Using MPS (Apple Silicon)")
            else:
                device = torch.device("cpu")
                print("Using CPU")
            
            vit.to(device)
            vit.eval()
            
            # Create dataset with custom processor
            dataset = ImageFolderDataset(crop_dir, self.custom_image_processor)
            print(f"Dataset size: {len(dataset)}")
            
            dataloader = DataLoader(
                dataset,
                batch_size=batch_size,
                shuffle=False,
                num_workers=0
            )
            
            predictions = []
            filenames = []
            probabilities = []
            entropy_scores = []
            ood_flags = []
            crop_paths = []
            
            print("Processing images...")
            for batch in dataloader:
                inputs_batch = batch['pixel_values'].to(device)
                
                with torch.no_grad():
                    outputs = vit(pixel_values=inputs_batch)
                
                # Apply temperature scaling
                scaled_logits = outputs.logits / temperature
                probs = torch.nn.functional.softmax(scaled_logits, dim=-1)
                
                # Calculate entropy
                entropy = -torch.sum(probs * torch.log(probs + 1e-10), dim=-1)
                
                if self.binary_mode:
                    top_probs, top_indices = torch.max(probs, dim=-1)
                    batch_labels = [[vit.config.id2label[idx.item()]] 
                                  for idx in top_indices]
                    top_probs_np = top_probs.unsqueeze(-1).cpu().numpy()
                else:
                    top_probs, top_indices = torch.topk(probs, min(5, probs.shape[-1]), dim=-1)
                    batch_labels = [[vit.config.id2label[idx.item()] for idx in indices_tensor] 
                                  for indices_tensor in top_indices]
                    top_probs_np = top_probs.cpu().numpy()
                
                batch_ood = (entropy > entropy_threshold).cpu().numpy()
                
                predictions.extend(batch_labels)
                filenames.extend(batch['label'])
                probabilities.extend(top_probs_np)
                entropy_scores.extend(entropy.cpu().numpy())
                ood_flags.extend(batch_ood)
                crop_paths.extend(batch['path'])
            
            print(f"Total predictions: {len(predictions)}")
            
            # Save results to CSV
            results_df = pd.DataFrame({
                'filename': filenames,
                'prediction': [pred[0] for pred in predictions],
                'probability': [prob[0] for prob in probabilities],
                'entropy': entropy_scores,
                'is_ood': ood_flags,
                'all_predictions': [str(pred) for pred in predictions],
                'all_probabilities': [str(prob) for prob in probabilities]
            })
            
            results_df.to_csv(self.output_csv, index=False)
            print(f"Results saved to {self.output_csv}")
            
            # Create annotated image
            annotated_img = original_img.copy()
            
            for i, (crop_path, prediction, probability, is_ood, filename) in enumerate(zip(crop_paths, 
                                                                                             predictions, 
                                                                                             probabilities, 
                                                                                             ood_flags,
                                                                                             filenames)):
                print(f"Processing crop {i}: {filename} -> {prediction[0]}, prob: {probability[0]:.2f}, OOD: {is_ood}")
                
                # Load the crop
                crop = cv.imread(crop_path)
                if crop is None:
                    print(f"  Warning: Could not load crop {crop_path}")
                    continue
                
                crop_h, crop_w = crop.shape[:2]
                
                # Use template matching to find location
                gray_orig = cv.cvtColor(original_img, cv.COLOR_BGR2GRAY) if len(original_img.shape) == 3 else original_img
                gray_crop = cv.cvtColor(crop, cv.COLOR_BGR2GRAY) if len(crop.shape) == 3 else crop
                
                result = cv.matchTemplate(gray_orig, gray_crop, cv.TM_CCOEFF_NORMED)
                min_val, max_val, min_loc, max_loc = cv.minMaxLoc(result)
                
                x, y = max_loc
                w, h = crop_w, crop_h
                
                print(f"  Found at: x={x}, y={y}, w={w}, h={h}, confidence={max_val:.3f}")
                
                # Choose color based on OOD status
                color = (0, 0, 255) if is_ood else (0, 255, 0)
                
                # Draw bounding box
                cv.rectangle(annotated_img, (x, y), (x + w, y + h), color, 2)
                
                # Prepare text
                label = prediction[0]
                prob = probability[0]
                text = f"{label}: {prob:.2f}"
                if is_ood:
                    text += " (OOD)"
                
                # Get text size for background
                (text_width, text_height), baseline = cv.getTextSize(
                    text, cv.FONT_HERSHEY_SIMPLEX, self.font_scale, self.font_thickness
                )
                
                # Draw text background
                cv.rectangle(annotated_img, 
                           (x, y - text_height - baseline - 5),
                           (x + text_width, y),
                           color, -1)
                
                # Draw text
                cv.putText(annotated_img, text, (x, y - baseline - 5),
                          cv.FONT_HERSHEY_SIMPLEX, self.font_scale, (255, 255, 255),
                          self.font_thickness, cv.LINE_AA)
            
            print(f"Annotated {len(predictions)} crops")
            status = f"Classified {len(predictions)} crops. Results saved to {self.output_csv}"
            return [ColorImage(value=annotated_img), Int(value=len(predictions)), String(value=status)]
            
        except Exception as e:
            import traceback
            error_msg = f"Error during classification: {str(e)}\n{traceback.format_exc()}"
            print(error_msg)
            return [ColorImage(value=None), Int(value=0), String(value=error_msg)]

class DeconvolutionNode(Node):
    def __init__(self, graph: Graph):
        super().__init__(graph, 
                         parameter_template=[
                             ("Input Image", GrayScaleImage),
                             ("Batch Size", Int),
                             ("Min StdDev", Float)  # Minimum std dev to process
                         ],
                         result_template=[
                             ("Deconvolved Image", GrayScaleImage),
                             ("Status", String)
                         ])
        
        self.name = "DeconvolutionNode"
        
        # Internal attributes
        self.model_name = 'lucyd-edof-plankton_231204.pth'
        self.model = None
        self.device = None
        
        # Set default values
        self.default_values[1] = Int(value=4)
        self.default_values[2] = Float(value=2.0)
        
        # Set min/max values
        self.min_values[1] = Int(value=1)
        self.max_values[1] = Int(value=32)
        self.min_values[2] = Float(value=0.0)
        self.max_values[2] = Float(value=100.0)

    def load_model(self):
        """Load the LUCYD model (called once on first use)"""
        if self.model is not None:
            return  # Already loaded
        
        import torch
        import os
        
        try:
            from .lucyd import LUCYD
        except ImportError:
            print("ERROR: lucyd package not found. Please install it.")
            return False
        
        print("Loading LUCYD deconvolution model...")
        
        # Get model path
        current_dir = os.path.dirname(__file__)
        model_path = os.path.join(current_dir, 'models', self.model_name)
        
        if not os.path.exists(model_path):
            print(f"ERROR: Model file not found at {model_path}")
            return False
        
        # Initialize model
        self.model = LUCYD(num_res=1)
        
        # Check if CUDA is available
        if torch.cuda.is_available():
            self.device = torch.device('cuda')
            print("CUDA is available, using GPU.")
            if torch.cuda.device_count() > 1:
                print(f"Using {torch.cuda.device_count()} GPUs.")
        else:
            # Check for MPS (Apple Silicon)
            if torch.backends.mps.is_available():
                self.device = torch.device('mps')
                print("Using MPS (Apple Silicon)")
            else:
                self.device = torch.device('cpu')
                print("Warning! Using CPU (slower).")
        
        # Load weights
        self.model.load_state_dict(torch.load(model_path, map_location=self.device))
        
        # Use DataParallel if multiple GPUs available
        if torch.cuda.is_available() and torch.cuda.device_count() > 1:
            self.model = torch.nn.DataParallel(self.model)
        
        self.model.to(self.device)
        self.model.eval()
        
        print("Model loaded successfully!")
        return True

    @override
    def compute_function(self, inputs: list):
        if inputs[0] is None:
            return [GrayScaleImage(value=None), String(value="Error: Missing input image")]
        
        img = inputs[0].value
        batch_size = inputs[1].value
        min_stddev = inputs[2].value
        
        if img is None:
            return [GrayScaleImage(value=None), String(value="Error: Invalid input image")]
        
        # Load model on first use
        if self.model is None:
            if not self.load_model():
                return [GrayScaleImage(value=None), String(value="Error: Failed to load model")]
        
        try:
            import torch
            
            # Check image statistics
            mean = np.mean(img)
            stddev = np.std(img)
            
            print(f"Image stats - Mean: {mean:.2f}, StdDev: {stddev:.2f}")
            
            if stddev < min_stddev:
                status = f"Skipped: StdDev {stddev:.2f} < threshold {min_stddev}"
                print(status)
                return [GrayScaleImage(value=img), String(value=status)]
            
            # Prepare image for deconvolution
            x = img / 255.0
            x = x.astype(np.float32)  # Add this line - convert to float32 for MPS compatibility
            x_t = torch.from_numpy(x).to(self.device)
            x_t = x_t.unsqueeze(0).unsqueeze(0)  # Add batch and channel dimensions
            
            # Perform deconvolution
            print("Running deconvolution...")
            with torch.no_grad():
                y_hat, _, _ = self.model(x_t.float())  # .float() ensures float32
            
            # Convert back to numpy
            deconv = y_hat.detach().cpu().numpy()[0, 0]
            deconv = deconv * 255.0
            deconv = np.clip(deconv, 0, 255).astype(np.uint8)
            
            status = f"Deconvolved successfully (StdDev: {stddev:.2f})"
            print(status)
            
            return [GrayScaleImage(value=deconv), String(value=status)]
            
        except Exception as e:
            import traceback
            error_msg = f"Error during deconvolution: {str(e)}\n{traceback.format_exc()}"
            print(error_msg)
            return [GrayScaleImage(value=None), String(value=error_msg)]
