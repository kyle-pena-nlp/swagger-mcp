import unittest
from unittest.mock import patch, MagicMock
from swagger_mcp.endpoint import Endpoint
from swagger_mcp.endpoint_invoker import EndpointInvoker
from swagger_mcp.openapi_parser import OpenAPIParser

class TestPathVariables(unittest.TestCase):
    def setUp(self):
        # Define a simple OpenAPI spec with path parameters
        self.openapi_spec = {
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
        
        # Parse the OpenAPI spec and get the endpoint
        parser = OpenAPIParser(spec=self.openapi_spec)
        self.endpoint = parser.get_endpoint_by_operation_id("getPetToy")
        self.invoker = EndpointInvoker(self.endpoint)

    @patch('swagger_mcp.endpoint_invoker.requests.request')
    def test_path_parameter_substitution(self, mock_request):
        # Setup mock response
        mock_response = MagicMock()
        mock_request.return_value = mock_response

        # Call the endpoint with path parameters
        path_params = {
            "petId": 123,
            "toyId": "ball"
        }
        self.invoker.invoke(path_params=path_params)

        # Verify the request was made with the correct URL
        mock_request.assert_called_once()
        call_args = mock_request.call_args
        
        # Check that path parameters were correctly substituted
        self.assertTrue(call_args[1]["url"].endswith("/pets/123/toys/ball"))

    @patch('swagger_mcp.endpoint_invoker.requests.request')
    def test_missing_path_parameter(self, mock_request):
        # Test that missing required path parameters raise an error
        path_params = {
            # Missing required 'toyId' parameter
            "petId": 123
        }
        with self.assertRaises(Exception) as context:
            self.invoker.invoke(path_params=path_params)

if __name__ == '__main__':
    unittest.main()