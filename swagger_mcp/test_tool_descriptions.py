from openapi_mcp_server import OpenAPIMCPServer
import asyncio
import json

async def test():
    # Create the server
    server = OpenAPIMCPServer('Test Server', 'https://petstore.swagger.io/v2/swagger.json')
    
    # Register the handlers (this already happens in __init__)
    # We need to access the tools a different way
    
    # Extract the tools from the server's simple_endpoints
    tools = []
    
    for operation_id, endpoint in server.simple_endpoints.items():
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
        
        # Create the tool definition (similar to what happens in _register_handlers)
        from mcp.types import Tool
        
        description = ""
        # Use summary as a title if available
        if endpoint.summary:
            description = endpoint.summary
        else:
            description = f"{endpoint.method.upper()} {endpoint.path}"
        
        # Add the full description if available
        if endpoint.description and endpoint.description.strip():
            # Add newline only if we already have content
            if description:
                description += "\n\n"
            description += endpoint.description.strip()
        
        tool = Tool(
            name=operation_id,
            description=description,
            inputSchema=input_schema
        )
        tools.append(tool)
    
    # Print information about the first 5 tools
    print(f"Found {len(tools)} tools\n")
    
    for tool in tools[:5]:
        print(f"Tool: {tool.name}")
        print(f"Description: {tool.description}")
        print("Schema properties:")
        
        for param_name, param_schema in tool.inputSchema.get('properties', {}).items():
            desc = param_schema.get('description', 'No description')
            print(f"  - {param_name}: {desc}")
        
        print()

if __name__ == "__main__":
    asyncio.run(test()) 