import unittest
from unittest.mock import patch, MagicMock
from swagger_mcp.endpoint import Endpoint
from swagger_mcp.endpoint_invoker import EndpointInvoker
from swagger_mcp.openapi_parser import OpenAPIParser

class TestFormDataVariables(unittest.TestCase):
    def setUp(self):
        # Define a simple OpenAPI spec with multipart form data
        self.openapi_spec = {
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
        
        # Parse the OpenAPI spec and get the endpoint
        parser = OpenAPIParser(spec=self.openapi_spec)
        self.endpoint = parser.get_endpoint_by_operation_id("uploadFile")
        self.invoker = EndpointInvoker(self.endpoint)

    @patch('swagger_mcp.endpoint_invoker.requests.request')
    def test_multipart_form_data(self, mock_request):
        # Setup mock response
        mock_response = MagicMock()
        mock_request.return_value = mock_response

        # Call the endpoint with mixed form data (file and array field)
        request_body = {
            "description": "Test with tags",
            "tags": ["test", "example"]
        }
        self.invoker.invoke(request_body=request_body)

        # Verify the request was made with all fields
        mock_request.assert_called_once()
        call_args = mock_request.call_args[1]
        
        # Check that both file and regular form fields are present
        self.assertIn("data", call_args)
        self.assertEqual(call_args["data"]["description"], "Test with tags")
        self.assertEqual(call_args["data"]["tags"], ["test", "example"])

    @patch('swagger_mcp.endpoint_invoker.requests.request')
    def test_multipart_form_data_omitting_optional_field(self, mock_request):
        # Setup mock response
        mock_response = MagicMock()
        mock_request.return_value = mock_response

        # Call the endpoint with mixed form data (file and array field)
        request_body = {
            "description": "Test with tags"
        }
        self.invoker.invoke(request_body=request_body)

        # Verify the request was made with all fields
        mock_request.assert_called_once()
        call_args = mock_request.call_args[1]
        
        # Check that both file and regular form fields are present
        self.assertIn("data", call_args)
        self.assertEqual(call_args["data"]["description"], "Test with tags")        

if __name__ == '__main__':
    unittest.main()