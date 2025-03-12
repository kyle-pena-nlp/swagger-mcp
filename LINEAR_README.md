# Linear API Service Layer

This project provides a service layer for interacting with the Linear API, along with MCP tools for integration with the MCP framework.

## Files

- `linear_service.py` - Contains the service layer with all the Linear API functionality
- `linear_mcp.py` - Contains the MCP tools that use the service layer
- `linear.py` - The original file, now updated to use the service layer
- `linear_service_example.py` - An example script that shows how to use the service layer directly

## Architecture

The code has been refactored to separate the Linear API functionality from the MCP tools. This allows you to:

1. Use the Linear API service layer directly in your own scripts without the MCP framework
2. Maintain the MCP tools separately from the API implementation
3. Reuse the same service layer code in multiple places

## Using the Service Layer

### In MCP Tools

The MCP tools in `linear_mcp.py` and `linear.py` now use the service layer:

```python
from linear_service import linear_service

@mcp.tool()
async def search_issues(query_string: str) -> List[LinearIssue]:
    """Search for Linear issues based on a query string"""
    return await linear_service.search_issues(query_string)
```

### In Your Own Scripts

You can use the service layer directly in your own scripts:

```python
import asyncio
from linear_service import linear_service

async def main():
    # Get all teams
    teams = await linear_service.get_teams()
    print(f"Found {len(teams)} teams:")
    for team in teams:
        print(f"- {team['name']} (ID: {team['id']})")
    
    # Search for issues
    issues = await linear_service.search_issues("in:backlog")
    print(f"Found {len(issues)} issues in backlog")

if __name__ == "__main__":
    asyncio.run(main())
```

### Creating Your Own Service Instance

You can also create your own service instance with a custom client:

```python
from linear_service import LinearClient, LinearService

# Create a custom client with your API key
custom_client = LinearClient(api_key="your-api-key")

# Create a custom service with the client
custom_service = LinearService(client=custom_client)

# Use the custom service
teams = await custom_service.get_teams()
```

## Logging

The service layer includes comprehensive logging to help debug issues and monitor API interactions. By default, logs are written to both the console and a file named `linear_api.log`.

### Default Logging Behavior

- When `linear.py` or `linear_mcp.py` is started, logs are automatically written to `linear_api.log`
- The default log level is INFO
- You can customize the default log file by setting the `LINEAR_LOG_FILE` environment variable
- You can customize the default log level by setting the `LINEAR_LOG_LEVEL` environment variable
- You can disable automatic logging by setting `LINEAR_AUTO_LOG=false`

### Configuring Logging Manually

You can also configure the logging level and output file manually:

```python
import logging
from linear_service import configure_logging

# Set to DEBUG level to see more detailed logs
configure_logging(level=logging.DEBUG, log_file="custom_log_file.log")
```

### Log Levels

- **DEBUG**: Detailed information, including full queries and responses
- **INFO**: General information about operations (default)
- **WARNING**: Warning messages
- **ERROR**: Error messages
- **CRITICAL**: Critical errors

### What Gets Logged

The service logs the following information:

1. **Requests**: GraphQL queries and variables
2. **Responses**: Status codes and data keys
3. **Errors**: API errors, GraphQL errors, and exceptions
4. **Operations**: Information about each operation (e.g., "Getting all teams", "Creating new issue")

### Example Log Output

```
2023-07-15 10:30:45,123 - linear_service - INFO - Logging level set to: DEBUG
2023-07-15 10:30:45,124 - linear_service.service - INFO - Getting all teams
2023-07-15 10:30:45,125 - linear_service.client - INFO - Executing GraphQL query with variables: {}
2023-07-15 10:30:45,126 - linear_service.client - DEBUG - Full query: query { teams { nodes { id name key } } }
2023-07-15 10:30:46,234 - linear_service.client - INFO - Response status: 200
2023-07-15 10:30:46,235 - linear_service.client - INFO - Successful response with data keys: ['teams']
2023-07-15 10:30:46,236 - linear_service.service - INFO - Retrieved 5 teams
```

## Environment Variables

The service uses the following environment variables:

- `LINEAR_API_KEY`: Your Linear API key (required)
- `LINEAR_LOG_FILE`: Path to the log file (default: `linear_api.log`)
- `LINEAR_LOG_LEVEL`: Log level to use (default: `INFO`)
- `LINEAR_AUTO_LOG`: Whether to automatically configure logging (default: `true`)

## Benefits of This Refactoring

1. **Separation of Concerns**: The API functionality is now separate from the MCP tools
2. **Reusability**: The service layer can be used in multiple places
3. **Testability**: The service layer can be tested independently of the MCP tools
4. **Maintainability**: Changes to the API implementation don't require changes to the MCP tools
5. **Flexibility**: You can use the service layer without the MCP framework
6. **Observability**: Comprehensive logging helps debug issues and monitor API interactions 