import unittest
from unittest.mock import patch, MagicMock
from swagger_mcp.endpoint import Endpoint
from swagger_mcp.endpoint_invoker import EndpointInvoker

class TestPathVariables(unittest.TestCase):
    def setUp(self):
        # Create a test endpoint with path parameters
        self.endpoint = Endpoint(
            path="/users/{userId}/posts/{postId}",
            method="GET",
            operation_id="getUserPost",
            summary="Get a user's post",
            path_parameters_schema={
                "type": "object",
                "required": ["userId", "postId"],
                "properties": {
                    "userId": {"type": "integer"},
                    "postId": {"type": "integer"}
                }
            },
            servers=[{"url": "https://api.example.com"}]
        )
        self.invoker = EndpointInvoker(self.endpoint)

    @patch('swagger_mcp.endpoint_invoker.requests.request')
    def test_path_parameter_substitution(self, mock_request):
        # Setup mock response
        mock_response = MagicMock()
        mock_request.return_value = mock_response

        # Call the endpoint with path parameters
        path_params = {
            "userId": 123,
            "postId": 456
        }
        self.invoker.invoke(path_params=path_params)

        # Verify the request was made with the correct URL
        mock_request.assert_called_once()
        call_args = mock_request.call_args[1]  # Get kwargs from the call
        self.assertEqual(
            call_args["url"],
            "https://api.example.com/users/123/posts/456"
        )

    @patch('swagger_mcp.endpoint_invoker.requests.request')
    def test_missing_path_parameter(self, mock_request):
        # Test that missing required path parameters raise an error
        path_params = {
            "userId": 123
            # Missing postId
        }
        with self.assertRaises(Exception) as context:
            self.invoker.invoke(path_params=path_params)

if __name__ == '__main__':
    unittest.main()