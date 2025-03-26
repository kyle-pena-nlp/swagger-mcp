import pytest
from unittest.mock import patch, MagicMock
from swagger_mcp.openapi_mcp_server import OpenAPIMCPServer

class TestMixedEndpointVariables:
    @pytest.fixture
    def server(self):
        # Define an OpenAPI spec with multiple endpoints using different combinations
        openapi_spec = {
            "openapi": "3.0.0",
            "info": {
                "title": "Pet API",
                "version": "1.0.0"
            },
            "servers": [{"url": "https://api.example.com"}],
            "paths": {
                # Endpoint with path params and form data (text fields only)
                "/pets/{petId}/details": {
                    "post": {
                        "operationId": "updatePetDetails",
                        "summary": "Update pet details",
                        "parameters": [
                            {
                                "name": "petId",
                                "in": "path",
                                "required": True,
                                "schema": {
                                    "type": "integer",
                                    "format": "int64"
                                }
                            }
                        ],
                        "requestBody": {
                            "required": True,
                            "content": {
                                "multipart/form-data": {
                                    "schema": {
                                        "type": "object",
                                        "required": ["name", "breed"],
                                        "properties": {
                                            "name": {
                                                "type": "string"
                                            },
                                            "breed": {
                                                "type": "string"
                                            },
                                            "color": {
                                                "type": "string"
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                # Endpoint with path params and JSON body
                "/pets/{petId}/medical/{recordId}": {
                    "put": {
                        "operationId": "updateMedicalRecord",
                        "summary": "Update a pet's medical record",
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
                                "name": "recordId",
                                "in": "path",
                                "required": True,
                                "schema": {
                                    "type": "string"
                                }
                            }
                        ],
                        "requestBody": {
                            "required": True,
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "required": ["diagnosis"],
                                        "properties": {
                                            "diagnosis": {
                                                "type": "string"
                                            },
                                            "treatment": {
                                                "type": "string"
                                            },
                                            "notes": {
                                                "type": "array",
                                                "items": {
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
        }

        server = OpenAPIMCPServer('Test Server', openapi_spec)
        return server

    @pytest.mark.asyncio
    @patch('swagger_mcp.endpoint_invoker.requests.request')
    async def test_path_params_and_form_data(self, mock_request, server):
        """Test endpoint with path parameters and form data (text fields only)."""
        # Setup mock response
        mock_response = MagicMock()
        mock_request.return_value = mock_response

        # Get the call_tool handler
        handlers = server._register_handlers()
        call_tool = handlers["call_tool"]

        # Call the endpoint with path params and form data
        await call_tool("updatePetDetails", {
            "petId": 123,
            "name": "Max",
            "breed": "Golden Retriever",
            "color": "Golden"
        })

        # Verify the request was made with correct parameters
        mock_request.assert_called_once()
        call_args = mock_request.call_args[1]
        
        # Check URL contains path parameter
        assert "123" in call_args["url"]
        
        # Check form data
        assert call_args["data"]["name"] == "Max"
        assert call_args["data"]["breed"] == "Golden Retriever"
        assert call_args["data"]["color"] == "Golden"

    @pytest.mark.asyncio
    @patch('swagger_mcp.endpoint_invoker.requests.request')
    async def test_path_params_and_json_body(self, mock_request, server):
        """Test endpoint with path parameters and JSON request body."""
        # Setup mock response
        mock_response = MagicMock()
        mock_request.return_value = mock_response

        # Get the call_tool handler
        handlers = server._register_handlers()
        call_tool = handlers["call_tool"]

        # Call the endpoint with path params and JSON body
        await call_tool("updateMedicalRecord", {
            "petId": 123,
            "recordId": "REC-456",
            "diagnosis": "Healthy",
            "treatment": "Annual checkup",
            "notes": ["Weight is normal", "No issues found"]
        })

        # Verify the request was made with correct parameters
        mock_request.assert_called_once()
        call_args = mock_request.call_args[1]
        
        # Check URL contains path parameters
        assert "123" in call_args["url"]
        assert "REC-456" in call_args["url"]
        
        # Check JSON body
        assert call_args["json"]["diagnosis"] == "Healthy"
        assert call_args["json"]["treatment"] == "Annual checkup"
        assert call_args["json"]["notes"] == ["Weight is normal", "No issues found"]
