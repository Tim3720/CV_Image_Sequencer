import cv2
import numpy as np

class ImageProcessor:
    def __init__(self):
        """
        Initializes the Image Processor.
        """
        pass

    def apply_operation(self, image, operation_name, parameters):
        """
        Applies a single image processing operation to an image.
        
        Args:
            image (np.ndarray): The input image (e.g., a frame from OpenCV).
            operation_name (str): The name of the operation to apply.
            parameters (dict): A dictionary of parameters for the operation.
            
        Returns:
            np.ndarray: The processed image.
        """
        if operation_name == "blur":
            # Apply a simple Gaussian blur
            ksize = parameters.get('ksize', (5, 5))
            return cv2.GaussianBlur(image, ksize, 0)
        
        # Add more operations here as you build them
        # For now, return the original image if the operation is not recognized
        return image
