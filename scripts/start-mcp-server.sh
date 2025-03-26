#!/bin/bash

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Ensure we're using the development virtual environment
cd "$PROJECT_ROOT"
source "$SCRIPT_DIR/setup_dev_venv.sh"

# Ensure the openapi.json spec is available on http://localhost:9000/openapi.json by sending a test request
# exit if not.
curl -s http://localhost:9000/openapi.json > /dev/null || { echo "Error: openapi.json spec not found at http://localhost:9000/openapi.json"; exit 1; }

# Start the MCP server in a separate process
python "$PROJECT_ROOT/swagger_mcp/openapi_mcp_server.py" http://localhost:9000/openapi.json --name product-mcp &

# Wait for the MCP server to start
sleep 1


