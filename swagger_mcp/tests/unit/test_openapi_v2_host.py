import pytest

from swagger_mcp.openapi_parser import OpenAPIParser


def _base_spec():
    """Return minimal v2 skeleton shared by all cases."""
    return {
        "swagger": "2.0",
        "info": {"title": "Test API", "version": "1.0.0"},
        "paths": {
            "/pets": {
                "get": {
                    "operationId": "listPets",
                    "responses": {
                        "200": {"description": "OK"}
                    },
                }
            }
        },
    }


@pytest.mark.parametrize(
    "modifier, expected_base",
    [
        (
            lambda s: s.update({
                "host": "api.example.com",
                "schemes": ["https"],
            }),
            "https://api.example.com",
        ),
        (
            lambda s: s.update({
                "host": "api.example.com",
                "schemes": ["https"],
                "basePath": "/v1",
            }),
            "https://api.example.com/v1",
        ),
        (
            lambda s: s.update({
                "host": "api.example.com",
                "schemes": ["http"],
                "basePath": "/v2",
            }),
            "http://api.example.com/v2",
        ),
        (
            lambda s: s.update({
                "host": "api.example.com",
            }),
            "http://api.example.com",
        ),
    ],
)
def test_v2_base_url_construction(modifier, expected_base):
    """Ensure host/basePath/schemes are combined into default server URL."""
    spec = _base_spec()
    modifier(spec)  # apply specific scenario changes

    parser = OpenAPIParser(spec)
    endpoint = parser.get_endpoint("GET", "/pets")

    assert endpoint is not None, "Endpoint should be parsed"
    assert (
        endpoint.default_server_url == expected_base
    ), f"Expected base URL '{expected_base}', got '{endpoint.default_server_url}'"
