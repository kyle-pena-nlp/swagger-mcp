import pytest
from unittest.mock import patch, MagicMock
from swagger_mcp.openapi_mcp_server import OpenAPIMCPServer

class TestRequestBodyVariables:
    @pytest.fixture
    def server(self):
        # Define a simple OpenAPI spec with request body
        openapi_spec = {
            "openapi": "3.0.0",
            "info": {
                "title": "Pet API",
                "version": "1.0.0"
            },
            "servers": [{"url": "https://api.example.com"}],
            "paths": {
                "/pets": {
                    "post": {
                        "operationId": "createPet",
                        "summary": "Create a new pet",
                        "requestBody": {
                            "required": True,
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "required": ["name", "type"],
                                        "properties": {
                                            "name": {
                                                "type": "string"
                                            },
                                            "type": {
                                                "type": "string",
                                                "enum": ["dog", "cat", "bird"]
                                            },
                                            "age": {
                                                "type": "integer",
                                                "minimum": 0
                                            },
                                            "tags": {
                                                "type": "array",
                                                "items": {
                                                    "type": "string"
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        },
                        "responses": {
                            "201": {
                                "description": "Pet created successfully"
                            }
                        }
                    }
                }
            }
        }
        
        server = OpenAPIMCPServer('Test Server', openapi_spec)
        return server

    @pytest.mark.asyncio
    @patch('swagger_mcp.endpoint_invoker.requests.request')
    async def test_request_body_with_required_fields(self, mock_request, server):
        # Setup mock response
        mock_response = MagicMock()
        mock_request.return_value = mock_response

        # Get the call_tool handler
        handlers = server._register_handlers()
        call_tool = handlers["call_tool"]

        # Call the endpoint with required fields
        await call_tool("createPet", {
            "name": "Fluffy",
            "type": "dog"
        })

        # Verify the request was made with correct parameters
        mock_request.assert_called_once()
        call_args = mock_request.call_args[1]
        
        # Check that request body was properly included
        assert "json" in call_args
        assert call_args["json"]["name"] == "Fluffy"
        assert call_args["json"]["type"] == "dog"

    @pytest.mark.asyncio
    @patch('swagger_mcp.endpoint_invoker.requests.request')
    async def test_request_body_with_all_fields(self, mock_request, server):
        # Setup mock response
        mock_response = MagicMock()
        mock_request.return_value = mock_response

        # Get the call_tool handler
        handlers = server._register_handlers()
        call_tool = handlers["call_tool"]

        # Call the endpoint with all fields
        await call_tool("createPet", {
            "name": "Whiskers",
            "type": "cat",
            "age": 5,
            "tags": ["friendly", "indoor"]
        })

        # Verify the request was made with correct parameters
        mock_request.assert_called_once()
        call_args = mock_request.call_args[1]
        
        # Check that all fields were properly included
        assert "json" in call_args
        assert call_args["json"]["name"] == "Whiskers"
        assert call_args["json"]["type"] == "cat"
        assert call_args["json"]["age"] == 5
        assert call_args["json"]["tags"] == ["friendly", "indoor"]