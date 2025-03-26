import unittest
from unittest.mock import patch, MagicMock
from swagger_mcp.endpoint import Endpoint
from swagger_mcp.endpoint_invoker import EndpointInvoker

class TestFormDataVariables(unittest.TestCase):
    def setUp(self):
        # Create a test endpoint with multipart form data parameters
        self.endpoint = Endpoint(
            path="/upload",
            method="POST",
            operation_id="uploadFile",
            summary="Upload a file with metadata",
            form_parameters_schema={
                "type": "object",
                "required": ["file", "description"],
                "properties": {
                    "file": {
                        "type": "string",
                        "format": "binary"
                    },
                    "description": {
                        "type": "string"
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"}
                    }
                }
            },
            request_content_types=["multipart/form-data"],
            servers=[{"url": "https://api.example.com"}]
        )
        self.invoker = EndpointInvoker(self.endpoint)

    @patch('swagger_mcp.endpoint_invoker.requests.request')
    def test_multipart_file_upload(self, mock_request):
        # Setup mock response
        mock_response = MagicMock()
        mock_request.return_value = mock_response

        # Simulate file content
        file_content = b"Hello, World!"
        
        # Call the endpoint with form data including a file
        form_params = {
            "file": ("test.txt", file_content, "text/plain"),
            "description": "Test file upload"
        }
        self.invoker.invoke(form_params=form_params)

        # Verify the request was made with the correct parameters
        mock_request.assert_called_once()
        call_args = mock_request.call_args[1]
        
        # Check that files were properly included
        self.assertIn("files", call_args)
        self.assertEqual(call_args["files"]["file"], ("test.txt", file_content, "text/plain"))
        
        # Check that other form fields were included
        self.assertIn("data", call_args)
        self.assertEqual(call_args["data"]["description"], "Test file upload")

    @patch('swagger_mcp.endpoint_invoker.requests.request')
    def test_mixed_form_data(self, mock_request):
        # Setup mock response
        mock_response = MagicMock()
        mock_request.return_value = mock_response

        # Call the endpoint with mixed form data (file and array field)
        form_params = {
            "file": ("test.txt", b"Hello, World!", "text/plain"),
            "description": "Test with tags",
            "tags": ["test", "example"]
        }
        self.invoker.invoke(form_params=form_params)

        # Verify the request was made with all fields
        mock_request.assert_called_once()
        call_args = mock_request.call_args[1]
        
        # Check that both file and regular form fields are present
        self.assertIn("files", call_args)
        self.assertIn("data", call_args)
        self.assertEqual(call_args["data"]["description"], "Test with tags")
        self.assertEqual(call_args["data"]["tags"], ["test", "example"])

    @patch('swagger_mcp.endpoint_invoker.requests.request')
    def test_missing_required_form_parameter(self, mock_request):
        # Test that missing required form parameters raise an error
        form_params = {
            # Missing required 'file' parameter
            "description": "Test missing file"
        }
        with self.assertRaises(Exception) as context:
            self.invoker.invoke(form_params=form_params)

    @patch('swagger_mcp.endpoint_invoker.requests.request')
    def test_file_upload_with_custom_headers(self, mock_request):
        # Setup mock response
        mock_response = MagicMock()
        mock_request.return_value = mock_response

        # Call the endpoint with minimal form data and custom headers
        form_params = {
            "file": ("test.txt", b"Hello", "text/plain"),
            "description": "Test with headers"
        }
        headers = {
            "X-Custom-Header": "test-value"
        }
        self.invoker.invoke(form_params=form_params, headers=headers)

        # Verify request was made with custom headers preserved
        mock_request.assert_called_once()
        call_args = mock_request.call_args[1]
        self.assertIn("headers", call_args)
        self.assertEqual(call_args["headers"]["X-Custom-Header"], "test-value")

if __name__ == '__main__':
    unittest.main()