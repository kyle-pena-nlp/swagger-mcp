import unittest
from unittest.mock import patch, MagicMock
import tempfile
import json
import pytest
from swagger_mcp.openapi_mcp_server import OpenAPIMCPServer
from swagger_mcp.endpoint import Endpoint
from swagger_mcp.endpoint_invoker import EndpointInvoker
from swagger_mcp.openapi_parser import OpenAPIParser

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
    @patch('swagger_mcp.endpoint_invoker.requests.request')
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

            # Get the list_tools handler and call it
            handlers = server._register_handlers()
            list_tools = handlers["list_tools"]
            tools = await list_tools()

            # Find the listPets tool
            list_pets_tool = next((tool for tool in tools if tool.name == "listPets"), None)
            self.assertIsNotNone(list_pets_tool, "listPets tool not found")

            # Create an invoker and call the endpoint
            parser = OpenAPIParser(spec=self.openapi_spec)
            endpoint = parser.get_endpoint_by_operation_id("listPets")
            invoker = EndpointInvoker(endpoint)
            invoker.invoke(server_url=base_url)  

            # Verify the request was made with the correct URL
            mock_request.assert_called_once()
            call_args = mock_request.call_args[1]
            self.assertEqual(call_args["url"], f"{base_url}/pets")

            # Test with path parameters
            mock_request.reset_mock()
            endpoint = parser.get_endpoint_by_operation_id("getPet")
            invoker = EndpointInvoker(endpoint)
            invoker.invoke(server_url=base_url, path_params={"petId": 123})  

            # Verify the request was made with the correct URL including path parameter
            mock_request.assert_called_once()
            call_args = mock_request.call_args[1]
            self.assertEqual(call_args["url"], f"{base_url}/pets/123")

        finally:
            # Clean up the temporary file
            import os
            os.unlink(temp_file_path)

    @pytest.mark.asyncio
    @patch('swagger_mcp.endpoint_invoker.requests.request')
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

            # Get the list_tools handler and call it
            handlers = server._register_handlers()
            list_tools = handlers["list_tools"]
            tools = await list_tools()

            # Find the listPets tool
            list_pets_tool = next((tool for tool in tools if tool.name == "listPets"), None)
            self.assertIsNotNone(list_pets_tool, "listPets tool not found")

            # Create an invoker and call the endpoint
            parser = OpenAPIParser(spec=spec_with_endpoint_servers)
            endpoint = parser.get_endpoint_by_operation_id("listPets")
            invoker = EndpointInvoker(endpoint)
            invoker.invoke()  # No server_url needed since it's in the endpoint spec

            # Verify the request was made with the correct URL
            mock_request.assert_called_once()
            call_args = mock_request.call_args[1]
            self.assertEqual(call_args["url"], "https://pets-api.example.com/pets")

            # Test with path parameters
            mock_request.reset_mock()
            endpoint = parser.get_endpoint_by_operation_id("getPet")
            invoker = EndpointInvoker(endpoint)
            invoker.invoke(path_params={"petId": 123})  # No server_url needed

            # Verify the request was made with the correct URL including path parameter
            mock_request.assert_called_once()
            call_args = mock_request.call_args[1]
            self.assertEqual(call_args["url"], "https://pets-api.example.com/pets/123")

        finally:
            # Clean up the temporary file
            import os
            os.unlink(temp_file_path)

    @pytest.mark.asyncio
    @patch('swagger_mcp.endpoint_invoker.requests.request')
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

            # Get the list_tools handler and call it
            handlers = server._register_handlers()
            list_tools = handlers["list_tools"]
            tools = await list_tools()

            # Find the listPets tool
            list_pets_tool = next((tool for tool in tools if tool.name == "listPets"), None)
            self.assertIsNotNone(list_pets_tool, "listPets tool not found")

            # Create an invoker and call the endpoint
            parser = OpenAPIParser(spec=spec_with_global_servers)
            endpoint = parser.get_endpoint_by_operation_id("listPets")
            invoker = EndpointInvoker(endpoint)
            invoker.invoke()  # No server_url needed since it's in the global spec

            # Verify the request was made with the correct URL
            mock_request.assert_called_once()
            call_args = mock_request.call_args[1]
            self.assertEqual(call_args["url"], "https://global-api.example.com/pets")

            # Test with path parameters
            mock_request.reset_mock()
            endpoint = parser.get_endpoint_by_operation_id("getPet")
            invoker = EndpointInvoker(endpoint)
            invoker.invoke(path_params={"petId": 123})  # No server_url needed

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
