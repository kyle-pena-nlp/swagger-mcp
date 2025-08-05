import pytest

from swagger_mcp.openapi_parser import OpenAPIParser


def _v2_spec_with_body(required: bool = True, consumes_at_op: bool = True):
    """Return a Swagger 2.0 spec with a single body parameter."""
    spec = {
        "swagger": "2.0",
        "info": {"title": "Pet API", "version": "1.0"},
        "paths": {
            "/pets": {
                "post": {
                    "operationId": "createPet",
                    "consumes": ["application/json"] if consumes_at_op else None,
                    "parameters": [
                        {
                            "name": "pet",
                            "in": "body",
                            "description": "Pet to add to store",
                            "required": required,
                            "schema": {
                                "type": "object",
                                "required": ["name"],
                                "properties": {
                                    "name": {"type": "string"},
                                    "age": {"type": "integer"},
                                },
                            },
                        }
                    ],
                    "responses": {"201": {"description": "Created"}},
                }
            }
        },
    }

    if not consumes_at_op:
        spec["consumes"] = ["application/json"]
    return spec


@pytest.mark.parametrize("required", [True, False])
@pytest.mark.parametrize("consumes_at_op", [True, False])
def test_v2_body_parameter_parsed(required, consumes_at_op):
    spec = _v2_spec_with_body(required=required, consumes_at_op=consumes_at_op)
    parser = OpenAPIParser(spec)

    endpoint = parser.get_endpoint("POST", "/pets")
    assert endpoint is not None, "Endpoint should be parsed"

    # Body schema resolved
    assert endpoint.request_body_schema is not None, "Body schema should be set"
    assert endpoint.request_body_schema["type"] == "object"

    # Required flag propagated
    assert endpoint.request_body_required is required

    # Content types detected
    assert "application/json" in endpoint.request_content_types
