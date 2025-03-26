import pytest
from unittest.mock import patch, MagicMock
from swagger_mcp.openapi_mcp_server import OpenAPIMCPServer

class TestFormDataVariables:
    @pytest.fixture
    def server(self):
        # Define a simple OpenAPI spec with multipart form data
        openapi_spec = {
            "openapi": "3.0.0",
            "info": {
                "title": "File Upload API",
                "version": "1.0.0"
            },
            "servers": [{"url": "https://api.example.com"}],
            "paths": {
                "/upload": {
                    "post": {
                        "operationId": "uploadFile",
                        "summary": "Upload a file with metadata",
                        "requestBody": {
                            "required": True,
                            "content": {
                                "multipart/form-data": {
                                    "schema": {
                                        "type": "object",
                                        "required": ["description"],
                                        "properties": {
                                            "description": {
                                                "type": "string"
                                            },
                                            "tags": {
                                                "type": "array",
                                                "items": {"type": "string"}
                                            }
                                        }
                                    }
                                }
                            }
                        },
                        "responses": {
                            "200": {
                                "description": "File uploaded successfully"
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
    async def test_multipart_form_data(self, mock_request, server):
        # Setup mock response
        mock_response = MagicMock()
        mock_request.return_value = mock_response

        # Get the call_tool handler
        handlers = server._register_handlers()
        call_tool = handlers["call_tool"]

        # Call the endpoint with mixed form data (file and array field)
        await call_tool("uploadFile", {
            "description": "Test with tags",
            "tags": ["test", "example"]
        })

        # Verify the request was made with all fields
        mock_request.assert_called_once()
        call_args = mock_request.call_args[1]
        
        # Check that both file and regular form fields are present
        assert "data" in call_args
        assert call_args["data"]["description"] == "Test with tags"
        assert call_args["data"]["tags"] == ["test", "example"]

    @pytest.mark.asyncio
    @patch('swagger_mcp.endpoint_invoker.requests.request')
    async def test_multipart_form_data_omitting_optional_field(self, mock_request, server):
        # Setup mock response
        mock_response = MagicMock()
        mock_request.return_value = mock_response

        # Get the call_tool handler
        handlers = server._register_handlers()
        call_tool = handlers["call_tool"]

        # Call the endpoint with mixed form data (file and array field)
        await call_tool("uploadFile", {
            "description": "Test with tags"
        })

        # Verify the request was made with all fields
        mock_request.assert_called_once()
        call_args = mock_request.call_args[1]
        
        # Check that both file and regular form fields are present
        assert "data" in call_args
        assert call_args["data"]["description"] == "Test with tags"