from openapi_mcp_server import OpenAPIMCPServer
import asyncio
import json
import tempfile
import os

# A sample OpenAPI spec with detailed descriptions
detailed_spec = {
    "openapi": "3.0.0",
    "info": {
        "title": "Sample API with Detailed Descriptions",
        "version": "1.0.0",
        "description": "This is a sample API to test detailed descriptions"
    },
    "paths": {
        "/users": {
            "get": {
                "operationId": "listUsers",
                "summary": "List all users",
                "description": "Returns a paginated list of all users in the system. The response can be filtered and sorted.",
                "parameters": [
                    {
                        "name": "limit",
                        "in": "query",
                        "description": "Maximum number of results to return per page (1-100)",
                        "schema": {"type": "integer", "minimum": 1, "maximum": 100}
                    },
                    {
                        "name": "offset",
                        "in": "query",
                        "description": "Number of results to skip for pagination",
                        "schema": {"type": "integer", "minimum": 0}
                    },
                    {
                        "name": "sort_by",
                        "in": "query",
                        "description": "Field to sort results by (name, email, created_at, updated_at)",
                        "schema": {"type": "string", "enum": ["name", "email", "created_at", "updated_at"]}
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Successfully retrieved users"
                    }
                }
            },
            "post": {
                "operationId": "createUser",
                "summary": "Create a new user",
                "description": "Creates a new user in the system with the provided information. Requires admin privileges.",
                "requestBody": {
                    "description": "User information",
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "required": ["name", "email"],
                                "properties": {
                                    "name": {
                                        "type": "string",
                                        "description": "The user's full name"
                                    },
                                    "email": {
                                        "type": "string",
                                        "format": "email",
                                        "description": "The user's email address (must be unique)"
                                    },
                                    "age": {
                                        "type": "integer",
                                        "minimum": 13,
                                        "description": "The user's age (must be at least 13)"
                                    },
                                    "role": {
                                        "type": "string",
                                        "enum": ["user", "admin", "guest"],
                                        "default": "user",
                                        "description": "The user's role in the system"
                                    }
                                }
                            }
                        }
                    }
                },
                "responses": {
                    "201": {
                        "description": "User created successfully"
                    }
                }
            }
        },
        "/users/{userId}": {
            "get": {
                "operationId": "getUser",
                "summary": "Get user by ID",
                "description": "Returns detailed information about a specific user identified by their unique ID",
                "parameters": [
                    {
                        "name": "userId",
                        "in": "path",
                        "required": True,
                        "description": "The unique identifier of the user",
                        "schema": {"type": "string", "format": "uuid"}
                    },
                    {
                        "name": "include_details",
                        "in": "query",
                        "description": "Whether to include additional user details in the response",
                        "schema": {"type": "boolean", "default": False}
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Successfully retrieved user"
                    }
                }
            }
        }
    }
}

def format_tool_description(endpoint):
    """
    Format a comprehensive tool description from the endpoint's summary and description.
    
    Args:
        endpoint: The SimpleEndpoint object
        
    Returns:
        A formatted description string
    """
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
        
    return description

async def test():
    # Write the spec to a temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
        json.dump(detailed_spec, temp_file)
        temp_file_path = temp_file.name
    
    try:
        # Create the server with our detailed spec
        server = OpenAPIMCPServer('Test Server', temp_file_path)
        
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
            
            # Create the tool definition using our helper function
            description = format_tool_description(endpoint)
            
            from mcp.types import Tool
            
            tool = Tool(
                name=operation_id,
                description=description,
                inputSchema=input_schema
            )
            tools.append(tool)
        
        # Print information about all the tools
        print(f"Found {len(tools)} tools\n")
        
        for tool in tools:
            print(f"Tool: {tool.name}")
            print(f"Description: {tool.description}")
            print("Schema properties:")
            
            for param_name, param_schema in tool.inputSchema.get('properties', {}).items():
                desc = param_schema.get('description', 'No description')
                required = "required" if param_name in tool.inputSchema.get('required', []) else "optional"
                print(f"  - {param_name} ({required}): {desc}")
            
            print()
    finally:
        # Clean up the temporary file
        if os.path.exists(temp_file_path):
            os.unlink(temp_file_path)

if __name__ == "__main__":
    asyncio.run(test()) 