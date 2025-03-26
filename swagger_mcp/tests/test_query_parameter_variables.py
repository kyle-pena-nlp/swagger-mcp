import pytest
from unittest.mock import patch, MagicMock
from swagger_mcp.openapi_mcp_server import OpenAPIMCPServer

class TestQueryVariables:
    @pytest.fixture
    def server(self):
        # Define a simple OpenAPI spec with query parameters
        openapi_spec = {
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
        
        server = OpenAPIMCPServer('Test Server', openapi_spec)
        return server

    @pytest.mark.asyncio
    @patch('swagger_mcp.endpoint_invoker.requests.request')
    async def test_query_parameter_basic(self, mock_request, server):
        """Test basic query parameter handling with a required parameter."""
        # Setup mock response
        mock_response = MagicMock()
        mock_request.return_value = mock_response

        # Get the call_tool handler
        handlers = server._register_handlers()
        call_tool = handlers["call_tool"]

        # Call the endpoint with just the required parameter
        await call_tool("searchProducts", {
            "category": "electronics"
        })

        # Verify the request was made with the correct query parameters
        mock_request.assert_called_once()
        call_args = mock_request.call_args[1]
        assert call_args["params"]["category"] == "electronics"

    @pytest.mark.asyncio
    @patch('swagger_mcp.endpoint_invoker.requests.request')
    async def test_query_parameter_multiple(self, mock_request, server):
        """Test handling multiple query parameters including optional ones."""
        mock_response = MagicMock()
        mock_request.return_value = mock_response

        # Get the call_tool handler
        handlers = server._register_handlers()
        call_tool = handlers["call_tool"]

        # Call the endpoint with multiple parameters
        await call_tool("searchProducts", {
            "category": "electronics",
            "minPrice": 100,
            "maxPrice": 500,
            "inStock": False
        })

        # Verify the request was made with all query parameters
        mock_request.assert_called_once()
        call_args = mock_request.call_args[1]
        assert call_args["params"]["category"] == "electronics"
        assert call_args["params"]["minPrice"] == 100
        assert call_args["params"]["maxPrice"] == 500
        assert call_args["params"]["inStock"] == False

    @pytest.mark.asyncio
    @patch('swagger_mcp.endpoint_invoker.requests.request')
    async def test_query_parameter_array(self, mock_request, server):
        """Test handling array query parameters."""
        mock_response = MagicMock()
        mock_request.return_value = mock_response

        # Get the call_tool handler
        handlers = server._register_handlers()
        call_tool = handlers["call_tool"]

        # Call the endpoint with array parameter
        await call_tool("searchProducts", {
            "category": "electronics",
            "tags": ["new", "sale", "featured"]
        })

        # Verify the request was made with array parameter
        mock_request.assert_called_once()
        call_args = mock_request.call_args[1]
        assert call_args["params"]["category"] == "electronics"
        # For style=form and explode=false, arrays should be comma-separated
        assert call_args["params"]["tags"] == ["new", "sale", "featured"] # the requests module accepts arrays here
