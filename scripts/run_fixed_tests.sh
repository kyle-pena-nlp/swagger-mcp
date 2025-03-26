#!/bin/bash

# Exit on any error
set -e

# Change to the project root directory
cd "$(dirname "$0")/.."

# Run the specified test file
echo "Running test_tool_descriptions.py..."
python -m pytest swagger_mcp/tests/test_tool_descriptions.py -v

# If we get here, all tests passed
echo "✅ All tests passed!"
