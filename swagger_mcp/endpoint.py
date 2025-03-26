from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Set


@dataclass
class Endpoint:
    """
    A dataclass representing an API endpoint from an OpenAPI specification.
    Contains all information needed to programmatically invoke the endpoint.
    """
    # Basic endpoint information
    path: str
    method: str
    operation_id: str
    summary: str
    description: str = ""
    deprecated: bool = False
    
    # Server information
    servers: List[Dict[str, Any]] = field(default_factory=list)
    
    # Authentication and security
    requires_bearer_auth: bool = False
    requires_oauth: bool = False  # Indicates if OAuth flow authentication is required
    security_requirements: List[Dict[str, List[str]]] = field(default_factory=list)
    oauth_scopes: List[str] = field(default_factory=list)  # OAuth scopes required for this endpoint
    
    # Request information
    request_body_schema: Optional[Dict[str, Any]] = None
    request_body_required: bool = False
    request_content_types: List[str] = field(default_factory=list)
    query_parameters_schema: Optional[Dict[str, Any]] = None
    path_parameters_schema: Optional[Dict[str, Any]] = None
    header_parameters_schema: Optional[Dict[str, Any]] = None
    form_parameters_schema: Optional[Dict[str, Any]] = None
    
    # Response information
    responses: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    response_content_types: List[str] = field(default_factory=list)
    
    # Additional metadata
    tags: List[str] = field(default_factory=list)
    
    @property
    def endpoint_key(self) -> str:
        """
        Generate a unique key for this endpoint based on method and path.
        
        Returns:
            A string in the format "METHOD /path"
        """
        return f"{self.method} {self.path}"
    
    @property
    def default_server_url(self) -> Optional[str]:
        """
        Get the default server URL for this endpoint, if available.
        
        Returns:
            The URL string or None if no servers are defined
        """
        if self.servers and 'url' in self.servers[0]:
            return self.servers[0]['url']
        return None
    
    def get_full_url(self, server_url: Optional[str] = None, path_params: Optional[Dict[str, Any]] = None) -> str:
        """
        Construct the full URL for this endpoint with path parameters substituted.
        
        Args:
            server_url: Server URL to use (defaults to the first server in the servers list)
            path_params: Dictionary of path parameter values to substitute
        
        Returns:
            The complete URL string
        """
        base_url = server_url or self.default_server_url or ""
        
        # Remove trailing slash from base URL if present
        if base_url and base_url.endswith('/'):
            base_url = base_url[:-1]
            
        # Ensure path starts with slash
        endpoint_path = self.path
        if not endpoint_path.startswith('/'):
            endpoint_path = '/' + endpoint_path
            
        # Substitute path parameters if provided
        if path_params:
            for param_name, param_value in path_params.items():
                placeholder = '{' + param_name + '}'
                endpoint_path = endpoint_path.replace(placeholder, str(param_value))
        
        return f"{base_url}{endpoint_path}"
    
    def requires_request_body(self) -> bool:
        """
        Check if this endpoint requires a request body.
        
        Returns:
            True if a request body is required, False otherwise
        """
        return self.request_body_required and self.request_body_schema is not None
    
    def get_required_parameters(self) -> Dict[str, Set[str]]:
        """
        Get a dictionary of all required parameters grouped by parameter type.
        
        Returns:
            Dictionary with keys 'path', 'query', 'header', 'form' and values as sets of parameter names
        """
        required_params = {
            'path': set(),
            'query': set(),
            'header': set(),
            'form': set()
        }
        
        # Path parameters - these are usually all required in OpenAPI
        if self.path_parameters_schema and 'required' in self.path_parameters_schema:
            required_params['path'] = set(self.path_parameters_schema['required'])
            
        # Query parameters
        if self.query_parameters_schema and 'required' in self.query_parameters_schema:
            required_params['query'] = set(self.query_parameters_schema['required'])
            
        # Header parameters
        if self.header_parameters_schema and 'required' in self.header_parameters_schema:
            required_params['header'] = set(self.header_parameters_schema['required'])
            
        # Form parameters
        if self.form_parameters_schema and 'required' in self.form_parameters_schema:
            required_params['form'] = set(self.form_parameters_schema['required'])
            
        return required_params
    
    def get_successful_response_schema(self) -> Optional[Dict[str, Any]]:
        """
        Get the schema for a successful response (2xx status code).
        
        Returns:
            Response schema or None if no successful response is defined
        """
        # Look for 200, 201, etc. responses
        for status_code in ['200', '201', '202', '203', '204', '205', '206']:
            if status_code in self.responses:
                response = self.responses[status_code]
                if 'content' in response:
                    for content_type in response['content']:
                        if 'schema' in response['content'][content_type]:
                            return response['content'][content_type]['schema']
        return None 