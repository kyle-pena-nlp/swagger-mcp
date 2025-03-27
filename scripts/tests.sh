#!/bin/bash

# Exit on any error
set -e

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Ensure we're using the development virtual environment
cd "$PROJECT_ROOT"
source "$SCRIPT_DIR/setup_dev_venv.sh"

# Run all unit tests
echo "Running unit tests..."
python -m pytest swagger_mcp/tests/unit -v "$@"

# If we get here, all tests passed
echo "✅ All unit tests passed!"
