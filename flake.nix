{
  description = "LLT Assistant Backend - FastAPI backend for pytest test analysis";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    pyproject-nix = {
      url = "github:pyproject-nix/pyproject.nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
    pyproject-build-systems = {
      url = "github:pyproject-nix/build-system-pkgs";
      inputs.pyproject-nix.follows = "pyproject-nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs = { self, nixpkgs, flake-utils, pyproject-nix, pyproject-build-systems }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs {
          inherit system;
        };

        # Python version to use
        python = pkgs.python311;

        # Load project metadata from pyproject.toml
        project = pyproject-nix.lib.project.loadPyproject {
          projectRoot = ./.;
        };

        # Render build attributes for buildPythonPackage
        attrs = project.renderers.buildPythonPackage { inherit python; };

        # Build the application using standard nixpkgs buildPythonPackage
        # pyproject.nix renders the attributes, nixpkgs provides the builder
        app = python.pkgs.buildPythonPackage (attrs // {
          # Override version (required when not using dynamic versioning)
          version = "0.1.0";

          # Disable tests during build (run separately in CI)
          doCheck = false;

          # Build inputs - packages needed at build time
          nativeBuildInputs = with pkgs; [
            python.pkgs.hatchling
          ];

          # Runtime dependencies
          propagatedBuildInputs = with python.pkgs; [
            fastapi
            uvicorn
            pydantic
            pydantic-settings
            httpx
            python-multipart
            pytest
            langchain
            langchain-openai
            langchain-core
            redis
            neo4j
          ];

          # Additional build configuration
          pythonImportsCheck = [ "app" ];
        });

      in
      {
        packages = {
          default = app;

          # Docker image output
          dockerImage = pkgs.dockerTools.buildLayeredImage {
            name = "llt-api";
            tag = "latest";

            contents = [
              app
              pkgs.coreutils
              pkgs.bash
            ];

            config = {
              Cmd = [ "${app}/bin/uvicorn" "app.main:app" "--host" "0.0.0.0" "--port" "8886" ];
              ExposedPorts = {
                "8886/tcp" = { };
              };
              Env = [
                "PYTHONUNBUFFERED=1"
                "PORT=8886"
              ];
              # Removed WorkingDir per Copilot suggestion - Nix paths are in /nix/store
            };
          };
        };

        devShells = {
          default = pkgs.mkShell {
            buildInputs = [
              python
              python.pkgs.hatchling
              app

              # Development tools
              pkgs.git
              pkgs.curl
              pkgs.uv
            ];

            shellHook = ''
              echo "🚀 LLT Assistant Backend Development Environment"
              echo "Python version: $(python --version)"
              echo ""
              echo "Available commands:"
              echo "  uvicorn app.main:app --reload  - Start development server"
              echo "  pytest                          - Run tests"
            '';
          };
        };

        # Formatter for nix files
        formatter = pkgs.nixpkgs-fmt;
      }
    );
}
