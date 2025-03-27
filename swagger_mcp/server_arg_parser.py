from argparse import ArgumentParser
from typing import Dict
from swagger_mcp.logging import logger

def parse_args(description):

    parser = ArgumentParser(description=description)
    parser.add_argument("--spec", required=True, help="Path or URL to your OpenAPI/Swagger specification")
    parser.add_argument("--name", required=True, help="Name for your MCP server (shows up in Windsurf/Cursor)")
    parser.add_argument("--server-url", help="Base URL for API calls (overrides servers defined in spec)")
    parser.add_argument("--bearer-token", help="Bearer token for authenticated requests")
    parser.add_argument("--header", action='append', help="Additional headers in the format 'key:value'. Can be specified multiple times.", dest='headers')
    parser.add_argument("--include-pattern", help="Regex pattern to include only specific endpoint paths (e.g., '/api/v1/.*')")
    parser.add_argument("--exclude-pattern", help="Regex pattern to exclude specific endpoint paths (e.g., '/internal/.*')")
    parser.add_argument("--cursor", action='store_true', help="Run the server in Cursor mode to deal with Cursor quirks")
    parser.add_argument("--const", action='append', help="Optional dictionary of parameter names and their constant values (in JSON format)")
    
    args = parser.parse_args()
    
    # Process headers into a dictionary if provided
    additional_headers = {}
    if args.headers:
        for header in args.headers:
            try:
                key, value = header.split(':', 1)
                additional_headers[key.strip()] = value.strip()
            except ValueError:
                logger.warning(f"Ignoring invalid header format: {header}. Headers should be in 'key:value' format.")
    
    # Process const values into a dictionary if provided
    const_values = {}
    if args.const:
        for const_value in args.const:
            try:
                key, value = const_value.split(':', 1)
                const_values[key.strip()] = value.strip()
            except ValueError:
                logger.warning(f"Ignoring invalid const value format: {const_value}. Const values should be in 'key:value' format.")

    logger.info(f"Parsed arguments: {args}")
    logger.info(f"Additional headers: {additional_headers}")
    logger.info(f"Const values: {const_values}")

    return args, additional_headers, const_values

    