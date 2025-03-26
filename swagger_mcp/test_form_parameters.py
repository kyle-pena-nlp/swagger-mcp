import unittest
from unittest.mock import patch, MagicMock
import json
import os
from typing import Dict, Any

from endpoint import Endpoint
from openapi_parser import OpenAPIParser
from endpoint_invoker import (
    EndpointInvoker,
    MissingFormParameterError
)

class TestFormParameters(unittest.TestCase):
    """Tests for formData parameter handling in OpenAPI parser and endpoint invoker."""

    def setUp(self):
        """Set up test OpenAPI spec with formData parameters."""
        # Create an OpenAPI 2.0 spec with formData parameters
        self.swagger_spec = {
            "swagger": "2.0",
            "info": {
                "version": "1.0.0",
                "title": "File Upload API",
                "description": "API for file uploads"
            },
            "host": "api.example.com",
            "basePath": "/v1",
            "schemes": ["https"],
            "paths": {
                "/files/upload": {
                    "post": {
                        "summary": "Upload a file",
                        "operationId": "uploadFile",
                        "consumes": [
                            "multipart/form-data"
                        ],
                        "parameters": [
                            {
                                "name": "file",
                                "in": "formData",
                                "description": "The file to upload",
                                "required": True,
                                "type": "file"
                            },
                            {
                                "name": "description",
                                "in": "formData",
                                "description": "Description of the file",
                                "required": False,
                                "type": "string"
                            }
                        ],
                        "responses": {
                            "200": {
                                "description": "File uploaded successfully"
                            }
                        }
                    }
                },
                "/form/submit": {
                    "post": {
                        "summary": "Submit a form",
                        "operationId": "submitForm",
                        "consumes": [
                            "application/x-www-form-urlencoded"
                        ],
                        "parameters": [
                            {
                                "name": "name",
                                "in": "formData",
                                "description": "User's name",
                                "required": True,
                                "type": "string"
                            },
                            {
                                "name": "email",
                                "in": "formData",
                                "description": "User's email",
                                "required": True,
                                "type": "string",
                                "format": "email"
                            },
                            {
                                "name": "age",
                                "in": "formData",
                                "description": "User's age",
                                "required": False,
                                "type": "integer",
                                "format": "int32"
                            }
                        ],
                        "responses": {
                            "200": {
                                "description": "Form submitted successfully"
                            }
                        }
                    }
                }
            }
        }
        
        # Save the spec to a file for testing file loading
        with open('formdata_api.json', 'w') as f:
            json.dump(self.swagger_spec, f)

        # Create the parser instance
        self.parser = OpenAPIParser(self.swagger_spec)
        
        # Also create a manual Endpoint with form parameters for direct testing
        self.form_endpoint = Endpoint(
            path="/manual/form",
            method="POST",
            operation_id="manualFormSubmit",
            summary="Manual form submission",
            servers=[{"url": "https://api.example.com"}],
            form_parameters_schema={
                "type": "object",
                "properties": {
                    "username": {"type": "string"},
                    "password": {"type": "string"},
                    "remember": {"type": "boolean"}
                },
                "required": ["username", "password"]
            },
            request_content_types=["application/x-www-form-urlencoded"]
        )

    def tearDown(self):
        """Clean up test files."""
        if os.path.exists('formdata_api.json'):
            os.remove('formdata_api.json')

    def test_parser_detects_form_parameters(self):
        """Test that the parser correctly detects and extracts formData parameters."""
        # Get the upload file endpoint
        upload_endpoint = self.parser.get_endpoint_by_operation_id('uploadFile')
        
        # Check that form parameters were detected
        self.assertIsNotNone(upload_endpoint.form_parameters_schema)
        
        # Check the properties of the form parameters
        properties = upload_endpoint.form_parameters_schema['properties']
        self.assertIn('file', properties)
        self.assertIn('description', properties)
        
        # Check required parameters
        self.assertIn('required', upload_endpoint.form_parameters_schema)
        self.assertIn('file', upload_endpoint.form_parameters_schema['required'])
        self.assertNotIn('description', upload_endpoint.form_parameters_schema['required'])
        
        # Check content types
        self.assertIn('multipart/form-data', upload_endpoint.request_content_types)

    def test_parser_detects_form_urlencoded_parameters(self):
        """Test that the parser correctly detects and extracts form urlencoded parameters."""
        # Get the submit form endpoint
        submit_endpoint = self.parser.get_endpoint_by_operation_id('submitForm')
        
        # Check that form parameters were detected
        self.assertIsNotNone(submit_endpoint.form_parameters_schema)
        
        # Check the properties of the form parameters
        properties = submit_endpoint.form_parameters_schema['properties']
        self.assertIn('name', properties)
        self.assertIn('email', properties)
        self.assertIn('age', properties)
        
        # Check required parameters
        self.assertIn('required', submit_endpoint.form_parameters_schema)
        self.assertIn('name', submit_endpoint.form_parameters_schema['required'])
        self.assertIn('email', submit_endpoint.form_parameters_schema['required'])
        self.assertNotIn('age', submit_endpoint.form_parameters_schema['required'])
        
        # Check content types
        self.assertIn('application/x-www-form-urlencoded', submit_endpoint.request_content_types)

    def test_get_endpoints_with_form_parameters(self):
        """Test the convenience method to get endpoints with form parameters."""
        # Get all endpoints with form parameters
        form_endpoints = self.parser.get_endpoints_with_form_parameters()
        
        # Should find exactly 2 endpoints with form parameters
        self.assertEqual(len(form_endpoints), 2)
        
        # Check that the correct endpoints were found
        operation_ids = [endpoint.operation_id for endpoint in form_endpoints]
        self.assertIn('uploadFile', operation_ids)
        self.assertIn('submitForm', operation_ids)

    @patch('endpoint_invoker.requests.request')
    def test_invoke_with_form_urlencoded(self, mock_request):
        """Test invoking an endpoint with application/x-www-form-urlencoded data."""
        # Setup the mock
        mock_response = MagicMock()
        mock_request.return_value = mock_response
        
        # Get the submit form endpoint
        submit_endpoint = self.parser.get_endpoint_by_operation_id('submitForm')
        
        # Create invoker and call invoke with form parameters
        invoker = EndpointInvoker(submit_endpoint)
        form_data = {
            "name": "John Doe",
            "email": "john@example.com",
            "age": 30
        }
        
        # Use server URL from test spec
        response = invoker.invoke(
            server_url="https://api.example.com/v1",
            form_params=form_data
        )
        
        # Check that requests.request was called with the correct parameters
        mock_request.assert_called_once()
        call_args = mock_request.call_args[1]
        
        # Check URL
        self.assertEqual(call_args['url'], 'https://api.example.com/v1/form/submit')
        
        # Check that data parameter contains the form data
        self.assertEqual(call_args['data'], form_data)
        
        # Check content type
        self.assertEqual(call_args['headers']['Content-Type'], 'application/x-www-form-urlencoded')
        
        # No JSON data should be sent
        self.assertIsNone(call_args['json'])

    @patch('endpoint_invoker.requests.request')
    def test_invoke_with_multipart_form_data(self, mock_request):
        """Test invoking an endpoint with multipart/form-data."""
        # Setup the mock
        mock_response = MagicMock()
        mock_request.return_value = mock_response
        
        # Get the upload file endpoint
        upload_endpoint = self.parser.get_endpoint_by_operation_id('uploadFile')
        
        # Create invoker and call invoke with form parameters
        invoker = EndpointInvoker(upload_endpoint)
        form_data = {
            "file": "file_content",  # In a real case, this would be a file object
            "description": "Test file"
        }
        
        # Use server URL from test spec
        response = invoker.invoke(
            server_url="https://api.example.com/v1",
            form_params=form_data
        )
        
        # Check that requests.request was called with the correct parameters
        mock_request.assert_called_once()
        call_args = mock_request.call_args[1]
        
        # Check URL
        self.assertEqual(call_args['url'], 'https://api.example.com/v1/files/upload')
        
        # Check that files parameter contains the form data
        self.assertEqual(call_args['files'], form_data)
        
        # Content-Type header should be removed to let requests set it with boundary parameter
        self.assertNotIn('Content-Type', call_args['headers'])
        
        # No JSON data should be sent
        self.assertIsNone(call_args['json'])

    def test_missing_required_form_parameter(self):
        """Test that an exception is raised when a required form parameter is missing."""
        invoker = EndpointInvoker(self.form_endpoint)
        
        # Should raise MissingFormParameterError because 'username' is required
        with self.assertRaises(MissingFormParameterError) as context:
            invoker.invoke(form_params={"password": "secret"})
            
        # Check that the exception has the correct parameter name
        self.assertEqual(context.exception.param_name, 'username')

    @patch('endpoint_invoker.requests.request')
    def test_invoke_with_params_form_data(self, mock_request):
        """Test invoking an endpoint with combined parameters including form data."""
        # Setup the mock
        mock_response = MagicMock()
        mock_request.return_value = mock_response
        
        # Create invoker for the manual form endpoint
        invoker = EndpointInvoker(self.form_endpoint)
        
        # Combined parameters
        params = {
            "username": "user123",
            "password": "secret",
            "remember": True
        }
        
        # Invoke with combined parameters
        response = invoker.invoke_with_params(params)
        
        # Check that requests.request was called with the correct parameters
        mock_request.assert_called_once()
        call_args = mock_request.call_args[1]
        
        # Check that data parameter contains the form data
        expected_form_data = {
            "username": "user123",
            "password": "secret",
            "remember": True
        }
        self.assertEqual(call_args['data'], expected_form_data)
        
        # Check content type
        self.assertEqual(call_args['headers']['Content-Type'], 'application/x-www-form-urlencoded')


if __name__ == '__main__':
    unittest.main() 