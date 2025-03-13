#!/usr/bin/env python3
"""
OpenAPI MCP Server Example

This example demonstrates how to create an MCP server that exposes tools based on
an OpenAPI specification. For demonstration purposes, we use the PetStore API.
"""

import os
import sys
import logging
import tempfile
import requests
from openapi_mcp_server import OpenAPIMCPServer, run_server

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# PetStore OpenAPI spec URL
PETSTORE_API_URL = "https://petstore3.swagger.io/api/v3/openapi.json"

def download_openapi_spec(url: str, output_path: str) -> None:
    """
    Download an OpenAPI specification from a URL.
    
    Args:
        url: The URL of the OpenAPI specification
        output_path: The path to save the OpenAPI specification
    """
    logger.info(f"Downloading OpenAPI spec from {url}")
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        with open(output_path, "w") as f:
            f.write(response.text)
        
        logger.info(f"Downloaded OpenAPI spec to {output_path}")
    except Exception as e:
        logger.error(f"Failed to download OpenAPI spec: {e}")
        raise

def main():
    """Run the OpenAPI MCP Server example."""
    # Create a temporary file for the OpenAPI spec
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as temp_file:
        spec_path = temp_file.name
    
    try:
        # Download the PetStore OpenAPI spec
        download_openapi_spec(PETSTORE_API_URL, spec_path)
        
        # Start the MCP server
        logger.info("Starting MCP server with PetStore API...")
        run_server(
            openapi_spec_path=spec_path,
            server_name="PetStore-MCP-Server",
            server_url="https://petstore3.swagger.io/api/v3"
        )
    finally:
        # Clean up the temporary file
        if os.path.exists(spec_path):
            os.unlink(spec_path)

if __name__ == "__main__":
    main() 