import os
import json
import tempfile
import pytest
import asyncio
import requests
from unittest.mock import patch, MagicMock

from openapi_mcp_server import OpenAPIMCPServer
from mcp.types import Tool, ToolParameter, ToolResult

# URL for the PetStore OpenAPI spec
PETSTORE_API_URL = "https://petstore3.swagger.io/api/v3/openapi.json"


@pytest.fixture
def petstore_spec_path():
    """
    Download the PetStore OpenAPI spec and return the path to the file.
    This is a real-world spec to test against.
    """
    # Create a temporary file for the OpenAPI spec
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as temp_file:
        spec_path = temp_file.name
    
    try:
        # Download the PetStore OpenAPI spec
        response = requests.get(PETSTORE_API_URL)
        response.raise_for_status()
        
        with open(spec_path, "w") as f:
            f.write(response.text)
        
        yield spec_path
    finally:
        # Clean up the temporary file
        if os.path.exists(spec_path):
            os.unlink(spec_path)


@pytest.fixture
def mock_server():
    """Create a mock Server with real decorator behavior."""
    with patch('openapi_mcp_server.Server') as MockServer:
        server_instance = MockServer.return_value
        
        # Store the registered handlers
        server_instance.list_tools_handler = None
        server_instance.call_tool_handler = None
        
        # Mock the decorators to capture the functions
        def list_tools_decorator():
            def decorator(func):
                server_instance.list_tools_handler = func
                return func
            return decorator
        
        def call_tool_decorator():
            def decorator(func):
                server_instance.call_tool_handler = func
                return func
            return decorator
        
        server_instance.list_tools.side_effect = list_tools_decorator
        server_instance.call_tool.side_effect = call_tool_decorator
        
        yield server_instance


@pytest.fixture
def petstore_server(petstore_spec_path, mock_server):
    """Create an OpenAPIMCPServer with the real PetStore spec."""
    server = OpenAPIMCPServer(
        server_name="petstore-test",
        openapi_spec_path=petstore_spec_path,
        server_url="https://petstore3.swagger.io/api/v3"
    )
    return server


