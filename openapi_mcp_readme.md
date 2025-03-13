# OpenAPI MCP Server

This project provides a Model Context Protocol (MCP) server implementation that dynamically generates tools based on an OpenAPI specification. It uses the low-level MCP server specification with the `list_tools` and `call_tool` decorators.

## Features

- Dynamically generate MCP tools from OpenAPI specifications
- Automatically convert OpenAPI endpoints to MCP tools
- Support for authentication with bearer tokens
- Easy-to-use interface with minimal configuration

## Prerequisites

- Python 3.8 or higher
- The MCP Python SDK (`pip install mcp`)
- Required packages: `requests`, `pydantic`, `anyio`

## Installation

1. Clone this repository or copy the relevant files:
   - `openapi_mcp_server.py`
   - `openapi_parser.py`
   - `endpoint.py`
   - `simple_endpoint.py`
   - `endpoint_invoker.py`

2. Install the required dependencies:
   ```bash
   pip install mcp requests pydantic anyio
   ```

## Usage

### Basic Usage

```python
from openapi_mcp_server import run_server

# Start the server with a local OpenAPI spec
run_server(
    openapi_spec_path="path/to/openapi.json",
    server_name="My-API-Server",
    server_url="https://api.example.com",
    bearer_token="optional-token-for-authenticated-endpoints",
    host="0.0.0.0",
    port=8000
)
```

### Command Line Usage

You can also run the server directly from the command line:

```bash
python openapi_mcp_server.py path/to/openapi.json --name "My-API-Server" --url "https://api.example.com" --token "optional-bearer-token" --port 8000
```

### Using the PetStore Example

The repository includes an example that demonstrates using the OpenAPI MCP Server with the PetStore API:

```bash
python openapi_mcp_example.py
```

This will:
1. Download the PetStore OpenAPI spec from Swagger's website
2. Create an MCP server with tools based on the PetStore API endpoints
3. Start the server on localhost:8000

## How It Works

The OpenAPI MCP Server works as follows:

1. **Parsing the OpenAPI Spec**: The server uses `OpenAPIParser` to parse the OpenAPI specification and extract endpoint information.

2. **Converting Endpoints to SimpleEndpoints**: Each endpoint is converted to a `SimpleEndpoint` object, which combines path parameters, query parameters, and request body properties into a single parameter object.

3. **Generating Tool Definitions**: The `list_tools` handler creates MCP `Tool` objects based on the `SimpleEndpoint` objects, extracting parameter information from the combined schema.

4. **Handling Tool Calls**: The `call_tool` handler uses `EndpointInvoker` to invoke the corresponding API endpoint with the provided parameters, converting the response to an MCP tool result.

## Customization

You can customize the OpenAPI MCP Server by:

1. **Extending the `OpenAPIMCPServer` class**: Override methods like `_register_handlers` to customize tool generation or handling.

2. **Filtering endpoints**: Modify the logic in `list_tools` to filter or transform endpoints based on your requirements.

3. **Custom response handling**: Customize how API responses are converted to MCP tool results in the `call_tool` handler.

## Example: Custom Response Handling

```python
from openapi_mcp_server import OpenAPIMCPServer

class CustomOpenAPIMCPServer(OpenAPIMCPServer):
    def _register_handlers(self):
        # Register the list_tools handler as in the base class
        super()._register_handlers()
        
        # Override the call_tool handler
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[Any]:
            # Find the corresponding endpoint
            if name not in self.simple_endpoints:
                return [ToolResult(error=f"Tool not found: {name}")]
            
            endpoint = self.simple_endpoints[name]
            invoker = EndpointInvoker(endpoint)
            
            # Invoke the endpoint
            response = invoker.invoke_with_params(
                params=arguments,
                server_url=self.server_url,
                bearer_token=self.bearer_token
            )
            
            # Custom response handling
            if response.status_code >= 400:
                return [ToolResult(error=f"API error: {response.status_code} - {response.text}")]
            
            try:
                result = response.json()
                # Add additional metadata
                return [ToolResult(value={
                    "result": result,
                    "metadata": {
                        "status_code": response.status_code,
                        "headers": dict(response.headers),
                        "endpoint": f"{endpoint.method.upper()} {endpoint.path}"
                    }
                })]
            except ValueError:
                return [ToolResult(value=response.text)]
```

## Contributing

Contributions are welcome! Feel free to submit issues or pull requests. 