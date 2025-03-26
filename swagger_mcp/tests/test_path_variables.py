import pytest
from unittest.mock import patch, MagicMock
from swagger_mcp.openapi_mcp_server import OpenAPIMCPServer

class TestPathVariables:
    @pytest.fixture
    def server(self):
        # Define a simple OpenAPI spec with path parameters
        openapi_spec = {
            "openapi": "3.0.0",
            "info": {
                "title": "Pet API",
                "version": "1.0.0"
            },
            "servers": [{"url": "https://api.example.com"}],
            "paths": {
                "/pets/{petId}/toys/{toyId}": {
                    "get": {
                        "operationId": "getPetToy",
                        "summary": "Get a specific toy for a pet",
                        "parameters": [
                            {
                                "name": "petId",
                                "in": "path",
                                "required": True,
                                "schema": {
                                    "type": "integer",
                                    "format": "int64"
                                }
                            },
                            {
                                "name": "toyId",
                                "in": "path",
                                "required": True,
                                "schema": {
                                    "type": "string"
                                }
                            }
                        ],
                        "responses": {
                            "200": {
                                "description": "Pet toy found"
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
    async def test_path_parameter_substitution(self, mock_request, server):
        # Setup mock response
        mock_response = MagicMock()
        mock_request.return_value = mock_response

        # Get the call_tool handler
        handlers = server._register_handlers()
        call_tool = handlers["call_tool"]

        # Call the endpoint with path parameters
        await call_tool("getPetToy", {
            "petId": 123,
            "toyId": "ball"
        })

        # Verify the request was made with the correct URL
        mock_request.assert_called_once()
        call_args = mock_request.call_args
        
        # Check that path parameters were correctly substituted
        assert call_args[1]["url"].endswith("/pets/123/toys/ball")