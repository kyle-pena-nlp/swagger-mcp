import pytest
import json
import os
import yaml
import copy
from swagger_mcp.openapi_parser import OpenAPIParser
from swagger_mcp.endpoint import Endpoint

# Petstore OpenAPI 3.0 example spec
@pytest.fixture
def petstore_spec():
    return {
        "openapi": "3.0.0",
        "info": {
            "version": "1.0.0",
            "title": "Swagger Petstore",
            "description": "A sample API that uses a petstore as an example to demonstrate features",
            "termsOfService": "http://swagger.io/terms/",
            "contact": {
                "name": "Swagger API Team",
                "email": "apiteam@swagger.io",
                "url": "http://swagger.io"
            },
            "license": {
                "name": "Apache 2.0",
                "url": "https://www.apache.org/licenses/LICENSE-2.0.html"
            }
        },
        "servers": [
            {
                "url": "http://petstore.swagger.io/api"
            }
        ],
        "paths": {
            "/pets": {
                "get": {
                    "summary": "List all pets",
                    "operationId": "listPets",
                    "tags": [
                        "pets"
                    ],
                    "parameters": [
                        {
                            "name": "limit",
                            "in": "query",
                            "description": "How many items to return at one time (max 100)",
                            "required": False,
                            "schema": {
                                "type": "integer",
                                "format": "int32"
                            }
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "A paged array of pets",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "array",
                                        "items": {
                                            "$ref": "#/components/schemas/Pet"
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "post": {
                    "summary": "Create a pet",
                    "operationId": "createPets",
                    "tags": [
                        "pets"
                    ],
                    "requestBody": {
                        "description": "Pet to add to the store",
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/NewPet"
                                }
                            }
                        }
                    },
                    "responses": {
                        "201": {
                            "description": "Null response"
                        }
                    }
                }
            },
            "/pets/{petId}": {
                "get": {
                    "summary": "Info for a specific pet",
                    "operationId": "showPetById",
                    "tags": [
                        "pets"
                    ],
                    "parameters": [
                        {
                            "name": "petId",
                            "in": "path",
                            "required": True,
                            "description": "The id of the pet to retrieve",
                            "schema": {
                                "type": "string"
                            }
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Expected response to a valid request",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/Pet"
                                    }
                                }
                            }
                        }
                    }
                },
                "delete": {
                    "summary": "Delete a pet",
                    "operationId": "deletePet",
                    "tags": [
                        "pets"
                    ],
                    "parameters": [
                        {
                            "name": "petId",
                            "in": "path",
                            "required": True,
                            "description": "The id of the pet to delete",
                            "schema": {
                                "type": "string"
                            }
                        }
                    ],
                    "responses": {
                        "204": {
                            "description": "No content"
                        }
                    }
                }
            }
        },
        "components": {
            "schemas": {
                "Pet": {
                    "type": "object",
                    "required": [
                        "id",
                        "name"
                    ],
                    "properties": {
                        "id": {
                            "type": "integer",
                            "format": "int64"
                        },
                        "name": {
                            "type": "string"
                        },
                        "tag": {
                            "type": "string"
                        }
                    }
                },
                "NewPet": {
                    "type": "object",
                    "required": [
                        "name"
                    ],
                    "properties": {
                        "name": {
                            "type": "string"
                        },
                        "tag": {
                            "type": "string"
                        }
                    }
                }
            }
        }
    }

@pytest.fixture
def spec_files(petstore_spec, tmp_path):
    """Create temporary spec files for testing."""
    # JSON version
    json_path = tmp_path / "petstore.json"
    with open(json_path, 'w') as f:
        json.dump(petstore_spec, f)
    
    # YAML version
    yaml_path = tmp_path / "petstore.yaml"
    with open(yaml_path, 'w') as f:
        yaml.dump(petstore_spec, f)
    
    return {'json': str(json_path), 'yaml': str(yaml_path)}

@pytest.fixture
def parser(petstore_spec):
    """Create the parser instance for the regular spec."""
    return OpenAPIParser(petstore_spec)

