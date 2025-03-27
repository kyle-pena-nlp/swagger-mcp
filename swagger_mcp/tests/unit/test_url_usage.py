import unittest
from unittest.mock import patch, MagicMock
import tempfile
import json
import pytest
from swagger_mcp.openapi_mcp_server import OpenAPIMCPServer

class TestUrlUsage(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        # Define a simple OpenAPI spec without any servers
        self.openapi_spec = {
            "openapi": "3.0.0",
            "info": {
                "title": "Test API",
                "version": "1.0.0"
            },
            "paths": {
                "/pets": {
                    "get": {
                        "operationId": "listPets",
                        "summary": "List all pets",
                        "responses": {
                            "200": {
                                "description": "A list of pets"
                            }
                        }
                    }
                },
                "/pets/{petId}": {
                    "get": {
                        "operationId": "getPet",
                        "summary": "Get a pet by ID",
                        "parameters": [
                            {
                                "name": "petId",
                                "in": "path",
                                "required": True,
                                "schema": {
                                    "type": "integer"
                                }
                            }
                        ],
                        "responses": {
                            "200": {
                                "description": "Pet details"
                            }
                        }
                    }
                }
            }
        }

    @pytest.mark.asyncio
    @patch('swagger_mcp.openapi_mcp_server.requests.request')
    async def test_constructor_specified_base_url(self, mock_request):
        """Test that manually specified base URL in constructor is used."""
        # Mock the request to return a response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}
        mock_request.return_value = mock_response

        # Create a temporary file to store the OpenAPI spec
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
            json.dump(self.openapi_spec, temp_file)
            temp_file_path = temp_file.name

        try:
            base_url = "https://custom-api.example.com"
            # Create server with manually specified base URL
            server = OpenAPIMCPServer(
                server_name="test-server",
                openapi_spec=temp_file_path,
                server_url=base_url
            )

            # Get the handlers
            handlers = server._register_handlers()
            list_tools = handlers["list_tools"]
            call_tool = handlers["call_tool"]
            tools = await list_tools()

            # Find the listPets tool
            list_pets_tool = next((tool for tool in tools if tool.name == "listPets"), None)
            self.assertIsNotNone(list_pets_tool, "listPets tool not found")

            # Call the listPets endpoint using call_tool
            await call_tool("listPets", {})  # Empty params object since no parameters needed

            # Verify the request was made with the correct URL
            mock_request.assert_called_once()
            call_args = mock_request.call_args[1]
            self.assertEqual(call_args["url"], f"{base_url}/pets")

            # Test with path parameters
            mock_request.reset_mock()
            await call_tool("getPet", {
                "petId": 123  # Parameters go directly in the params object
            })

            # Verify the request was made with the correct URL including path parameter
            mock_request.assert_called_once()
            call_args = mock_request.call_args[1]
            self.assertEqual(call_args["url"], f"{base_url}/pets/123")

        finally:
            # Clean up the temporary file
            import os
            os.unlink(temp_file_path)

    @pytest.mark.asyncio
    @patch('swagger_mcp.openapi_mcp_server.requests.request')
    async def test_endpoint_level_server_url(self, mock_request):
        """Test that server URL specified at the endpoint level is used."""
        # Mock the request to return a response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}
        mock_request.return_value = mock_response

        # Create a spec with endpoint-level servers
        spec_with_endpoint_servers = self.openapi_spec.copy()
        spec_with_endpoint_servers["paths"]["/pets"]["get"]["servers"] = [
            {"url": "https://pets-api.example.com"}
        ]
        spec_with_endpoint_servers["paths"]["/pets/{petId}"]["get"]["servers"] = [
            {"url": "https://pets-api.example.com"}
        ]

        # Create a temporary file to store the OpenAPI spec
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
            json.dump(spec_with_endpoint_servers, temp_file)
            temp_file_path = temp_file.name

        try:
            # Create server without specifying a base URL
            server = OpenAPIMCPServer(
                server_name="test-server",
                openapi_spec=temp_file_path
            )

            # Get the handlers
            handlers = server._register_handlers()
            list_tools = handlers["list_tools"]
            call_tool = handlers["call_tool"]
            tools = await list_tools()

            # Find the listPets tool
            list_pets_tool = next((tool for tool in tools if tool.name == "listPets"), None)
            self.assertIsNotNone(list_pets_tool, "listPets tool not found")

            # Call the listPets endpoint using call_tool
            await call_tool("listPets", {})  # Empty params object since no parameters needed

            # Verify the request was made with the correct URL
            mock_request.assert_called_once()
            call_args = mock_request.call_args[1]
            self.assertEqual(call_args["url"], "https://pets-api.example.com/pets")

            # Test with path parameters
            mock_request.reset_mock()
            await call_tool("getPet", {
                "petId": 123  # Parameters go directly in the params object
            })

            # Verify the request was made with the correct URL including path parameter
            mock_request.assert_called_once()
            call_args = mock_request.call_args[1]
            self.assertEqual(call_args["url"], "https://pets-api.example.com/pets/123")

        finally:
            # Clean up the temporary file
            import os
            os.unlink(temp_file_path)

    @pytest.mark.asyncio
    @patch('swagger_mcp.openapi_mcp_server.requests.request')
    async def test_global_server_url(self, mock_request):
        """Test that server URL specified in the global servers list is used."""
        # Mock the request to return a response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}
        mock_request.return_value = mock_response

        # Create a spec with global servers
        spec_with_global_servers = self.openapi_spec.copy()
        spec_with_global_servers["servers"] = [
            {"url": "https://global-api.example.com"}
        ]

        # Create a temporary file to store the OpenAPI spec
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
            json.dump(spec_with_global_servers, temp_file)
            temp_file_path = temp_file.name

        try:
            # Create server without specifying a base URL
            server = OpenAPIMCPServer(
                server_name="test-server",
                openapi_spec=temp_file_path
            )

            # Get the handlers
            handlers = server._register_handlers()
            list_tools = handlers["list_tools"]
            call_tool = handlers["call_tool"]
            tools = await list_tools()

            # Find the listPets tool
            list_pets_tool = next((tool for tool in tools if tool.name == "listPets"), None)
            self.assertIsNotNone(list_pets_tool, "listPets tool not found")

            # Call the listPets endpoint using call_tool
            await call_tool("listPets", {})  # Empty params object since no parameters needed

            # Verify the request was made with the correct URL
            mock_request.assert_called_once()
            call_args = mock_request.call_args[1]
            self.assertEqual(call_args["url"], "https://global-api.example.com/pets")

            # Test with path parameters
            mock_request.reset_mock()
            await call_tool("getPet", {
                "petId": 123  # Parameters go directly in the params object
            })

            # Verify the request was made with the correct URL including path parameter
            mock_request.assert_called_once()
            call_args = mock_request.call_args[1]
            self.assertEqual(call_args["url"], "https://global-api.example.com/pets/123")

        finally:
            # Clean up the temporary file
            import os
            os.unlink(temp_file_path)

if __name__ == '__main__':
    unittest.main()
