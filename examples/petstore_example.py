#!/usr/bin/env python3
"""
Example script showing how to use the OpenAPI MCP Server with the Swagger Petstore API
"""
import os
import sys

# Add parent directory to Python path so we can import our module
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

# Import from the main module
from openapi_mcp_server import OpenApiService, FastMCP, register_operation_tool, logger

# Petstore OpenAPI spec URL
PETSTORE_SPEC_URL = "https://petstore3.swagger.io/api/v3/openapi.json"

def main():
    """Run the Petstore example MCP server"""
    # Initialize MCP server with a custom name
    mcp = FastMCP("Petstore API")
    
    # Initialize the OpenAPI service with the Petstore spec
    api_service = OpenApiService(PETSTORE_SPEC_URL)
    
    try:
        # Load and parse the OpenAPI spec
        logger.info(f"Loading Petstore API spec from {PETSTORE_SPEC_URL}")
        api_service.load_spec()
        
        # Register only the pet-related endpoints as tools
        pet_path_prefix = "/pet"
        
        # Count how many tools we register
        tool_count = 0
        
        # Register tools for each path and operation
        for path in api_service.spec.paths:
            # Filter to only include pet endpoints
            if path.url.startswith(pet_path_prefix):
                for operation in path.operations:
                    register_operation_tool(mcp, api_service, path, operation)
                    tool_count += 1
        
        # Log registration completion
        logger.info(f"Registered {tool_count} pet operations from Petstore API as MCP tools")
        
        # Run the MCP server
        logger.info("Starting Petstore MCP server")
        mcp.run(transport='stdio')
    except Exception as e:
        logger.error(f"Error initializing Petstore MCP server: {e}")
        raise

if __name__ == "__main__":
    main() 