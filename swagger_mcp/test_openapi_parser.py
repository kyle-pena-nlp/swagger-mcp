import unittest
import json
import os
from openapi_parser import OpenAPIParser
from endpoint import Endpoint


class TestOpenAPIParser(unittest.TestCase):
    """Test the OpenAPIParser class with the Petstore OpenAPI example."""

    def setUp(self):
        """Set up the test with the Petstore OpenAPI example."""
        # Petstore OpenAPI 3.0 example spec
        self.petstore_spec = {
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
        
        # Save the spec to a file for testing file loading
        with open('petstore.json', 'w') as f:
            json.dump(self.petstore_spec, f)
        
        # Create YAML version for testing YAML loading
        import yaml
        with open('petstore.yaml', 'w') as f:
            yaml.dump(self.petstore_spec, f)

        # Create the parser instance for the regular spec
        self.parser = OpenAPIParser(self.petstore_spec)
        
    def setup_secure_parser(self):
        """Set up a parser with a secure version of the Petstore OpenAPI example."""
        # Create a deep copy of the petstore spec
        import copy
        self.secure_petstore_spec = copy.deepcopy(self.petstore_spec)
        
        # Add security schemes
        self.secure_petstore_spec['components'] = self.secure_petstore_spec.get('components', {})
        self.secure_petstore_spec['components']['securitySchemes'] = {
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
        self.secure_petstore_spec['security'] = [{'BearerAuth': []}]
        
        # Override security for one endpoint (GET /pets will not require auth)
        self.secure_petstore_spec['paths']['/pets']['get']['security'] = []
        
        # Add another security scheme to POST /pets (both bearer and API key)
        self.secure_petstore_spec['paths']['/pets']['post']['security'] = [
            {'BearerAuth': []},
            {'ApiKeyAuth': []}  # This is an OR relationship
        ]
        
        # Save the secure spec to a file
        with open('secure_petstore.json', 'w') as f:
            json.dump(self.secure_petstore_spec, f)

        # Create the parser instance for the secure spec
        self.secure_parser = OpenAPIParser(self.secure_petstore_spec)

    def tearDown(self):
        """Clean up test files."""
        for file in ['petstore.json', 'petstore.yaml', 'secure_petstore.json']:
            if os.path.exists(file):
                os.remove(file)

    def test_load_spec_from_dict(self):
        """Test loading a spec from a dictionary."""
        parser = OpenAPIParser(self.petstore_spec)
        self.assertEqual(parser.spec['info']['title'], 'Swagger Petstore')
        self.assertEqual(len(parser.get_endpoints()), 4)

    def test_load_spec_from_json_file(self):
        """Test loading a spec from a JSON file."""
        parser = OpenAPIParser('petstore.json')
        self.assertEqual(parser.spec['info']['title'], 'Swagger Petstore')
        self.assertEqual(len(parser.get_endpoints()), 4)

    def test_load_spec_from_yaml_file(self):
        """Test loading a spec from a YAML file."""
        parser = OpenAPIParser('petstore.yaml')
        self.assertEqual(parser.spec['info']['title'], 'Swagger Petstore')
        self.assertEqual(len(parser.get_endpoints()), 4)

    def test_load_spec_from_json_string(self):
        """Test loading a spec from a JSON string."""
        json_string = json.dumps(self.petstore_spec)
        parser = OpenAPIParser(json_string)
        self.assertEqual(parser.spec['info']['title'], 'Swagger Petstore')
        self.assertEqual(len(parser.get_endpoints()), 4)

    def test_endpoint_count(self):
        """Test that the correct number of endpoints is extracted."""
        endpoints = self.parser.get_endpoints()
        self.assertEqual(len(endpoints), 4)

    def test_endpoint_methods(self):
        """Test that the HTTP methods are correctly extracted."""
        endpoints = self.parser.get_endpoints()
        methods = [endpoint.method for endpoint in endpoints]
        self.assertIn('GET', methods)
        self.assertIn('POST', methods)
        self.assertIn('DELETE', methods)
        self.assertEqual(methods.count('GET'), 2)  # Two GET endpoints

    def test_endpoint_paths(self):
        """Test that the paths are correctly extracted."""
        endpoints = self.parser.get_endpoints()
        paths = [endpoint.path for endpoint in endpoints]
        self.assertIn('/pets', paths)
        self.assertIn('/pets/{petId}', paths)

    def test_operation_ids(self):
        """Test that operation IDs are correctly extracted."""
        endpoints = self.parser.get_endpoints()
        operation_ids = [endpoint.operation_id for endpoint in endpoints]
        self.assertIn('listPets', operation_ids)
        self.assertIn('createPets', operation_ids)
        self.assertIn('showPetById', operation_ids)
        self.assertIn('deletePet', operation_ids)

    def test_get_endpoint_by_operation_id(self):
        """Test finding an endpoint by its operation ID."""
        endpoint = self.parser.get_endpoint_by_operation_id('createPets')
        self.assertEqual(endpoint.method, 'POST')
        self.assertEqual(endpoint.path, '/pets')

    def test_get_endpoint_by_method_path(self):
        """Test finding an endpoint by its method and path."""
        endpoint = self.parser.get_endpoint('POST', '/pets')
        self.assertIsNotNone(endpoint)
        self.assertEqual(endpoint.operation_id, 'createPets')
        
        # Test with lowercase method
        endpoint = self.parser.get_endpoint('get', '/pets')
        self.assertIsNotNone(endpoint)
        self.assertEqual(endpoint.operation_id, 'listPets')
        
        # Test non-existent endpoint
        endpoint = self.parser.get_endpoint('PUT', '/pets')
        self.assertIsNone(endpoint)

    def test_request_body_schema(self):
        """Test that request body schemas are correctly extracted."""
        endpoints_with_body = self.parser.get_endpoints_with_request_body()
        self.assertEqual(len(endpoints_with_body), 1)  # Only POST /pets has a request body
        
        create_pet_endpoint = endpoints_with_body[0]
        self.assertEqual(create_pet_endpoint.method, 'POST')
        self.assertEqual(create_pet_endpoint.path, '/pets')
        self.assertIsNotNone(create_pet_endpoint.request_body_schema)
        self.assertEqual(create_pet_endpoint.request_body_schema['$ref'], '#/components/schemas/NewPet')

    def test_query_parameters_schema(self):
        """Test that query parameters schemas are correctly extracted."""
        endpoints_with_query = self.parser.get_endpoints_with_query_parameters()
        self.assertEqual(len(endpoints_with_query), 1)  # Only GET /pets has query parameters
        
        list_pets_endpoint = endpoints_with_query[0]
        self.assertEqual(list_pets_endpoint.method, 'GET')
        self.assertEqual(list_pets_endpoint.path, '/pets')
        self.assertIsNotNone(list_pets_endpoint.query_parameters_schema)
        
        query_schema = list_pets_endpoint.query_parameters_schema
        self.assertEqual(query_schema['type'], 'object')
        self.assertIn('properties', query_schema)
        self.assertIn('limit', query_schema['properties'])
        self.assertEqual(query_schema['properties']['limit']['type'], 'integer')
        self.assertEqual(query_schema['properties']['limit']['format'], 'int32')
        self.assertNotIn('required', query_schema)  # limit is not required

    def test_path_parameters_schema(self):
        """Test that path parameters schemas are correctly extracted."""
        endpoints_with_path = self.parser.get_endpoints_with_path_parameters()
        self.assertEqual(len(endpoints_with_path), 2)  # Both GET and DELETE /pets/{petId} have path parameters
        
        for endpoint in endpoints_with_path:
            self.assertEqual(endpoint.path, '/pets/{petId}')
            self.assertIsNotNone(endpoint.path_parameters_schema)
            
            path_schema = endpoint.path_parameters_schema
            self.assertEqual(path_schema['type'], 'object')
            self.assertIn('properties', path_schema)
            self.assertIn('petId', path_schema['properties'])
            self.assertEqual(path_schema['properties']['petId']['type'], 'string')
            self.assertIn('required', path_schema)
            self.assertIn('petId', path_schema['required'])  # petId is required

    def test_convenience_methods(self):
        """Test the convenience methods for filtering endpoints."""
        self.assertEqual(len(self.parser.get_endpoints_with_request_body()), 1)
        self.assertEqual(len(self.parser.get_endpoints_with_query_parameters()), 1)
        self.assertEqual(len(self.parser.get_endpoints_with_path_parameters()), 2)

    def test_to_json(self):
        """Test converting endpoints to JSON."""
        json_str = self.parser.to_json()
        parsed_json = json.loads(json_str)
        self.assertEqual(len(parsed_json), 4)
        
    def test_bearer_auth_not_required_by_default(self):
        """Test that bearer auth is not required by default for the regular petstore spec."""
        for endpoint in self.parser.get_endpoints():
            self.assertFalse(endpoint.requires_bearer_auth)
        
        self.assertEqual(len(self.parser.get_endpoints_requiring_bearer_auth()), 0)
    
    def test_bearer_auth_detection_global_security(self):
        """Test that bearer auth is correctly detected when specified globally."""
        # Set up the secure parser
        self.setup_secure_parser()
        
        secure_endpoints = self.secure_parser.get_endpoints_requiring_bearer_auth()
        self.assertEqual(len(secure_endpoints), 3)  # All except GET /pets should require auth
        
        # GET /pets should not require auth (it overrides global security with empty array)
        get_pets = self.secure_parser.get_endpoint_by_operation_id('listPets')
        self.assertFalse(get_pets.requires_bearer_auth)
        
        # All other endpoints should require auth
        create_pets = self.secure_parser.get_endpoint_by_operation_id('createPets')
        show_pet = self.secure_parser.get_endpoint_by_operation_id('showPetById')
        delete_pet = self.secure_parser.get_endpoint_by_operation_id('deletePet')
        
        self.assertTrue(create_pets.requires_bearer_auth)
        self.assertTrue(show_pet.requires_bearer_auth)
        self.assertTrue(delete_pet.requires_bearer_auth)
    
    def test_multiple_security_schemes(self):
        """Test that bearer auth is correctly detected when multiple security schemes are specified."""
        # Set up the secure parser
        self.setup_secure_parser()
        
        # POST /pets has both bearer and API key as alternatives
        create_pets = self.secure_parser.get_endpoint_by_operation_id('createPets')
        self.assertTrue(create_pets.requires_bearer_auth)


if __name__ == '__main__':
    unittest.main() 