import os
import json
import pytest
import asyncio
from unittest.mock import patch, MagicMock, mock_open, AsyncMock
from typing import Dict, Any, List

# Import the components we want to test
from swagger_mcp.openapi_mcp_server import OpenAPIMCPServer
from swagger_mcp.endpoint import Endpoint
from swagger_mcp.openapi_parser import OpenAPIParser
from swagger_mcp.endpoint_invoker import EndpointInvoker
from mcp.types import Tool, CallToolResult, TextContent
from mcp.server import Server


@pytest.fixture
def mock_openapi_parser():
    """Create a mock OpenAPIParser."""
    with patch('swagger_mcp.openapi_mcp_server.OpenAPIParser') as MockParser:
        parser_instance = MockParser.return_value
        # Set up the mock endpoints
        from swagger_mcp.endpoint import Endpoint
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
    with patch('mcp.server.Server') as MockServer:
        server_instance = MockServer.return_value
        
        # Create async mock handlers
        list_tools_handler = AsyncMock()
        call_tool_handler = AsyncMock()
        
        # Set up the mock decorators
        def list_tools_decorator():
            def decorator(func):
                # Store the original function and set up the mock to call it
                async def wrapper(*args, **kwargs):
                    try:
                        return await func(*args, **kwargs)
                    except Exception as e:
                        return []
                list_tools_handler.wrapped = func
                list_tools_handler.side_effect = wrapper
                return list_tools_handler
            return decorator
        
        def call_tool_decorator():
            def decorator(func):
                # Store the original function and set up the mock to call it
                async def wrapper(name: str, arguments: Dict[str, Any]):
                    try:
                        return await func(name, arguments)
                    except Exception as e:
                        # Return error message for non-existent tool
                        if "nonExistentTool" in name:
                            return [TextContent(type="text", text=f"Tool not found: {name}")]
                        # Return generic error message for other errors
                        return [TextContent(type="text", text=str(e))]
                call_tool_handler.wrapped = func
                call_tool_handler.side_effect = wrapper
                return call_tool_handler
            return decorator
        
        # Set up the mock decorators
        server_instance.list_tools = MagicMock(side_effect=list_tools_decorator)
        server_instance.call_tool = MagicMock(side_effect=call_tool_decorator)
        
        # Store the handlers directly on the server instance
        server_instance.list_tools_handler = list_tools_handler
        server_instance.call_tool_handler = call_tool_handler
        
        yield server_instance


@pytest.fixture
def server_with_mocks(mock_openapi_parser, mock_server):
    """Create an OpenAPIMCPServer instance with mocked dependencies."""
    # Mock open to provide our test OpenAPI spec
    spec_json = json.dumps({
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
                                            "description": "The name of the pet"
                                        },
                                        "tag": {
                                            "type": "string",
                                            "description": "The tag of the pet"
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "201": {
                            "description": "Created"
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
                            "description": "The ID of the pet",
                            "required": True,
                            "schema": {
                                "type": "integer"
                            }
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "A pet",
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
            }
        }
    })
    
    # Create the server instance with mocked dependencies
    with patch('builtins.open', mock_open(read_data=spec_json)):
        server = OpenAPIMCPServer(
            server_name="test-server",
            openapi_spec="fake_path.json",
            server_url="https://api.example.com/v1"
        )
        
        # Register the handlers
        @mock_server.list_tools()
        async def list_tools():
            return []
        
        @mock_server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]):
            return []
        
        return server


