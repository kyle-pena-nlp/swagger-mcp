from swagger_mcp.endpoint import Endpoint
from swagger_mcp.openapi_parser import OpenAPIParser
from swagger_mcp.simple_endpoint import SimpleEndpoint, create_simple_endpoint
from swagger_mcp.server_arg_parser import parse_args
import re
import json
from typing import Dict
from swagger_mcp.openapi_mcp_server import OpenAPIMCPServer
import asyncio

def main():

    args, additional_headers, const_values = parse_args("Parse a dry run of an OpenAPI/Swagger specification")

    print("Dry run of OpenAPI/Swagger specification:")
    print(f"Spec: {args.spec}")
    print(f"Name: {args.name}")
    print(f"Server URL: {args.server_url}")
    print(f"Bearer Token: {args.bearer_token}")
    print(f"Additional Headers: {additional_headers}")
    print(f"Include Pattern: {args.include_pattern}")
    print(f"Exclude Pattern: {args.exclude_pattern}")
    print(f"Cursor Mode: {args.cursor}")
    print(f"Const Values: {const_values}")

    parser = OpenAPIParser(args.spec)
    endpoints = parser.endpoints

    simple_endpoints: Dict[str, SimpleEndpoint] = {}
    for endpoint in endpoints:
        simple_endpoint = create_simple_endpoint(endpoints[endpoint])
        simple_endpoints[simple_endpoint.operation_id] = simple_endpoint

    server = OpenAPIMCPServer(
        server_name=args.name,
        openapi_spec=args.spec,
        server_url=args.server_url,
        bearer_token=args.bearer_token,
        additional_headers=additional_headers,
        include_pattern=args.include_pattern,
        exclude_pattern=args.exclude_pattern,
        cursor_mode=args.cursor,
        const_values=const_values
    )

    handlers = server._register_handlers()
    list_tools = handlers["list_tools"]

    print("\nAvailable tools:")
    for tool in asyncio.run(list_tools()):
        print(f"- {tool.name}")
        print(f"  Description: {tool.description}")
        print(f"  Parameters: {json.dumps(tool.inputSchema, indent=2)}")
        print("\n")

    print(const_values)


if __name__ == "__main__":
    main()