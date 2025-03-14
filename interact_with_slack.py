#!/usr/bin/env python3
import os
import sys
import json
from openapi_parser import OpenAPIParser
from endpoint_invoker import EndpointInvoker
from oauth_handler import OAuthHandler
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def list_endpoints(parser):
    """List all endpoints in the Slack API that require OAuth authentication."""
    oauth_endpoints = parser.get_endpoints_requiring_oauth_auth()
    
    if not oauth_endpoints:
        print("No endpoints requiring OAuth authentication found.")
        return
    
    print(f"\nFound {len(oauth_endpoints)} endpoints requiring OAuth authentication:")
    for i, endpoint in enumerate(oauth_endpoints):
        method = endpoint.method.ljust(7)
        print(f"{i+1}. {method} {endpoint.path}")
        if endpoint.summary:
            print(f"   Summary: {endpoint.summary}")
        print()

def get_oauth_credentials():
    """
    Get OAuth credentials from environment variables or prompt the user.
    
    Returns:
        Dictionary with client_id, client_secret
    """
    # First check environment variables
    client_id = os.environ.get('SLACK_CLIENT_ID')
    client_secret = os.environ.get('SLACK_CLIENT_SECRET')
    
    # If not set, prompt the user
    if not client_id:
        client_id = input("Enter your Slack client ID: ")
    
    if not client_secret:
        client_secret = input("Enter your Slack client secret: ")
    
    return {
        'client_id': client_id,
        'client_secret': client_secret
    }

def main():
    """
    Main function to interact with the Slack API.
    """
    # Check command line arguments
    if len(sys.argv) < 2:
        print("Usage: python interact_with_slack.py <slack_openapi_spec> [endpoint_method endpoint_path]")
        print("\nExamples:")
        print("  python interact_with_slack.py slack_openapi.json")
        print("  python interact_with_slack.py slack_openapi.json GET /users.list")
        sys.exit(1)
    
    # Get the Slack OpenAPI spec file path
    slack_spec_file = sys.argv[1]
    
    try:
        # Parse the Slack OpenAPI spec
        parser = OpenAPIParser(slack_spec_file)
        
        # Get OAuth 2.0 security schemes
        oauth_schemes = parser.get_oauth_auth_code_schemes()
        
        if not oauth_schemes:
            print("No OAuth 2.0 authorization code flow schemes found in the Slack specification.")
            sys.exit(1)
        
        # Use the first OAuth scheme (usually there's only one for Slack)
        scheme_name, scheme = next(iter(oauth_schemes.items()))
        
        # Extract OAuth auth and token URLs
        oauth_handler = OAuthHandler()
        auth_url, token_url, scopes = oauth_handler.extract_oauth_urls_from_scheme(scheme)
        
        # Get or choose an endpoint to invoke
        if len(sys.argv) >= 4:
            # User specified an endpoint method and path
            method = sys.argv[2].upper()
            path = sys.argv[3]
            
            # Find the endpoint
            endpoint = parser.get_endpoint(method, path)
            if not endpoint:
                print(f"Endpoint {method} {path} not found in the spec.")
                list_endpoints(parser)
                sys.exit(1)
                
        else:
            # List endpoints and let user choose
            list_endpoints(parser)
            
            # Get user selection
            oauth_endpoints = parser.get_endpoints_requiring_oauth_auth()
            while True:
                try:
                    selection = input("\nEnter the number of the endpoint to invoke (or 'q' to quit): ")
                    if selection.lower() == 'q':
                        sys.exit(0)
                        
                    index = int(selection) - 1
                    if 0 <= index < len(oauth_endpoints):
                        endpoint = oauth_endpoints[index]
                        break
                    else:
                        print(f"Please enter a number between 1 and {len(oauth_endpoints)}.")
                except ValueError:
                    print("Please enter a valid number.")
        
        # Show the selected endpoint
        print(f"\nSelected endpoint: {endpoint.method} {endpoint.path}")
        if endpoint.summary:
            print(f"Summary: {endpoint.summary}")
        
        # Get OAuth credentials
        creds = get_oauth_credentials()
        
        # Prepare OAuth credentials with auth and token URLs
        oauth_credentials = {
            'client_id': creds['client_id'],
            'client_secret': creds['client_secret'],
            'auth_url': auth_url,
            'token_url': token_url,
            'scope': 'chat:write users:read',  # Common Slack scopes - adjust as needed
            'service_name': 'slack'
        }
        
        # Check if the endpoint has parameters and collect them
        params = {}
        
        # Process path parameters
        if endpoint.path_parameters_schema and 'properties' in endpoint.path_parameters_schema:
            print("\nPath parameters:")
            for param_name, param_schema in endpoint.path_parameters_schema['properties'].items():
                is_required = 'required' in endpoint.path_parameters_schema and param_name in endpoint.path_parameters_schema['required']
                desc = param_schema.get('description', '')
                if desc:
                    desc = f" ({desc})"
                
                if is_required:
                    param_value = input(f"  Enter {param_name}{desc} (required): ")
                    params[param_name] = param_value
                else:
                    param_value = input(f"  Enter {param_name}{desc} (optional, press Enter to skip): ")
                    if param_value:
                        params[param_name] = param_value
        
        # Process query parameters
        if endpoint.query_parameters_schema and 'properties' in endpoint.query_parameters_schema:
            print("\nQuery parameters:")
            for param_name, param_schema in endpoint.query_parameters_schema['properties'].items():
                is_required = 'required' in endpoint.query_parameters_schema and param_name in endpoint.query_parameters_schema['required']
                desc = param_schema.get('description', '')
                if desc:
                    desc = f" ({desc})"
                    
                if is_required:
                    param_value = input(f"  Enter {param_name}{desc} (required): ")
                    params[param_name] = param_value
                else:
                    param_value = input(f"  Enter {param_name}{desc} (optional, press Enter to skip): ")
                    if param_value:
                        params[param_name] = param_value
        
        # Prepare server URL
        server_url = "https://slack.com/api"
        
        # Create endpoint invoker
        invoker = EndpointInvoker(endpoint, oauth_handler)
        
        # Invoke the endpoint
        print(f"\nInvoking {endpoint.method} {endpoint.path}...")
        try:
            response = invoker.invoke_with_params(
                params=params,
                server_url=server_url,
                oauth_credentials=oauth_credentials
            )
            
            # Print response
            print(f"\nResponse status code: {response.status_code}")
            
            # Parse and pretty-print the JSON response
            try:
                json_response = response.json()
                print("\nResponse body:")
                print(json.dumps(json_response, indent=2))
                
                # For Slack, check if successful
                if not json_response.get('ok', False):
                    print(f"\nSlack API Error: {json_response.get('error', 'Unknown error')}")
                    if 'needed' in json_response:
                        print(f"Scope needed: {json_response['needed']}")
                
            except ValueError:
                print("\nNon-JSON response:")
                print(response.text)
                
        except Exception as e:
            print(f"\nError invoking Slack API: {e}")
    
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 