#!/usr/bin/env python3
import os
import sys
import json
from openapi_parser import OpenAPIParser
from endpoint_invoker import EndpointInvoker
from oauth_handler import OAuthHandler

def main():
    """
    Example of using the OpenAPI parser and endpoint invoker with OAuth 2.0 authorization code flow.
    """
    # Check for command-line arguments
    if len(sys.argv) < 2:
        print("Usage: python oauth_example.py <openapi_spec_file>")
        sys.exit(1)
    
    # Load the OpenAPI specification from the command-line argument
    openapi_spec_file = sys.argv[1]
    
    try:
        # Parse the OpenAPI specification
        parser = OpenAPIParser(openapi_spec_file)
        
        # Get OAuth 2.0 security schemes with authorization code flow
        oauth_schemes = parser.get_oauth_auth_code_schemes()
        
        if not oauth_schemes:
            print("No OAuth 2.0 authorization code flow schemes found in the specification.")
            sys.exit(1)
        
        print(f"Found {len(oauth_schemes)} OAuth 2.0 authorization code flow schemes:")
        for scheme_name, scheme in oauth_schemes.items():
            print(f"  - {scheme_name}")
            
            # Print the authorization URL and token URL for each scheme
            if 'flows' in scheme:
                flow_type = 'authorizationCode' if 'authorizationCode' in scheme['flows'] else 'accessCode'
                flow = scheme['flows'][flow_type]
                
                print(f"    Authorization URL: {flow.get('authorizationUrl', 'N/A')}")
                print(f"    Token URL: {flow.get('tokenUrl', 'N/A')}")
                print(f"    Scopes: {', '.join(flow.get('scopes', {}).keys())}")
        
        # Get endpoints that require OAuth 2.0 authentication
        oauth_endpoints = parser.get_endpoints_requiring_oauth_auth()
        
        print(f"\nFound {len(oauth_endpoints)} endpoints requiring OAuth 2.0 authentication:")
        for i, endpoint in enumerate(oauth_endpoints):
            print(f"  {i+1}. {endpoint.method} {endpoint.path} - {endpoint.summary}")
        
        # If no OAuth endpoints are found, exit
        if not oauth_endpoints:
            print("No endpoints requiring OAuth 2.0 authentication found.")
            sys.exit(0)
        
        # Let the user choose an endpoint to invoke
        endpoint_index = 0
        if len(oauth_endpoints) > 1:
            while True:
                try:
                    endpoint_index = int(input("\nEnter the number of the endpoint to invoke: ")) - 1
                    if 0 <= endpoint_index < len(oauth_endpoints):
                        break
                    print(f"Please enter a number between 1 and {len(oauth_endpoints)}.")
                except ValueError:
                    print("Please enter a valid number.")
        
        endpoint = oauth_endpoints[endpoint_index]
        print(f"\nSelected endpoint: {endpoint.method} {endpoint.path}")
        
        # Create an OAuth handler
        oauth_handler = OAuthHandler()
        
        # Create an endpoint invoker
        invoker = EndpointInvoker(endpoint, oauth_handler)
        
        # Let the user choose an OAuth scheme
        scheme_name, scheme = next(iter(oauth_schemes.items()))
        if len(oauth_schemes) > 1:
            print("\nAvailable OAuth schemes:")
            for i, (name, _) in enumerate(oauth_schemes.items()):
                print(f"  {i+1}. {name}")
            
            while True:
                try:
                    scheme_index = int(input("\nEnter the number of the OAuth scheme to use: ")) - 1
                    if 0 <= scheme_index < len(oauth_schemes):
                        scheme_name = list(oauth_schemes.keys())[scheme_index]
                        scheme = oauth_schemes[scheme_name]
                        break
                    print(f"Please enter a number between 1 and {len(oauth_schemes)}.")
                except ValueError:
                    print("Please enter a valid number.")
        
        print(f"\nUsing OAuth scheme: {scheme_name}")
        
        # Get the flow information - handling both OpenAPI 3.0 and 2.0 structures
        auth_url = None
        token_url = None
        available_scopes = {}
        
        if 'flows' in scheme:
            # OpenAPI 3.0 style
            flow_type = 'authorizationCode' if 'authorizationCode' in scheme['flows'] else 'accessCode'
            flow = scheme['flows'][flow_type]
            auth_url = flow.get('authorizationUrl')
            token_url = flow.get('tokenUrl')
            available_scopes = flow.get('scopes', {})
        else:
            # OpenAPI 2.0 (Swagger) style like in Slack's API
            auth_url = scheme.get('authorizationUrl')
            token_url = scheme.get('tokenUrl')
            available_scopes = scheme.get('scopes', {})
        
        # Ask for client ID and secret
        client_id = input("\nEnter the client ID: ")
        client_secret = input("Enter the client secret: ")
        
        # Ask for scopes if available
        scope = None
        if available_scopes:
            print("\nAvailable scopes:")
            for i, (scope_name, scope_desc) in enumerate(available_scopes.items()):
                print(f"  {i+1}. {scope_name} - {scope_desc}")
            
            selected_scopes = input("\nEnter scope(s) to request (comma-separated, or leave empty for all): ")
            
            if selected_scopes.strip():
                scope = selected_scopes
            else:
                scope = " ".join(available_scopes.keys())
        
        # Prepare OAuth credentials
        oauth_credentials = {
            'client_id': client_id,
            'client_secret': client_secret,
            'auth_url': auth_url,
            'token_url': token_url,
            'scope': scope,
            'service_name': scheme_name
        }
        
        print("\nPreparing to invoke endpoint with OAuth authentication...")
        print(f"  Authorization URL: {auth_url}")
        print(f"  Token URL: {token_url}")
        print(f"  Scope: {scope}")
        
        # Prepare any additional parameters for the endpoint
        params = {}
        server_url = None
        
        # If the endpoint has a server URL, use it
        if endpoint.servers:
            server_url = endpoint.servers[0].get('url')
        
        # If the endpoint has path parameters, ask for them
        if endpoint.path_parameters_schema:
            print("\nThis endpoint requires path parameters:")
            for param_name in endpoint.path_parameters_schema.get('properties', {}):
                is_required = param_name in endpoint.path_parameters_schema.get('required', [])
                if is_required:
                    param_value = input(f"  Enter value for required path parameter '{param_name}': ")
                    params[param_name] = param_value
                else:
                    param_value = input(f"  Enter value for optional path parameter '{param_name}' (leave empty to skip): ")
                    if param_value:
                        params[param_name] = param_value
        
        # If the endpoint has query parameters, ask for them
        if endpoint.query_parameters_schema:
            print("\nThis endpoint accepts query parameters:")
            for param_name in endpoint.query_parameters_schema.get('properties', {}):
                is_required = param_name in endpoint.query_parameters_schema.get('required', [])
                if is_required:
                    param_value = input(f"  Enter value for required query parameter '{param_name}': ")
                    params[param_name] = param_value
                else:
                    param_value = input(f"  Enter value for optional query parameter '{param_name}' (leave empty to skip): ")
                    if param_value:
                        params[param_name] = param_value
        
        # Invoke the endpoint
        try:
            print("\nInvoking endpoint with OAuth authentication...")
            response = invoker.invoke_with_params(
                params=params,
                server_url=server_url,
                oauth_credentials=oauth_credentials
            )
            
            # Print the response
            print(f"\nResponse status code: {response.status_code}")
            print("Response headers:")
            for header, value in response.headers.items():
                print(f"  {header}: {value}")
            
            # Try to pretty-print JSON response
            try:
                json_response = response.json()
                print("\nResponse body (JSON):")
                print(json.dumps(json_response, indent=2))
            except ValueError:
                # Not JSON, print as text
                print("\nResponse body:")
                print(response.text)
            
        except Exception as e:
            print(f"\nError invoking endpoint: {e}")
    
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 