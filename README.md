# OpenAPI Parser

A Python utility for parsing OpenAPI specifications and extracting endpoint information, including HTTP methods and JSON request body schemas.

## Features

- Parse OpenAPI 3.0 specifications from:
  - File paths (JSON or YAML)
  - JSON strings
  - YAML strings
  - Python dictionaries
- Extract detailed endpoint information:
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
- Find endpoints by operation ID
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

# Get all endpoints
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

# Convert to JSON
json_string = parser.to_json()
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

For each endpoint, the parser produces a dictionary with the following structure:

```python
{
    'path': '/users/{userId}',
    'method': 'GET',
    'operation_id': 'getUserById',
    'summary': 'Get user by ID',
    'requires_bearer_auth': True,  # Indicates bearer token authorization is required
    'path_parameters_schema': {
        'type': 'object',
        'properties': {
            'userId': {'type': 'string'}
        },
        'required': ['userId']
    },
    'query_parameters_schema': {
        'type': 'object',
        'properties': {
            'fields': {'type': 'string', 'enum': ['basic', 'full']}
        }
    },
    'request_body_schema': {
        'type': 'object',
        'properties': {
            'name': {'type': 'string'},
            'email': {'type': 'string'}
        }
    }
}
```

Note that parameters and request bodies are only included if they exist in the API definition.

## License

MIT 