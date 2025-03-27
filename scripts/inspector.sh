#!/bin/bash

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Ensure we're using the development virtual environment
cd "$PROJECT_ROOT"
source "$SCRIPT_DIR/setup_dev_venv.sh"

# Ensure the openapi.json spec is available on http://localhost:9000/openapi.json by sending a test request
# exit if not.
curl -s http://localhost:9000/openapi.json > /dev/null || { echo "Error: openapi.json spec not found at http://localhost:9000/openapi.json - run bash scripts/sample-rest-api.sh first"; exit 1; }

npx @modelcontextprotocol/inspector swagger-mcp --spec http://localhost:9000/openapi.json --name product-mcp --server-url http://localhost:9000