import os
import json
import requests
import yaml

from typing import Dict, List, Any, Optional, Union, Set
from swagger_mcp.endpoint import Endpoint
from swagger_mcp.logging import setup_logger

logger = setup_logger(__name__)

class CircularReferenceError(ValueError):
    """Raised when a circular reference is detected in schema resolution."""
    
    def record_occurrence(self, ref: str) -> None:
        """Record that this error occurred for a specific reference.
        This method exists purely for testing purposes."""
        pass

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
                  a URL to fetch the spec from (http/https),
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
        Load an OpenAPI specification from various sources.
        
        Args:
            spec: Either a file path to the OpenAPI spec (JSON or YAML),
                  a URL to fetch the spec from (http/https),
                  a JSON string, or a dictionary containing the spec
                  
        Returns:
            dict: The loaded OpenAPI specification
        """
        if isinstance(spec, dict):
            return spec
            
        if isinstance(spec, str):
            # Check if it's a URL
            if spec.startswith(('http://', 'https://')):
                logger.info(f"Fetching OpenAPI spec from URL: {spec}")
                response = requests.get(spec)
                response.raise_for_status()  # Raise exception for non-200 status codes
                
                # Parse content based on content type
                content_type = response.headers.get('Content-Type', '')
                if 'json' in content_type:
                    return response.json()
                else:
                    # Assume YAML or try to parse as such
                    return yaml.safe_load(response.text)
                    
            # Check if it's a file path
            if os.path.isfile(spec):
                with open(spec, 'r') as f:
                    content = f.read()
                    try:
                        if spec.lower().endswith('.json'):
                            return json.loads(content)
                        else:
                            return yaml.safe_load(content)
                    except Exception as e:
                        raise ValueError(f"Failed to parse spec file {spec}: {str(e)}")
                        
            # Try parsing as JSON string
            try:
                return json.loads(spec)
            except json.JSONDecodeError:
                # Try parsing as YAML string
                try:
                    return yaml.safe_load(spec)
                except yaml.YAMLError as e:
                    raise ValueError(f"Failed to parse spec as JSON or YAML string: {str(e)}")
                    
        raise ValueError("Spec must be a file path, URL, JSON/YAML string, or dictionary")
    
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
    
    def _resolve_schema_ref(self, schema: Dict[str, Any], visited_refs: Optional[Set[str]] = None) -> Dict[str, Any]:
        """
        Resolve a schema reference to its actual schema definition.
        
        Args:
            schema: The schema that may contain a $ref
            visited_refs: Set of already visited references to detect cycles
            
        Returns:
            The resolved schema
            
        Raises:
            CircularReferenceError: If a reference cycle is detected
            ValueError: If reference is invalid
        """
        if not isinstance(schema, dict):
            return schema
            
        if visited_refs is None:
            visited_refs = set()
            
        if '$ref' in schema:
            ref = schema['$ref']
            if not ref.startswith('#/'):
                raise ValueError(f"Only local references are supported, got: {ref}")
                
            if ref in visited_refs:
                error = CircularReferenceError(f"Circular reference detected: {ref}")
                error.record_occurrence(ref)
                raise error
                
            visited_refs.add(ref)
                
            # Split the reference path and traverse the spec
            parts = ref.lstrip('#/').split('/')
            current = self.spec
            for part in parts:
                if part not in current:
                    raise ValueError(f"Invalid reference path: {ref}")
                current = current[part]
            
            # Recursively resolve any nested references
            return self._resolve_schema_ref(current, visited_refs)
        
        # Recursively resolve references in nested objects
        resolved = {}
        for key, value in schema.items():
            if isinstance(value, dict):
                resolved[key] = self._resolve_schema_ref(value, visited_refs.copy())
            elif isinstance(value, list):
                resolved[key] = [
                    self._resolve_schema_ref(item, visited_refs.copy()) if isinstance(item, dict) else item
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

    def _build_parameters_schema(self, parameters: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Build a JSON Schema object from a list of parameters.
        
        Args:
            parameters: List of parameter objects from the OpenAPI spec
            
        Returns:
            A JSON Schema object representing the parameters, or None if required parameters have errors
            
        Raises:
            ValueError: If the parameter definition is invalid
        """
        schema = {
            'type': 'object',
            'properties': {},
            'required': []
        }
        
        for param in parameters:
            param_name = param.get('name', '')
            param_schema = param.get('schema', {}).copy()
            is_required = param.get('required', False) or param.get('in') == 'path'
            
            try:
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
                
                # Try to resolve any schema references
                if isinstance(param_schema, dict) and '$ref' in param_schema:
                    param_schema = self._resolve_schema_ref(param_schema)
                
                # Add description from parameter to schema if present
                if 'description' in param:
                    param_schema['description'] = param.get('description')
                
                schema['properties'][param_name] = param_schema
                
                if is_required:
                    schema['required'].append(param_name)
                    
            except CircularReferenceError as e:
                if is_required:
                    # If a required parameter has a circular reference, skip the entire endpoint
                    logger.warning(f"Required parameter {param_name} has circular reference, skipping endpoint")
                    return None
                else:
                    # If an optional parameter has a circular reference, just skip that parameter
                    logger.warning(f"Optional parameter {param_name} has circular reference, omitting parameter")
                    continue
            except ValueError as e:
                if is_required:
                    # If a required parameter has any other error, skip the entire endpoint
                    logger.warning(f"Required parameter {param_name} has error: {str(e)}, skipping endpoint")
                    return None
                else:
                    # If an optional parameter has any other error, just skip that parameter
                    logger.warning(f"Optional parameter {param_name} has error: {str(e)}, omitting parameter")
                    continue
        
        # Only add required array if there are required parameters
        if not schema['required']:
            del schema['required']
        
        return schema

    def _parse_endpoints(self) -> Dict[str, Endpoint]:
        """
        Parse the OpenAPI spec to extract all endpoints.
        
        Returns:
            A dictionary mapping endpoint keys to Endpoint objects
        """
        logger.info("Parsing OpenAPI specification endpoints")
        endpoints = {}
        
        # Get the global security requirements
        self.global_security = self.spec.get('security', [])
        
        # Get the global servers list
        self.servers = self.spec.get('servers', [])
        
        # Process each path
        for path, path_item in self.spec.get('paths', {}).items():
            # Skip non-operation fields
            if not isinstance(path_item, dict):
                continue
                
            # Get path-level parameters
            path_level_params = path_item.get('parameters', [])
            
            # Process each HTTP method
            for method, operation in path_item.items():
                if method not in ['get', 'put', 'post', 'delete', 'options', 'head', 'patch', 'trace']:
                    continue
                
                try:
                    # Create a new endpoint
                    endpoint = Endpoint(
                        path=path,
                        method=method.upper(),
                        operation_id=operation.get('operationId', ''),
                        summary=operation.get('summary', ''),
                        description=operation.get('description', ''),
                        deprecated=operation.get('deprecated', False),
                        servers=operation.get('servers', self.servers),
                        tags=operation.get('tags', [])
                    )
                    
                    # Process security requirements
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
                    
                    # Process parameters
                    operation_params = operation.get('parameters', [])
                    all_params = path_level_params + operation_params
                    
                    # Group parameters by type
                    path_params = []
                    query_params = []
                    header_params = []
                    form_params = []
                    
                    skip_endpoint = False
                    for param in all_params:
                        # Resolve parameter schema if it's a reference
                        if isinstance(param, dict) and '$ref' in param:
                            try:
                                param = self._resolve_schema_ref(param)
                            except (ValueError, CircularReferenceError) as e:
                                logger.warning(f"Error resolving parameter reference: {str(e)}")
                                if param.get('required', False) or param.get('in') == 'path':
                                    skip_endpoint = True
                                continue
                        
                        param_schema = param.get('schema', {})
                        if isinstance(param_schema, dict) and '$ref' in param_schema:
                            try:
                                param['schema'] = self._resolve_schema_ref(param_schema)
                            except (ValueError, CircularReferenceError) as e:
                                logger.warning(f"Error resolving parameter schema reference: {str(e)}")
                                if param.get('required', False) or param.get('in') == 'path':
                                    skip_endpoint = True
                                continue
                        
                        param_in = param.get('in')
                        if param_in == 'path':
                            path_params.append(param)
                        elif param_in == 'query':
                            query_params.append(param)
                        elif param_in == 'header':
                            header_params.append(param)
                        elif param_in == 'formData':
                            form_params.append(param)
                    
                    # Skip this endpoint if any required parameters had errors
                    if skip_endpoint:
                        logger.warning(f"Skipping endpoint {method.upper()} {path} due to required parameter errors")
                        continue
                    
                    try:
                        # Set parameter schemas on the endpoint
                        if path_params:
                            endpoint.path_parameters_schema = self._build_parameters_schema(path_params)
                            if endpoint.path_parameters_schema is None:
                                # Skip this endpoint if path parameters had errors
                                logger.warning(f"Skipping endpoint {method.upper()} {path} due to path parameter errors")
                                continue
                        if query_params:
                            endpoint.query_parameters_schema = self._build_parameters_schema(query_params)
                            if endpoint.query_parameters_schema is None:
                                # Skip this endpoint if query parameters had errors
                                logger.warning(f"Skipping endpoint {method.upper()} {path} due to query parameter errors")
                                continue
                        if header_params:
                            endpoint.header_parameters_schema = self._build_parameters_schema(header_params)
                            if endpoint.header_parameters_schema is None:
                                # Skip this endpoint if header parameters had errors
                                logger.warning(f"Skipping endpoint {method.upper()} {path} due to header parameter errors")
                                continue
                        if form_params:
                            endpoint.form_parameters_schema = self._build_parameters_schema(form_params)
                            if endpoint.form_parameters_schema is None:
                                # Skip this endpoint if form parameters had errors
                                logger.warning(f"Skipping endpoint {method.upper()} {path} due to form parameter errors")
                                continue
                        
                        # Process request body
                        request_body = operation.get('requestBody', {})
                        if request_body:
                            try:
                                content = request_body.get('content', {})
                                endpoint.request_body_required = request_body.get('required', False)
                                endpoint.request_content_types = list(content.keys())
                                
                                # Get the first content type's schema
                                if content:
                                    first_content_type = next(iter(content))
                                    schema = content[first_content_type].get('schema', {})
                                    if schema:
                                        endpoint.request_body_schema = self._resolve_schema_ref(schema)
                            except CircularReferenceError as e:
                                if endpoint.request_body_required:
                                    # Skip this endpoint if required request body has errors
                                    logger.warning(f"Skipping endpoint {method.upper()} {path} due to required request body errors")
                                    continue
                                else:
                                    # Just skip the request body if it's optional
                                    logger.warning(f"Omitting optional request body for {method.upper()} {path} due to errors")
                                    endpoint.request_body_schema = None
                                    endpoint.request_body_required = False
                                    endpoint.request_content_types = []
                        
                        # Process responses
                        responses = operation.get('responses', {})
                        for status_code, response in responses.items():
                            if isinstance(response, dict) and '$ref' in response:
                                try:
                                    response = self._resolve_schema_ref(response)
                                except (ValueError, CircularReferenceError) as e:
                                    logger.warning(f"Error resolving response reference: {str(e)}")
                                    continue
                            
                            content = response.get('content', {})
                            for content_type, content_info in content.items():
                                if content_type not in endpoint.response_content_types:
                                    endpoint.response_content_types.append(content_type)
                                
                                if 'schema' in content_info:
                                    try:
                                        content_info['schema'] = self._resolve_schema_ref(content_info['schema'])
                                    except (ValueError, CircularReferenceError) as e:
                                        logger.warning(f"Error resolving response schema reference: {str(e)}")
                                        continue
                            
                            endpoint.responses[str(status_code)] = response
                        
                        # Add the endpoint to our collection
                        key = f"{method.upper()}_{path}"
                        endpoints[key] = endpoint
                        logger.info(f"Successfully parsed endpoint: {method.upper()} {path}")
                        
                    except ValueError as e:
                        logger.warning(f"Error processing parameters for {method.upper()} {path}: {str(e)}")
                        continue
                        
                except Exception as e:
                    logger.warning(f"Error processing endpoint {method.upper()} {path}: {str(e)}")
                    continue
        
        return endpoints

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
        key = f"{method.upper()}_{path}"
        return self.endpoints.get(key)

    def get_endpoint_by_method_path(self, method: str, path: str) -> Optional[Endpoint]:
        """
        Get an endpoint by its HTTP method and path.
        
        Args:
            method: HTTP method (e.g., GET, POST)
            path: URL path
            
        Returns:
            The Endpoint object or None if not found
        """
        key = f"{method.upper()}_{path}"
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