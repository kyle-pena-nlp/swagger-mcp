#!/usr/bin/env python3
"""
Simple test script for checking MCP tool generation and return values.
"""
import json
import asyncio
import sys
import inspect
from typing import Dict, Any, List

from openapi_mcp_server import OpenAPIMCPServer

async def test_server_tools():
    """Test the server's tool generation and invocation."""
    print("Creating MCP server instance...")
    server = OpenAPIMCPServer(
        server_name="Test-MCP-Server",
        openapi_spec="http://localhost:9000/openapi.json",
        server_url="http://localhost:9000"
    )
    
    # Directly access the _register_handlers method to get the handlers
    # This is a bit of a hack but it helps us test the functionality
    server._register_handlers()
    
    # We can inspect the server object to find how to access the handlers
    print("\nDirectly calling list_tools and call_tool inside a new instance")
    
    # Get a reference to the list_tools and call_tool handlers
    # These will be in the server._handlers dictionary or similar
    for method_name in dir(server):
        if method_name.startswith('_') and not method_name.startswith('__'):
            # Skip special methods
            continue
        
        # Try to find any decorated methods
        method = getattr(server, method_name, None)
        if callable(method):
            print(f"Found method: {method_name}")
    
    # Since we can't easily get the handlers, let's recreate them and use them
    async def list_tools_test():
        # Directly create the OpenAPIMCPServer and run the list_tools handler
        print("\nCreating a new server instance and running _register_handlers...")
        # Get the source code of _register_handlers to extract the list_tools implementation
        source = inspect.getsource(server._register_handlers)
        print(f"Found _register_handlers method with {len(source)} characters")
        
        # Extract the async list_tools function
        list_tools_start = source.find("@self.server.list_tools()")
        if list_tools_start == -1:
            print("Could not find list_tools implementation in source")
            return []
        
        # Create a new instance and directly access the created tools
        new_server = OpenAPIMCPServer(
            server_name="Test-MCP-Server-Direct",
            openapi_spec="http://localhost:9000/openapi.json",
            server_url="http://localhost:9000"
        )
        
        # Get all the tools from the simple_endpoints
        tools = []
        print(f"Server has {len(new_server.simple_endpoints)} endpoints")
        for operation_id, endpoint in new_server.simple_endpoints.items():
            # Skip deprecated endpoints
            if endpoint.deprecated:
                continue
            
            # Create the tool definition like in the server code
            from mcp.types import Tool
            
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
            print(f"Added tool: {operation_id} ({endpoint.method.upper()} {endpoint.path})")
        
        return tools
    
    # Call our test function to get the tools
    tools = await list_tools_test()
    print(f"Found {len(tools)} tools:")
    
    # Print tool information
    for tool in tools:
        print(f"- {tool.name}: {tool.description}")
        
    # Try to manually call a tool using the endpoint_invoker directly
    if tools and hasattr(server, 'simple_endpoints'):
        test_tool = tools[0]  # Get the first tool
        print(f"\nTrying to invoke endpoint for tool: {test_tool.name}")
        
        # Build arguments
        args = {}
        if test_tool.input_schema and "properties" in test_tool.input_schema:
            required = test_tool.input_schema.get("required", [])
            for param_name, prop in test_tool.input_schema["properties"].items():
                if param_name in required:
                    if prop.get("type") == "string":
                        args[param_name] = "test_value"
                    elif prop.get("type") in ["integer", "number"]:
                        args[param_name] = 1
                    elif prop.get("type") == "boolean":
                        args[param_name] = True
                    else:
                        args[param_name] = None
        
        print(f"Using arguments: {json.dumps(args, indent=2)}")
        
        # Directly use the EndpointInvoker
        try:
            from endpoint_invoker import EndpointInvoker
            
            # Get the endpoint from the server
            endpoint = server.simple_endpoints[test_tool.name]
            
            # Create an endpoint invoker
            invoker = EndpointInvoker(endpoint)
            
            # Invoke the endpoint
            response = invoker.invoke_with_params(
                params=args,
                server_url=server.server_url
            )
            
            # Process the response
            print(f"Response status code: {response.status_code}")
            
            try:
                result = response.json()
                print(f"Response JSON: {json.dumps(result, indent=2)}")
            except:
                print(f"Response text: {response.text}")
                
        except Exception as e:
            print(f"Error invoking endpoint: {e}")
            import traceback
            print(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(test_server_tools()) 