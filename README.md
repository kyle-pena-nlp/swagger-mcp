```
   _____                                    __  __  _____ _____  
  / ____|                                  |  \/  |/ ____|  __ \ 
 | (_____      ____ _  __ _  __ _  ___ _ __| \  / | |    | |__) |
  \___ \ \ /\ / / _` |/ _` |/ _` |/ _ \ '__| |\/| | |    |  ___/ 
  ____) \ V  V / (_| | (_| | (_| |  __/ |  | |  | | |____| |     
 |_____/ \_/\_/ \__,_|\__, |\__, |\___|_|  |_|  |_|\_____|_|     
                       __/ | __/ |                               
                      |___/ |___/                                
```
# Swagger MCP

Automatically convert any Swagger/OpenAPI specification into an MCP server for use with Windsurf, Cursor, and other AI tools. This package enables AI agents to interact with your API endpoints through natural language, making API integration seamless and intuitive.

## Quickstart

Install using pipx (recommended):
```bash
pipx install swagger-mcp
```

### Cursor
Configure an MCP server in Cursor (Top Right Settings -> MCP -> Add New MCP Server -> Command Server):
```bash
swagger-mcp --spec /path/to/openapi.yaml --name "My API Server" --server-url https://api.example.com
```

**Please Note**: *In Cursor, you may need to replace `swagger-mcp` with the full path to the `swagger-mcp` executable, which you can find by running `which swagger-mcp`.*

### Windsurf
Start an MCP Server in Windsurf (Windsurf Settings -> Settings -> Windsurf Settings -> Cascade -> Add Server -> Add Custom Server):
```json
    "product-mcp": {
      "command": "swagger-mcp",
      "args": [
        "--spec",
        "/path/to/openapi.yaml",
        "--name",
        "My API Server",
        "--server-url",
        "http://localhost:9000"
      ] 
    }
``` 

### Claude
Edit `~/Library/Application\ Support/Claude/claude_desktop_config.json`:

```json
{
    "mcpServers": {
        "my-api-server": {
            "command": "swagger-mcp",
            "args": [
                "--spec",
                "/path/to/openapi.yaml",
                "--name",
                "My API Server",
                "--server-url",
                "http://localhost:9000"
            ]
        }
    }
}
```

That's it! Your API is now accessible through Windsurf, Cursor, or Claude as a set of AI-friendly tools.

## Additional Options

1. You can pass a JSON file, YAML file, or URL for the `--spec` option:

i.e.;
* /path/to/openapi.json
* /path/to/openapi.yaml
* https://api.example.com/openapi.json

2. Filter endpoints: Only include endpoints by path:
This will regex search the endpoint paths and only include those that match the pattern.
```bash
swagger-mcp --spec /path/to/openapi.yaml --name "My API Server" --server-url https://api.example.com --include-pattern "apples|oranges"
```

3. Filter endpoints: Exclude endpoints by path:
This will exclude any endpoints that match the regex pattern.
```bash
swagger-mcp --spec /path/to/openapi.yaml --name "My API Server" --server-url https://api.example.com --exclude-pattern "grapes|bananas"
```

4. Authentication
```bash
swagger-mcp --spec /path/to/openapi.yaml --name "My API Server" --server-url https://api.example.com --bearer-token "your-token-here"
```

5. Custom headers
```bash
swagger-mcp --spec /path/to/openapi.yaml --name "My API Server" --server-url https://api.example.com --additional-headers '{"X-API-Key": "your-key"}'
```

6. Server URLs
If the OpenAPI spec already contains a specific server URL, you don't have to provide it as a command line argument.  The command line argument overrides all endpoints.

## Supported Features
- All HTTP methods (GET, POST, PUT, DELETE, etc.)
- Path parameters
- Query parameters
- Textual Multi-Part Request Body Fields
- JSON Request body
- Bearer Token Authentication

## Limitations

- If you find a Swagger API specification that is not supported, please file an issue. We will add support for it as needed / requested.
- We do not support Swagger/OpenAPI specifications spread across multiple files (i.e.; fragments, extensions, etc.).
- We do not support path variable substitution in the base server URLs (but we *do* support path variable in the endpoint paths).
- We do not support automatic OAuth workflow execution.  If the OAuth workflow ends in a bearer token, you must provide this bearer token as a command line argument.
- In general, we do not support all Swagger/OpenAPI features.  The Swagger/OpenAPI standard is vast, and support for more obscure features will be added as needed / requested.
- All endpoints are exposed as tools.  When Cursor re-implements support for MCP resources, Swagger MCP will support resources as well.

## Command Line Options

- `--spec` (required): Path or URL to your OpenAPI/Swagger specification
- `--name` (required): Name for your MCP server (shows up in Windsurf/Cursor)
- `--server-url`: Base URL for API calls (overrides servers defined in spec)
- `--bearer-token`: Bearer token for authenticated requests
- `--additional-headers`: JSON string of additional headers to include in all requests
- `--include-pattern`: Regex pattern to include only specific endpoint paths (e.g., "/api/v1/.*")
- `--exclude-pattern`: Regex pattern to exclude specific endpoint paths (e.g., "/internal/.*")

## Authentication

For APIs requiring authentication:

```bash
# Using bearer token
swagger-mcp --spec api.yaml --name "Secured API" --bearer-token "your-token-here"

# Using custom headers
swagger-mcp --spec api.yaml --name "Custom Auth API" --additional-headers '{"X-API-Key": "your-key"}'
```

## For Developers

### Installation

For a global installation on your local machine, use:
```bash
bash scripts/install-global.sh
```

### Unit Tests

```bash
bash scripts/tests.sh
```

### Integration Tests

```bash
bash scripts/integration-tests.sh
```

### MCP Inspector (For interactive exploration of the MCP Server)

You'll have to do a global installation of your latest code first (`bash scripts/install-global.sh`), then you can run the inspector script.

You'll see the server type `STDIO` and the command `swagger-mcp` pre-filled.

```bash
bash scripts/inspector.sh
```

Click "Connect" and then "List Tools" to begin interacting with your MCP Server.

![MCP Inspector](images/mcp-inspector.png)

