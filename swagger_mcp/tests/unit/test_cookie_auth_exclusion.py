import pytest

from swagger_mcp.openapi_parser import OpenAPIParser


def _spec(cookie_only: bool = True):
    """Return an OpenAPI 3.0 spec with cookie security.

    If *cookie_only* is False the operation will allow an alternative non-cookie scheme as well.
    """
    spec = {
        "openapi": "3.0.0",
        "info": {"title": "Cookie API", "version": "1.0.0"},
        "components": {
            "securitySchemes": {
                "CookieAuth": {
                    "type": "apiKey",
                    "in": "cookie",
                    "name": "session_id",
                },
                "BearerAuth": {
                    "type": "http",
                    "scheme": "bearer",
                    "bearerFormat": "JWT",
                },
            }
        },
        "paths": {
            "/cookie-only": {
                "get": {
                    "operationId": "cookieOnly",
                    "security": [{"CookieAuth": []}],
                    "responses": {"200": {"description": "OK"}},
                }
            },
            "/cookie-and-bearer": {
                "get": {
                    "operationId": "cookieAndBearer",
                    "security": (
                        [{"CookieAuth": []}] if cookie_only else [{"CookieAuth": []}, {"BearerAuth": []}]
                    ),
                    "responses": {"200": {"description": "OK"}},
                }
            },
        },
    }
    return spec


def test_cookie_only_endpoint_excluded():
    parser = OpenAPIParser(_spec(cookie_only=True))
    op = parser.get_endpoint_by_operation_id("cookieOnly")
    assert op is None, "Endpoint requiring only cookie auth should be excluded"


def test_cookie_and_bearer_endpoint_included():
    parser = OpenAPIParser(_spec(cookie_only=False))
    op = parser.get_endpoint_by_operation_id("cookieAndBearer")
    assert op is not None, "Endpoint with alternative auth should be kept"
