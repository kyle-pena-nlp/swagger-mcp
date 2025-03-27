#!/bin/bash
set -e

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Function to create and activate a virtual environment
setup_venv() {
    local venv_dir="$1"
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "$venv_dir" ]; then
        echo "Creating virtual environment..."
        python3 -m venv "$venv_dir"
    fi
    
    # Activate virtual environment
    source "$venv_dir/bin/activate"
    
    # Install the package in normal mode
    echo "Installing package..."
    pip install -e "$PROJECT_ROOT"
}

# Set up the main project's virtual environment
setup_venv "$PROJECT_ROOT/.venv"