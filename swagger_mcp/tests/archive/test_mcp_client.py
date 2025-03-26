#!/usr/bin/env python3
"""
Simple MCP client for testing tool invocation.
This connects to an MCP server and attempts to invoke tools.
"""
import json
import asyncio
import sys
import subprocess
import os
from typing import Dict, Any, List, Optional

from mcp import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters

async def main():
    server_process = None
    try:
        print("Connecting to MCP server...")
        
        # Start the server in a subprocess
        server_process = subprocess.Popen(
            ["python", "openapi_mcp_server.py", "http://localhost:9000/openapi.json", 
             "--name", "ProductAPI-MCP-Server", "--url", "http://localhost:9000"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Give the server a moment to start
        await asyncio.sleep(2)
        
        # Create the client session
        server_params = StdioServerParameters(
            command="python openapi_mcp_server.py http://localhost:9000/openapi.json",
            cwd=os.getcwd()
        )
        
        async with stdio_client(server_params) as (read_stream, write_stream):
            session = ClientSession(read_stream, write_stream)
            
            # Initialize the session
            init_result = await session.initialize(client_capabilities={})
            print(f"Connected to server: {init_result.server_info.name} v{init_result.server_info.version}")
            
            # List available tools
            tools_result = await session.list_tools()
            print(f"Found {len(tools_result.tools)} tools:")
            
            for tool in tools_result.tools:
                print(f"- {tool.name}: {tool.description}")
            
            # Try to call a tool
            if tools_result.tools:
                tool = tools_result.tools[0]  # Get the first tool
                print(f"\nTrying to call tool: {tool.name}")
                
                # Build simple arguments based on required properties
                args = {}
                if hasattr(tool, 'input_schema') and tool.input_schema:
                    schema = tool.input_schema
                    required = schema.get('required', [])
                    properties = schema.get('properties', {})
                    
                    for param_name, param_schema in properties.items():
                        if param_name in required:
                            # Set a default value based on type
                            param_type = param_schema.get('type')
                            if param_type == 'string':
                                args[param_name] = "test_value"
                            elif param_type == 'integer' or param_type == 'number':
                                args[param_name] = 1
                            elif param_type == 'boolean':
                                args[param_name] = True
                            else:
                                args[param_name] = "default"
                
                print(f"Using arguments: {json.dumps(args, indent=2)}")
                
                # Call the tool
                try:
                    tool_result = await session.call_tool(tool.name, args)
                    print(f"Tool response: {json.dumps(tool_result, indent=2)}")
                except Exception as e:
                    print(f"Error calling tool: {e}")
            
            print("\nTest completed.")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        print(traceback.format_exc())
    finally:
        # Clean up if we started a server
        if server_process:
            server_process.terminate()
            print("Server process terminated.")
            
if __name__ == "__main__":
    asyncio.run(main()) 