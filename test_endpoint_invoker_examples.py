#!/usr/bin/env python3
"""
Example script for testing EndpointInvoker with the OpenAPI spec at http://localhost:9000/openapi.json

This script:
1. Fetches the OpenAPI spec from the local server
2. Shows basic information about the API
3. Runs a few example API calls using EndpointInvoker
"""
import sys
import os
import json
import requests
from typing import Dict, List, Any, Optional

# Add the local-mcp directory to the path if needed
current_dir = os.path.dirname(os.path.abspath(__file__))
local_mcp_dir = os.path.join(current_dir, 'local-mcp')
if os.path.exists(local_mcp_dir):
    sys.path.append(local_mcp_dir)

# Import the required classes
from openapi_parser import OpenAPIParser
from endpoint_invoker import EndpointInvoker, EndpointInvocationError

# URL for the OpenAPI spec
OPENAPI_SPEC_URL = "http://localhost:9000/openapi.json"
# Default server URL to use for API calls if not defined in the spec
DEFAULT_SERVER_URL = "http://localhost:9000"

def fetch_openapi_spec(url: str) -> dict:
    """
    Fetch the OpenAPI specification from a URL.
    
    Args:
        url: The URL to fetch the OpenAPI spec from
        
    Returns:
        The parsed OpenAPI spec as a dictionary
    """
    print(f"Fetching OpenAPI spec from {url}...")
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        # Try to parse as JSON
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching OpenAPI spec: {e}")
        raise
    except json.JSONDecodeError as e:
        print(f"Error parsing OpenAPI spec as JSON: {e}")
        raise

def print_api_info(parser: OpenAPIParser) -> None:
    """
    Print basic information about the API.
    
    Args:
        parser: The OpenAPIParser instance
    """
    spec = parser.spec
    
    print("\n=== API Information ===")
    print(f"Title: {spec.get('info', {}).get('title', 'Unknown')}")
    print(f"Version: {spec.get('info', {}).get('version', 'Unknown')}")
    print(f"Description: {spec.get('info', {}).get('description', 'No description available')}")
    
    # Print server information
    servers = spec.get('servers', [])
    if servers:
        print("\nServers:")
        for server in servers:
            print(f"  {server.get('url')} - {server.get('description', 'No description')}")
    
    # Print endpoint count by path
    paths = spec.get('paths', {})
    print(f"\nEndpoints: {len(parser.endpoints)} across {len(paths)} paths")

def run_example(parser: OpenAPIParser, operation_id: str, params: Optional[Dict[str, Any]] = None, 
                server_url: Optional[str] = None, description: str = "") -> None:
    """
    Run an example API call using EndpointInvoker.
    
    Args:
        parser: The OpenAPIParser instance
        operation_id: The operation ID of the endpoint to invoke
        params: Parameters to pass to the endpoint
        server_url: Optional server URL to override the one in the spec
        description: Description of the example
    """
    print(f"\n=== Example: {description or operation_id} ===")
    
    # Get the endpoint
    endpoint = parser.get_endpoint_by_operation_id(operation_id)
    if not endpoint:
        print(f"Error: No endpoint found with operation ID '{operation_id}'")
        return
    
    # Print endpoint information
    print(f"Operation ID: {operation_id}")
    print(f"Method: {endpoint.method}")
    print(f"Path: {endpoint.path}")
    
    # Create an EndpointInvoker
    invoker = EndpointInvoker(endpoint)
    
    try:
        # If server_url is not provided, use the default
        server_url = server_url or DEFAULT_SERVER_URL
        
        # Invoke the endpoint with parameters
        if params:
            print(f"Parameters: {json.dumps(params, indent=2)}")
            response = invoker.invoke_with_params(
                params=params,
                server_url=server_url
            )
        else:
            print("No parameters provided")
            response = invoker.invoke(server_url=server_url)
        
        # Print response
        print(f"Status code: {response.status_code}")
        
        # Try to print JSON response
        try:
            json_response = response.json()
            print(f"Response body: {json.dumps(json_response, indent=2)}")
        except:
            # If not JSON, print text (limit length to avoid huge output)
            print(f"Response body: {response.text[:500]}")
            if len(response.text) > 500:
                print("... (truncated)")
                
    except EndpointInvocationError as e:
        print(f"Error invoking endpoint: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

def main() -> None:
    """Run the example script."""
    try:
        # Fetch the OpenAPI spec
        spec = fetch_openapi_spec(OPENAPI_SPEC_URL)
        
        # Parse the spec
        parser = OpenAPIParser(spec)
        print(f"Successfully parsed OpenAPI spec with {len(parser.endpoints)} endpoints")
        
        # Print API information
        print_api_info(parser)
        
        # Find all operation IDs for reference
        print("\n=== Available Operation IDs ===")
        endpoints = parser.get_endpoints()
        operation_ids = [endpoint.operation_id for endpoint in endpoints if endpoint.operation_id]
        
        for op_id in sorted(operation_ids):
            endpoint = parser.get_endpoint_by_operation_id(op_id)
            print(f"- {op_id}: {endpoint.method} {endpoint.path}")
        
        # Run a specific example for listing categories
        try:
            run_example(
                parser,
                "list_categories_categories__get",
                description="Simple GET request to list categories"
            )
        except Exception as e:
            print(f"Error running list categories example: {e}")
        
        # Example 2: GET request with path parameter
        try:
            # Find a GET endpoint with path parameters
            get_with_path_endpoints = [
                e for e in endpoints 
                if e.method == "GET" and e.path_parameters_schema and e.operation_id
            ]
            
            if get_with_path_endpoints:
                path_param_endpoint = get_with_path_endpoints[0]
                
                # Build a sample parameter dictionary
                # This is a placeholder - actual values depend on your API
                params = {}
                if path_param_endpoint.path_parameters_schema and 'properties' in path_param_endpoint.path_parameters_schema:
                    for param in path_param_endpoint.path_parameters_schema['properties'].keys():
                        # Sample value - in a real implementation, use appropriate values
                        params[param] = "1" 
                
                run_example(
                    parser,
                    path_param_endpoint.operation_id,
                    params=params,
                    description=f"GET request with path parameter to {path_param_endpoint.path}"
                )
        except Exception as e:
            print(f"Error running path parameter example: {e}")
        
        # Example 3: POST request with request body
        try:
            # Find a POST endpoint with request body
            post_endpoints = [
                e for e in endpoints 
                if e.method == "POST" and e.request_body_required and e.operation_id
            ]
            
            if post_endpoints:
                post_endpoint = post_endpoints[0]
                
                # Build a sample request body
                # This is a placeholder - actual values depend on your API
                sample_body = {"name": "Test Item", "description": "Created via EndpointInvoker"}
                
                run_example(
                    parser,
                    post_endpoint.operation_id,
                    params=sample_body,
                    description=f"POST request with body to {post_endpoint.path}"
                )
        except Exception as e:
            print(f"Error running POST example: {e}")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 