# Linear MCP Server

This is an MCP (Model Control Protocol) server that integrates with the Linear API, allowing you to manage Linear issues, comments, and more through a standardized interface.

## Features

- Get all issues or a specific issue
- Search for issues
- Create new issues
- Update issue descriptions
- Add comments to issues
- Assign issues to team members
- Change issue states
- Get teams and team members

## Setup

1. Clone this repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Create a `.env` file with your Linear API key:
   ```
   LINEAR_API_KEY=your_linear_api_key
   ```
   You can get your Linear API key from the Linear app under Settings > API > Personal API Keys.

## Usage

### Starting the server

```bash
python linear_server.py
```

This will start the MCP server on `http://0.0.0.0:8000`.

### Available Resources

- `linear://issues` - Get all issues
- `linear://issue/{issue_id}` - Get a specific issue
- `linear://issue/{issue_id}/comments` - Get comments for a specific issue

### Available Tools

- `search_issues(query_string)` - Search for issues
- `create_issue(title, description, team_id)` - Create a new issue
- `update_issue_description(issue_id, description)` - Update an issue description
- `add_comment(issue_id, body)` - Add a comment to an issue
- `assign_issue(issue_id, assignee_id)` - Assign an issue to a user
- `change_issue_state(issue_id, state_id)` - Change the state of an issue
- `get_teams()` - Get all teams
- `get_team_members(team_id)` - Get members of a specific team

### Available Prompts

- `linear_issue_prompt(issue_id)` - Create a prompt to analyze a Linear issue

## Example Usage with Python

```python
import httpx

# Get all issues
response = httpx.get("http://localhost:8000/resource/linear://issues")
issues = response.json()

# Create a new issue
response = httpx.post(
    "http://localhost:8000/tool/create_issue",
    json={
        "title": "New issue",
        "description": "This is a new issue created via MCP",
        "team_id": "TEAM_ID"
    }
)
new_issue = response.json()

# Add a comment to an issue
response = httpx.post(
    "http://localhost:8000/tool/add_comment",
    json={
        "issue_id": "ISSUE_ID",
        "body": "This is a comment added via MCP"
    }
)
comment = response.json()
```

## Example Usage with MCP Client

```python
from mcp.client import MCPClient

client = MCPClient("http://localhost:8000")

# Get all issues
issues = client.resource("linear://issues")

# Create a new issue
new_issue = client.tool("create_issue", {
    "title": "New issue",
    "description": "This is a new issue created via MCP",
    "team_id": "TEAM_ID"
})

# Add a comment to an issue
comment = client.tool("add_comment", {
    "issue_id": "ISSUE_ID",
    "body": "This is a comment added via MCP"
})
```

## License

MIT
