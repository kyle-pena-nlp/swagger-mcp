# Swagger MCP

Automatically convert any Swagger/OpenAPI specification into an MCP server for use with Windsurf, Cursor, or other tools.

## Quickstart

Install from PyPI using pipx (recommended):
```bash
brew install pipx
pipx ensurepath
pipx install swagger-mcp
```

Alternatively, install from source:
```bash
git clone https://github.com/context-labs/swagger-mcp.git
cd swagger-mcp
pipx install -e . --force
```

Confirm the installation succeeded:
```bash
which swagger-mcp
which swagger-mcp-sample-server
```

Spin up a sample "products and product categories" API on your local machine on port 9000:
```bash
swagger-mcp-sample-server
```

Visit [http://localhost:9000/docs](http://localhost:9000/docs) to confirm the sample server is running.

We'll use this sample server to show how to configure an MCP server in Cursor or Windsurf.

### Cursor
Configure an MCP server in Cursor (Top Right Settings -> MCP -> Add New MCP Server -> Command Server):
```bash
swagger-mcp --spec http://localhost:9000/openapi.json --name product-mcp --server-url http://localhost:9000 --cursor
```

**Please Note**: *In Cursor, you may need to replace `swagger-mcp` with the full path to the `swagger-mcp` executable, which you can find by running `which swagger-mcp`.*

Also note the `--cursor` flag.

### Windsurf
Start an MCP Server in Windsurf (Windsurf Settings -> Settings -> Windsurf Settings -> Cascade -> Add Server -> Add Custom Server):
```json
{
  "mcpServers": {
    "product-mcp": {
      "command": "swagger-mcp",
      "args": [
        "--spec",
        "http://localhost:9000/openapi.json",
        "--name",
        "Product MCP",
        "--server-url",
        "http://localhost:9000"
      ]
    }
  }
}
```

That's it! Your API is now accessible through Windsurf, Cursor, or other tools as a set of AI-friendly tools.

Ask your AI agent to list, create, update, and delete products and categories.

![Demo](images/furniture.gif)

## Additional Options

1. You can pass a JSON file, YAML file, or URL for the `--spec` option:
    * /path/to/openapi.json
    * /path/to/openapi.yaml
    * https://api.example.com/openapi.json

2. Filter endpoints: Only include endpoints where the path matches the regex pattern:
```bash
swagger-mcp --spec http://localhost:9000/openapi.json --name product-mcp --server-url http://localhost:9000 --include-pattern category --cursor
```

3. Filter endpoints: Exclude endpoints where the path matches the regex pattern:
```bash
swagger-mcp --spec http://localhost:9000/openapi.json --name product-mcp --server-url http://localhost:9000 --exclude-pattern product --cursor
```

4. Authentication
```bash
swagger-mcp --spec http://localhost:9000/openapi.json --name product-mcp --server-url http://localhost:9000 --bearer-token your-token-here --cursor
```

5. Custom headers
```bash
swagger-mcp --spec http://localhost:9000/openapi.json --name product-mcp --server-url http://localhost:9000 --header X-Some-Header:your-value --header X-Some-Other-Header:your-value --cursor
```

6. Server URLs
If the OpenAPI spec already contains a specific server URL, you don't have to provide it as a command line argument.  But if you do, the command line `--server-url` overrides all endpoints.

7. Constant Values

If you want to always automatically provide a value for a parameter, you can use the `--const` option.
You can include as many `--const` options as you need.

```bash
swagger-mcp --spec http://localhost:9000/openapi.json --name product-mcp --server-url http://localhost:9000 --const parameter-name:your-value --const parameter-name2:your-value2 --cursor
```

## Supported Features
- All HTTP methods (GET, POST, PUT, DELETE, etc.)
- Path parameters
- Query parameters
- Textual Multi-Part Request Body Fields
- JSON Request body
- Bearer Token Authentication
- Custom Headers

## Limitations

- Cursor MCP integration is very early and limited.  It does not like double quotes in the command line arguments.  You probably still have to fully path to the command (`which swagger-mcp` to get the path).
- If you find a Swagger API specification that is not supported and you can't do a workaround with any of the available parameters, please file an issue. We will add support for it as needed / requested.
- We will not support automatic OAuth workflow execution.  If the OAuth workflow ends in a bearer token, you must provide this bearer token as a command line argument.
- We do not support Swagger/OpenAPI specifications spread across multiple files (i.e.; fragments, extensions, etc.).
- We do not support path variable substitution in the base server URLs (but we *do* support path variable in the endpoint paths).
- In general, we do not support all Swagger/OpenAPI features.  The Swagger/OpenAPI standard is vast, and support for more obscure features will be added as needed / requested.
- When Cursor re-implements support for MCP resources, you will have the option to specify some endpoints as resources instead of tools.

## Command Line Options

- `--spec` (required): Path or URL to your OpenAPI/Swagger specification
- `--name` (required): Name for your MCP server (shows up in Windsurf/Cursor)
- `--server-url`: Base URL for API calls (overrides servers defined in spec)
- `--bearer-token`: Bearer token for authenticated requests
- `--additional-headers`: JSON string of additional headers to include in all requests
- `--include-pattern`: Regex pattern to include only specific endpoint paths (e.g., "/api/v1/.*")
- `--exclude-pattern`: Regex pattern to exclude specific endpoint paths (e.g., "/internal/.*")
- `--header`: key:value pair of an extra header to include with all requests. Can be included multiple times.
- `--const`: key:value pair of a constant value to always use for a parameter, if the parameter is present on the endpoint (can be a path variable, query parameter, top-level request body property, or multi-part form data field). Can be included multiple times to specify multiple const values.
- `--cursor`: Run in cursor mode

## Authentication

For APIs requiring authentication:

```bash
# Using bearer token
swagger-mcp --spec http://localhost:9000/openapi.json --name product-mcp --bearer-token "your-token-here" --cursor

# Using custom headers
swagger-mcp --spec http://localhost:9000/openapi.json --name product-mcp --additional-headers '{"X-API-Key": "your-key"}' --cursor
```

## Other Fun Servers You Can Try:

```bash
# Countries API
swagger-mcp --spec https://restcountries.com/openapi/rest-countries-3.1.yml --name countries --server-url https://restcountries.com/ --const fields:name --cursor
```

## For Developers

### Installation

For development, install with development dependencies:
```bash
# Clone the repository
git clone https://github.com/context-labs/swagger-mcp.git
cd swagger-mcp

# Install in development mode with dev dependencies
pip install -e ".[dev]"
```

For a global installation on your local machine, use:
```bash
bash scripts/install-global.sh
```

### Unit Tests

```bash
pytest swagger_mcp/tests/unit -v
```

### Integration Tests

```bash
pytest swagger_mcp/tests/integration -v --capture=no --log-cli-level=INFO
```

### MCP Inspector (For interactive exploration of the MCP Server)

You'll have to do a global installation of your latest code first (`bash scripts/install-global.sh`), then you can run the inspector script.

You'll see the server type `STDIO` and the command `swagger-mcp` pre-filled.

```bash
bash scripts/inspector.sh
```

Click "Connect" and then "List Tools" to begin interacting with your MCP Server.

![MCP Inspector](images/mcp-inspector.png)

### Logging

To run the server with logs enabled, set the `REAL_LOGGER` environment variable to `true`:
```bash
REAL_LOGGER=true swagger-mcp --spec http://localhost:9000/openapi.json --name product-mcp --server-url http://localhost:9000
```
