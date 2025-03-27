# Swagger MCP

Automatically convert a Swagger/OpenAPI specification into an MCP server for use with Windsurf, Cursor, or other tools.

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

We'll use this sample server to show how to configure an MCP server in Windsurf.

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

### Cursor (>=v0.46)

Support for Cursor is still in beta as Cursor MCP integration matures.  Windsurf is currently the preferred experience.

```json
{
  "mcpServers": {
    "product mcp": {
      "command": "swagger-mcp",
      "args": [
        "--spec",
        "http://localhost:9000/openapi.json",
        "--name",
        "Product MCP",
        "--server-url",
        "http://localhost:9000",
        "--cursor"
      ]
    }
  }
}
```

**Please Note**: *In Cursor, you may need to replace the command `swagger-mcp` with the full path to the `swagger-mcp` executable, which you can find by running `which swagger-mcp`.*

Also note the `--cursor` flag. This is for Cursor compatibility.

Again, MCP integration is currently in beta in Cursor as of v0.46 and may not work as expected.  Currently, Windsurf is a better experience in general.




See other examples in [Other Fun Servers](#other-fun-servers).

## Additional Options

1. You can pass a JSON file, YAML file, or URL for the `--spec` option:
    * /path/to/openapi.json
    * /path/to/openapi.yaml
    * https://api.example.com/openapi.json

2. Filter endpoints: Only include endpoints where the path matches the regex pattern:
```json
{
  "mcpServers": {
    "product mcp": {
      "command": "swagger-mcp",
      "args": [
        "--spec",
        "http://localhost:9000/openapi.json",
        "--name",
        "product-mcp",
        "--server-url",
        "http://localhost:9000",
        "--include-pattern",
        "category"
      ]
    }
  }
}
```

3. Filter endpoints: Exclude endpoints where the path matches the regex pattern:
```json
{
  "mcpServers": {
    "product mcp": {
      "command": "swagger-mcp",
      "args": [
        "--spec",
        "http://localhost:9000/openapi.json",
        "--name",
        "product-mcp",
        "--server-url",
        "http://localhost:9000",
        "--exclude-pattern",
        "product"
      ]
    }
  }
}
```

4. Authentication
```json
{
  "mcpServers": {
    "product mcp": {
      "command": "swagger-mcp",
      "args": [
        "--spec",
        "http://localhost:9000/openapi.json",
        "--name",
        "product-mcp",
        "--server-url",
        "http://localhost:9000",
        "--bearer-token",
        "your-token-here",
      ]
    }
  }
}
```

5. Custom headers
```json
{
  "mcpServers": {
    "product mcp": {
      "command": "swagger-mcp",
      "args": [
        "--spec",
        "http://localhost:9000/openapi.json",
        "--name",
        "product-mcp",
        "--server-url",
        "http://localhost:9000",
        "--header",
        "X-Some-Header:your-value",
        "--header",
        "X-Some-Other-Header:your-value",
      ]
    }
  }
}
```

6. Server URLs
If the OpenAPI spec already contains a specific server URL, you don't have to provide it as a command line argument.  But if you do, the command line `--server-url` overrides all endpoints.

7. Constant Values

If you want to always automatically provide a value for a parameter, you can use the `--const` option.
You can include as many `--const` options as you need.
```json
{
  "mcpServers": {
    "product mcp": {
      "command": "swagger-mcp",
      "args": [
        "--spec",
        "http://localhost:9000/openapi.json",
        "--name",
        "product-mcp",
        "--server-url",
        "http://localhost:9000",
        "--const",
        "parameter-name:your-value",
        "--const",
        "parameter-name2:your-value2"
      ]
    }
  }
}
```

## Supported Features
- All HTTP methods (GET, POST, PUT, DELETE, etc.)
- Path parameters
- Query parameters
- Textual Multi-Part Request Body Fields
- JSON Request body
- Bearer Token Authentication
- Custom Headers
- Constant Values

## Limitations

- Endpoints that have recursive schema references are not yet supported.
- Cursor MCP integration is very early and frankly broken.  (It does not like double quotes in the command line arguments.  It does not like dashes in tool names.  Sometimes, parameter descriptions cause silent errors).  I try to address some of these with cursor mode `--cursor`, but it's still not great.  Until Cursor MCP support gets better, you'll be happier with Windsurf.
- We will never support automatic OAuth workflow execution.  If the OAuth workflow creates a bearer token, you must obtain this token yourself by performing OAuth out-of-band, and provide this bearer token as a command line argument.
- We do not support Swagger/OpenAPI specifications spread across multiple files (i.e.; fragments, extensions, etc.).
- We do not support path variable substitution in server URLs (but we *do* support path variables in endpoints).
- In general, we do not support all Swagger/OpenAPI features.  The Swagger/OpenAPI standard is vast, and support for more obscure features will be added as needed / requested.

## Help

- If you have trouble spinning up a server, try the following command: `REAL_LOGGER=true swagger-mcp-parse-dry-run ...` and provide all the same arguments you would use to spin up a server. Include this information in any issue you file.
- If you find a Swagger API specification that is not supported and you can't use any of the available parameters for a workaround, please file an issue. We will add support for it as needed / requested.


## Roadmap

- Support recursive schema references
- Support path variable substitution in server URLs
- Revamp the `--cursor` mode to better work around Cursor's limitations
- Provide support for MCP resources

## Command Line Options

- `--spec` (required): Path or URL to your OpenAPI/Swagger specification
- `--name` (required): Name for your MCP server (shows up in Windsurf/Cursor)
- `--server-url`: Base URL for API calls (overrides servers defined in spec)
- `--bearer-token`: Bearer token for authenticated requests
- `--additional-headers`: JSON string of additional headers to include in all requests
- `--include-pattern`: Regex pattern to include only specific endpoint paths (e.g., "/api/v1/.*")
- `--exclude-pattern`: Regex pattern to exclude specific endpoint paths (e.g., "/internal/.*")
- `--header`: key:value pair of an extra header to include with all requests. Can be included multiple times to specify multiple headers.
- `--const`: key:value pair of a constant value to always use for a parameter, if the parameter is present on the endpoint (can be a path variable, query parameter, top-level request body property, or multi-part non-file form data field). Can be included multiple times to specify multiple const values.
- `--cursor`: Run in cursor mode

## Authentication

For APIs requiring authentication:
```json
{
  "mcpServers": {
    "product mcp": {
      "command": "swagger-mcp",
      "args": [
        "--spec",
        "http://localhost:9000/openapi.json",
        "--name",
        "product-mcp",
        "--server-url",
        "http://localhost:9000",
        "--bearer-token",
        "your-token-here",
        "--cursor"
      ]
    }
  }
}
```

```json
{
  "mcpServers": {
    "product mcp": {
      "command": "swagger-mcp",
      "args": [
        "--spec",
        "http://localhost:9000/openapi.json",
        "--name",
        "product-mcp",
        "--server-url",
        "http://localhost:9000",
        "--header",
        "X-API-Key:your-key",
        "--cursor"
      ]
    }
  }
}
```

## Other Fun Servers

### Countries

```json
{
  "mcpServers": {
    "countries": {
      "command": "swagger-mcp",
      "args": [
        "--spec",
        "https://restcountries.com/openapi/rest-countries-3.1.yml",
        "--name",
        "countries",
        "--server-url",
        "https://restcountries.com/",
        "--const",
        "fields:name",
        "--cursor"
      ]
    }
  }
}
```

## PokeAPI

```json
{
  "mcpServers": {
    "pokeapi": {
      "command": "swagger-mcp",
      "args": [
        "--spec",
        "https://raw.githubusercontent.com/PokeAPI/pokeapi/refs/heads/master/openapi.yml",
        "--name",
        "pokeapi",
        "--include-pattern",
        "pokemon"
      ]
    }
  }
}
```

## TODO: Slack

## TODO: Petstore


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
