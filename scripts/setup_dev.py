#!/usr/bin/env python3
"""
Development environment setup script for KrathongScanner.

This script helps set up the development environment by:
1. Creating necessary directories
2. Setting up virtual environment
3. Installing dependencies
4. Setting up pre-commit hooks
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path


def run_command(command, check=True):
    """Run a shell command."""
    print(f"Running: {command}")
    result = subprocess.run(command, shell=True, check=check)
    return result


def create_directories():
    """Create necessary project directories."""
    directories = [
        "logs",
        "temp",
        "output",
        "models",
        "checkpoints",
        "data/aruco_markers",
        "data/calibration",
        "data/test_images",
    ]

    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {directory}")


def setup_virtual_environment():
    """Set up Python virtual environment."""
    if not Path("venv").exists():
        print("Creating virtual environment...")
        run_command("python -m venv venv")
    else:
        print("Virtual environment already exists.")

    # Activate virtual environment and install dependencies
    if os.name == "nt":  # Windows
        activate_script = "venv\\Scripts\\activate"
        pip_path = "venv\\Scripts\\pip"
    else:  # Unix/Linux/Mac
        activate_script = "venv/bin/activate"
        pip_path = "venv/bin/pip"

    print("Installing dependencies...")
    run_command(f"{pip_path} install --upgrade pip")
    run_command(f"{pip_path} install -r requirements.txt")
    run_command(f"{pip_path} install -r requirements-dev.txt")


def setup_pre_commit():
    """Set up pre-commit hooks."""
    try:
        run_command("pre-commit install", check=False)
        print("Pre-commit hooks installed successfully.")
    except subprocess.CalledProcessError:
        print("Warning: Could not install pre-commit hooks.")
        print("You can install them manually with: pre-commit install")


def setup_git():
    """Set up Git repository if not already done."""
    if not Path(".git").exists():
        print("Initializing Git repository...")
        run_command("git init")
        run_command("git add .")
        run_command("git commit -m 'Initial commit'")
    else:
        print("Git repository already exists.")


def create_env_file():
    """Create .env file from template."""
    if not Path(".env").exists() and Path("env.example").exists():
        shutil.copy("env.example", ".env")
        print("Created .env file from template.")
        print("Please update .env with your specific configuration.")
    elif Path(".env").exists():
        print(".env file already exists.")
    else:
        print("Warning: env.example not found. Please create .env manually.")


def main():
    """Main setup function."""
    print("Setting up KrathongScanner development environment...")

    # Check Python version
    if sys.version_info < (3, 8):
        print("Error: Python 3.8+ is required.")
        sys.exit(1)

    try:
        create_directories()
        setup_virtual_environment()
        setup_pre_commit()
        setup_git()
        create_env_file()

        print("\nSetup completed successfully!")
        print("\nNext steps:")
        print("1. Activate virtual environment:")
        if os.name == "nt":
            print("   venv\\Scripts\\activate")
        else:
            print("   source venv/bin/activate")
        print("2. Update .env file with your configuration")
        print("3. Run tests: pytest")
        print("4. Start development!")

    except subprocess.CalledProcessError as e:
        print(f"Error during setup: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
