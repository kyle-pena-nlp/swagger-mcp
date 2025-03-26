"""
Example usage of the EndpointInvoker class.
"""
from openapi_parser import OpenAPIParser
from endpoint_invoker import EndpointInvoker, EndpointInvocationError


def main():
    """Demo using the EndpointInvoker with a real API."""
    # Parse an OpenAPI spec
    spec = {
        "openapi": "3.0.0",
        "info": {
            "title": "Example API",
            "version": "1.0.0"
        },
        "servers": [
            {"url": "https://jsonplaceholder.typicode.com"}
        ],
        "paths": {
            "/posts": {
                "get": {
                    "operationId": "getPosts",
                    "summary": "Get all posts",
                    "parameters": [
                        {
                            "name": "userId",
                            "in": "query",
                            "schema": {"type": "integer"}
                        }
                    ]
                },
                "post": {
                    "operationId": "createPost",
                    "summary": "Create a new post",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "title": {"type": "string"},
                                        "body": {"type": "string"},
                                        "userId": {"type": "integer"}
                                    },
                                    "required": ["title", "body", "userId"]
                                }
                            }
                        }
                    }
                }
            },
            "/posts/{id}": {
                "get": {
                    "operationId": "getPostById",
                    "summary": "Get a post by ID",
                    "parameters": [
                        {
                            "name": "id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "integer"}
                        }
                    ]
                }
            }
        }
    }
    
    parser = OpenAPIParser(spec)
    
    # Example 1: Get all posts
    print("\n--- Example 1: Get all posts ---")
    get_posts_endpoint = parser.get_endpoint_by_operation_id("getPosts")
    invoker = EndpointInvoker(get_posts_endpoint)
    
    try:
        # Make the request
        response = invoker.invoke()
        
        # Print results
        print(f"Status code: {response.status_code}")
        print(f"Got {len(response.json())} posts")
    except EndpointInvocationError as e:
        print(f"Error: {e}")
    
    # Example 2: Get posts for a specific user
    print("\n--- Example 2: Get posts for user 1 ---")
    try:
        # Make the request with query parameters
        response = invoker.invoke(query_params={"userId": 1})
        
        # Print results
        print(f"Status code: {response.status_code}")
        if response.status_code == 200:
            posts = response.json()
            print(f"Got {len(posts)} posts for user 1")
            for i, post in enumerate(posts[:3]):  # Show first 3
                print(f"Post {i+1}: {post['title'][:40]}...")
            if len(posts) > 3:
                print(f"... and {len(posts) - 3} more")
    except EndpointInvocationError as e:
        print(f"Error: {e}")
    
    # Example 3: Get a post by ID
    print("\n--- Example 3: Get post by ID ---")
    get_post_endpoint = parser.get_endpoint_by_operation_id("getPostById")
    invoker = EndpointInvoker(get_post_endpoint)
    
    try:
        # Make the request with path parameters
        response = invoker.invoke(path_params={"id": 1})
        
        # Print results
        print(f"Status code: {response.status_code}")
        if response.status_code == 200:
            post = response.json()
            print(f"Post ID: {post['id']}")
            print(f"Title: {post['title']}")
            print(f"Body: {post['body'][:100]}...")
    except EndpointInvocationError as e:
        print(f"Error: {e}")
    
    # Example 4: Create a new post
    print("\n--- Example 4: Create a new post ---")
    create_post_endpoint = parser.get_endpoint_by_operation_id("createPost")
    invoker = EndpointInvoker(create_post_endpoint)
    
    try:
        # Create a post
        new_post = {
            "title": "Testing EndpointInvoker",
            "body": "This post was created using the EndpointInvoker class",
            "userId": 1
        }
        
        # Make the request with a request body
        response = invoker.invoke(request_body=new_post)
        
        # Print results
        print(f"Status code: {response.status_code}")
        if response.status_code in (200, 201):
            created_post = response.json()
            print(f"Created post ID: {created_post['id']}")
            print(f"Title: {created_post['title']}")
    except EndpointInvocationError as e:
        print(f"Error: {e}")
    
    # Example 5: This will fail (missing path parameter)
    print("\n--- Example 5: Error handling (missing parameter) ---")
    try:
        # Try to make a request without required path parameter
        invoker = EndpointInvoker(get_post_endpoint)
        response = invoker.invoke()  # Missing 'id' path parameter
    except EndpointInvocationError as e:
        print(f"Expected error caught: {e}")


if __name__ == "__main__":
    main() 