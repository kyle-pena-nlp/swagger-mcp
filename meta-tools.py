import os
import logging
from mcp.server.fastmcp import FastMCP
from linear_service import linear_service, LinearIssue, LinearComment, configure_logging
from typing import Dict, List, Any, Optional

# Configure logging to write to linear_api.log by default
configure_logging(level=logging.INFO, log_file="linear_api.log")

# Initialize MCP server
mcp = FastMCP("Linear")

# MCP resources and tools
@mcp.tool()
async def get_issues() -> List[LinearIssue]:
    """Get all Linear issues"""
    return await linear_service.get_issues()

@mcp.tool()
async def get_issue(issue_id: str) -> LinearIssue:
    """Get a specific Linear issue by ID"""
    return await linear_service.get_issue(issue_id)

@mcp.tool()
async def get_issue_comments(issue_id: str) -> List[LinearComment]:
    """Get comments for a specific Linear issue"""
    return await linear_service.get_issue_comments(issue_id)

@mcp.tool()
async def search_issues(query_string : str) -> List[LinearIssue]:
    """Search for Linear issues based on a query string"""
    return await linear_service.search_issues(query_string, query_string)

@mcp.tool()
async def create_issue(title: str, description: str, team_id: str) -> LinearIssue:
    """Create a new Linear issue"""
    return await linear_service.create_issue(title, description, team_id)

@mcp.tool()
async def update_issue_description(issue_id: str, description: str) -> LinearIssue:
    """Update the description of a Linear issue"""
    return await linear_service.update_issue_description(issue_id, description)

@mcp.tool()
async def add_comment(issue_id: str, body: str) -> LinearComment:
    """Add a comment to a Linear issue"""
    return await linear_service.add_comment(issue_id, body)

@mcp.tool()
async def assign_issue(issue_id: str, assignee_id: str) -> LinearIssue:
    """Assign a Linear issue to a user"""
    return await linear_service.assign_issue(issue_id, assignee_id)

@mcp.tool()
async def change_issue_state(issue_id: str, state_id: str) -> LinearIssue:
    """Change the state of a Linear issue"""
    return await linear_service.change_issue_state(issue_id, state_id)

@mcp.tool()
async def get_teams() -> List[Dict[str, Any]]:
    """Get all teams in Linear"""
    return await linear_service.get_teams()

@mcp.tool()
async def get_team_members(team_id: str) -> List[Dict[str, Any]]:
    """Get all members of a specific team"""
    return await linear_service.get_team_members(team_id)

@mcp.prompt()
def linear_issue_prompt(issue_id: str) -> str:
    """Create a prompt to analyze a Linear issue"""
    return f"""
    Please analyze the Linear issue with ID {issue_id}. 
    Consider the following aspects:
    - Is the issue description clear and complete?
    - Are there any missing details that should be added?
    - What would be the best approach to solve this issue?
    - Are there any potential blockers or dependencies?
    """

if __name__ == "__main__":
    # Log that the server is starting
    logging.getLogger("linear_service").info("Starting Linear MCP server")
    
    # Run the server using SSE transport
    mcp.run(transport='stdio') 