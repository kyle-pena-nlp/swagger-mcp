import json
import requests
import os
import yaml
import logging
import argparse
import asyncio
import re
import traceback
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Callable, Awaitable, Iterator

from mcp.server import Server, NotificationOptions
from mcp.types import Tool, CallToolResult, TextContent, ImageContent, EmbeddedResource
from mcp.server.stdio import stdio_server
from mcp.server.models import InitializationOptions
from swagger_mcp.openapi_parser import OpenAPIParser
from swagger_mcp.endpoint import Endpoint
from swagger_mcp.simple_endpoint import SimpleEndpoint, create_simple_endpoint
from swagger_mcp.endpoint_invoker import EndpointInvoker
from swagger_mcp.logging import setup_logger
from swagger_mcp.server_arg_parser import parse_args

logger = setup_logger(__name__)

class OpenAPIMCPServer:
    """
    A server implementation for the Model Context Protocol (MCP) that dynamically
    generates tools based on an OpenAPI specification.
    """
    
    def __init__(
        self, 
        server_name: str, 
        openapi_spec: Union[str, Dict[str, Any]],  
        server_url: Optional[str] = None,
        bearer_token: Optional[str] = None,
        server_version: Optional[str] = "1.0.0",
        instructions: Optional[str] = None,
        additional_headers: Optional[Dict[str, str]] = None,
        include_pattern: Optional[str] = None,
        exclude_pattern: Optional[str] = None,
        cursor_mode: bool = False,
        const_values: Optional[Dict[str, str]] = None
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
            additional_headers: Optional dictionary of additional headers to include in all requests
            include_pattern: Optional regex pattern to filter endpoints by path (e.g., "/admin/.*" or "/api/v1")
            exclude_pattern: Optional regex pattern to exclude endpoints by path (e.g., "/internal/.*")
            cursor_mode: Whether to enable Cursor-specific quirk handling
            const_values: Optional dictionary of parameter names and their constant values
        """
        self.server_name = server_name
        self.server_version = server_version or "1.0.0"  
        self.server_url = server_url
        self.bearer_token = bearer_token
        self.additional_headers = additional_headers or {}
        self.include_pattern = include_pattern
        self.exclude_pattern = exclude_pattern
        self.cursor_mode = cursor_mode
        self.const_values = const_values or {}
        
        # Create the MCP server
        self.server = Server(
            name=server_name,
            version=self.server_version
        )
        
        # Load and parse the OpenAPI spec
        try:
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
                
                # Apply include and exclude patterns if specified
                if self.include_pattern or self.exclude_pattern:
                    
                    # Check exclude pattern first - if path matches exclude pattern, skip this endpoint
                    if self.exclude_pattern and re.search(self.exclude_pattern, endpoint.path):
                        logger.info(f"Excluding endpoint {endpoint.path} due to exclude pattern")
                        continue
                    
                    # If include pattern is specified and path doesn't match, skip this endpoint
                    if self.include_pattern and not re.search(self.include_pattern, endpoint.path):
                        logger.info(f"Excluding endpoint {endpoint.path} due to include pattern")
                        continue
                
                # Create input schema from the endpoint's combined parameter schema
                input_schema = {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
                
                if endpoint.combined_parameter_schema and 'properties' in endpoint.combined_parameter_schema:
                    input_schema["properties"] = endpoint.combined_parameter_schema['properties'].copy()
                    
                    # Remove const parameters from the input schema
                    for param_name in self.const_values:
                        if param_name in input_schema["properties"]:
                            del input_schema["properties"][param_name]
                            
                    # In cursor mode, remove parameter descriptions
                    if self.cursor_mode and isinstance(input_schema["properties"], dict):
                        for param in input_schema["properties"].values():
                            if isinstance(param, dict) and "description" in param:
                                del param["description"]
                    
                    if 'required' in endpoint.combined_parameter_schema:
                        input_schema["required"] = [r for r in endpoint.combined_parameter_schema['required'] if r not in self.const_values]
                
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
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[Union[TextContent, ImageContent, EmbeddedResource]]:
            """
            Handle a tool call by invoking the corresponding endpoint.
            
            Args:
                name: The name of the tool (operation_id)
                arguments: The tool arguments
                
            Returns:
                List of content objects (TextContent, ImageContent, or EmbeddedResource)
            """
            logger.info(f"Tool call received: {name}")
            logger.info(f"Tool arguments: {json.dumps(arguments, indent=2, default=str)}")
            
            try:
                # Find the corresponding endpoint
                if name not in self.simple_endpoints:
                    logger.error(f"Tool not found: {name}")
                    return [TextContent(type="text", text=f"Tool not found: {name}")]
                
                endpoint = self.simple_endpoints[name]
                logger.info(f"Invoking endpoint: {endpoint.method.upper()} {endpoint.path}")
                
                # Create an endpoint invoker
                invoker = EndpointInvoker(endpoint)
                
                # Invoke the endpoint with the provided parameters and const values
                logger.info(f"Sending request to: {self.server_url or '[default server]'}")
                
                # Merge const values with provided arguments
                merged_arguments = {**arguments}
                for param_name, value in self.const_values.items():
                    if param_name in endpoint.combined_parameter_schema.get('properties', {}):
                        merged_arguments[param_name] = value
                
                response = invoker.invoke_with_params(
                    params=merged_arguments,
                    server_url=self.server_url,
                    bearer_token=self.bearer_token,
                    headers=self.additional_headers
                )
                
                logger.info(f"Response status code: {response.status_code}")
                
                # Process the response
                try:
                    result = response.json()
                    logger.info(f"Received JSON response of size: {len(json.dumps(result))} bytes")
                    # Format the result as a pretty JSON string
                    formatted_result = json.dumps(result, indent=2, default=str)
                    return [TextContent(type="text", text=formatted_result)]
                except ValueError:
                    # Not JSON content
                    text_response = response.text
                    logger.info(f"Received text response of size: {len(text_response)} bytes")
                    return [TextContent(type="text", text=text_response)]
                    
            except Exception as e:
                logger.error(f"Error calling tool {name}: {e}")
                error_trace = traceback.format_exc()
                logger.error(f"Traceback: {error_trace}")
                return [TextContent(type="text", text=f"Error calling tool {name}: {str(e)}\n{error_trace}")]

        # For the purposes of testing, return the handlers so they can be manually invoked by tests
        return { "list_tools": list_tools, "call_tool": call_tool }

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
    openapi_spec: str,  
    server_name: str = "OpenAPI-MCP-Server",
    server_url: Optional[str] = None,
    bearer_token: Optional[str] = None,
    additional_headers: Optional[Dict[str, str]] = None,
    include_pattern: Optional[str] = None,
    exclude_pattern: Optional[str] = None,
    cursor_mode: bool = False,
    const_values: Optional[Dict[str, str]] = None
):
    """
    Run an OpenAPI MCP Server with the given parameters.
    
    Args:
        openapi_spec: Path or URL to the OpenAPI spec file
        server_name: Name for the MCP server
        server_url: Base URL for API calls (overrides servers in spec)
        bearer_token: Optional bearer token for authenticated requests
        additional_headers: Optional dictionary of additional headers to include in all requests
        include_pattern: Optional regex pattern to filter endpoints by path (e.g., "/admin/.*" or "/api/v1")
        exclude_pattern: Optional regex pattern to exclude endpoints by path (e.g., "/internal/.*")
        cursor_mode: Whether to enable Cursor-specific quirk handling
        const_values: Optional dictionary of parameter names and their constant values
    """
    logger.info(f"Starting OpenAPI MCP Server: {server_name}")
    logger.info(f"OpenAPI spec: {openapi_spec}")
    logger.info(f"Server URL: {server_url}")
    if include_pattern:
        logger.info(f"Include pattern: {include_pattern}")
    if exclude_pattern:
        logger.info(f"Exclude pattern: {exclude_pattern}")
    if additional_headers:
        logger.info(f"Additional headers: {json.dumps(additional_headers)}")
    
    server = OpenAPIMCPServer(
        server_name=server_name,
        openapi_spec=openapi_spec,
        server_url=server_url,
        bearer_token=bearer_token,
        additional_headers=additional_headers,
        include_pattern=include_pattern,
        exclude_pattern=exclude_pattern,
        cursor_mode=cursor_mode,
        const_values=const_values
    )
    
    logger.info("Server initialized, starting main loop")
    asyncio.run(server.run())


def main():
    try:
        args, additional_headers, const_values = parse_args("Start an MCP server based on an OpenAPI/Swagger specification")
        
        run_server(
            openapi_spec=args.spec,
            server_name=args.name,
            server_url=args.server_url,
            bearer_token=args.bearer_token,
            additional_headers=additional_headers if additional_headers else None,
            include_pattern=args.include_pattern,
            exclude_pattern=args.exclude_pattern,
            cursor_mode=args.cursor,
            const_values=const_values
        )
    except Exception as e:
        logger.error(f"Server failed to start: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    main()