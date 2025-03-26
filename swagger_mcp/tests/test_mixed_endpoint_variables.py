import unittest
from unittest.mock import patch, MagicMock
from swagger_mcp.endpoint import Endpoint
from swagger_mcp.endpoint_invoker import EndpointInvoker
from swagger_mcp.openapi_parser import OpenAPIParser

class TestMixedEndpointVariables(unittest.TestCase):
    def setUp(self):
        # Define an OpenAPI spec with multiple endpoints using different combinations
        self.openapi_spec = {
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

    @patch('swagger_mcp.endpoint_invoker.requests.request')
    def test_path_params_and_form_data(self, mock_request):
        """Test endpoint with path parameters and form data (text fields only)."""
        # Parse the OpenAPI spec and get the endpoint
        parser = OpenAPIParser(spec=self.openapi_spec)
        endpoint = parser.get_endpoint_by_operation_id("updatePetDetails")
        invoker = EndpointInvoker(endpoint)

        # Setup mock response
        mock_response = MagicMock()
        mock_request.return_value = mock_response

        # Call the endpoint with path params and form data
        path_params = {"petId": 123}
        request_body = {
            "name": "Max",
            "breed": "Golden Retriever",
            "color": "Golden"
        }
        invoker.invoke(path_params=path_params, request_body=request_body)

        # Verify the request was made with correct parameters
        mock_request.assert_called_once()
        call_args = mock_request.call_args[1]
        
        # Check URL contains path parameter
        self.assertIn("123", call_args["url"])
        
        # Check form data
        self.assertEqual(call_args["data"]["name"], "Max")
        self.assertEqual(call_args["data"]["breed"], "Golden Retriever")
        self.assertEqual(call_args["data"]["color"], "Golden")

    @patch('swagger_mcp.endpoint_invoker.requests.request')
    def test_path_params_and_json_body(self, mock_request):
        """Test endpoint with path parameters and JSON request body."""
        # Parse the OpenAPI spec and get the endpoint
        parser = OpenAPIParser(spec=self.openapi_spec)
        endpoint = parser.get_endpoint_by_operation_id("updateMedicalRecord")
        invoker = EndpointInvoker(endpoint)

        # Setup mock response
        mock_response = MagicMock()
        mock_request.return_value = mock_response

        # Call the endpoint with path params and JSON body
        path_params = {
            "petId": 123,
            "recordId": "REC-456"
        }
        request_body = {
            "diagnosis": "Healthy",
            "treatment": "Annual checkup",
            "notes": ["Weight is normal", "No issues found"]
        }
        invoker.invoke(path_params=path_params, request_body=request_body)

        # Verify the request was made with correct parameters
        mock_request.assert_called_once()
        call_args = mock_request.call_args[1]
        
        # Check URL contains path parameters
        self.assertIn("123", call_args["url"])
        self.assertIn("REC-456", call_args["url"])
        
        # Check JSON body
        self.assertEqual(call_args["json"]["diagnosis"], "Healthy")
        self.assertEqual(call_args["json"]["treatment"], "Annual checkup")
        self.assertEqual(call_args["json"]["notes"], ["Weight is normal", "No issues found"])

if __name__ == '__main__':
    unittest.main()
