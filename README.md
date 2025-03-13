# OpenAPI Parser

A Python utility for parsing OpenAPI specifications and extracting endpoint information, including HTTP methods and JSON request body schemas.

## Features

- Parse OpenAPI 3.0 specifications from:
  - File paths (JSON or YAML)
  - JSON strings
  - YAML strings
  - Python dictionaries
- Extract detailed endpoint information using a strongly-typed `Endpoint` dataclass:
  - Paths
  - HTTP methods
  - Operation IDs
  - Summaries
  - Request body JSON schemas
  - Query parameter schemas
  - Path parameter schemas
  - Bearer authorization requirements
- Filter endpoints by:
  - Endpoints with request bodies
  - Endpoints with query parameters
  - Endpoints with path parameters
  - Endpoints requiring bearer token authentication
- Find endpoints by:
  - Operation ID
  - Method + Path combination
- Convert parsed endpoints to JSON

## Installation

This package requires Python 3.6+ and the PyYAML package.

```bash
# Install with uv
uv pip install pyyaml
```

If you don't have uv installed, you can install it following the instructions at [https://github.com/astral-sh/uv](https://github.com/astral-sh/uv).

## Usage

```python
from openapi_parser import OpenAPIParser
from endpoint import Endpoint

# Load from a file
parser = OpenAPIParser('path/to/openapi.json')

# Or from a dictionary
spec = {
    "openapi": "3.0.0",
    "info": {"title": "Example API", "version": "1.0.0"},
    "components": {
        "securitySchemes": {
            "BearerAuth": {
                "type": "http",
                "scheme": "bearer"
            }
        }
    },
    "security": [{"BearerAuth": []}],  # Global security requirement
    "paths": {
        "/users": {
            "get": {
                "operationId": "getUsers",
                "summary": "Get all users",
                "security": [],  # Override global security (no auth required)
                "parameters": [
                    {
                        "name": "limit",
                        "in": "query",
                        "description": "Maximum number of results",
                        "schema": {"type": "integer", "format": "int32"}
                    }
                ]
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
                                    "email": {"type": "string"}
                                }
                            }
                        }
                    }
                }
            }
        },
        "/users/{userId}": {
            "get": {
                "operationId": "getUserById",
                "summary": "Get user by ID",
                "parameters": [
                    {
                        "name": "userId",
                        "in": "path",
                        "required": true,
                        "schema": {"type": "string"}
                    }
                ]
            }
        }
    }
}
parser = OpenAPIParser(spec)

# Get all endpoints as a list of Endpoint objects
endpoints = parser.get_endpoints()

# Get endpoints with request bodies
endpoints_with_body = parser.get_endpoints_with_request_body()

# Get endpoints with query parameters
endpoints_with_query = parser.get_endpoints_with_query_parameters()

# Get endpoints with path parameters
endpoints_with_path = parser.get_endpoints_with_path_parameters()

# Get endpoints requiring bearer authorization
endpoints_with_auth = parser.get_endpoints_requiring_bearer_auth()

# Find an endpoint by operation ID
user_endpoint = parser.get_endpoint_by_operation_id('createUser')
if user_endpoint:
    print(f"Found endpoint: {user_endpoint.method} {user_endpoint.path}")
    if user_endpoint.request_body_schema:
        print(f"Request body schema: {user_endpoint.request_body_schema}")

# Find an endpoint by method and path
get_user_endpoint = parser.get_endpoint('GET', '/users/{userId}')
if get_user_endpoint:
    print(f"Operation ID: {get_user_endpoint.operation_id}")
    if get_user_endpoint.path_parameters_schema:
        print(f"Path parameters: {get_user_endpoint.path_parameters_schema}")

# Convert to JSON
json_string = parser.to_json()
```

## Endpoint Dataclass

The `Endpoint` dataclass provides a strongly-typed representation of each API endpoint, with all the information needed to programmatically invoke it:

