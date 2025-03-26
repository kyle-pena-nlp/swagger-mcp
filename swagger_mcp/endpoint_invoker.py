from logging.handlers import RotatingFileHandler
import requests, json
import logging
from typing import Dict, List, Any, Optional, Union
from swagger_mcp.endpoint import Endpoint
from swagger_mcp.simple_endpoint import SimpleEndpoint, create_simple_endpoint
from swagger_mcp.logging import setup_logger

logger = setup_logger(__name__)


class EndpointInvocationError(Exception):
    """Base exception for errors that occur during endpoint invocation."""
    pass


class MissingPathParameterError(EndpointInvocationError):
    """Exception raised when a required path parameter is missing."""
    def __init__(self, param_name: str):
        self.param_name = param_name
        super().__init__(f"Missing required path parameter: {param_name}")


class MissingQueryParameterError(EndpointInvocationError):
    """Exception raised when a required query parameter is missing."""
    def __init__(self, param_name: str):
        self.param_name = param_name
        super().__init__(f"Missing required query parameter: {param_name}")


class MissingFormParameterError(EndpointInvocationError):
    """Exception raised when a required form parameter is missing."""
    def __init__(self, param_name: str):
        self.param_name = param_name
        super().__init__(f"Missing required form parameter: {param_name}")


class MissingHeaderParameterError(EndpointInvocationError):
    """Exception raised when a required header parameter is missing."""
    def __init__(self, param_name: str):
        self.param_name = param_name
        super().__init__(f"Missing required header parameter: {param_name}")


class MissingRequestBodyError(EndpointInvocationError):
    """Exception raised when a request body is required but not provided."""
    def __init__(self):
        super().__init__("Request body is required but was not provided")


class MissingBearerTokenError(EndpointInvocationError):
    """Exception raised when bearer token authentication is required but not provided."""
    def __init__(self):
        super().__init__("Bearer token is required but was not provided")


class MissingServerUrlError(EndpointInvocationError):
    """Exception raised when no server URL is available."""
    def __init__(self):
        super().__init__("No server URL available. Provide a server URL or ensure the endpoint has servers defined.")


class MissingRequiredParameterError(EndpointInvocationError):
    """Exception raised when a required parameter is missing."""
    def __init__(self, param_name: str):
        self.param_name = param_name
        super().__init__(f"Missing required parameter: {param_name}")


class InvalidRequestBodyError(EndpointInvocationError):
    """Exception raised when a request body is invalid."""
    def __init__(self, message: str):
        super().__init__(f"Invalid request body: {message}")


