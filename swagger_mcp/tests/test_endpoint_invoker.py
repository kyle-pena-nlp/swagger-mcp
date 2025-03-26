import unittest
from unittest.mock import patch, MagicMock
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field

from swagger_mcp.endpoint import Endpoint
from swagger_mcp.endpoint_invoker import (
    EndpointInvoker,
    MissingPathParameterError,
    MissingQueryParameterError,
    MissingHeaderParameterError,
    MissingRequestBodyError,
    MissingBearerTokenError,
    MissingServerUrlError
)


class TestEndpointInvoker(unittest.TestCase):
    """Tests for the EndpointInvoker class."""

    def setUp(self):
        """Set up test endpoints."""
        # Basic endpoint with no requirements
        self.basic_endpoint = Endpoint(
            path="/simple",
            method="GET",
            operation_id="simpleGet",
            summary="Simple endpoint",
            servers=[{"url": "https://api.example.com"}]
        )
        
        # Endpoint with path parameters
        self.path_param_endpoint = Endpoint(
            path="/users/{userId}",
            method="GET",
            operation_id="getUserById",
            summary="Get a user by ID",
            servers=[{"url": "https://api.example.com"}],
            path_parameters_schema={
                "type": "object",
                "properties": {
                    "userId": {"type": "string"}
                },
                "required": ["userId"]
            }
        )
        
        # Endpoint with query parameters
        self.query_param_endpoint = Endpoint(
            path="/users",
            method="GET",
            operation_id="getUsers",
            summary="Get users",
            servers=[{"url": "https://api.example.com"}],
            query_parameters_schema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer"},
                    "offset": {"type": "integer"}
                },
                "required": ["limit"]
            }
        )
        
        # Endpoint with header parameters
        self.header_param_endpoint = Endpoint(
            path="/secure",
            method="GET",
            operation_id="getSecure",
            summary="Secure endpoint",
            servers=[{"url": "https://api.example.com"}],
            header_parameters_schema={
                "type": "object",
                "properties": {
                    "X-API-Key": {"type": "string"}
                },
                "required": ["X-API-Key"]
            }
        )
        
        # Endpoint requiring bearer authentication
        self.auth_endpoint = Endpoint(
            path="/protected",
            method="GET",
            operation_id="getProtected",
            summary="Protected endpoint",
            servers=[{"url": "https://api.example.com"}],
            requires_bearer_auth=True
        )
        
        # Endpoint requiring a request body
        self.body_endpoint = Endpoint(
            path="/users",
            method="POST",
            operation_id="createUser",
            summary="Create a user",
            servers=[{"url": "https://api.example.com"}],
            request_body_schema={
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "email": {"type": "string"}
                }
            },
            request_body_required=True,
            request_content_types=["application/json"]
        )
        
        # Endpoint with no server URL
        self.no_server_endpoint = Endpoint(
            path="/no-server",
            method="GET",
            operation_id="noServer",
            summary="No server endpoint"
        )

    @patch('swagger_mcp.endpoint_invoker.requests.request')
    def test_basic_endpoint_invocation(self, mock_request):
        """Test invoking a basic endpoint with no special requirements."""
        # Setup the mock
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_request.return_value = mock_response
        
        # Create invoker and call invoke
        invoker = EndpointInvoker(self.basic_endpoint)
        response = invoker.invoke()
        
        # Check that requests.request was called with the correct arguments
        mock_request.assert_called_once_with(
            method='GET',
            url='https://api.example.com/simple',
            params={},
            headers={},
            json=None,
            timeout=None
        )
        
        # Check that we got the mock response back
        self.assertEqual(response, mock_response)

    @patch('swagger_mcp.endpoint_invoker.requests.request')
    def test_path_parameter_endpoint(self, mock_request):
        """Test invoking an endpoint with path parameters."""
        # Setup the mock
        mock_response = MagicMock()
        mock_request.return_value = mock_response
        
        # Create invoker and call invoke with path parameters
        invoker = EndpointInvoker(self.path_param_endpoint)
        response = invoker.invoke(path_params={"userId": "123"})
        
        # Check that requests.request was called with the correct URL
        mock_request.assert_called_once()
        call_args = mock_request.call_args[1]
        self.assertEqual(call_args['url'], 'https://api.example.com/users/123')

    def test_missing_path_parameter(self):
        """Test that an exception is raised when a required path parameter is missing."""
        invoker = EndpointInvoker(self.path_param_endpoint)
        
        # Should raise MissingPathParameterError because userId is required
        with self.assertRaises(MissingPathParameterError) as context:
            invoker.invoke()
            
        # Check that the exception has the correct parameter name
        self.assertEqual(context.exception.param_name, 'userId')

    @patch('swagger_mcp.endpoint_invoker.requests.request')
    def test_query_parameter_endpoint(self, mock_request):
        """Test invoking an endpoint with query parameters."""
        # Setup the mock
        mock_response = MagicMock()
        mock_request.return_value = mock_response
        
        # Create invoker and call invoke with query parameters
        invoker = EndpointInvoker(self.query_param_endpoint)
        response = invoker.invoke(query_params={"limit": 10, "offset": 0})
        
        # Check that requests.request was called with the correct parameters
        mock_request.assert_called_once()
        call_args = mock_request.call_args[1]
        self.assertEqual(call_args['params'], {"limit": 10, "offset": 0})

    def test_missing_query_parameter(self):
        """Test that an exception is raised when a required query parameter is missing."""
        invoker = EndpointInvoker(self.query_param_endpoint)
        
        # Should raise MissingQueryParameterError because limit is required
        with self.assertRaises(MissingQueryParameterError) as context:
            invoker.invoke()
            
        # Check that the exception has the correct parameter name
        self.assertEqual(context.exception.param_name, 'limit')

    @patch('swagger_mcp.endpoint_invoker.requests.request')
    def test_header_parameter_endpoint(self, mock_request):
        """Test invoking an endpoint with header parameters."""
        # Setup the mock
        mock_response = MagicMock()
        mock_request.return_value = mock_response
        
        # Create invoker and call invoke with header parameters
        invoker = EndpointInvoker(self.header_param_endpoint)
        response = invoker.invoke(headers={"X-API-Key": "secret-key"})
        
        # Check that requests.request was called with the correct headers
        mock_request.assert_called_once()
        call_args = mock_request.call_args[1]
        self.assertEqual(call_args['headers'], {"X-API-Key": "secret-key"})

    def test_missing_header_parameter(self):
        """Test that an exception is raised when a required header parameter is missing."""
        invoker = EndpointInvoker(self.header_param_endpoint)
        
        # Should raise MissingHeaderParameterError because X-API-Key is required
        with self.assertRaises(MissingHeaderParameterError) as context:
            invoker.invoke()
            
        # Check that the exception has the correct parameter name
        self.assertEqual(context.exception.param_name, 'X-API-Key')

    @patch('swagger_mcp.endpoint_invoker.requests.request')
    def test_auth_endpoint(self, mock_request):
        """Test invoking an endpoint that requires bearer authentication."""
        # Setup the mock
        mock_response = MagicMock()
        mock_request.return_value = mock_response
        
        # Create invoker and call invoke with bearer token
        invoker = EndpointInvoker(self.auth_endpoint)
        response = invoker.invoke(bearer_token="my-token")
        
        # Check that requests.request was called with the correct headers
        mock_request.assert_called_once()
        call_args = mock_request.call_args[1]
        self.assertEqual(call_args['headers'], {"Authorization": "Bearer my-token"})

    def test_missing_bearer_token(self):
        """Test that an exception is raised when a bearer token is required but not provided."""
        invoker = EndpointInvoker(self.auth_endpoint)
        
        # Should raise MissingBearerTokenError
        with self.assertRaises(MissingBearerTokenError):
            invoker.invoke()

    @patch('swagger_mcp.endpoint_invoker.requests.request')
    def test_body_endpoint(self, mock_request):
        """Test invoking an endpoint that requires a request body."""
        # Setup the mock
        mock_response = MagicMock()
        mock_request.return_value = mock_response
        
        # Create invoker and call invoke with request body
        invoker = EndpointInvoker(self.body_endpoint)
        body = {"name": "John", "email": "john@example.com"}
        response = invoker.invoke(request_body=body)
        
        # Check that requests.request was called with the correct JSON body and Content-Type header
        mock_request.assert_called_once()
        call_args = mock_request.call_args[1]
        self.assertEqual(call_args['json'], body)
        self.assertEqual(call_args['headers'], {"Content-Type": "application/json"})

    def test_missing_request_body(self):
        """Test that an exception is raised when a request body is required but not provided."""
        invoker = EndpointInvoker(self.body_endpoint)
        
        # Should raise MissingRequestBodyError
        with self.assertRaises(MissingRequestBodyError):
            invoker.invoke()

    def test_no_server_url(self):
        """Test that an exception is raised when no server URL is available."""
        invoker = EndpointInvoker(self.no_server_endpoint)
        
        # Should raise MissingServerUrlError
        with self.assertRaises(MissingServerUrlError):
            invoker.invoke()
            
    @patch('swagger_mcp.endpoint_invoker.requests.request')
    def test_override_server_url(self, mock_request):
        """Test providing a server URL that overrides the endpoint's servers."""
        # Setup the mock
        mock_response = MagicMock()
        mock_request.return_value = mock_response
        
        # Create invoker and call invoke with custom server URL
        invoker = EndpointInvoker(self.basic_endpoint)
        response = invoker.invoke(server_url="https://custom-api.example.com")
        
        # Check that requests.request was called with the custom URL
        mock_request.assert_called_once()
        call_args = mock_request.call_args[1]
        self.assertEqual(call_args['url'], 'https://custom-api.example.com/simple')

    @patch('swagger_mcp.endpoint_invoker.requests.request')
    def test_custom_timeout(self, mock_request):
        """Test providing a custom timeout value."""
        # Setup the mock
        mock_response = MagicMock()
        mock_request.return_value = mock_response
        
        # Create invoker and call invoke with custom timeout
        invoker = EndpointInvoker(self.basic_endpoint)
        response = invoker.invoke(timeout=5.0)
        
        # Check that requests.request was called with the custom timeout
        mock_request.assert_called_once()
        call_args = mock_request.call_args[1]
        self.assertEqual(call_args['timeout'], 5.0)


if __name__ == '__main__':
    unittest.main() 