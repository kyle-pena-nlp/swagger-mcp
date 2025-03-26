#!/usr/bin/env python3
import subprocess
import time
import sys
import os
import signal
import argparse
import venv
from pathlib import Path

def ensure_venv(api_dir):
    """Ensure the virtual environment exists and requirements are installed."""
    venv_dir = api_dir / ".venv"
    requirements_file = api_dir / "requirements.txt"
    
    # Create venv if it doesn't exist
    if not venv_dir.exists():
        print("Creating virtual environment for sample REST API...")
        venv.create(venv_dir, with_pip=True)
    
    # Determine pip path
    if sys.platform == "win32":
        pip_path = venv_dir / "Scripts" / "pip"
    else:
        pip_path = venv_dir / "bin" / "pip"
    
    # Install requirements
    if requirements_file.exists():
        print("Installing sample REST API requirements...")
        subprocess.run(
            [str(pip_path), "install", "-r", str(requirements_file)],
            check=True,
            cwd=str(api_dir)
        )

def get_python_path(api_dir):
    """Get the Python interpreter path from the virtual environment."""
    if sys.platform == "win32":
        python_path = api_dir / ".venv" / "Scripts" / "python"
    else:
        python_path = api_dir / ".venv" / "bin" / "python"
    return python_path

def start_sample_api():
    """Start the sample REST API server."""
    project_root = Path(__file__).parent.parent
    api_dir = project_root / "sample-rest-api"
    
    # Ensure virtual environment is set up
    ensure_venv(api_dir)
    
    # Get the Python interpreter from the virtual environment
    python_path = get_python_path(api_dir)
    
    api_process = subprocess.Popen(
        [str(python_path), "app.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=str(api_dir)
    )
    
    # Wait for the server to start
    time.sleep(2)
    
    # Check if the process is still running
    if api_process.poll() is not None:
        stdout, stderr = api_process.communicate()
        print("Failed to start sample REST API:")
        print(f"stdout: {stdout.decode()}")
        print(f"stderr: {stderr.decode()}")
        sys.exit(1)
    
    return api_process

def run_tests():
    """Run the integration tests."""
    test_process = subprocess.run(
        ["pytest", "swagger_mcp/tests/test_openapi_mcp_integration.py", "-v"],
        cwd=str(Path(__file__).parent.parent)
    )
    return test_process.returncode

def run_examples():
    """Run the example scripts."""
    examples_dir = Path(__file__).parent.parent / "examples"
    failed = False
    
    for example in examples_dir.glob("*.py"):
        if example.name.startswith("test_"):
            continue
        print(f"\nRunning example: {example.name}")
        result = subprocess.run(
            ["python", str(example)],
            cwd=str(examples_dir)
        )
        if result.returncode != 0:
            print(f"Example {example.name} failed with exit code {result.returncode}")
            failed = True
    
    return 1 if failed else 0

def main():
    parser = argparse.ArgumentParser(description="Run integration tests with sample REST API")
    parser.add_argument("--examples", action="store_true", help="Run example scripts instead of tests")
    args = parser.parse_args()
    
    # Start the sample REST API
    print("Starting sample REST API...")
    api_process = start_sample_api()
    
    try:
        # Run either tests or examples
        if args.examples:
            print("\nRunning example scripts...")
            exit_code = run_examples()
        else:
            print("\nRunning integration tests...")
            exit_code = run_tests()
        
        if exit_code == 0:
            print("\nAll tests passed successfully!")
        else:
            print("\nSome tests failed!")
        
        return exit_code
    
    finally:
        # Clean up: terminate the API server
        print("\nShutting down sample REST API...")
        api_process.terminate()
        api_process.wait()

if __name__ == "__main__":
    sys.exit(main())
