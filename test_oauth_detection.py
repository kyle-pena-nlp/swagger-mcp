#!/usr/bin/env python3
from openapi_parser import OpenAPIParser

# OpenAPI 3.0 style
openapi3_spec = {
    "components": {
        "securitySchemes": {
            "oauth3": {
                "type": "oauth2",
                "flows": {
                    "authorizationCode": {
                        "authorizationUrl": "https://example.com/auth",
                        "tokenUrl": "https://example.com/token",
                        "scopes": {
                            "read": "Read access",
                            "write": "Write access"
                        }
                    }
                }
            }
        }
    }
}

# OpenAPI 2.0 style (like Slack)
openapi2_spec = {
    "securityDefinitions": {
        "oauth2": {
            "flow": "accessCode",
            "authorizationUrl": "https://slack.com/oauth/authorize",
            "tokenUrl": "https://slack.com/api/oauth.access",
            "scopes": {
                "identify": "Identify the user",
                "chat:write": "Send messages"
            }
        }
    }
}

def test_openapi3():
    parser = OpenAPIParser(openapi3_spec)
    schemes = parser.get_oauth_auth_code_schemes()
    
    print("=== Testing OpenAPI 3.0 OAuth Detection ===")
    print(f"Found OAuth schemes: {list(schemes.keys())}")
    
    if schemes:
        scheme_name, scheme = next(iter(schemes.items()))
        print(f"Is OAuth scheme: {parser._is_oauth_auth_code_scheme(scheme_name)}")

def test_openapi2():
    # For OpenAPI 2.0, we need to manually move securityDefinitions to components.securitySchemes
    # since our parser expects that format
    api2_for_parser = {
        "components": {
            "securitySchemes": openapi2_spec["securityDefinitions"]
        }
    }
    
    parser = OpenAPIParser(api2_for_parser)
    schemes = parser.get_oauth_auth_code_schemes()
    
    print("\n=== Testing OpenAPI 2.0 OAuth Detection ===")
    print(f"Found OAuth schemes: {list(schemes.keys())}")
    
    if schemes:
        scheme_name, scheme = next(iter(schemes.items()))
        print(f"Is OAuth scheme: {parser._is_oauth_auth_code_scheme(scheme_name)}")

if __name__ == "__main__":
    test_openapi3()
    test_openapi2() 