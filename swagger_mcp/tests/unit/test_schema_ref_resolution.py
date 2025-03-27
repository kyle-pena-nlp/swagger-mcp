import pytest
from swagger_mcp.openapi_parser import OpenAPIParser

def test_request_body_schema_ref_resolution():
    """Test that request body schema references are properly resolved."""
    spec = {
        "openapi": "3.0.0",
        "info": {"title": "Test API", "version": "1.0.0"},
        "components": {
            "schemas": {
                "User": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "name": {"type": "string"},
                        "address": {"$ref": "#/components/schemas/Address"}
                    },
                    "required": ["name"]
                },
                "Address": {
                    "type": "object",
                    "properties": {
                        "street": {"type": "string"},
                        "city": {"type": "string"},
                        "country": {"type": "string"}
                    },
                    "required": ["street", "city"]
                }
            }
        },
        "paths": {
            "/users": {
                "post": {
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/User"
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    parser = OpenAPIParser(spec)
    endpoints = parser.get_endpoints()
    assert len(endpoints) == 1
    
    endpoint = endpoints[0]
    assert endpoint.request_body_schema is not None
    assert "$ref" not in str(endpoint.request_body_schema)  # No unresolved refs
    assert endpoint.request_body_schema["type"] == "object"
    assert "name" in endpoint.request_body_schema["properties"]
    assert "address" in endpoint.request_body_schema["properties"]
    
    # Verify nested reference was resolved
    address_schema = endpoint.request_body_schema["properties"]["address"]
    assert "$ref" not in str(address_schema)
    assert address_schema["type"] == "object"
    assert "street" in address_schema["properties"]
    assert "city" in address_schema["properties"]

def test_parameter_schema_ref_resolution():
    """Test that parameter schema references are properly resolved."""
    spec = {
        "openapi": "3.0.0",
        "info": {"title": "Test API", "version": "1.0.0"},
        "components": {
            "schemas": {
                "Pagination": {
                    "type": "object",
                    "properties": {
                        "page": {"type": "integer", "minimum": 1},
                        "limit": {"type": "integer", "minimum": 1, "maximum": 100}
                    }
                },
                "Filter": {
                    "type": "object",
                    "properties": {
                        "status": {"type": "string", "enum": ["active", "inactive"]},
                        "type": {"type": "string"}
                    }
                }
            }
        },
        "paths": {
            "/items/{id}": {
                "get": {
                    "parameters": [
                        {
                            "name": "id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"}
                        },
                        {
                            "name": "pagination",
                            "in": "query",
                            "schema": {"$ref": "#/components/schemas/Pagination"}
                        },
                        {
                            "name": "filter",
                            "in": "query",
                            "schema": {"$ref": "#/components/schemas/Filter"}
                        }
                    ]
                }
            }
        }
    }

    parser = OpenAPIParser(spec)
    endpoints = parser.get_endpoints()
    assert len(endpoints) == 1
    
    endpoint = endpoints[0]
    
    # Check path parameters
    assert endpoint.path_parameters_schema is not None
    assert "id" in endpoint.path_parameters_schema["properties"]
    
    # Check query parameters
    assert endpoint.query_parameters_schema is not None
    assert "pagination" in endpoint.query_parameters_schema["properties"]
    assert "filter" in endpoint.query_parameters_schema["properties"]
    
    # Verify pagination schema reference was resolved
    pagination_schema = endpoint.query_parameters_schema["properties"]["pagination"]
    assert "$ref" not in str(pagination_schema)
    assert pagination_schema["type"] == "object"
    assert "page" in pagination_schema["properties"]
    assert pagination_schema["properties"]["page"]["minimum"] == 1
    
    # Verify filter schema reference was resolved
    filter_schema = endpoint.query_parameters_schema["properties"]["filter"]
    assert "$ref" not in str(filter_schema)
    assert filter_schema["type"] == "object"
    assert "status" in filter_schema["properties"]
    assert "active" in filter_schema["properties"]["status"]["enum"]

def test_nested_schema_ref_resolution():
    """Test that deeply nested schema references are properly resolved."""
    spec = {
        "openapi": "3.0.0",
        "info": {"title": "Test API", "version": "1.0.0"},
        "components": {
            "schemas": {
                "Order": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "customer": {"$ref": "#/components/schemas/Customer"},
                        "items": {
                            "type": "array",
                            "items": {"$ref": "#/components/schemas/OrderItem"}
                        }
                    }
                },
                "Customer": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "name": {"type": "string"},
                        "address": {"$ref": "#/components/schemas/Address"}
                    }
                },
                "OrderItem": {
                    "type": "object",
                    "properties": {
                        "product": {"$ref": "#/components/schemas/Product"},
                        "quantity": {"type": "integer"}
                    }
                },
                "Product": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "name": {"type": "string"},
                        "category": {"$ref": "#/components/schemas/Category"}
                    }
                },
                "Category": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "name": {"type": "string"}
                    }
                },
                "Address": {
                    "type": "object",
                    "properties": {
                        "street": {"type": "string"},
                        "city": {"type": "string"}
                    }
                }
            }
        },
        "paths": {
            "/orders": {
                "post": {
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/Order"
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    parser = OpenAPIParser(spec)
    endpoints = parser.get_endpoints()
    assert len(endpoints) == 1
    
    endpoint = endpoints[0]
    assert endpoint.request_body_schema is not None
    
    # Verify no unresolved references remain anywhere in the schema
    def check_no_refs(schema):
        if isinstance(schema, dict):
            assert "$ref" not in schema
            for value in schema.values():
                check_no_refs(value)
        elif isinstance(schema, list):
            for item in schema:
                check_no_refs(item)
    
    check_no_refs(endpoint.request_body_schema)
    
    # Verify the deeply nested structure was preserved and resolved
    schema = endpoint.request_body_schema
    assert "customer" in schema["properties"]
    assert "items" in schema["properties"]
    
    customer_schema = schema["properties"]["customer"]
    assert "address" in customer_schema["properties"]
    
    items_schema = schema["properties"]["items"]
    assert items_schema["type"] == "array"
    assert "product" in items_schema["items"]["properties"]
    
    product_schema = items_schema["items"]["properties"]["product"]
    assert "category" in product_schema["properties"]
