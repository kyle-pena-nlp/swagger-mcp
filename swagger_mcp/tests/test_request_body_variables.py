import unittest
from unittest.mock import patch, MagicMock
from swagger_mcp.endpoint import Endpoint
from swagger_mcp.endpoint_invoker import EndpointInvoker
from swagger_mcp.openapi_parser import OpenAPIParser

class TestRequestBodyVariables(unittest.TestCase):
    def setUp(self):
        # Define a simple OpenAPI spec with request body
        self.openapi_spec = {
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
        
        # Parse the OpenAPI spec and get the endpoint
        parser = OpenAPIParser(spec=self.openapi_spec)
        self.endpoint = parser.get_endpoint_by_operation_id("createPet")
        self.invoker = EndpointInvoker(self.endpoint)

    @patch('swagger_mcp.endpoint_invoker.requests.request')
    def test_request_body_with_required_fields(self, mock_request):
        # Setup mock response
        mock_response = MagicMock()
        mock_request.return_value = mock_response

        # Call the endpoint with required fields
        request_body = {
            "name": "Fluffy",
            "type": "dog"
        }
        self.invoker.invoke(request_body=request_body)

        # Verify the request was made with correct parameters
        mock_request.assert_called_once()
        call_args = mock_request.call_args[1]
        
        # Check that request body was properly included
        self.assertIn("json", call_args)
        self.assertEqual(call_args["json"]["name"], "Fluffy")
        self.assertEqual(call_args["json"]["type"], "dog")

    @patch('swagger_mcp.endpoint_invoker.requests.request')
    def test_request_body_with_all_fields(self, mock_request):
        # Setup mock response
        mock_response = MagicMock()
        mock_request.return_value = mock_response

        # Call the endpoint with all fields
        request_body = {
            "name": "Whiskers",
            "type": "cat",
            "age": 5,
            "tags": ["friendly", "indoor"]
        }
        self.invoker.invoke(request_body=request_body)

        # Verify the request was made with correct parameters
        mock_request.assert_called_once()
        call_args = mock_request.call_args[1]
        
        # Check that all fields were properly included
        self.assertIn("json", call_args)
        self.assertEqual(call_args["json"]["name"], "Whiskers")
        self.assertEqual(call_args["json"]["type"], "cat")
        self.assertEqual(call_args["json"]["age"], 5)
        self.assertEqual(call_args["json"]["tags"], ["friendly", "indoor"])

if __name__ == '__main__':
    unittest.main()