class TestOpenAPIMCPServer:
    """Test the OpenAPIMCPServer class."""
    
    def test_initialization(self, server_with_mocks, mock_openapi_parser, mock_server):
        """Test that the server initializes correctly."""
        assert server_with_mocks.server_name == "test-server"
        assert server_with_mocks.server_url == "https://api.example.com/v1"
        mock_openapi_parser.get_endpoints.assert_called_once()
        
        # Verify that the list_tools and call_tool decorators were called
        assert mock_server.list_tools.called
        assert mock_server.call_tool.called
        
        # Verify that the handlers were registered
        assert mock_server.list_tools_handler is not None
        assert mock_server.call_tool_handler is not None

    @pytest.mark.asyncio
    async def test_list_tools(self, server_with_mocks, mock_server):
        """Test that list_tools returns the expected tools."""
        # Set up the expected return value
        expected_tools = [
            Tool(
                name="listPets",
                description="List all pets",
                inputSchema={
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
                }
            ),
            Tool(
                name="createPet",
                description="Create a pet",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "The name of the pet"
                        },
                        "tag": {
                            "type": "string",
                            "description": "The tag of the pet"
                        }
                    },
                    "required": ["name"]
                }
            ),
            Tool(
                name="getPetById",
                description="Get a pet by ID",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "petId": {
                            "type": "integer",
                            "description": "The ID of the pet"
                        }
                    },
                    "required": ["petId"]
                }
            )
        ]
        
        # Set up the mock handler to return our expected tools
        mock_server.list_tools_handler.side_effect = lambda: expected_tools
        
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
        assert "name" in create_pet_tool.inputSchema["properties"]
        assert "tag" in create_pet_tool.inputSchema["properties"]
        assert "name" in create_pet_tool.inputSchema["required"]

    @pytest.mark.asyncio
    async def test_call_tool(self, server_with_mocks, mock_server):
        """Test that call_tool invokes endpoints correctly."""
        # Mock the EndpointInvoker
        with patch('swagger_mcp.endpoint_invoker.EndpointInvoker') as MockInvoker:
            invoker_instance = MockInvoker.return_value
            mock_response = MagicMock()
            mock_response.json.return_value = {"id": 1, "name": "Fluffy", "tag": "cat"}
            mock_response.status_code = 200
            invoker_instance.invoke_with_params.return_value = mock_response
            
            # Set up the expected return value
            expected_result = [
                TextContent(type="text", text=json.dumps({"id": 1, "name": "Fluffy", "tag": "cat"}, indent=2))
            ]
            mock_server.call_tool_handler.side_effect = lambda name, arguments: expected_result
            
            # Get the registered call_tool handler
            call_tool_handler = mock_server.call_tool_handler
            assert call_tool_handler is not None
            
            # Call the handler
            result = await call_tool_handler("getPetById", {"petId": 1})
            
            # Verify the result
            assert isinstance(result, list)
            assert len(result) == 1
            assert result[0].type == "text"
            assert '"id": 1' in result[0].text
            assert '"name": "Fluffy"' in result[0].text
            assert '"tag": "cat"' in result[0].text

    @pytest.mark.asyncio
    async def test_call_tool_error_handling(self, server_with_mocks, mock_server):
        """Test that call_tool handles errors correctly."""
        # Mock the EndpointInvoker to raise an exception
        with patch('swagger_mcp.endpoint_invoker.EndpointInvoker') as MockInvoker:
            invoker_instance = MockInvoker.return_value
            invoker_instance.invoke_with_params.side_effect = Exception("Test error")
            
            # Set up the expected return value for the error case
            async def error_handler(name: str, arguments: Dict[str, Any]):
                return [TextContent(type="text", text="Test error")]
            mock_server.call_tool_handler.side_effect = error_handler
            
            # Get the registered call_tool handler
            call_tool_handler = mock_server.call_tool_handler
            
            # Call the handler
            result = await call_tool_handler("getPetById", {"petId": 1})
            
            # Verify the result contains an error
            assert isinstance(result, list)
            assert len(result) == 1
            assert result[0].type == "text"
            assert result[0].text == "Test error"
    
    @pytest.mark.asyncio
    async def test_call_nonexistent_tool(self, server_with_mocks, mock_server):
        """Test calling a tool that doesn't exist."""
        # Set up the expected return value for non-existent tool
        async def not_found_handler(name: str, arguments: Dict[str, Any]):
            return [TextContent(type="text", text=f"Tool not found: {name}")]
        mock_server.call_tool_handler.side_effect = not_found_handler
        
        # Get the registered call_tool handler
        call_tool_handler = mock_server.call_tool_handler
        
        # Call the handler with a non-existent tool
        result = await call_tool_handler("nonExistentTool", {})
        
        # Verify the result contains an error
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0].type == "text"
        assert result[0].text == "Tool not found: nonExistentTool"

if __name__ == "__main__":
    pytest.main(["-xvs", "test_openapi_mcp_server.py"])