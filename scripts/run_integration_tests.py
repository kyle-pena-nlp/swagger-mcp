#!/usr/bin/env python3
import subprocess
import time
import sys
import os
import signal
import argparse
from pathlib import Path

def start_sample_api():
    """Start the sample REST API server."""
    api_process = subprocess.Popen(
        ["python", "sample-rest-api/app.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=str(Path(__file__).parent.parent)
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
