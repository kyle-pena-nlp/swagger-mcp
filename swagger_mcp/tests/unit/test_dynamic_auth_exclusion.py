import pytest

from swagger_mcp.openapi_parser import OpenAPIParser


# ---------- OpenAPI 3.0 specs ----------

def _v3_spec(oauth_only: bool = True):
    """Return an OpenAPI 3.0 spec with OAuth2 and Bearer schemes."""
    spec = {
        "openapi": "3.0.0",
        "info": {"title": "Auth API", "version": "1.0.0"},
        "components": {
            "securitySchemes": {
                "OAuth": {
                    "type": "oauth2",
                    "flows": {
                        "authorizationCode": {
                            "authorizationUrl": "https://example.com/auth",
                            "tokenUrl": "https://example.com/token",
                            "scopes": {"read": "Read access"},
                        }
                    },
                },
                "BearerAuth": {"type": "http", "scheme": "bearer"},
            }
        },
        "paths": {
            "/oauth-only": {
                "get": {
                    "operationId": "oauthOnly",
                    "security": [{"OAuth": ["read"]}],
                    "responses": {"200": {"description": "OK"}},
                }
            },
            "/oauth-or-bearer": {
                "get": {
                    "operationId": "oauthOrBearer",
                    "security": (
                        [{"OAuth": ["read"]}] if oauth_only else [{"OAuth": ["read"]}, {"BearerAuth": []}]
                    ),
                    "responses": {"200": {"description": "OK"}},
                }
            },
        },
    }
    return spec


# ---------- Swagger 2.0 specs ----------

def _v2_spec(oauth_only: bool = True):
    spec = {
        "swagger": "2.0",
        "info": {"title": "Auth API", "version": "1.0.0"},
        "securityDefinitions": {
            "OAuth2": {
                "type": "oauth2",
                "authorizationUrl": "https://example.com/auth",
                "flow": "implicit",
                "scopes": {"read": "Read data"},
            },
            "ApiKeyHeader": {"type": "apiKey", "in": "header", "name": "X-API-Key"},
        },
        "paths": {
            "/oauth-only": {
                "get": {
                    "operationId": "v2OauthOnly",
                    "security": [{"OAuth2": ["read"]}],
                    "responses": {"200": {"description": "OK"}},
                }
            },
            "/oauth-or-apikey": {
                "get": {
                    "operationId": "v2OauthOrApiKey",
                    "security": (
                        [{"OAuth2": ["read"]}] if oauth_only else [{"OAuth2": ["read"]}, {"ApiKeyHeader": []}]
                    ),
                    "responses": {"200": {"description": "OK"}},
                }
            },
        },
    }
    return spec


# ---------- Tests ----------

@pytest.mark.parametrize("oauth_only", [True])
def test_v3_oauth_only_endpoint_excluded(oauth_only):
    parser = OpenAPIParser(_v3_spec(oauth_only=True))
    assert parser.get_endpoint_by_operation_id("oauthOnly") is None


def test_v3_oauth_or_bearer_included():
    parser = OpenAPIParser(_v3_spec(oauth_only=False))
    assert parser.get_endpoint_by_operation_id("oauthOrBearer") is not None


def test_v2_oauth_only_endpoint_excluded():
    parser = OpenAPIParser(_v2_spec(oauth_only=True))
    assert parser.get_endpoint_by_operation_id("v2OauthOnly") is None


def test_v2_oauth_or_apikey_included():
    parser = OpenAPIParser(_v2_spec(oauth_only=False))
    assert parser.get_endpoint_by_operation_id("v2OauthOrApiKey") is not None
