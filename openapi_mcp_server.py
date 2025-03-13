from typing import List, Dict, Any, Optional, Union, Callable, Awaitable, Iterator
import asyncio
import json
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import sys
import requests  # Add requests for URL fetching

from mcp.server import Server, NotificationOptions
from mcp.types import Tool
from openapi_parser import OpenAPIParser
from simple_endpoint import SimpleEndpoint, create_simple_endpoint
from endpoint_invoker import EndpointInvoker
from mcp.server.stdio import stdio_server
from mcp.server.models import InitializationOptions
# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                   handlers=[
                       logging.StreamHandler(),  # Console handler
                       RotatingFileHandler(
                           'openapi_mcp_server.log',
                           maxBytes=10485760,  # 10MB
                           backupCount=5
                       )
                   ])
logger = logging.getLogger(__name__)

class OpenAPIMCPServer:
    """
    A server implementation for the Model Context Protocol (MCP) that dynamically
    generates tools based on an OpenAPI specification.
    """
    
    def __init__(
        self, 
        server_name: str, 
        openapi_spec: str,  # Changed parameter name from openapi_spec_path to openapi_spec
        server_url: Optional[str] = None,
        bearer_token: Optional[str] = None,
        server_version: Optional[str] = "1.0.0",
        instructions: Optional[str] = None
    ):
        """
        Initialize the OpenAPI MCP Server.
        
        Args:
            server_name: Name of the MCP server
            openapi_spec: Path or URL to the OpenAPI spec file
            server_url: Base URL for API calls (overrides servers in spec)
            bearer_token: Optional bearer token for authenticated requests
            server_version: Optional server version
            instructions: Optional instructions for the server
        """
        self.server_name = server_name
        self.server_version = server_version or "1.0.0"  # Ensure server_version is not None
        self.server_url = server_url
        self.bearer_token = bearer_token
        
        # Create the MCP server
        self.server = Server(
            name=server_name,
            version=self.server_version
        )
        
        # Load and parse the OpenAPI spec
        try:
            # Check if the spec is a URL
            if openapi_spec.startswith(('http://', 'https://')):
                logger.info(f"Fetching OpenAPI spec from URL: {openapi_spec}")
                response = requests.get(openapi_spec)
                response.raise_for_status()  # Raise exception for non-200 status codes
                
                # Parse content based on content type
                content_type = response.headers.get('Content-Type', '')
                if 'json' in content_type:
                    spec_content = response.json()
                else:
                    # Assume YAML or try to parse as such
                    spec_content = response.text
                
                self.openapi_parser = OpenAPIParser(spec_content)
            else:
                # Treat as file path
                self.openapi_parser = OpenAPIParser(openapi_spec)
                
            logger.info(f"Loaded OpenAPI spec with {len(self.openapi_parser.endpoints)} endpoints")
        except Exception as e:
            logger.error(f"Failed to load OpenAPI spec: {e}")
            raise
        
        # Store the simplified endpoints for easier access
        self.simple_endpoints: Dict[str, SimpleEndpoint] = {}
        for endpoint in self.openapi_parser.get_endpoints():
            simple_endpoint = create_simple_endpoint(endpoint)
            self.simple_endpoints[simple_endpoint.operation_id] = simple_endpoint
            
        # Register the list_tools and call_tool handlers
        self._register_handlers()
    
    def _register_handlers(self):
        """Register the MCP handlers for listing tools and handling tool calls."""
        
        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            """Return a list of tools based on the OpenAPI spec endpoints."""
            logger.info("Listing available tools")
            tools = []
            
            for operation_id, endpoint in self.simple_endpoints.items():
                # Skip deprecated endpoints
                if endpoint.deprecated:
                    continue
                
                # Create input schema from the endpoint's combined parameter schema
                input_schema = {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
                
                if endpoint.combined_parameter_schema and 'properties' in endpoint.combined_parameter_schema:
                    input_schema["properties"] = endpoint.combined_parameter_schema['properties']
                    if 'required' in endpoint.combined_parameter_schema:
                        input_schema["required"] = endpoint.combined_parameter_schema['required']
                
                # Create the tool definition
                tool = Tool(
                    name=operation_id,
                    description=endpoint.summary or f"{endpoint.method.upper()} {endpoint.path}",
                    inputSchema=input_schema
                )
                tools.append(tool)
                logger.info(f"Added tool: {operation_id} ({endpoint.method.upper()} {endpoint.path})")
            
            logger.info(f"Total tools available: {len(tools)}")
            return tools
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> Any:
            """
            Handle a tool call by invoking the corresponding endpoint.
            
            Args:
                name: The name of the tool (operation_id)
                arguments: The tool arguments
                
            Returns:
                The API response result
            """
            logger.info(f"Tool call received: {name}")
            logger.info(f"Tool arguments: {json.dumps(arguments, indent=2, default=str)}")
            
            try:
                # Find the corresponding endpoint
                if name not in self.simple_endpoints:
                    logger.error(f"Tool not found: {name}")
                    raise ValueError(f"Tool not found: {name}")
                
                endpoint = self.simple_endpoints[name]
                logger.info(f"Invoking endpoint: {endpoint.method.upper()} {endpoint.path}")
                
                # Create an endpoint invoker
                invoker = EndpointInvoker(endpoint)
                
                # Invoke the endpoint with the provided parameters
                logger.info(f"Sending request to: {self.server_url or '[default server]'}")
                response = invoker.invoke_with_params(
                    params=arguments,
                    server_url=self.server_url,
                    bearer_token=self.bearer_token
                )
                
                logger.info(f"Response status code: {response.status_code}")
                
                # Process the response
                try:
                    result = response.json()
                    logger.info(f"Received JSON response of size: {len(json.dumps(result))} bytes")
                    return result
                except ValueError:
                    # Not JSON content
                    text_response = response.text
                    logger.info(f"Received text response of size: {len(text_response)} bytes")
                    return text_response
                    
            except Exception as e:
                logger.error(f"Error calling tool {name}: {e}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
                raise


    async def run(self):
       async with stdio_server() as (read_stream, write_stream):
           await self.server.run(
               read_stream,
               write_stream,
               InitializationOptions(
                   server_name=self.server_name,
                   server_version=self.server_version,
                   capabilities=self.server.get_capabilities(
                       notification_options=NotificationOptions(),
                       experimental_capabilities={},
                   ),
               ),
           )        


# Helper function to run the server
def run_server(
    openapi_spec: str,  # Changed parameter name from openapi_spec_path to openapi_spec
    server_name: str = "OpenAPI-MCP-Server",
    server_url: Optional[str] = None,
    bearer_token: Optional[str] = None
):
    """
    Run an OpenAPI MCP Server with the given parameters.
    
    Args:
        openapi_spec: Path or URL to the OpenAPI spec file
        server_name: Name for the MCP server
        server_url: Base URL for API calls (overrides servers in spec)
        bearer_token: Optional bearer token for authenticated requests
        host: Host to bind to
        port: Port to listen on
    """
    logger.info(f"Starting OpenAPI MCP Server: {server_name}")
    logger.info(f"OpenAPI spec: {openapi_spec}")
    logger.info(f"Server URL: {server_url}")
    
    server = OpenAPIMCPServer(
        server_name=server_name,
        openapi_spec=openapi_spec,
        server_url=server_url,
        bearer_token=bearer_token
    )
    
    logger.info("Server initialized, starting main loop")
    asyncio.run(server.run())


if __name__ == "__main__":
    # Simple CLI to start the server
    import argparse
    
    parser = argparse.ArgumentParser(description="Start an MCP server based on an OpenAPI spec")
    parser.add_argument("spec", help="Path or URL to the OpenAPI specification file (JSON or YAML)", nargs="?")
    parser.add_argument("--name", help="Server name")
    parser.add_argument("--url", help="Base URL for API calls (overrides servers in spec)")
    parser.add_argument("--token", help="Bearer token for authenticated requests")
    
    args = parser.parse_args()
    
    run_server(
        openapi_spec=args.spec,
        server_name=args.name,
        server_url=args.url,
        bearer_token=args.token
    ) 