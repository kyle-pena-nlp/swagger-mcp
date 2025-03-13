import os
import json
import pytest
import asyncio
from unittest.mock import patch, MagicMock, mock_open
from typing import Dict, Any, List

# Import the components we want to test
from openapi_mcp_server import OpenAPIMCPServer
from mcp.types import Tool, ToolParameter, ToolResult

# Sample OpenAPI spec for testing
SAMPLE_OPENAPI_SPEC = {
    "openapi": "3.0.0",
    "info": {
        "title": "Test API",
        "version": "1.0.0"
    },
    "servers": [
        {
            "url": "https://api.example.com/v1"
        }
    ],
    "paths": {
        "/pets": {
            "get": {
                "summary": "List all pets",
                "operationId": "listPets",
                "parameters": [
                    {
                        "name": "limit",
                        "in": "query",
                        "description": "How many items to return",
                        "required": False,
                        "schema": {
                            "type": "integer",
                            "format": "int32"
                        }
                    },
                    {
                        "name": "tags",
                        "in": "query",
                        "description": "Tags to filter by",
                        "required": False,
                        "schema": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            }
                        }
                    }
                ],
                "responses": {
                    "200": {
                        "description": "A list of pets",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "id": {
                                                "type": "integer"
                                            },
                                            "name": {
                                                "type": "string"
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "post": {
                "summary": "Create a pet",
                "operationId": "createPet",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "required": ["name"],
                                "properties": {
                                    "name": {
                                        "type": "string",
                                        "description": "The pet's name"
                                    },
                                    "tag": {
                                        "type": "string",
                                        "description": "Tag for the pet"
                                    }
                                }
                            }
                        }
                    }
                },
                "responses": {
                    "201": {
                        "description": "Created pet object",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "id": {
                                            "type": "integer"
                                        },
                                        "name": {
                                            "type": "string"
                                        },
                                        "tag": {
                                            "type": "string"
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        "/pets/{petId}": {
            "get": {
                "summary": "Get a pet by ID",
                "operationId": "getPetById",
                "parameters": [
                    {
                        "name": "petId",
                        "in": "path",
                        "description": "The ID of the pet to retrieve",
                        "required": True,
                        "schema": {
                            "type": "integer"
                        }
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Pet object",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "id": {
                                            "type": "integer"
                                        },
                                        "name": {
                                            "type": "string"
                                        },
                                        "tag": {
                                            "type": "string"
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "404": {
                        "description": "Pet not found"
                    }
                }
            }
        }
    }
}


@pytest.fixture
def mock_openapi_parser():
    """Create a mock OpenAPIParser."""
    with patch('openapi_mcp_server.OpenAPIParser') as MockParser:
        parser_instance = MockParser.return_value
        # Set up the mock endpoints
        from endpoint import Endpoint
        endpoints = [
            Endpoint(
                path="/pets",
                method="get",
                operation_id="listPets",
                summary="List all pets",
                query_parameters_schema={
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "description": "How many items to return"
                        },
                        "tags": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Tags to filter by"
                        }
                    }
                },
                responses={
                    "200": {
                        "description": "A list of pets",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "id": {"type": "integer"},
                                            "name": {"type": "string"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                servers=[{"url": "https://api.example.com/v1"}]
            ),
            Endpoint(
                path="/pets",
                method="post",
                operation_id="createPet",
                summary="Create a pet",
                request_body_schema={
                    "schema": {
                        "type": "object",
                        "required": ["name"],
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": "The pet's name"
                            },
                            "tag": {
                                "type": "string",
                                "description": "Tag for the pet"
                            }
                        }
                    },
                    "required": True
                },
                request_content_types=["application/json"],
                responses={
                    "201": {
                        "description": "Created pet object",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "id": {"type": "integer"},
                                        "name": {"type": "string"},
                                        "tag": {"type": "string"}
                                    }
                                }
                            }
                        }
                    }
                },
                servers=[{"url": "https://api.example.com/v1"}]
            ),
            Endpoint(
                path="/pets/{petId}",
                method="get",
                operation_id="getPetById",
                summary="Get a pet by ID",
                path_parameters_schema={
                    "type": "object",
                    "properties": {
                        "petId": {
                            "type": "integer",
                            "description": "The ID of the pet to retrieve"
                        }
                    },
                    "required": ["petId"]
                },
                responses={
                    "200": {
                        "description": "Pet object",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "id": {"type": "integer"},
                                        "name": {"type": "string"},
                                        "tag": {"type": "string"}
                                    }
                                }
                            }
                        }
                    },
                    "404": {
                        "description": "Pet not found"
                    }
                },
                servers=[{"url": "https://api.example.com/v1"}]
            )
        ]
        
        parser_instance.get_endpoints.return_value = endpoints
        yield parser_instance