@pytest.fixture
def secure_spec(petstore_spec):
    """Create a secure version of the petstore spec."""
    secure_spec = copy.deepcopy(petstore_spec)
    
    # Add security schemes
    secure_spec['components'] = secure_spec.get('components', {})
    secure_spec['components']['securitySchemes'] = {
        'BearerAuth': {
            'type': 'http',
            'scheme': 'bearer',
            'bearerFormat': 'JWT'
        },
        'ApiKeyAuth': {
            'type': 'apiKey',
            'in': 'header',
            'name': 'X-API-KEY'
        }
    }
    
    # Add global security (applies to all operations unless overridden)
    secure_spec['security'] = [{'BearerAuth': []}]
    
    # Override security for one endpoint (GET /pets will not require auth)
    secure_spec['paths']['/pets']['get']['security'] = []
    
    # Add another security scheme to POST /pets (both bearer and API key)
    secure_spec['paths']['/pets']['post']['security'] = [
        {'BearerAuth': []},
        {'ApiKeyAuth': []}  # This is an OR relationship
    ]
    
    return secure_spec

@pytest.fixture
def secure_parser(secure_spec):
    """Create the parser instance for the secure spec."""
    return OpenAPIParser(secure_spec)

def test_load_spec_from_dict(petstore_spec):
    """Test loading a spec from a dictionary."""
    parser = OpenAPIParser(petstore_spec)
    assert parser.spec['info']['title'] == 'Swagger Petstore'
    assert len(parser.get_endpoints()) == 4

def test_load_spec_from_json_file(spec_files):
    """Test loading a spec from a JSON file."""
    parser = OpenAPIParser(spec_files['json'])
    assert parser.spec['info']['title'] == 'Swagger Petstore'
    assert len(parser.get_endpoints()) == 4

def test_load_spec_from_yaml_file(spec_files):
    """Test loading a spec from a YAML file."""
    parser = OpenAPIParser(spec_files['yaml'])
    assert parser.spec['info']['title'] == 'Swagger Petstore'
    assert len(parser.get_endpoints()) == 4

def test_load_spec_from_json_string(petstore_spec):
    """Test loading a spec from a JSON string."""
    json_string = json.dumps(petstore_spec)
    parser = OpenAPIParser(json_string)
    assert parser.spec['info']['title'] == 'Swagger Petstore'
    assert len(parser.get_endpoints()) == 4

def test_endpoint_count(parser):
    """Test that the correct number of endpoints is extracted."""
    endpoints = parser.get_endpoints()
    assert len(endpoints) == 4

def test_endpoint_methods(parser):
    """Test that the HTTP methods are correctly extracted."""
    endpoints = parser.get_endpoints()
    methods = [endpoint.method for endpoint in endpoints]
    assert 'GET' in methods
    assert 'POST' in methods
    assert 'DELETE' in methods
    assert methods.count('GET') == 2  # Two GET endpoints

def test_endpoint_paths(parser):
    """Test that the paths are correctly extracted."""
    endpoints = parser.get_endpoints()
    paths = [endpoint.path for endpoint in endpoints]
    assert '/pets' in paths
    assert '/pets/{petId}' in paths

def test_operation_ids(parser):
    """Test that operation IDs are correctly extracted."""
    endpoints = parser.get_endpoints()
    operation_ids = [endpoint.operation_id for endpoint in endpoints]
    assert 'listPets' in operation_ids
    assert 'createPets' in operation_ids
    assert 'showPetById' in operation_ids
    assert 'deletePet' in operation_ids

def test_get_endpoint_by_operation_id(parser):
    """Test finding an endpoint by its operation ID."""
    endpoint = parser.get_endpoint_by_operation_id('createPets')
    assert endpoint.method == 'POST'
    assert endpoint.path == '/pets'

def test_get_endpoint_by_method_path(parser):
    """Test finding an endpoint by its method and path."""
    endpoint = parser.get_endpoint('POST', '/pets')
    assert endpoint is not None
    assert endpoint.operation_id == 'createPets'
    
    # Test with lowercase method
    endpoint = parser.get_endpoint('get', '/pets')
    assert endpoint is not None
    assert endpoint.operation_id == 'listPets'
    
    # Test non-existent endpoint
    endpoint = parser.get_endpoint('PUT', '/pets')
    assert endpoint is None

def test_request_body_schema(parser):
    """Test that request body schemas are correctly extracted."""
    endpoints_with_body = parser.get_endpoints_with_request_body()
    assert len(endpoints_with_body) == 1  # Only POST /pets has a request body
    
    create_pet_endpoint = endpoints_with_body[0]
    assert create_pet_endpoint.method == 'POST'
    assert create_pet_endpoint.path == '/pets'
    assert create_pet_endpoint.request_body_schema is not None
    
