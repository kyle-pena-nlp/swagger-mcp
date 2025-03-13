import requests
from typing import Dict, List, Any, Optional, Union
from endpoint import Endpoint
from simple_endpoint import SimpleEndpoint, create_simple_endpoint


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
        
        # Extract path, query, and body parameters
        path_params = simple_endpoint.get_path_parameters(params) if params else {}
        query_params = simple_endpoint.get_query_parameters(params) if params else {}
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
        request_body = self._validate_request_body(request_body, endpoint_to_use)
        
        # Get HTTP method
        method = endpoint_to_use.method
        
        # Make the request
        return requests.request(
            method=method,
            url=url,
            params=query_params,
            headers=headers,
            json=request_body if request_body is not None else None,
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
        if endpoint_to_use.requires_bearer_auth:
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
        query_params = query_params or {}
        
        # Different validation for SimpleEndpoint vs Endpoint
        if isinstance(endpoint_to_use, SimpleEndpoint):
            # SimpleEndpoint required params are validated in invoke_with_params
            pass
        else:
            # Regular Endpoint has separate query parameter tracking
            required_params = endpoint_to_use.get_required_parameters()
            for param_name in required_params.get('query', set()):
                if param_name not in query_params:
                    raise MissingQueryParameterError(param_name)
                
        return query_params
    
    def _validate_request_body(self, 
                              request_body: Optional[Any],
                              endpoint_to_use: Union[Endpoint, SimpleEndpoint]) -> Optional[Any]:
        """
        Validate that a request body is provided if required.
        
        Args:
            request_body: Body of the request
            endpoint_to_use: The endpoint to use for validation
            
        Returns:
            Validated request body
            
        Raises:
            MissingRequestBodyError: If a request body is required but not provided
        """
        # For SimpleEndpoint, we don't validate request body here as it's done in invoke_with_params
        # For regular Endpoint, check if request body is required
        if isinstance(endpoint_to_use, Endpoint) and endpoint_to_use.requires_request_body() and request_body is None:
            raise MissingRequestBodyError()
            
        return request_body 