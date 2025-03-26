#!/bin/bash

# Exit on any error
set -e

# Change to the project root directory
cd "$(dirname "$0")/.."

# Run the specified test files
echo "Running fixed test suite..."

echo "1. Running test_tool_descriptions.py..."
python -m pytest swagger_mcp/tests/test_tool_descriptions.py -v

echo "2. Running test_parameter_descriptions.py..."
python -m pytest swagger_mcp/tests/test_parameter_descriptions.py -v

echo "3. Running test_openapi_parser.py..."
python -m pytest swagger_mcp/tests/test_openapi_parser.py -v

echo "4. Running test_openapi_mcp_server.py..."
python -m pytest swagger_mcp/tests/test_openapi_mcp_server.py -v

# If we get here, all tests passed
echo "✅ All tests passed!"
