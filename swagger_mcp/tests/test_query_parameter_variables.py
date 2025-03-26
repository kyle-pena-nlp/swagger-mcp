import unittest
from unittest.mock import patch, MagicMock
from swagger_mcp.endpoint import Endpoint
from swagger_mcp.endpoint_invoker import EndpointInvoker
from swagger_mcp.openapi_parser import OpenAPIParser

class TestQueryVariables(unittest.TestCase):
    def setUp(self):
        # Define a simple OpenAPI spec with query parameters
        self.openapi_spec = {
            "openapi": "3.0.0",
            "info": {
                "title": "Product API",
                "version": "1.0.0"
            },
            "servers": [{"url": "https://api.example.com"}],
            "paths": {
                "/products": {
                    "get": {
                        "operationId": "searchProducts",
                        "summary": "Search for products",
                        "parameters": [
                            {
                                "name": "category",
                                "in": "query",
                                "required": True,
                                "schema": {
                                    "type": "string",
                                    "enum": ["electronics", "books", "clothing"]
                                }
                            },
                            {
                                "name": "minPrice",
                                "in": "query",
                                "required": False,
                                "schema": {
                                    "type": "number",
                                    "minimum": 0
                                }
                            },
                            {
                                "name": "maxPrice",
                                "in": "query",
                                "required": False,
                                "schema": {
                                    "type": "number",
                                    "minimum": 0
                                }
                            },
                            {
                                "name": "inStock",
                                "in": "query",
                                "required": False,
                                "schema": {
                                    "type": "boolean",
                                    "default": True
                                }
                            },
                            {
                                "name": "tags",
                                "in": "query",
                                "required": False,
                                "schema": {
                                    "type": "array",
                                    "items": {
                                        "type": "string"
                                    }
                                },
                                "style": "form",
                                "explode": False
                            }
                        ],
                        "responses": {
                            "200": {
                                "description": "Products found"
                            }
                        }
                    }
                }
            }
        }
        
        # Parse the OpenAPI spec and get the endpoint
        parser = OpenAPIParser(spec=self.openapi_spec)
        self.endpoint = parser.get_endpoint_by_operation_id("searchProducts")
        self.invoker = EndpointInvoker(self.endpoint)

    @patch('swagger_mcp.endpoint_invoker.requests.request')
    def test_query_parameter_basic(self, mock_request):
        """Test basic query parameter handling with a required parameter."""
        # Setup mock response
        mock_response = MagicMock()
        mock_request.return_value = mock_response

        # Call the endpoint with just the required parameter
        query_params = {
            "category": "electronics"
        }
        self.invoker.invoke(query_params=query_params)

        # Verify the request was made with the correct query parameters
        mock_request.assert_called_once()
        call_args = mock_request.call_args[1]
        self.assertEqual(call_args["params"]["category"], "electronics")

    @patch('swagger_mcp.endpoint_invoker.requests.request')
    def test_query_parameter_multiple(self, mock_request):
        """Test handling multiple query parameters including optional ones."""
        mock_response = MagicMock()
        mock_request.return_value = mock_response

        # Call the endpoint with multiple parameters
        query_params = {
            "category": "electronics",
            "minPrice": 100,
            "maxPrice": 500,
            "inStock": False
        }
        self.invoker.invoke(query_params=query_params)

        # Verify the request was made with all query parameters
        mock_request.assert_called_once()
        call_args = mock_request.call_args[1]
        self.assertEqual(call_args["params"]["category"], "electronics")
        self.assertEqual(call_args["params"]["minPrice"], 100)
        self.assertEqual(call_args["params"]["maxPrice"], 500)
        self.assertEqual(call_args["params"]["inStock"], False)

    @patch('swagger_mcp.endpoint_invoker.requests.request')
    def test_query_parameter_array(self, mock_request):
        """Test handling array query parameters."""
        mock_response = MagicMock()
        mock_request.return_value = mock_response

        # Call the endpoint with array parameter
        query_params = {
            "category": "electronics",
            "tags": ["new", "sale", "featured"]
        }
        self.invoker.invoke(query_params=query_params)

        # Verify the request was made with array parameter
        mock_request.assert_called_once()
        call_args = mock_request.call_args[1]
        self.assertEqual(call_args["params"]["category"], "electronics")
        # For style=form and explode=false, arrays should be comma-separated
        self.assertEqual(call_args["params"]["tags"], ["new", "sale", "featured"]) # the requests module accepts arrays here
        
if __name__ == '__main__':
    unittest.main()