```python
# endpoint.py
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Set

@dataclass
class Endpoint:
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
    security_requirements: List[Dict[str, List[str]]] = field(default_factory=list)
    
    # Request information
    request_body_schema: Optional[Dict[str, Any]] = None
    request_body_required: bool = False
    request_content_types: List[str] = field(default_factory=list)
    query_parameters_schema: Optional[Dict[str, Any]] = None
    path_parameters_schema: Optional[Dict[str, Any]] = None
    header_parameters_schema: Optional[Dict[str, Any]] = None
    
    # Response information
    responses: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    response_content_types: List[str] = field(default_factory=list)
    
    # Additional metadata
    tags: List[str] = field(default_factory=list)
    
    # Utility methods
    @property
    def endpoint_key(self) -> str:
        """Generate a unique key for this endpoint based on method and path."""
        return f"{self.method} {self.path}"
        
    def get_full_url(self, server_url: Optional[str] = None, path_params: Optional[Dict[str, Any]] = None) -> str:
        """Construct the full URL with path parameters substituted."""
        # Implementation details...
        
    def get_required_parameters(self) -> Dict[str, Set[str]]:
        """Get all required parameters grouped by type (path, query, header)."""
        # Implementation details...
        
    def get_successful_response_schema(self) -> Optional[Dict[str, Any]]:
        """Get the schema for a successful response (2xx status code)."""
        # Implementation details...
```

### Programmatically Invoking an Endpoint

With the enhanced `Endpoint` class, you can now easily create HTTP clients that can automatically invoke API endpoints:

```python
from openapi_parser import OpenAPIParser
from endpoint import Endpoint
import requests
import json

# Load the API specification
parser = OpenAPIParser('api_spec.json')

# Get an endpoint
endpoint = parser.get_endpoint('GET', '/users/{userId}')

if endpoint:
    # Prepare the URL with path parameters
    url = endpoint.get_full_url(
        server_url="https://api.example.com",  # Or use endpoint.default_server_url
        path_params={"userId": "123"}
    )
    
    # Prepare query parameters
    query_params = {"fields": "name,email"}
    
    # Prepare headers
    headers = {}
    if endpoint.requires_bearer_auth:
        headers["Authorization"] = "Bearer my-token"
        
    # Add content type if sending a request body
    content_type = None
    if endpoint.request_content_types:
        content_type = endpoint.request_content_types[0]
        headers["Content-Type"] = content_type
    
    # Make the request
    response = requests.request(
        method=endpoint.method,
        url=url,
        params=query_params,
        headers=headers,
        # Add request body for POST/PUT/PATCH
        json={"name": "John"} if endpoint.method in ['POST', 'PUT', 'PATCH'] else None
    )
    
    # Process the response based on expected response schemas
    if str(response.status_code) in endpoint.responses:
        print(f"Success: {response.status_code}")
        # Parse response according to schema
        data = response.json()
        print(data)
    else:
        print(f"Error: {response.status_code}")
```

## Running Tests

The package includes comprehensive tests using the standard Python unittest framework. The tests use the well-known Petstore OpenAPI example to validate the parser's functionality.

To run the tests with uv:

```bash
# Install test requirements with uv
uv pip install pyyaml

# Run the tests
uv run python -m unittest test_openapi_parser.py
```

## Example Output

The parser produces a list of `Endpoint` objects, which can be converted to JSON:

```json
[
  {
    "path": "/users/{userId}",
    "method": "GET",
    "operation_id": "getUserById",
    "summary": "Get user by ID",
    "requires_bearer_auth": true,
    "path_parameters_schema": {
      "type": "object",
      "properties": {
        "userId": {"type": "string"}
      },
      "required": ["userId"]
    }
  },
  {
    "path": "/users",
    "method": "POST",
    "operation_id": "createUser",
    "summary": "Create a new user",
    "requires_bearer_auth": true,
    "request_body_schema": {
      "type": "object",
      "properties": {
        "name": {"type": "string"},
        "email": {"type": "string"}
      }
    }
  }
]
```

Note that fields like `request_body_schema`, `query_parameters_schema`, and `path_parameters_schema` are only included in the JSON output if they exist in the API definition.

## License

MIT 