{
  description = "LLT Assistant Backend - FastAPI backend for pytest test analysis";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    poetry2nix = {
      url = "github:nix-community/poetry2nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs = { self, nixpkgs, flake-utils, poetry2nix }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs {
          inherit system;
          overlays = [ poetry2nix.overlays.default ];
        };

        # Python version to use
        python = pkgs.python311;

        # Poetry2nix instance
        p2n = pkgs.poetry2nix;

        # Custom overrides for problematic packages
        poetryOverrides = p2n.defaultPoetryOverrides.extend (self: super: {
          # Neo4j driver requires specific build inputs
          neo4j = super.neo4j.overridePythonAttrs (old: {
            buildInputs = (old.buildInputs or [ ]) ++ [ pkgs.libffi ];
          });

          # Skip tests for packages that have problematic test dependencies
          httpx = super.httpx.overridePythonAttrs (old: {
            doCheck = false;
          });

          # LangChain packages may need test skipping
          langchain = super.langchain.overridePythonAttrs (old: {
            doCheck = false;
          });

          langchain-openai = super.langchain-openai.overridePythonAttrs (old: {
            doCheck = false;
          });

          langchain-core = super.langchain-core.overridePythonAttrs (old: {
            doCheck = false;
          });

          # Redis client
          redis = super.redis.overridePythonAttrs (old: {
            doCheck = false;
          });

          # FastAPI and related packages
          fastapi = super.fastapi.overridePythonAttrs (old: {
            doCheck = false;
          });

          uvicorn = super.uvicorn.overridePythonAttrs (old: {
            doCheck = false;
          });
        });

        # Main Python application
        app = p2n.mkPoetryApplication {
          inherit python;
          projectDir = ./.;
          overrides = poetryOverrides;

          # Additional arguments
          preferWheels = true;

          # Skip tests during build (we'll run them separately)
          checkPhase = ''
            echo "Skipping tests during Nix build"
          '';
        };

        # Development shell with all dependencies
        devShell = p2n.mkPoetryEnv {
          inherit python;
          projectDir = ./.;
          overrides = poetryOverrides;

          # Include dev dependencies
          groups = [ "dev" ];
          preferWheels = true;
        };

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
              WorkingDir = "/app";
            };
          };
        };

        devShells = {
          default = pkgs.mkShell {
            buildInputs = [
              devShell
              pkgs.poetry
              python

              # Development tools
              pkgs.git
              pkgs.curl
            ];

            shellHook = ''
              echo "🚀 LLT Assistant Backend Development Environment"
              echo "Python version: $(python --version)"
              echo "Poetry version: $(poetry --version)"
              echo ""
              echo "Available commands:"
              echo "  poetry install      - Install dependencies"
              echo "  poetry run pytest   - Run tests"
              echo "  uvicorn app.main:app --reload - Start development server"
            '';
          };
        };

        # Formatter for nix files
        formatter = pkgs.nixpkgs-fmt;
      }
    );
}
