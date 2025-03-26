from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Set
from swagger_mcp.endpoint import Endpoint
from swagger_mcp.logging import setup_logger

logger = setup_logger(__name__)

@dataclass
class SimpleEndpoint:
    """
    A simplified representation of an API endpoint where path parameters,
    query parameters, and request body are combined into a single parameter object.
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
    
    # Combined parameter information
    combined_parameter_schema: Dict[str, Any] = field(default_factory=dict)
    
    # Parameter type mapping
    parameter_type_mapping: Dict[str, str] = field(default_factory=dict)
    
    # Content type information
    request_content_types: List[str] = field(default_factory=list)
    response_content_types: List[str] = field(default_factory=list)
    
    # Response information
    responses: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
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
    
    def get_full_url(self, server_url: Optional[str] = None, params: Optional[Dict[str, Any]] = None) -> str:
        """
        Construct the full URL for this endpoint with path parameters substituted.
        
        Args:
            server_url: Server URL to use (defaults to the first server in the servers list)
            params: Dictionary of combined parameters (path parameters will be extracted)
        
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
        if params:
            path_params = {k: v for k, v in params.items() 
                          if k in self.parameter_type_mapping and self.parameter_type_mapping[k] == 'path'}
            
            for param_name, param_value in path_params.items():
                placeholder = '{' + param_name + '}'
                endpoint_path = endpoint_path.replace(placeholder, str(param_value))
        
        return f"{base_url}{endpoint_path}"
    
    def get_required_parameters(self) -> Set[str]:
        """
        Get a set of all required parameters.
        
        Returns:
            Set of required parameter names
        """
        required_params = set()
        
        if 'required' in self.combined_parameter_schema:
            required_params = set(self.combined_parameter_schema['required'])
            
        return required_params
    
    def get_path_parameters(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract path parameters from the combined parameters.
        
        Args:
            params: Combined parameters dictionary
            
        Returns:
            Dictionary containing only path parameters
        """
        return {k: v for k, v in params.items() 
                if k in self.parameter_type_mapping and self.parameter_type_mapping[k] == 'path'}
    
    def get_query_parameters(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract query parameters from the combined parameters.
        
        Args:
            params: Combined parameters dictionary
            
        Returns:
            Dictionary containing only query parameters
        """
        return {k: v for k, v in params.items() 
                if k in self.parameter_type_mapping and self.parameter_type_mapping[k] == 'query'}
    
    def get_form_parameters(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract form parameters from the combined parameters.
        
        Args:
            params: Combined parameters dictionary
            
        Returns:
            Dictionary containing only form parameters
        """
        return {k: v for k, v in params.items() 
                if k in self.parameter_type_mapping and self.parameter_type_mapping[k] == 'form'}
    
    def get_request_body(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract request body parameters from the combined parameters.
        
        Args:
            params: Combined parameters dictionary
            
        Returns:
            Dictionary containing only request body parameters
        """
        # Parameters that are not path, query, or form are considered request body parameters
        return {k: v for k, v in params.items() 
                if k not in self.parameter_type_mapping or self.parameter_type_mapping[k] == 'body'}
    

def create_simple_endpoint(endpoint: Endpoint) -> SimpleEndpoint:
    """
    Transform a regular Endpoint into a SimpleEndpoint with combined parameters.
    
    Args:
        endpoint: The original Endpoint object
        
    Returns:
        A new SimpleEndpoint object with combined parameter schema
    """
    # Create a parameter mapping to track where each parameter belongs
    parameter_type_mapping = {}
    
    # Start building the combined schema
    combined_schema = {
        'type': 'object',
        'properties': {},
        'required': []
    }
    
    # Add path parameters to the combined schema
    if endpoint.path_parameters_schema and 'properties' in endpoint.path_parameters_schema:
        for param_name, param_schema in endpoint.path_parameters_schema['properties'].items():
            combined_schema['properties'][param_name] = param_schema
            parameter_type_mapping[param_name] = 'path'
            
        # Add required path parameters
        if 'required' in endpoint.path_parameters_schema:
            combined_schema['required'].extend(endpoint.path_parameters_schema['required'])
    
    # Add query parameters to the combined schema
    if endpoint.query_parameters_schema and 'properties' in endpoint.query_parameters_schema:
        for param_name, param_schema in endpoint.query_parameters_schema['properties'].items():
            combined_schema['properties'][param_name] = param_schema
            parameter_type_mapping[param_name] = 'query'
            
        # Add required query parameters
        if 'required' in endpoint.query_parameters_schema:
            combined_schema['required'].extend(endpoint.query_parameters_schema['required'])
    
    # Add form parameters to the combined schema
    if endpoint.form_parameters_schema and 'properties' in endpoint.form_parameters_schema:
        for param_name, param_schema in endpoint.form_parameters_schema['properties'].items():
            combined_schema['properties'][param_name] = param_schema
            parameter_type_mapping[param_name] = 'form'
            
        # Add required form parameters
        if 'required' in endpoint.form_parameters_schema:
            combined_schema['required'].extend(endpoint.form_parameters_schema['required'])
    
    # Add request body parameters to the combined schema
    if endpoint.request_body_schema:
        # For simplicity, we'll assume JSON content type and look for a schema
        if 'properties' in endpoint.request_body_schema:
            for param_name, param_schema in endpoint.request_body_schema['properties'].items():
                combined_schema['properties'][param_name] = param_schema
                parameter_type_mapping[param_name] = 'body'
            
            # Add required body parameters
            if 'required' in endpoint.request_body_schema:
                combined_schema['required'].extend(endpoint.request_body_schema['required'])
    
    # Create the SimpleEndpoint with the combined schema
    return SimpleEndpoint(
        path=endpoint.path,
        method=endpoint.method,
        operation_id=endpoint.operation_id,
        summary=endpoint.summary,
        description=endpoint.description,
        deprecated=endpoint.deprecated,
        servers=endpoint.servers,
        requires_bearer_auth=endpoint.requires_bearer_auth,
        requires_oauth=endpoint.requires_oauth,
        oauth_scopes=endpoint.oauth_scopes,
        security_requirements=endpoint.security_requirements,
        combined_parameter_schema=combined_schema,
        parameter_type_mapping=parameter_type_mapping,
        request_content_types=endpoint.request_content_types,
        response_content_types=endpoint.response_content_types,
        responses=endpoint.responses,
        tags=endpoint.tags
    ) 