def test_query_parameters_schema(parser):
    """Test that query parameters schemas are correctly extracted."""
    endpoints_with_query = parser.get_endpoints_with_query_parameters()
    assert len(endpoints_with_query) == 1  # Only GET /pets has query parameters
    
    list_pets_endpoint = endpoints_with_query[0]
    assert list_pets_endpoint.method == 'GET'
    assert list_pets_endpoint.path == '/pets'
    assert list_pets_endpoint.query_parameters_schema is not None
    
    query_schema = list_pets_endpoint.query_parameters_schema
    assert query_schema['type'] == 'object'
    assert 'properties' in query_schema
    assert 'limit' in query_schema['properties']
    assert query_schema['properties']['limit']['type'] == 'integer'
    assert query_schema['properties']['limit']['format'] == 'int32'
    assert 'required' not in query_schema  # limit is not required

def test_path_parameters_schema(parser):
    """Test that path parameters schemas are correctly extracted."""
    endpoints_with_path = parser.get_endpoints_with_path_parameters()
    assert len(endpoints_with_path) == 2  # Both GET and DELETE /pets/{petId} have path parameters
    
    for endpoint in endpoints_with_path:
        assert endpoint.path == '/pets/{petId}'
        assert endpoint.path_parameters_schema is not None
        
        path_schema = endpoint.path_parameters_schema
        assert path_schema['type'] == 'object'
        assert 'properties' in path_schema
        assert 'petId' in path_schema['properties']
        assert path_schema['properties']['petId']['type'] == 'string'
        assert 'required' in path_schema
        assert 'petId' in path_schema['required']  # petId is required

def test_convenience_methods(parser):
    """Test the convenience methods for filtering endpoints."""
    assert len(parser.get_endpoints_with_request_body()) == 1
    assert len(parser.get_endpoints_with_query_parameters()) == 1
    assert len(parser.get_endpoints_with_path_parameters()) == 2

def test_to_json(parser):
    """Test converting endpoints to JSON."""
    json_str = parser.to_json()
    parsed_json = json.loads(json_str)
    assert len(parsed_json) == 4
    
def test_bearer_auth_not_required_by_default(parser):
    """Test that bearer auth is not required by default for the regular petstore spec."""
    for endpoint in parser.get_endpoints():
        assert not endpoint.requires_bearer_auth
    
    assert len(parser.get_endpoints_requiring_bearer_auth()) == 0

def test_bearer_auth_detection_global_security(secure_parser):
    """Test that bearer auth is correctly detected when specified globally."""
    secure_endpoints = secure_parser.get_endpoints_requiring_bearer_auth()
    assert len(secure_endpoints) == 3  # All except GET /pets should require auth
    
    # GET /pets should not require auth (it overrides global security with empty array)
    get_pets = secure_parser.get_endpoint_by_operation_id('listPets')
    assert not get_pets.requires_bearer_auth
    
    # All other endpoints should require auth
    create_pets = secure_parser.get_endpoint_by_operation_id('createPets')
    show_pet = secure_parser.get_endpoint_by_operation_id('showPetById')
    delete_pet = secure_parser.get_endpoint_by_operation_id('deletePet')
    
    assert create_pets.requires_bearer_auth
    assert show_pet.requires_bearer_auth
    assert delete_pet.requires_bearer_auth

def test_multiple_security_schemes(secure_parser):
    """Test that bearer auth is correctly detected when multiple security schemes are specified."""
    # POST /pets has both bearer and API key as alternatives
    create_pets = secure_parser.get_endpoint_by_operation_id('createPets')
    assert create_pets.requires_bearer_auth

def test_parse_countries_spec():
    """Test parsing the countries.yaml OpenAPI specification."""
    countries_yaml_path = os.path.join(os.path.dirname(__file__), 'fixtures', 'countries.yaml')
    parser = OpenAPIParser(countries_yaml_path)
    # If we get here without exceptions, the test passes
    assert True

def test_parse_pokeapi_spec():
    """Test parsing the pokeapi.yaml OpenAPI specification."""
    pokeapi_yaml_path = os.path.join(os.path.dirname(__file__), 'fixtures', 'pokeapi.yaml')
    parser = OpenAPIParser(pokeapi_yaml_path)
    # If we get here without exceptions, the test passes
    assert True