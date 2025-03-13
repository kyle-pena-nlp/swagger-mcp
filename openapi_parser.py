import json
import yaml
import os
from typing import Dict, List, Optional, Any, Union


class OpenAPIParser:
    """
    A class for parsing OpenAPI specifications and extracting endpoint information,
    including HTTP methods and JSON schemas for request bodies.
    """

    def __init__(self, spec: Union[str, dict]):
        """
        Initialize the parser with an OpenAPI specification.
        
        Args:
            spec: Either a file path to the OpenAPI spec (JSON or YAML),
                  a JSON string, or a dictionary containing the spec
        """
        self.spec = self._load_spec(spec)
        self.security_schemes = self._parse_security_schemes()
        self.global_security = self.spec.get('security', [])
        self.has_bearer_schemes = self._has_bearer_schemes()
        self.endpoints = self._parse_endpoints()

    def _has_bearer_schemes(self) -> bool:
        """
        Determine if any security schemes are bearer token schemes.
        
        Returns:
            True if at least one bearer token scheme is defined, False otherwise
        """
        return any(self._is_bearer_scheme(scheme_name) for scheme_name in self.security_schemes)

    def _load_spec(self, spec: Union[str, dict]) -> dict:
        """
        Load the OpenAPI specification from various input formats.
        
        Args:
            spec: File path, JSON string, or dictionary
            
        Returns:
            Dictionary containing the parsed OpenAPI spec
        """
        if isinstance(spec, dict):
            return spec
        
        if isinstance(spec, str):
            # Check if it looks like a file path
            if os.path.exists(spec) and (spec.endswith('.json') or spec.endswith('.yaml') or spec.endswith('.yml') or len(spec) < 256):
                try:
                    with open(spec, 'r') as f:
                        content = f.read()
                        if spec.endswith('.json'):
                            return json.loads(content)
                        elif spec.endswith(('.yaml', '.yml')):
                            return yaml.safe_load(content)
                        else:
                            # Try JSON first for files without extension
                            try:
                                return json.loads(content)
                            except json.JSONDecodeError:
                                return yaml.safe_load(content)
                except (FileNotFoundError, json.JSONDecodeError, yaml.YAMLError, OSError) as e:
                    # If file loading fails, fall through to string parsing
                    pass
            
            # Try to parse as JSON string
            try:
                return json.loads(spec)
            except json.JSONDecodeError:
                # Try to parse as YAML string
                try:
                    return yaml.safe_load(spec)
                except yaml.YAMLError:
                    raise ValueError("Could not parse the specification as file path, JSON, or YAML")
        
        raise ValueError("Specification must be a file path, JSON string, or dictionary")
    
    def _parse_security_schemes(self) -> Dict[str, Dict[str, Any]]:
        """
        Parse security schemes from the OpenAPI specification.
        
        Returns:
            Dictionary of security scheme names to their definitions
        """
        components = self.spec.get('components', {})
        return components.get('securitySchemes', {})
    
    def _is_bearer_scheme(self, scheme_name: str) -> bool:
        """
        Determine if a security scheme is a bearer token scheme.
        
        Args:
            scheme_name: The name of the security scheme
            
        Returns:
            True if the scheme is a bearer token scheme, False otherwise
        """
        scheme = self.security_schemes.get(scheme_name, {})
        return (
            scheme.get('type') == 'http' and 
            scheme.get('scheme', '').lower() == 'bearer'
        )
    
    def _requires_bearer_auth(self, security_requirements: List[Dict[str, Any]]) -> bool:
        """
        Determine if a set of security requirements includes bearer token authentication.
        
        Args:
            security_requirements: List of security requirement objects
            
        Returns:
            True if bearer token authentication is required, False otherwise
        """
        # If there are no bearer schemes defined, no endpoint requires bearer auth
        if not self.has_bearer_schemes:
            return False
            
        # If no security requirements are specified, no bearer auth is required
        if not security_requirements:
            return False
        
        # In OpenAPI, security requirements are a list of objects, where each object
        # represents an alternative security requirement (OR relationship).
        # Inside each object, keys are security scheme names and values are scopes (AND relationship).
        for requirement in security_requirements:
            # Check if any of the schemes in this requirement is a bearer scheme
            if any(self._is_bearer_scheme(scheme_name) for scheme_name in requirement):
                return True
        
        return False

    def _parse_endpoints(self) -> List[Dict[str, Any]]:
        """
        Parse the OpenAPI specification to extract endpoints information.
        
        Returns:
            A list of dictionaries, each containing endpoint details:
            {
                'path': str,
                'method': str,
                'operation_id': str,
                'summary': str,
                'request_body_schema': dict (optional),
                'query_parameters_schema': dict (optional),
                'path_parameters_schema': dict (optional),
                'requires_bearer_auth': bool
            }
        """
        result = []
        
        # Get the paths from the OpenAPI spec
        paths = self.spec.get('paths', {})
        
        for path, path_item in paths.items():
            for method, operation in path_item.items():
                # Skip non-HTTP methods (like parameters, servers, etc.)
                if method not in ['get', 'post', 'put', 'delete', 'patch', 'head', 'options', 'trace']:
                    continue
                
                endpoint_info = {
                    'path': path,
                    'method': method.upper(),
                    'operation_id': operation.get('operationId', ''),
                    'summary': operation.get('summary', ''),
                    'requires_bearer_auth': False  # Default to False
                }
                
                # Check if this operation requires bearer authorization
                # First check operation-level security, if present
                operation_security = operation.get('security')
                if operation_security is not None:
                    endpoint_info['requires_bearer_auth'] = self._requires_bearer_auth(operation_security)
                elif self.global_security:
                    # Fall back to global security if no operation-level security is defined
                    endpoint_info['requires_bearer_auth'] = self._requires_bearer_auth(self.global_security)
                
                # Extract request body schema if present
                request_body = operation.get('requestBody', {})
                if request_body:
                    content = request_body.get('content', {})
                    json_content = content.get('application/json', {})
                    
                    if json_content and 'schema' in json_content:
                        endpoint_info['request_body_schema'] = json_content['schema']
                
                # Extract parameters (both from operation and path item levels)
                parameters = []
                
                # Add path-level parameters if present
                if 'parameters' in path_item:
                    parameters.extend(path_item['parameters'])
                
                # Add operation-level parameters if present (these override path parameters with the same name and location)
                if 'parameters' in operation:
                    operation_param_names = {(p.get('name', ''), p.get('in', '')) for p in operation.get('parameters', [])}
                    # Only keep path-level parameters that aren't overridden
                    parameters = [p for p in parameters if (p.get('name', ''), p.get('in', '')) not in operation_param_names]
                    parameters.extend(operation.get('parameters', []))
                
                # Process parameters into query and path schemas
                query_params = [p for p in parameters if p.get('in') == 'query']
                path_params = [p for p in parameters if p.get('in') == 'path']
                
                # Create query parameters schema
                if query_params:
                    query_schema = {
                        'type': 'object',
                        'properties': {},
                        'required': []
                    }
                    
                    for param in query_params:
                        param_name = param.get('name', '')
                        param_schema = param.get('schema', {})
                        
                        query_schema['properties'][param_name] = param_schema
                        
                        if param.get('required', False):
                            query_schema['required'].append(param_name)
                    
                    # Only add required array if there are required parameters
                    if not query_schema['required']:
                        del query_schema['required']
                    
                    endpoint_info['query_parameters_schema'] = query_schema
                
                # Create path parameters schema
                if path_params:
                    path_schema = {
                        'type': 'object',
                        'properties': {},
                        'required': []
                    }
                    
                    for param in path_params:
                        param_name = param.get('name', '')
                        param_schema = param.get('schema', {})
                        
                        path_schema['properties'][param_name] = param_schema
                        
                        # Path parameters are required by default in OpenAPI
                        if param.get('required', True):
                            path_schema['required'].append(param_name)
                    
                    # Only add required array if there are required parameters
                    if not path_schema['required']:
                        del path_schema['required']
                    
                    endpoint_info['path_parameters_schema'] = path_schema
                
                result.append(endpoint_info)
        
        return result

    def get_endpoints(self) -> List[Dict[str, Any]]:
        """
        Get the list of all parsed endpoints.
        
        Returns:
            A list of dictionaries containing endpoint information
        """
        return self.endpoints
    
    def get_endpoints_with_request_body(self) -> List[Dict[str, Any]]:
        """
        Get only the endpoints that have a JSON request body.
        
        Returns:
            A list of dictionaries containing endpoint information with request bodies
        """
        return [endpoint for endpoint in self.endpoints if 'request_body_schema' in endpoint]
    
    def get_endpoints_with_query_parameters(self) -> List[Dict[str, Any]]:
        """
        Get only the endpoints that have query parameters.
        
        Returns:
            A list of dictionaries containing endpoint information with query parameters
        """
        return [endpoint for endpoint in self.endpoints if 'query_parameters_schema' in endpoint]
    
    def get_endpoints_with_path_parameters(self) -> List[Dict[str, Any]]:
        """
        Get only the endpoints that have path parameters.
        
        Returns:
            A list of dictionaries containing endpoint information with path parameters
        """
        return [endpoint for endpoint in self.endpoints if 'path_parameters_schema' in endpoint]
    
    def get_endpoints_requiring_bearer_auth(self) -> List[Dict[str, Any]]:
        """
        Get only the endpoints that require bearer token authentication.
        
        Returns:
            A list of dictionaries containing endpoint information that require bearer auth
        """
        return [endpoint for endpoint in self.endpoints if endpoint.get('requires_bearer_auth', False)]
    
    def get_endpoint_by_operation_id(self, operation_id: str) -> Optional[Dict[str, Any]]:
        """
        Find an endpoint by its operationId.
        
        Args:
            operation_id: The operationId to search for
            
        Returns:
            The endpoint dictionary or None if not found
        """
        for endpoint in self.endpoints:
            if endpoint.get('operation_id') == operation_id:
                return endpoint
        return None

    def to_json(self) -> str:
        """
        Convert the parsed endpoints to a JSON string.
        
        Returns:
            JSON string representation of the endpoints
        """
        return json.dumps(self.endpoints, indent=2)


# Example usage
if __name__ == "__main__":
    # Example with a dictionary
    example_spec = {
        "openapi": "3.0.0",
        "info": {
            "title": "Example API",
            "version": "1.0.0"
        },
        "paths": {
            "/users": {
                "get": {
                    "operationId": "getUsers",
                    "summary": "Get all users"
                },
                "post": {
                    "operationId": "createUser",
                    "summary": "Create a new user",
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "name": {"type": "string"},
                                        "email": {"type": "string", "format": "email"}
                                    },
                                    "required": ["name", "email"]
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    
    parser = OpenAPIParser(example_spec)
    print("All endpoints:")
    print(parser.to_json())
    
    print("\nEndpoints with request bodies:")
    for endpoint in parser.get_endpoints_with_request_body():
        print(f"{endpoint['method']} {endpoint['path']}: {endpoint['request_body_schema']}") 