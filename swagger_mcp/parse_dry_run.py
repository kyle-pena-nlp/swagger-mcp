from swagger_mcp.endpoint import Endpoint
from swagger_mcp.openapi_parser import OpenAPIParser
from swagger_mcp.simple_endpoint import SimpleEndpoint, create_simple_endpoint
from swagger_mcp.server_arg_parser import parse_args


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
    if args.server_url:
        endpoints = [endpoint for endpoint in endpoints if endpoint.server_url == args.server_url]
    if args.include_pattern:
        endpoints = [endpoint for endpoint in endpoints if re.match(args.include_pattern, endpoint.path)]
    if args.exclude_pattern:
        endpoints = [endpoint for endpoint in endpoints if not re.match(args.exclude_pattern, endpoint.path)]
    print(f"Endpoints: {json.dumps([endpoint.to_dict() for endpoint in endpoints], indent=4)}")

    simple_endpoints: Dict[str, SimpleEndpoint] = {}
    for endpoint in endpoints:
        simple_endpoint = create_simple_endpoint(endpoint)
        simple_endpoints[simple_endpoint.operation_id] = simple_endpoint


if __name__ == "__main__":
    main()