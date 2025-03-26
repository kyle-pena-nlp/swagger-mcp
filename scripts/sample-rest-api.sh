#!/bin/bash

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Ensure we're using the development virtual environment
cd "$PROJECT_ROOT"
source "$SCRIPT_DIR/setup_dev_venv.sh"

python -m sample_rest_api.run