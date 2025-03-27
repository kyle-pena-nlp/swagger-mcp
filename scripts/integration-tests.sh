#!/bin/bash
set -e

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Ensure we're using the development virtual environment
cd "$PROJECT_ROOT"
source "$SCRIPT_DIR/setup_dev_venv.sh"

echo "Running integration tests..."
# Run pytest with specific markers and configuration
python -m pytest swagger_mcp/tests/integration/ \
    -v \
    --capture=no \
    --log-cli-level=INFO \
    "$@"  # Pass any additional arguments to pytest

# Check the exit status
status=$?
if [ $status -eq 0 ]; then
    echo "✅ All integration tests passed!"
    exit 0
else
    echo "❌ Integration tests failed!"
    exit $status
fi
