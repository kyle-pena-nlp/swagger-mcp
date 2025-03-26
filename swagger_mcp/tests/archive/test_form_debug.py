import unittest
from unittest.mock import patch, MagicMock, call
import json
from endpoint import Endpoint
from endpoint_invoker import EndpointInvoker

class TestFormDebug(unittest.TestCase):
    """Debug tests for form parameter handling."""

    def setUp(self):
        """Set up test data."""
        # Create a simple form endpoint manually
        self.form_endpoint = Endpoint(
            path="/form",
            method="POST",
            operation_id="submitForm",
            summary="Submit a form",
            servers=[{"url": "https://api.example.com"}],
            form_parameters_schema={
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "email": {"type": "string"}
                },
                "required": ["name", "email"]
            },
            request_content_types=["application/x-www-form-urlencoded"]
        )

    @patch('endpoint_invoker.requests.request')
    def test_form_urlencoded_debug(self, mock_request):
        """Simplified test for form urlencoded data."""
        # Setup the mock
        mock_response = MagicMock()
        mock_request.return_value = mock_response
        
        # Create invoker
        invoker = EndpointInvoker(self.form_endpoint)
        
        # Form data
        form_data = {
            "name": "John Doe",
            "email": "john@example.com"
        }
        
        # Invoke the endpoint
        invoker.invoke(form_params=form_data)
        
        # Print the call arguments for debugging
        print("\n--- DEBUG: Mock call arguments ---")
        print(f"Called with: {mock_request.call_args}")
        
        # Check if the request was properly formed
        mock_request.assert_called_once()
        call_args = mock_request.call_args[1]
        
        print(f"Headers: {call_args.get('headers', {})}")
        print(f"Data: {call_args.get('data', None)}")
        print(f"JSON: {call_args.get('json', None)}")
        print(f"Files: {call_args.get('files', None)}")
        
        # Make explicit assertions
        self.assertEqual(call_args['url'], 'https://api.example.com/form')
        self.assertEqual(call_args['method'], 'POST')
        self.assertEqual(call_args['data'], form_data)
        self.assertEqual(call_args['headers'].get('Content-Type'), 'application/x-www-form-urlencoded')
        self.assertIsNone(call_args['json'])

if __name__ == '__main__':
    unittest.main() 