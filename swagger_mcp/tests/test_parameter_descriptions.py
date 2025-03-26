import pytest
import json
import os
from swagger_mcp.openapi_mcp_server import OpenAPIMCPServer
from mcp.types import Tool

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

@pytest.fixture
def spec_file(tmp_path):
    """Create a temporary file with the detailed spec."""
    spec_path = tmp_path / "detailed_spec.json"
    with open(spec_path, 'w') as f:
        json.dump(detailed_spec, f)
    return str(spec_path)

@pytest.fixture
def server(spec_file):
    """Create an OpenAPIMCPServer instance with the detailed spec."""
    return OpenAPIMCPServer('Test Server', spec_file)

@pytest.fixture
def tools(server):
    """Extract tools from the server's endpoints."""
    result = []
    for operation_id, endpoint in server.simple_endpoints.items():
        if endpoint.deprecated:
            continue
            
        input_schema = {
            "type": "object",
            "properties": {},
            "required": []
        }
        
        if endpoint.combined_parameter_schema and 'properties' in endpoint.combined_parameter_schema:
            input_schema["properties"] = endpoint.combined_parameter_schema['properties']
            if 'required' in endpoint.combined_parameter_schema:
                input_schema["required"] = endpoint.combined_parameter_schema['required']
        
        description = format_tool_description(endpoint)
        
        tool = Tool(
            name=operation_id,
            description=description,
            inputSchema=input_schema
        )
        result.append(tool)
    return result

def test_tools_creation(tools):
    """Test that tools are created successfully."""
    assert len(tools) > 0, "No tools were created"
    
    # Test specific tools we expect to find
    tool_names = {tool.name for tool in tools}
    expected_tools = {'listUsers', 'createUser', 'getUser'}
    assert expected_tools.issubset(tool_names), f"Missing expected tools. Found: {tool_names}"

def test_tool_descriptions(tools):
    """Test that tool descriptions are properly formatted."""
    for tool in tools:
        assert tool.description, f"Tool {tool.name} has no description"
        if tool.name == 'listUsers':
            assert "paginated list" in tool.description.lower(), "listUsers description should mention pagination"
        elif tool.name == 'createUser':
            assert "admin privileges" in tool.description.lower(), "createUser description should mention admin privileges"
        elif tool.name == 'getUser':
            assert "unique id" in tool.description.lower(), "getUser description should mention user ID"

def test_tool_parameters(tools):
    """Test that tool parameters have proper descriptions and constraints."""
    for tool in tools:
        assert tool.inputSchema, f"Tool {tool.name} has no input schema"
        properties = tool.inputSchema.get('properties', {})
        
        if tool.name == 'listUsers':
            assert 'limit' in properties, "listUsers should have a limit parameter"
            assert 'offset' in properties, "listUsers should have an offset parameter"
            assert properties['limit'].get('maximum') == 100, "limit should have a maximum of 100"
            
        elif tool.name == 'createUser':
            assert 'name' in properties, "createUser should have a name parameter"
            assert 'email' in properties, "createUser should have an email parameter"
            assert 'name' in tool.inputSchema.get('required', []), "name should be required"
            assert 'email' in tool.inputSchema.get('required', []), "email should be required"
            
        elif tool.name == 'getUser':
            assert 'userId' in properties, "getUser should have a userId parameter"
            assert 'userId' in tool.inputSchema.get('required', []), "userId should be required"
            assert properties['userId'].get('format') == 'uuid', "userId should be a UUID format"