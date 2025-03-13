import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
import tempfile
import json

from openapi_mcp_server import run_server, OpenAPIMCPServer


class TestRunServer:
    """Test the run_server function."""
    
    @patch('openapi_mcp_server.OpenAPIMCPServer')
    @patch('openapi_mcp_server.asyncio.run')
    def test_run_server_with_defaults(self, mock_asyncio_run, mock_server_class):
        """Test run_server with default parameters."""
        # Create a mock server instance
        mock_server_instance = MagicMock()
        mock_server_instance.run = AsyncMock()
        mock_server_class.return_value = mock_server_instance
        
        # Call run_server with a sample spec path
        run_server(
            openapi_spec_path="sample_spec.json",
        )
        
        # Verify the server was created with the right parameters
        mock_server_class.assert_called_once_with(
            server_name="OpenAPI-MCP-Server",
            openapi_spec_path="sample_spec.json",
            server_url=None,
            bearer_token=None
        )
        
        # Verify asyncio.run was called with the server.run coroutine
        assert mock_asyncio_run.called
        # Get the coroutine that was passed to asyncio.run
        coro = mock_asyncio_run.call_args[0][0]
        # Verify it was the server.run coroutine with default host and port
        assert coro.cr_origin is mock_server_instance.run
        assert mock_server_instance.run.called_with(host="0.0.0.0", port=8000)
    
    @patch('openapi_mcp_server.OpenAPIMCPServer')
    @patch('openapi_mcp_server.asyncio.run')
    def test_run_server_with_custom_params(self, mock_asyncio_run, mock_server_class):
        """Test run_server with custom parameters."""
        # Create a mock server instance
        mock_server_instance = MagicMock()
        mock_server_instance.run = AsyncMock()
        mock_server_class.return_value = mock_server_instance
        
        # Call run_server with custom parameters
        run_server(
            openapi_spec_path="custom_spec.json",
            server_name="Custom-API-Server",
            server_url="https://api.example.com",
            bearer_token="test-token",
            host="127.0.0.1",
            port=9000
        )
        
        # Verify the server was created with the right parameters
        mock_server_class.assert_called_once_with(
            server_name="Custom-API-Server",
            openapi_spec_path="custom_spec.json",
            server_url="https://api.example.com",
            bearer_token="test-token"
        )
        
        # Verify asyncio.run was called with the server.run coroutine
        assert mock_asyncio_run.called
        # Get the coroutine that was passed to asyncio.run
        coro = mock_asyncio_run.call_args[0][0]
        # Verify it was the server.run coroutine with custom host and port
        assert coro.cr_origin is mock_server_instance.run
        assert mock_server_instance.run.called_with(host="127.0.0.1", port=9000)
    
    @patch('openapi_mcp_server.OpenAPIMCPServer')
    @patch('openapi_mcp_server.asyncio.run')
    def test_run_server_error_handling(self, mock_asyncio_run, mock_server_class):
        """Test that run_server properly handles errors."""
        # Make the server constructor raise an exception
        mock_server_class.side_effect = ValueError("Invalid spec")
        
        # Call run_server and expect it to raise the error
        with pytest.raises(ValueError, match="Invalid spec"):
            run_server(openapi_spec_path="invalid_spec.json")
        
        # Verify asyncio.run was not called
        mock_asyncio_run.assert_not_called()
    
    @patch('openapi_mcp_server.asyncio.run')
    def test_run_server_integration(self, mock_asyncio_run):
        """Integration test for run_server with a simple JSON spec."""
        # Create a simple OpenAPI spec as a temporary file
        simple_spec = {
            "openapi": "3.0.0",
            "info": {
                "title": "Test API",
                "version": "1.0.0"
            },
            "paths": {
                "/test": {
                    "get": {
                        "summary": "Test endpoint",
                        "operationId": "testEndpoint",
                        "responses": {
                            "200": {
                                "description": "OK"
                            }
                        }
                    }
                }
            }
        }
        
        with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False) as temp_file:
            json.dump(simple_spec, temp_file)
            spec_path = temp_file.name
        
        try:
            # Mock the server run method
            with patch.object(OpenAPIMCPServer, 'run', new_callable=AsyncMock) as mock_run:
                # Call run_server with the temp spec
                run_server(
                    openapi_spec_path=spec_path,
                    server_name="Test-Server"
                )
                
                # Verify the run method was called
                assert mock_run.called
                mock_run.assert_called_once_with(host="0.0.0.0", port=8000)
        finally:
            # Clean up the temporary file
            import os
            if os.path.exists(spec_path):
                os.unlink(spec_path)


if __name__ == "__main__":
    pytest.main(["-xvs", "test_openapi_mcp_run.py"]) 