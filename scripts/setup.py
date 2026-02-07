import os
import subprocess
import sys

def run_command(command):
    """Run a command and check for errors."""
    try:
        subprocess.run(command, check=True, shell=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {e}")
        sys.exit(1)

def main():
    """Set up the project."""
    print("Setting up the project...")

    # Create a virtual environment
    print("Creating virtual environment...")
    run_command("uv venv")

    # Install dependencies
    print("Installing dependencies...")
    run_command("uv pip install -e .[dev]")

    print("Project setup complete.")
    print("To activate the virtual environment, run: source .venv/bin/activate")

if __name__ == "__main__":
    main()
