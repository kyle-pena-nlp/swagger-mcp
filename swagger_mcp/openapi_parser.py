import os
import json
import requests
import yaml

from typing import Dict, List, Any, Optional, Union
from swagger_mcp.endpoint import Endpoint
from swagger_mcp.logging import setup_logger

logger = setup_logger(__name__)

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
        self.servers = self.spec.get('servers', [])
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
        security_schemes = components.get('securitySchemes', {})
        
        # Check for OpenAPI v2 style security definitions
        if not security_schemes and 'securityDefinitions' in self.spec:
            security_schemes = self.spec.get('securityDefinitions', {})
            
        return security_schemes
    
    def _is_bearer_scheme(self, scheme_name: str) -> bool:
        """
        Determine if a security scheme is a bearer token scheme.
        
        Args:
            scheme_name: The name of the security scheme
            
        Returns:
            True if the scheme is a bearer token scheme, False otherwise
        """
        scheme = self.security_schemes.get(scheme_name, {})
        
        # Check for OpenAPI v3 style http bearer scheme
        if (scheme.get('type') == 'http' and 
            scheme.get('scheme', '').lower() == 'bearer'):
            return True
            
        # Check for OpenAPI v3 style OAuth2 scheme
        if scheme.get('type') == 'oauth2' and scheme.get('flows', {}):
            return True
            
        # Check for OpenAPI v2 style OAuth2 scheme
        if (scheme.get('type') == 'oauth2' and 
            (scheme.get('flow') or scheme.get('authorizationUrl'))):
            return True
            
        return False
    
    def _resolve_schema_ref(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Resolve a schema reference to its actual schema definition.
        
        Args:
            schema: The schema that may contain a $ref
            
        Returns:
            The resolved schema
        """
        if not isinstance(schema, dict):
            return schema
            
        if '$ref' in schema:
            ref = schema['$ref']
            if not ref.startswith('#/'):
                raise ValueError(f"Only local references are supported, got: {ref}")
                
            # Split the reference path and traverse the spec
            parts = ref.lstrip('#/').split('/')
            current = self.spec
            for part in parts:
                if part not in current:
                    raise ValueError(f"Invalid reference path: {ref}")
                current = current[part]
            
            # Recursively resolve any nested references
            return self._resolve_schema_ref(current)
        
        # Recursively resolve references in nested objects
        resolved = {}
        for key, value in schema.items():
            if isinstance(value, dict):
                resolved[key] = self._resolve_schema_ref(value)
            elif isinstance(value, list):
                resolved[key] = [
                    self._resolve_schema_ref(item) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                resolved[key] = value
                
        return resolved

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
        
    def _get_oauth_scopes(self, security_requirements: List[Dict[str, Any]]) -> List[str]:
        """
        Extract OAuth scopes from security requirements.
        
        Args:
            security_requirements: List of security requirement objects
            
        Returns:
            List of OAuth scopes required for the endpoint
        """
        scopes = []
        
        for requirement in security_requirements:
            for scheme_name, scheme_scopes in requirement.items():
                scheme = self.security_schemes.get(scheme_name, {})
                if scheme.get('type') == 'oauth2' and scheme_scopes:
                    scopes.extend(scheme_scopes)
        
        return list(set(scopes))  # Remove duplicates
        
    def _is_oauth_scheme(self, scheme_name: str) -> bool:
        """
        Determine if a security scheme is an OAuth scheme.
        
        Args:
            scheme_name: The name of the security scheme
            
        Returns:
            True if the scheme is an OAuth scheme, False otherwise
        """
        scheme = self.security_schemes.get(scheme_name, {})
        return scheme.get('type') == 'oauth2'
        
    def _requires_oauth(self, security_requirements: List[Dict[str, Any]]) -> bool:
        """
        Determine if a set of security requirements includes OAuth authentication.
        
        Args:
            security_requirements: List of security requirement objects
            
        Returns:
            True if OAuth authentication is required, False otherwise
        """
        if not security_requirements:
            return False
            
        for requirement in security_requirements:
            if any(self._is_oauth_scheme(scheme_name) for scheme_name in requirement):
                return True
                
        return False

    def _parse_endpoints(self) -> Dict[str, Endpoint]:
        """
        Parse the OpenAPI specification to extract endpoints information.
        
        Returns:
            A dictionary mapping endpoint keys (method + path) to Endpoint objects
        """
        result: Dict[str, Endpoint] = {}
        
        # Get the paths from the OpenAPI spec
        paths = self.spec.get('paths', {})
        
        for path, path_item in paths.items():
            for method, operation in path_item.items():
                # Skip non-HTTP methods (like parameters, servers, etc.)
                if method not in ['get', 'post', 'put', 'delete', 'patch', 'head', 'options', 'trace']:
                    continue
                
                # Create a new endpoint with the basic information
                endpoint = Endpoint(
                    path=path,
                    method=method.upper(),
                    operation_id=operation.get('operationId', ''),
                    summary=operation.get('summary', ''),
                    description=operation.get('description', ''),
                    deprecated=operation.get('deprecated', False),
                    requires_bearer_auth=False,  # Default value
                    requires_oauth=False,  # Default value
                    servers=operation.get('servers', self.servers.copy()),
                    tags=operation.get('tags', [])
                )
                
                # Check if this operation requires bearer authorization or OAuth
                # First check operation-level security, if present
                operation_security = operation.get('security')
                if operation_security is not None:
                    endpoint.security_requirements = operation_security
                    endpoint.requires_bearer_auth = self._requires_bearer_auth(operation_security)
                    endpoint.requires_oauth = self._requires_oauth(operation_security)
                    if endpoint.requires_oauth:
                        endpoint.oauth_scopes = self._get_oauth_scopes(operation_security)
                elif self.global_security:
                    # Fall back to global security if no operation-level security is defined
                    endpoint.security_requirements = self.global_security
                    endpoint.requires_bearer_auth = self._requires_bearer_auth(self.global_security)
                    endpoint.requires_oauth = self._requires_oauth(self.global_security)
                    if endpoint.requires_oauth:
                        endpoint.oauth_scopes = self._get_oauth_scopes(self.global_security)
                
                # Extract request body schema if present
                request_body = operation.get('requestBody', {})
                if request_body:
                    endpoint.request_body_required = request_body.get('required', False)
                    content = request_body.get('content', {})
                    
                    # Look for application/json content type first
                    json_content = content.get('application/json', {})
                    if json_content and 'schema' in json_content:
                        endpoint.request_body_schema = self._resolve_schema_ref(json_content['schema'])
                        endpoint.request_content_types.append('application/json')
                    else:
                        # If no JSON content type, use the first available content type
                        for content_type, content_info in content.items():
                            if 'schema' in content_info:
                                endpoint.request_body_schema = self._resolve_schema_ref(content_info['schema'])
                                endpoint.request_content_types.append(content_type)
                                break
                
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
                
                # Process parameters into query, path, header, and form schemas
                query_params = [p for p in parameters if p.get('in') == 'query']
                path_params = [p for p in parameters if p.get('in') == 'path']
                header_params = [p for p in parameters if p.get('in') == 'header']
                form_params = [p for p in parameters if p.get('in') == 'formData']
                
                # Create query parameters schema
                if query_params:
                    query_schema = {
                        'type': 'object',
                        'properties': {},
                        'required': []
                    }
                    
                    for param in query_params:
                        param_name = param.get('name', '')
                        param_schema = param.get('schema', {}).copy()  # Make a copy to avoid modifying original
                        
                        # Handle OpenAPI 2.0 style parameters where schema fields are directly in the parameter
                        if not param_schema and 'type' in param:
                            param_schema = {
                                'type': param.get('type'),
                                'description': param.get('description', '')
                            }
                            # Copy over other schema-related fields
                            for field in ['format', 'enum', 'default', 'minimum', 'maximum', 'pattern']:
                                if field in param:
                                    param_schema[field] = param[field]
                        else:
                            # Resolve any schema references
                            param_schema = self._resolve_schema_ref(param_schema)
                            # Add description from parameter to schema if present
                            if 'description' in param:
                                param_schema['description'] = param.get('description')
                        
                        query_schema['properties'][param_name] = param_schema
                        
                        if param.get('required', False):
                            query_schema['required'].append(param_name)
                    
                    # Only add required array if there are required parameters
                    if not query_schema['required']:
                        del query_schema['required']
                    
                    endpoint.query_parameters_schema = query_schema
                
                # Create path parameters schema
                if path_params:
                    path_schema = {
                        'type': 'object',
                        'properties': {},
                        'required': []
                    }
                    
                    for param in path_params:
                        param_name = param.get('name', '')
                        param_schema = param.get('schema', {}).copy()  # Make a copy to avoid modifying original
                        
                        # Handle OpenAPI 2.0 style parameters where schema fields are directly in the parameter
                        if not param_schema and 'type' in param:
                            param_schema = {
                                'type': param.get('type'),
                                'description': param.get('description', '')
                            }
                            # Copy over other schema-related fields
                            for field in ['format', 'enum', 'default', 'minimum', 'maximum', 'pattern']:
                                if field in param:
                                    param_schema[field] = param[field]
                        else:
                            # Resolve any schema references
                            param_schema = self._resolve_schema_ref(param_schema)
                            # Add description from parameter to schema if present
                            if 'description' in param:
                                param_schema['description'] = param.get('description')
                        
                        path_schema['properties'][param_name] = param_schema
                        
                        # Path parameters are required by default in OpenAPI
                        if param.get('required', True):
                            path_schema['required'].append(param_name)
                    
                    # Only add required array if there are required parameters
                    if not path_schema['required']:
                        del path_schema['required']
                    
                    endpoint.path_parameters_schema = path_schema
                
                # Create header parameters schema
                if header_params:
                    header_schema = {
                        'type': 'object',
                        'properties': {},
                        'required': []
                    }
                    
                    for param in header_params:
                        param_name = param.get('name', '')
                        param_schema = param.get('schema', {}).copy()  # Make a copy to avoid modifying original
                        
                        # Add description from parameter to schema if present
                        if 'description' in param:
                            param_schema['description'] = param.get('description')
                        
                        header_schema['properties'][param_name] = param_schema
                        
                        if param.get('required', False):
                            header_schema['required'].append(param_name)
                    
                    # Only add required array if there are required parameters
                    if not header_schema['required']:
                        del header_schema['required']
                    
                    endpoint.header_parameters_schema = header_schema
                
                # Create form parameters schema
                if form_params:
                    form_schema = {
                        'type': 'object',
                        'properties': {},
                        'required': []
                    }
                    
                    for param in form_params:
                        param_name = param.get('name', '')
                        param_schema = param.get('schema', {}).copy() or {}  # Make a copy to avoid modifying original
                        
                        # Handle OpenAPI 2.0 style parameters where schema fields are directly in the parameter
                        if not param_schema and 'type' in param:
                            param_schema = {
                                'type': param.get('type'),
                                'description': param.get('description', '')
                            }
                            # Copy over other schema-related fields
                            for field in ['format', 'enum', 'default', 'minimum', 'maximum', 'pattern']:
                                if field in param:
                                    param_schema[field] = param[field]
                        else:
                            # Resolve any schema references
                            param_schema = self._resolve_schema_ref(param_schema)
                            # Add description from parameter to schema if present
                            if 'description' in param:
                                param_schema['description'] = param.get('description')
                        
                        form_schema['properties'][param_name] = param_schema
                        
                        if param.get('required', False):
                            form_schema['required'].append(param_name)
                    
                    # Only add required array if there are required parameters
                    if not form_schema['required']:
                        del form_schema['required']
                    
                    endpoint.form_parameters_schema = form_schema
                    
                    # Add multipart/form-data and application/x-www-form-urlencoded content types
                    # if not already added via request body
                    if 'multipart/form-data' not in endpoint.request_content_types:
                        endpoint.request_content_types.append('multipart/form-data')
                    if 'application/x-www-form-urlencoded' not in endpoint.request_content_types:
                        endpoint.request_content_types.append('application/x-www-form-urlencoded')
                
                # Extract response schemas
                responses = operation.get('responses', {})
                if responses:
                    # Resolve any references in response schemas
                    resolved_responses = {}
                    for status_code, response in responses.items():
                        resolved_response = response.copy()
                        if 'content' in response:
                            resolved_content = {}
                            for content_type, content_info in response['content'].items():
                                resolved_content_info = content_info.copy()
                                if 'schema' in content_info:
                                    resolved_content_info['schema'] = self._resolve_schema_ref(content_info['schema'])
                                resolved_content[content_type] = resolved_content_info
                            resolved_response['content'] = resolved_content
                        resolved_responses[status_code] = resolved_response
                    
                    endpoint.responses = resolved_responses
                    
                    # Extract response content types
                    for status_code, response in resolved_responses.items():
                        if 'content' in response:
                            for content_type in response['content']:
                                if content_type not in endpoint.response_content_types:
                                    endpoint.response_content_types.append(content_type)
                
                # Add the endpoint to the result
                result[endpoint.endpoint_key] = endpoint
        
        return result

    def get_endpoints(self) -> List[Endpoint]:
        """
        Get a list of all parsed endpoints.
        
        Returns:
            A list of Endpoint objects
        """
        return list(self.endpoints.values())
    
    def get_endpoints_with_request_body(self) -> List[Endpoint]:
        """
        Get only the endpoints that have a JSON request body.
        
        Returns:
            A list of Endpoint objects with request bodies
        """
        return [endpoint for endpoint in self.endpoints.values() if endpoint.request_body_schema is not None]
    
    def get_endpoints_with_query_parameters(self) -> List[Endpoint]:
        """
        Get only the endpoints that have query parameters.
        
        Returns:
            A list of Endpoint objects with query parameters
        """
        return [endpoint for endpoint in self.endpoints.values() if endpoint.query_parameters_schema is not None]
    
    def get_endpoints_with_path_parameters(self) -> List[Endpoint]:
        """
        Get a list of all endpoints that have path parameters.
        
        Returns:
            List of Endpoint objects that have path parameters
        """
        return [endpoint for endpoint in self.endpoints.values() if endpoint.path_parameters_schema is not None]
    
    def get_endpoints_with_form_parameters(self) -> List[Endpoint]:
        """
        Get a list of all endpoints that have form parameters.
        
        Returns:
            List of Endpoint objects that have form parameters
        """
        return [endpoint for endpoint in self.endpoints.values() if endpoint.form_parameters_schema is not None]
    
    def get_endpoints_requiring_bearer_auth(self) -> List[Endpoint]:
        """
        Get all endpoints that require bearer token authentication.
        
        Returns:
            List of Endpoint objects that require bearer token authentication
        """
        return [endpoint for endpoint in self.endpoints.values() if endpoint.requires_bearer_auth]
    
    def get_endpoints_requiring_oauth(self) -> List[Endpoint]:
        """
        Get all endpoints that require OAuth authentication.
        
        Returns:
            List of Endpoint objects that require OAuth authentication
        """
        return [endpoint for endpoint in self.endpoints.values() if endpoint.requires_oauth]
    
    def get_endpoint_by_operation_id(self, operation_id: str) -> Optional[Endpoint]:
        """
        Find an endpoint by its operationId.
        
        Args:
            operation_id: The operationId to search for
            
        Returns:
            The Endpoint object or None if not found
        """
        for endpoint in self.endpoints.values():
            if endpoint.operation_id == operation_id:
                return endpoint
        return None
    
    def get_endpoint(self, method: str, path: str) -> Optional[Endpoint]:
        """
        Find an endpoint by its method and path.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            path: URL path
            
        Returns:
            The Endpoint object or None if not found
        """
        key = f"{method.upper()} {path}"
        return self.endpoints.get(key)

    def to_json(self) -> str:
        """
        Convert the parsed endpoints to a JSON string.
        
        Returns:
            JSON string representation of the endpoints
        """
        # Convert endpoints to a list of dictionaries for JSON serialization
        endpoints_dicts = []
        for endpoint in self.endpoints.values():
            endpoint_dict = {
                'path': endpoint.path,
                'method': endpoint.method,
                'operation_id': endpoint.operation_id,
                'summary': endpoint.summary
            }
            
            # Only include non-empty fields
            if endpoint.description:
                endpoint_dict['description'] = endpoint.description
                
            if endpoint.deprecated:
                endpoint_dict['deprecated'] = endpoint.deprecated
                
            if endpoint.servers:
                endpoint_dict['servers'] = endpoint.servers
                
            if endpoint.requires_bearer_auth:
                endpoint_dict['requires_bearer_auth'] = endpoint.requires_bearer_auth
                
            if endpoint.security_requirements:
                endpoint_dict['security_requirements'] = endpoint.security_requirements
                
            if endpoint.request_body_schema:
                endpoint_dict['request_body_schema'] = endpoint.request_body_schema
                
            if endpoint.request_body_required:
                endpoint_dict['request_body_required'] = endpoint.request_body_required
                
            if endpoint.request_content_types:
                endpoint_dict['request_content_types'] = endpoint.request_content_types
                
            if endpoint.query_parameters_schema:
                endpoint_dict['query_parameters_schema'] = endpoint.query_parameters_schema
                
            if endpoint.path_parameters_schema:
                endpoint_dict['path_parameters_schema'] = endpoint.path_parameters_schema
                
            if endpoint.header_parameters_schema:
                endpoint_dict['header_parameters_schema'] = endpoint.header_parameters_schema
                
            if endpoint.responses:
                endpoint_dict['responses'] = endpoint.responses
                
            if endpoint.response_content_types:
                endpoint_dict['response_content_types'] = endpoint.response_content_types
                
            if endpoint.tags:
                endpoint_dict['tags'] = endpoint.tags
            
            endpoints_dicts.append(endpoint_dict)
            
        return json.dumps(endpoints_dicts, indent=2)


# Example usage
if __name__ == "__main__":
    # Example with a dictionary
    spec = {
        "openapi": "3.0.0",
        "info": {"title": "Test API", "version": "1.0.0"},
        "paths": {
            "/test": {
                "post": {
                    "operationId": "testEndpoint",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "name": {"type": "string"},
                                        "age": {"type": "integer"}
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    
    parser = OpenAPIParser(spec)
    logger.info("All endpoints:")
    logger.info(parser.to_json())
    
    logger.info("Endpoints with request bodies:")
    for endpoint in parser.endpoints.values():
        if endpoint.request_body_schema:
            logger.info(f"{endpoint.method} {endpoint.path}: {endpoint.request_body_schema}")