class TestPetStoreIntegration:
    """Integration tests using the real PetStore OpenAPI spec."""
    
    @pytest.mark.asyncio
    async def test_list_tools_with_real_spec(self, petstore_server, mock_server):
        """Test that tools are correctly generated from the real PetStore spec."""
        # Get the registered list_tools handler
        list_tools_handler = mock_server.list_tools_handler
        assert list_tools_handler is not None
        
        # Call the handler
        tools = await list_tools_handler()
        
        # Verify we have tools
        assert isinstance(tools, list)
        assert len(tools) > 0
        
        # Check for some expected tool names (these should be in the PetStore API)
        tool_names = [tool.name for tool in tools]
        
        # Common PetStore operation IDs
        expected_tools = [
            "getPetById",
            "updatePet",
            "addPet",
            "findPetsByStatus"
        ]
        
        # Verify at least some of these exist (the spec might change over time)
        found_tools = [name for name in expected_tools if name in tool_names]
        assert len(found_tools) > 0, f"None of the expected tools found in {tool_names}"
        
        # Examine a specific tool in more detail
        if "getPetById" in tool_names:
            get_pet_tool = next(tool for tool in tools if tool.name == "getPetById")
            
            # Should have a petId parameter
            param_names = [param.name for param in get_pet_tool.parameters]
            assert "petId" in param_names
            
            # petId should be required
            pet_id_param = next(param for param in get_pet_tool.parameters if param.name == "petId")
            assert pet_id_param.required is True
    
    @pytest.mark.asyncio
    async def test_call_tool_with_mocked_response(self, petstore_server, mock_server):
        """Test calling a tool with a mocked API response."""
        # Mock the EndpointInvoker
        with patch('openapi_mcp_server.EndpointInvoker') as MockInvoker:
            invoker_instance = MockInvoker.return_value
            
            # Create a mock response for a pet
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "id": 10,
                "name": "doggie",
                "category": {
                    "id": 1,
                    "name": "Dogs"
                },
                "photoUrls": [
                    "https://example.com/dog.jpg"
                ],
                "tags": [
                    {
                        "id": 1,
                        "name": "friendly"
                    }
                ],
                "status": "available"
            }
            invoker_instance.invoke_with_params.return_value = mock_response
            
            # Get the registered call_tool handler
            call_tool_handler = mock_server.call_tool_handler
            assert call_tool_handler is not None
            
            # Call the handler to get a pet by ID
            result = await call_tool_handler("getPetById", {"petId": 10})
            
            # Verify the result
            assert isinstance(result, list)
            assert len(result) == 1
            assert isinstance(result[0], ToolResult)
            assert result[0].value["id"] == 10
            assert result[0].value["name"] == "doggie"
            
            # Verify the invoker was called with correct parameters
            invoker_instance.invoke_with_params.assert_called_once_with(
                params={"petId": 10},
                server_url="https://petstore3.swagger.io/api/v3",
                bearer_token=None
            )
    
    @pytest.mark.asyncio
    async def test_call_tool_with_complex_parameters(self, petstore_server, mock_server):
        """Test calling a tool that requires complex parameters."""
        # Mock the EndpointInvoker
        with patch('openapi_mcp_server.EndpointInvoker') as MockInvoker:
            invoker_instance = MockInvoker.return_value
            
            # Create a mock response for adding a pet
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "id": 12345,
                "name": "Rex",
                "category": {
                    "id": 1,
                    "name": "Dogs"
                },
                "photoUrls": [
                    "https://example.com/rex.jpg"
                ],
                "tags": [
                    {
                        "id": 2,
                        "name": "large"
                    }
                ],
                "status": "pending"
            }
            invoker_instance.invoke_with_params.return_value = mock_response
            
            # Get the registered call_tool handler
            call_tool_handler = mock_server.call_tool_handler
            
            # Prepare complex parameters for adding a pet
            pet_data = {
                "name": "Rex",
                "category": {
                    "id": 1,
                    "name": "Dogs"
                },
                "photoUrls": [
                    "https://example.com/rex.jpg"
                ],
                "tags": [
                    {
                        "id": 2,
                        "name": "large"
                    }
                ],
                "status": "pending"
            }
            
            # Call the handler to add a pet
            result = await call_tool_handler("addPet", pet_data)
            
            # Verify the result
            assert isinstance(result, list)
            assert len(result) == 1
            assert result[0].value["id"] == 12345
            assert result[0].value["name"] == "Rex"
            
            # Verify the invoker was called with correct parameters
            invoker_instance.invoke_with_params.assert_called_once_with(
                params=pet_data,
                server_url="https://petstore3.swagger.io/api/v3",
                bearer_token=None
            )
    
    @pytest.mark.asyncio
    async def test_call_tool_with_error_response(self, petstore_server, mock_server):
        """Test handling of an error response from the API."""
        # Mock the EndpointInvoker
        with patch('openapi_mcp_server.EndpointInvoker') as MockInvoker:
            invoker_instance = MockInvoker.return_value
            
            # Create a mock response for a 404 error
            mock_response = MagicMock()
            mock_response.json.side_effect = ValueError("Invalid JSON")
            mock_response.text = "Pet not found"
            invoker_instance.invoke_with_params.return_value = mock_response
            
            # Get the registered call_tool handler
            call_tool_handler = mock_server.call_tool_handler
            
            # Call the handler with a non-existent pet ID
            result = await call_tool_handler("getPetById", {"petId": 99999})
            
            # Verify the result
            assert isinstance(result, list)
            assert len(result) == 1
            assert result[0].value == "Pet not found"


if __name__ == "__main__":
    pytest.main(["-xvs", "test_openapi_mcp_integration.py"]) 