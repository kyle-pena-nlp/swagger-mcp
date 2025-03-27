import pytest
import json
import os
import tempfile
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
                        "schema": {
                            "type": "string",
                            "enum": ["name", "email", "created_at", "updated_at"]
                        }
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
                "description": "Creates a new user in the system with the provided information.",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "required": ["name", "email"],
                                "properties": {
                                    "name": {
                                        "type": "string",
                                        "description": "Full name of the user"
                                    },
                                    "email": {
                                        "type": "string",
                                        "format": "email",
                                        "description": "Email address of the user"
                                    }
                                }
                            }
                        }
                    }
                },
                "responses": {
                    "201": {
                        "description": "User successfully created"
                    }
                }
            }
        },
        "/users/{userId}/profile": {
            "put": {
                "operationId": "updateUserProfile",
                "summary": "Update user profile",
                "description": "Updates a user's profile information using multipart form data.",
                "parameters": [
                    {
                        "name": "userId",
                        "in": "path",
                        "required": True,
                        "description": "ID of the user to update",
                        "schema": {
                            "type": "integer"
                        }
                    }
                ],
                "requestBody": {
                    "required": True,
                    "content": {
                        "multipart/form-data": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "displayName": {
                                        "type": "string",
                                        "description": "Display name shown in the UI"
                                    },
                                    "bio": {
                                        "type": "string",
                                        "description": "User's biographical information"
                                    },
                                    "location": {
                                        "type": "string",
                                        "description": "User's geographical location"
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}

@pytest.mark.asyncio
async def test_parameter_descriptions():
    # Create a temporary file to store the OpenAPI spec
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
        json.dump(detailed_spec, temp_file)
        temp_file_path = temp_file.name

    try:
        # Create an instance of OpenAPIMCPServer with our detailed spec
        server = OpenAPIMCPServer(
            server_name="test-server",
            openapi_spec=temp_file_path
        )

        # Get the list_tools handler from _register_handlers
        handlers = server._register_handlers()
        list_tools = handlers["list_tools"]

        # Call list_tools to get the available tools
        tools = await list_tools()

        # Print the tool schemas for debugging
        for tool in tools:
            print(f"\nTool: {tool.name}")
            print(json.dumps(tool.inputSchema, indent=2))

        # Verify we have the expected number of tools
        assert len(tools) == 3, f"Expected 3 tools, got {len(tools)}"

        # Find the listUsers tool
        list_users_tool = next((tool for tool in tools if tool.name == "listUsers"), None)
        assert list_users_tool is not None, "listUsers tool not found"

        # Verify the listUsers tool has the correct parameter descriptions
        properties = list_users_tool.inputSchema["properties"]
        assert "limit" in properties, "limit parameter not found"
        assert properties["limit"]["description"] == "Maximum number of results to return per page (1-100)"
        assert properties["limit"]["type"] == "integer"

        assert "offset" in properties, "offset parameter not found"
        assert properties["offset"]["description"] == "Number of results to skip for pagination"
        assert properties["offset"]["type"] == "integer"

        assert "sort_by" in properties, "sort_by parameter not found"
        assert properties["sort_by"]["description"] == "Field to sort results by (name, email, created_at, updated_at)"
        assert properties["sort_by"]["type"] == "string"

        # Find the createUser tool
        create_user_tool = next((tool for tool in tools if tool.name == "createUser"), None)
        assert create_user_tool is not None, "createUser tool not found"

        # Verify the createUser tool has the correct request body parameter descriptions
        properties = create_user_tool.inputSchema["properties"]
        assert "name" in properties, "name parameter not found"
        assert properties["name"]["description"] == "Full name of the user"
        assert properties["name"]["type"] == "string"

        assert "email" in properties, "email parameter not found"
        assert properties["email"]["description"] == "Email address of the user"
        assert properties["email"]["type"] == "string"

        # Find the updateUserProfile tool
        update_profile_tool = next((tool for tool in tools if tool.name == "updateUserProfile"), None)
        assert update_profile_tool is not None, "updateUserProfile tool not found"

        # Verify the updateUserProfile tool has the correct multipart form data parameter descriptions
        properties = update_profile_tool.inputSchema["properties"]

        assert "userId" in properties, "userId parameter not found"
        assert properties["userId"]["description"] == "ID of the user to update"
        assert properties["userId"]["type"] == "integer"

        assert "displayName" in properties, "displayName parameter not found"
        assert properties["displayName"]["description"] == "Display name shown in the UI"
        assert properties["displayName"]["type"] == "string"

        assert "bio" in properties, "bio parameter not found"
        assert properties["bio"]["description"] == "User's biographical information"
        assert properties["bio"]["type"] == "string"

        assert "location" in properties, "location parameter not found"
        assert properties["location"]["description"] == "User's geographical location"
        assert properties["location"]["type"] == "string"

    finally:
        # Clean up the temporary file
        os.unlink(temp_file_path)
