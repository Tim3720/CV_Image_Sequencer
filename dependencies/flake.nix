{
inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-25.05";
    flake-utils = {
        url = "github:numtide/flake-utils";
        inputs.system.follows = "systems";
    };
};

outputs = { self, nixpkgs, flake-utils, ... }:
    flake-utils.lib.eachDefaultSystem
    (system:
    let
        pkgs = import nixpkgs {
            inherit system;
            config.allowUnfree = true;
        };
        libs = [
        ];
    in
        with pkgs;
            {
            devShells.default = mkShell {
                nativeBuildInputs = with pkgs; [
                    bashInteractive
                ];
                buildInputs = [
                    (pkgs.python312.withPackages(ps: with ps;[
						pip
                        pylint
                        pyside6
                        numpy
                        matplotlib
						(opencv4.override {enableGtk3 = true;})
						scikit-learn
						streamlit
						pydantic
                    ]))
                ];
                LD_LIBRARY_PATH = "${pkgs.lib.makeLibraryPath libs}";
				shellHook = ''
					export QT_QPA_PLATFORM=xcb
				'';
            };
        }
    );
}
