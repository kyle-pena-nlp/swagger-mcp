#!/bin/bash

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Ensure we're using the development virtual environment
source "$SCRIPT_DIR/setup_dev_venv.sh"

# Start the API server
python "$PROJECT_ROOT/sample_rest_api/run.py"