@pytest.fixture
def mock_server():
    """Create a mock Server."""
    with patch('openapi_mcp_server.Server') as MockServer:
        server_instance = MockServer.return_value
        # Store the registered handlers
        server_instance.list_tools_handler = None
        server_instance.call_tool_handler = None
        
        # Mock the decorators
        def list_tools_decorator():
            def decorator(func):
                server_instance.list_tools_handler = func
                return func
            return decorator
        
        def call_tool_decorator():
            def decorator(func):
                server_instance.call_tool_handler = func
                return func
            return decorator
        
        server_instance.list_tools.side_effect = list_tools_decorator
        server_instance.call_tool.side_effect = call_tool_decorator
        
        yield server_instance


@pytest.fixture
def server_with_mocks(mock_openapi_parser, mock_server):
    """Create an OpenAPIMCPServer instance with mocked dependencies."""
    # Mock open to provide our test OpenAPI spec
    spec_json = json.dumps(SAMPLE_OPENAPI_SPEC)
    
    with patch('builtins.open', mock_open(read_data=spec_json)):
        server = OpenAPIMCPServer(
            server_name="test-server",
            openapi_spec_path="fake_path.json",
            server_url="https://api.example.com/v1"
        )
        
        return server


class TestOpenAPIMCPServer:
    """Test the OpenAPIMCPServer class."""
    
    def test_initialization(self, server_with_mocks, mock_openapi_parser, mock_server):
        """Test that the server initializes correctly."""
        assert server_with_mocks.server_name == "test-server"
        assert server_with_mocks.server_url == "https://api.example.com/v1"
        assert mock_openapi_parser.get_endpoints.called
        assert mock_server.list_tools.called
        assert mock_server.call_tool.called
    
    @pytest.mark.asyncio
    async def test_list_tools(self, server_with_mocks, mock_server):
        """Test that list_tools returns the expected tools."""
        # Get the registered list_tools handler
        list_tools_handler = mock_server.list_tools_handler
        assert list_tools_handler is not None
        
        # Call the handler
        tools = await list_tools_handler()
        
        # Verify the result
        assert isinstance(tools, list)
        assert len(tools) == 3  # We have 3 endpoints in our test spec
        
        # Check tool properties
        tool_names = [tool.name for tool in tools]
        assert "listPets" in tool_names
        assert "createPet" in tool_names
        assert "getPetById" in tool_names
        
        # Check parameters for a specific tool
        create_pet_tool = next(tool for tool in tools if tool.name == "createPet")
        param_names = [param.name for param in create_pet_tool.parameters]
        assert "name" in param_names
        assert "tag" in param_names
        
        # Verify a required parameter
        name_param = next(param for param in create_pet_tool.parameters if param.name == "name")
        assert name_param.required is True
    
    @pytest.mark.asyncio
    async def test_call_tool(self, server_with_mocks, mock_server):
        """Test that call_tool invokes endpoints correctly."""
        # Mock the EndpointInvoker
        with patch('openapi_mcp_server.EndpointInvoker') as MockInvoker:
            invoker_instance = MockInvoker.return_value
            mock_response = MagicMock()
            mock_response.json.return_value = {"id": 1, "name": "Fluffy", "tag": "cat"}
            invoker_instance.invoke_with_params.return_value = mock_response
            
            # Get the registered call_tool handler
            call_tool_handler = mock_server.call_tool_handler
            assert call_tool_handler is not None
            
            # Call the handler with sample arguments
            result = await call_tool_handler("getPetById", {"petId": 1})
            
            # Verify the result
            assert isinstance(result, list)
            assert len(result) == 1
            assert isinstance(result[0], ToolResult)
            assert result[0].value == {"id": 1, "name": "Fluffy", "tag": "cat"}
            
            # Verify the invoker was called with correct parameters
            invoker_instance.invoke_with_params.assert_called_once_with(
                params={"petId": 1},
                server_url="https://api.example.com/v1",
                bearer_token=None
            )
    
    @pytest.mark.asyncio
    async def test_call_tool_error_handling(self, server_with_mocks, mock_server):
        """Test that call_tool handles errors correctly."""
        # Mock the EndpointInvoker to raise an exception
        with patch('openapi_mcp_server.EndpointInvoker') as MockInvoker:
            invoker_instance = MockInvoker.return_value
            invoker_instance.invoke_with_params.side_effect = Exception("Test error")
            
            # Get the registered call_tool handler
            call_tool_handler = mock_server.call_tool_handler
            
            # Call the handler with a tool that will cause an error
            result = await call_tool_handler("getPetById", {"petId": 1})
            
            # Verify the result contains an error
            assert isinstance(result, list)
            assert len(result) == 1
            assert result[0].error == "Test error"
    
    @pytest.mark.asyncio
    async def test_call_nonexistent_tool(self, server_with_mocks, mock_server):
        """Test calling a tool that doesn't exist."""
        # Get the registered call_tool handler
        call_tool_handler = mock_server.call_tool_handler
        
        # Call the handler with a non-existent tool
        result = await call_tool_handler("nonExistentTool", {})
        
        # Verify the result contains an error
        assert isinstance(result, list)
        assert len(result) == 1
        assert "Tool not found" in result[0].error


if __name__ == "__main__":
    pytest.main(["-xvs", "test_openapi_mcp_server.py"]) 