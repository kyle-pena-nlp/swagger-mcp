#!/usr/bin/env python3
import sys
import json
from openapi_parser import OpenAPIParser
import requests

def main():
    """
    Test script to verify that our parser can correctly identify Slack's OAuth security definition.
    """
    # Check for command-line arguments
    if len(sys.argv) < 2:
        print("Usage: python test_slack_auth.py <slack_openapi_spec_file>")
        sys.exit(1)
    
    # Load the Slack OpenAPI specification
    slack_spec_file = sys.argv[1]
    
    try:
        # Parse the OpenAPI specification
        parser = OpenAPIParser(slack_spec_file)
        
        # Get OAuth 2.0 security schemes
        oauth_schemes = parser.get_oauth_auth_code_schemes()
        
        if not oauth_schemes:
            print("No OAuth 2.0 authorization code flow schemes found in the Slack specification.")
            sys.exit(1)
        
        print(f"Found {len(oauth_schemes)} OAuth 2.0 authorization code flow schemes:")
        for scheme_name, scheme in oauth_schemes.items():
            print(f"\nScheme: {scheme_name}")
            print(json.dumps(scheme, indent=2))
            
            # Print the authorization URL and token URL
            if 'flows' in scheme:
                # OpenAPI 3.0 style
                flow_type = 'authorizationCode' if 'authorizationCode' in scheme['flows'] else 'accessCode'
                flow = scheme['flows'][flow_type]
                auth_url = flow.get('authorizationUrl')
                token_url = flow.get('tokenUrl')
            else:
                # OpenAPI 2.0 style (like Slack)
                auth_url = scheme.get('authorizationUrl')
                token_url = scheme.get('tokenUrl')
                
            print(f"\nAuthorization URL: {auth_url}")
            print(f"Token URL: {token_url}")
            
            # Get and print scopes
            scopes = scheme.get('scopes', {})
            if not scopes and 'flows' in scheme:
                # Try OpenAPI 3.0 structure
                flow_type = 'authorizationCode' if 'authorizationCode' in scheme['flows'] else 'accessCode'
                flow = scheme['flows'][flow_type]
                scopes = flow.get('scopes', {})
                
            print(f"\nAvailable scopes ({len(scopes)}):")
            for scope_name, scope_desc in list(scopes.items())[:10]:  # Show first 10 scopes
                print(f"  {scope_name}: {scope_desc}")
            
            if len(scopes) > 10:
                print(f"  ... and {len(scopes) - 10} more")
        
        # Count endpoints requiring OAuth authentication
        oauth_endpoints = parser.get_endpoints_requiring_oauth_auth()
        print(f"\nFound {len(oauth_endpoints)} endpoints requiring OAuth authentication")
        
        # Show a few example endpoints
        if oauth_endpoints:
            print("\nExample endpoints requiring OAuth:")
            for endpoint in oauth_endpoints[:5]:  # Show first 5 endpoints
                print(f"  {endpoint.method} {endpoint.path} - {endpoint.summary}")
            
            if len(oauth_endpoints) > 5:
                print(f"  ... and {len(oauth_endpoints) - 5} more")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 