class EndpointInvoker:
    """Class for programmatically invoking API endpoints described by Endpoint objects."""
    
    def __init__(self, endpoint: Union[Endpoint, SimpleEndpoint]):
        """
        Initialize the invoker with an endpoint.
        
        Args:
            endpoint: The Endpoint or SimpleEndpoint object describing the API endpoint to invoke
        """
        if isinstance(endpoint, Endpoint):
            self.endpoint = endpoint
            self.simple_endpoint = create_simple_endpoint(endpoint)
        else:
            self.simple_endpoint = endpoint
            # We don't need the original endpoint if we're provided with a SimpleEndpoint
            self.endpoint = None
    
    def to_simple_endpoint(self) -> SimpleEndpoint:
        """
        Convert the endpoint to a SimpleEndpoint if it's not already.
        
        Returns:
            A SimpleEndpoint representation of the endpoint
        """
        if self.simple_endpoint:
            return self.simple_endpoint
        
        if self.endpoint:
            self.simple_endpoint = create_simple_endpoint(self.endpoint)
            return self.simple_endpoint
        
        raise ValueError("No endpoint available to convert")
    
    def invoke_with_params(self,
                          params: Dict[str, Any],
                          server_url: Optional[str] = None,
                          headers: Optional[Dict[str, str]] = None,
                          bearer_token: Optional[str] = None,
                          timeout: Optional[float] = None) -> requests.Response:
        """
        Invoke the endpoint with a single parameter object that contains path parameters,
        query parameters, and request body properties combined.
        
        Args:
            params: Combined dictionary containing path parameters, query parameters, and request body properties
            server_url: Server URL to use (overrides endpoint's servers)
            headers: HTTP headers to include in the request
            bearer_token: Bearer token for authentication
            timeout: Request timeout in seconds
            
        Returns:
            Response object from the requests library
            
        Raises:
            Various EndpointInvocationError subclasses for validation failures
        """
        # Ensure we have a SimpleEndpoint to work with
        simple_endpoint = self.to_simple_endpoint()
        
        # Validate required parameters
        if params:
            required_params = simple_endpoint.get_required_parameters()
            for param_name in required_params:
                if param_name not in params:
                    raise MissingRequiredParameterError(param_name)
        
        # Extract path, query, form, and body parameters
        path_params = simple_endpoint.get_path_parameters(params) if params else {}
        query_params = simple_endpoint.get_query_parameters(params) if params else {}
        form_params = simple_endpoint.get_form_parameters(params) if params else {}
        request_body = simple_endpoint.get_request_body(params) if params else None
        
        # If we have a request body but it's empty, set it to None unless it's required
        if request_body and not request_body:
            if not self.endpoint or not self.endpoint.request_body_required:
                request_body = None
        
        # Call the regular invoke method with the separated parameters
        return self._invoke_internal(
            server_url=server_url,
            path_params=path_params,
            query_params=query_params,
            form_params=form_params,
            headers=headers,
            request_body=request_body,
            bearer_token=bearer_token,
            timeout=timeout,
            simple_endpoint=simple_endpoint
        )
        
    def invoke(self, 
               server_url: Optional[str] = None,
               path_params: Optional[Dict[str, Any]] = None,
               query_params: Optional[Dict[str, Any]] = None,
               form_params: Optional[Dict[str, Any]] = None,
               headers: Optional[Dict[str, str]] = None,
               request_body: Optional[Any] = None,
               bearer_token: Optional[str] = None,
               timeout: Optional[float] = None) -> requests.Response:
        """
        Invoke the endpoint with the provided parameters.
        
        Args:
            server_url: Server URL to use (overrides endpoint's servers)
            path_params: Parameters to substitute in the path
            query_params: Query parameters to include in the URL
            form_params: Form data parameters (for multipart/form-data or application/x-www-form-urlencoded)
            headers: HTTP headers to include in the request
            request_body: Body of the request (for POST, PUT, PATCH)
            bearer_token: Bearer token for authentication
            timeout: Request timeout in seconds
            
        Returns:
            Response object from the requests library
            
        Raises:
            Various EndpointInvocationError subclasses for validation failures
        """
        # Use the original endpoint if available, otherwise use the SimpleEndpoint
        endpoint_to_use = self.endpoint if self.endpoint else self.simple_endpoint
        
        # Call the internal invoke method
        return self._invoke_internal(
            server_url=server_url,
            path_params=path_params,
            query_params=query_params,
            form_params=form_params,
            headers=headers,
            request_body=request_body,
            bearer_token=bearer_token,
            timeout=timeout,
            simple_endpoint=None
        )
    
    def _invoke_internal(self,
                        server_url: Optional[str] = None,
                        path_params: Optional[Dict[str, Any]] = None,
                        query_params: Optional[Dict[str, Any]] = None,
                        form_params: Optional[Dict[str, Any]] = None,
                        headers: Optional[Dict[str, str]] = None,
                        request_body: Optional[Any] = None,
                        bearer_token: Optional[str] = None,
                        timeout: Optional[float] = None,
                        simple_endpoint: Optional[SimpleEndpoint] = None) -> requests.Response:
        """
        Internal method to invoke the endpoint with the provided parameters.
        
        Args:
            server_url: Server URL to use (overrides endpoint's servers)
            path_params: Parameters to substitute in the path
            query_params: Query parameters to include in the URL
            form_params: Form data parameters (for multipart/form-data or application/x-www-form-urlencoded)
            headers: HTTP headers to include in the request
            request_body: Body of the request (for POST, PUT, PATCH)
            bearer_token: Bearer token for authentication
            timeout: Request timeout in seconds
            simple_endpoint: Optional SimpleEndpoint to use instead of self.endpoint
            
        Returns:
            Response object from the requests library
            
        Raises:
            Various EndpointInvocationError subclasses for validation failures
        """
        # Determine which endpoint to use
        endpoint_to_use = simple_endpoint if simple_endpoint else (self.endpoint if self.endpoint else self.simple_endpoint)
        
        # Validate and prepare all request components
        url = self._build_url(server_url, path_params, endpoint_to_use)
        headers = self._prepare_headers(headers, bearer_token, endpoint_to_use)
        query_params = self._validate_query_params(query_params, endpoint_to_use)
        form_params = self._validate_form_params(form_params, endpoint_to_use)
        request_body = self._validate_request_body(request_body, endpoint_to_use)
        
        # Get HTTP method
        method = endpoint_to_use.method
        
        # Determine content type and data format
        content_type = None
        if headers and 'Content-Type' in headers:
            content_type = headers['Content-Type']
        elif hasattr(endpoint_to_use, 'request_content_types') and endpoint_to_use.request_content_types:
            # Use the first available content type as default
            content_type = endpoint_to_use.request_content_types[0]
            # Add content type to headers
            if headers is None:
                headers = {}
            headers['Content-Type'] = content_type
        
        # Prepare request based on content type
        data = None
        files = None
        json_data = None
        
        if form_params:
            if content_type == 'multipart/form-data':
                # For multipart/form-data, we need to remove the Content-Type header
                # and let requests set it with the boundary parameter
                if headers and 'Content-Type' in headers:
                    del headers['Content-Type']
                
                # Separate file fields from regular form fields
                files = {}
                data = {}
                
                for key, value in form_params.items():
                    # Check if the value represents a file (could be a file-like object or a tuple)
                    # Common file-like objects have 'read' and 'name' attributes
                    is_file = (hasattr(value, 'read') and callable(value.read)) or isinstance(value, tuple)
                    
                    if is_file:
                        files[key] = value
                    else:
                        data[key] = value
                
                # If no files were found, treat all as regular form data
                if not files:
                    data = form_params
                    files = None
            elif content_type == 'application/x-www-form-urlencoded':
                data = form_params
            else:
                # Default to application/x-www-form-urlencoded if no specific content type is set
                data = form_params
        elif request_body is not None:
            if content_type and 'json' in content_type:
                json_data = request_body
            else:
                data = request_body
        
        # Create a detailed log message with all request components
        log_message = f"""
Request details:
  Method: {method}
  URL: {url}
  Query Parameters: {json.dumps(query_params, indent=2, default=str) if query_params else 'None'}
  Headers: {json.dumps({k: '***' if k.lower() in ('authorization', 'api-key', 'token') else v 
                        for k, v in headers.items()} if headers else {}, indent=2, default=str)}
  JSON Data: {json.dumps(json_data, indent=2, default=str) if json_data else 'None'}
  Form Data: {json.dumps(data, indent=2, default=str) if data else 'None'}
  Files: {json.dumps({k: f"<{type(v).__name__}>" for k, v in files.items()} if files else 'None', indent=2, default=str)}
  Timeout: {timeout}
  Bearer Token: {bearer_token}
"""
        logger.info(log_message)

        # Make the request
        return requests.request(
            method=method,
            url=url,
            params=query_params,
            headers=headers,
            json=json_data,
            data=data,
            files=files,
            timeout=timeout
        )
    
    def _build_url(self, 
                  server_url: Optional[str], 
                  path_params: Optional[Dict[str, Any]],
                  endpoint_to_use: Union[Endpoint, SimpleEndpoint]) -> str:
        """
        Build the full URL for the request, validating path parameters.
        
        Args:
            server_url: Server URL to use (overrides endpoint's servers)
            path_params: Parameters to substitute in the path
            endpoint_to_use: The endpoint to use for building the URL
            
        Returns:
            Full URL for the request
            
        Raises:
            MissingPathParameterError: If a required path parameter is missing
            MissingServerUrlError: If no server URL is available
        """
        path_params = path_params or {}
        
        # Handle different endpoint types
        if isinstance(endpoint_to_use, SimpleEndpoint):
            # For SimpleEndpoint, use its get_full_url method with params
            url = endpoint_to_use.get_full_url(server_url, path_params)
        else:
            # For regular Endpoint, validate required parameters
            required_params = endpoint_to_use.get_required_parameters()
            for param_name in required_params.get('path', set()):
                if param_name not in path_params:
                    raise MissingPathParameterError(param_name)
            
            # Build the URL using the endpoint's method
            url = endpoint_to_use.get_full_url(server_url, path_params)
        
        # Ensure we have a valid URL (at least a server part)
        if not url or url.startswith('/'):
            raise MissingServerUrlError()
            
        return url
    
    def _prepare_headers(self, 
                        headers: Optional[Dict[str, str]], 
                        bearer_token: Optional[str],
                        endpoint_to_use: Union[Endpoint, SimpleEndpoint]) -> Dict[str, str]:
        """
        Prepare the headers for the request, including authentication.
        
        Args:
            headers: HTTP headers to include in the request
            bearer_token: Bearer token for authentication
            endpoint_to_use: The endpoint to use for header preparation
            
        Returns:
            Dictionary of headers to include in the request
            
        Raises:
            MissingBearerTokenError: If bearer token authentication is required but not provided
            MissingHeaderParameterError: If a required header parameter is missing
        """
        prepared_headers = headers.copy() if headers else {}
        
        # Check if bearer token is required
        auth_required = False
        
        if hasattr(endpoint_to_use, 'requires_bearer_auth') and endpoint_to_use.requires_bearer_auth:
            auth_required = True
            
        # Check if OAuth is required
        if hasattr(endpoint_to_use, 'requires_oauth') and endpoint_to_use.requires_oauth:
            auth_required = True
            
        if auth_required:
            if not bearer_token:
                raise MissingBearerTokenError()
            prepared_headers['Authorization'] = f"Bearer {bearer_token}"
        
        # Check required header parameters - different for SimpleEndpoint vs Endpoint
        if isinstance(endpoint_to_use, SimpleEndpoint):
            # SimpleEndpoint doesn't currently track header parameters separately
            pass
        else:
            # Regular Endpoint has separate header parameter tracking
            required_params = endpoint_to_use.get_required_parameters()
            for param_name in required_params.get('header', set()):
                # Convert to lowercase for case-insensitive header comparison
                if param_name.lower() not in [k.lower() for k in prepared_headers]:
                    raise MissingHeaderParameterError(param_name)
        
        # Add content type if sending a request body and content type is not already set
        request_content_types = endpoint_to_use.request_content_types
        
        if request_content_types and 'Content-Type' not in prepared_headers:
            # For SimpleEndpoint, we don't have a requires_request_body method
            if isinstance(endpoint_to_use, Endpoint) and not endpoint_to_use.requires_request_body():
                pass
            else:
                # For all other cases, add the content type
                prepared_headers['Content-Type'] = request_content_types[0]
            
        return prepared_headers
    
    def _validate_query_params(self, 
                              query_params: Optional[Dict[str, Any]],
                              endpoint_to_use: Union[Endpoint, SimpleEndpoint]) -> Dict[str, Any]:
        """
        Validate that all required query parameters are present.
        
        Args:
            query_params: Query parameters to include in the URL
            endpoint_to_use: The endpoint to use for validation
            
        Returns:
            Validated query parameters
            
        Raises:
            MissingQueryParameterError: If a required query parameter is missing
        """
        if not query_params:
            query_params = {}
            
        # Get required query parameters from the endpoint
        required_params = set()
        if hasattr(endpoint_to_use, 'get_required_parameters'):
            required_params_result = endpoint_to_use.get_required_parameters()
            if isinstance(required_params_result, dict):
                # Handle Endpoint case where result is Dict[str, Set[str]]
                required_params = required_params_result.get('query', set())
            else:
                # Handle SimpleEndpoint case where result is Set[str]
                # Only include parameters that are marked as query parameters in the mapping
                required_params = {param for param in required_params_result 
                                if hasattr(endpoint_to_use, 'parameter_type_mapping') and 
                                endpoint_to_use.parameter_type_mapping.get(param) == 'query'}
        
        # Check that all required parameters are present
        for param_name in required_params:
            if param_name not in query_params:
                raise MissingQueryParameterError(param_name)
        
        # Handle array parameters
        if hasattr(endpoint_to_use, 'parameters'):
            for param in endpoint_to_use.parameters:
                if param['in'] == 'query' and param['name'] in query_params:
                    value = query_params[param['name']]
                    if param['schema'].get('type') == 'array':
                        # For array parameters, create multiple entries with the same name
                        if isinstance(value, (list, tuple)):
                            query_params[param['name']] = value
                        else:
                            query_params[param['name']] = [value]
        
        return query_params
    
    def _validate_form_params(self, 
                          form_params: Optional[Dict[str, Any]],
                          endpoint_to_use: Union[Endpoint, SimpleEndpoint]) -> Dict[str, Any]:
        """
        Validate form parameters against the endpoint's form parameters schema.
        
        Args:
            form_params: Form parameters to validate
            endpoint_to_use: The endpoint containing the form parameter schema
            
        Returns:
            Validated form parameters (defaults to empty dict if None provided)
            
        Raises:
            MissingFormParameterError: If a required form parameter is missing
        """
        # Default to empty dict if None
        form_params = form_params or {}
        
        # Check if this is a SimpleEndpoint
        if isinstance(endpoint_to_use, SimpleEndpoint):
            # For SimpleEndpoint, we don't need to check further as all validation
            # is done at the combined parameter level in invoke_with_params
            return form_params
        
        # For regular Endpoint, check required form parameters
        if hasattr(endpoint_to_use, 'form_parameters_schema') and endpoint_to_use.form_parameters_schema:
            if 'required' in endpoint_to_use.form_parameters_schema:
                for param_name in endpoint_to_use.form_parameters_schema['required']:
                    if param_name not in form_params:
                        raise MissingFormParameterError(param_name)
        
        return form_params
    
    def _validate_request_body(self, 
                          request_body: Optional[Any],
                          endpoint_to_use: Union[Endpoint, SimpleEndpoint]) -> Optional[Any]:
        """
        Validate request body against the endpoint's request body schema.
        
        Args:
            request_body: Request body to validate
            endpoint_to_use: The endpoint containing the request body schema
            
        Returns:
            Validated request body (or None if not required)
            
        Raises:
            MissingRequestBodyError: If a request body is required but not provided
            InvalidRequestBodyError: If the request body is invalid
        """
        # Check if a request body is required
        requires_body = False
        if hasattr(endpoint_to_use, 'request_body_required'):
            requires_body = endpoint_to_use.request_body_required
        
        # If the body is required but not provided, raise an error
        if requires_body and request_body is None:
            raise MissingRequestBodyError()

        # If there's no request body schema or no request body, we're done
        if not hasattr(endpoint_to_use, 'request_body_schema') or not endpoint_to_use.request_body_schema or not request_body:
            return request_body

        # Get the schema from the endpoint and content type
        schema = endpoint_to_use.request_body_schema
        content_type = None
        if hasattr(endpoint_to_use, 'request_content_types') and endpoint_to_use.request_content_types:
            content_type = endpoint_to_use.request_content_types[0]

        # Extract the schema based on content type
        if content_type and schema:
            if 'content' in schema and content_type in schema['content']:
                content_schema = schema['content'][content_type].get('schema', {})
                
                # Check required fields
                if 'required' in content_schema and isinstance(content_schema['required'], list):
                    for field in content_schema['required']:
                        if field not in request_body:
                            raise InvalidRequestBodyError(f"Missing required field: {field}")

                # Check field types and constraints
                if 'properties' in content_schema and isinstance(content_schema['properties'], dict):
                    for field, field_schema in content_schema['properties'].items():
                        if field in request_body:
                            value = request_body[field]
                            
                            # Check type
                            field_type = field_schema.get('type')
                            if field_type == 'string' and not isinstance(value, str):
                                raise InvalidRequestBodyError(f"Field '{field}' must be a string")
                            elif field_type == 'integer' and not isinstance(value, int):
                                raise InvalidRequestBodyError(f"Field '{field}' must be an integer")
                            elif field_type == 'array' and not isinstance(value, list):
                                raise InvalidRequestBodyError(f"Field '{field}' must be an array")
                            
                            # Check enum values
                            if 'enum' in field_schema and value not in field_schema['enum']:
                                raise InvalidRequestBodyError(f"Field '{field}' must be one of: {field_schema['enum']}")
                            
                            # Check minimum value for integers
                            if field_type == 'integer' and 'minimum' in field_schema and value < field_schema['minimum']:
                                raise InvalidRequestBodyError(f"Field '{field}' must be greater than or equal to {field_schema['minimum']}")

        return request_body