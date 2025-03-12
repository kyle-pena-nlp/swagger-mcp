#!/usr/bin/env python3
"""
Example script demonstrating how to use the Linear MCP server.
"""

import asyncio
import json
from mcp.client import MCPClient

async def main():
    # Connect to the MCP server
    client = MCPClient("http://localhost:8000")
    
    # Get all teams
    print("Getting all teams...")
    teams = await client.tool("get_teams")
    print(f"Found {len(teams)} teams:")
    for team in teams:
        print(f"- {team['name']} (ID: {team['id']}, Key: {team['key']})")
    
    if not teams:
        print("No teams found. Exiting.")
        return
    
    # Use the first team for our examples
    team_id = teams[0]["id"]
    team_name = teams[0]["name"]
    print(f"\nUsing team: {team_name} (ID: {team_id})")
    
    # Get team members
    print("\nGetting team members...")
    members = await client.tool("get_team_members", {"team_id": team_id})
    print(f"Found {len(members)} members in team {team_name}:")
    for member in members:
        print(f"- {member['name']} (ID: {member['id']})")
    
    # Create a new issue
    print("\nCreating a new issue...")
    new_issue = await client.tool("create_issue", {
        "title": "Test issue from MCP",
        "description": "This is a test issue created using the Linear MCP server.",
        "team_id": team_id
    })
    print(f"Created issue: {new_issue.title} (ID: {new_issue.id})")
    
    # Update the issue description
    print("\nUpdating issue description...")
    updated_issue = await client.tool("update_issue_description", {
        "issue_id": new_issue.id,
        "description": "This is an updated description for the test issue."
    })
    print(f"Updated issue description: {updated_issue.description}")
    
    # Add a comment to the issue
    print("\nAdding a comment to the issue...")
    comment = await client.tool("add_comment", {
        "issue_id": new_issue.id,
        "body": "This is a test comment added using the Linear MCP server."
    })
    print(f"Added comment: {comment.body} (ID: {comment.id})")
    
    # Get all issues
    print("\nGetting all issues...")
    issues = await client.resource("linear://issues")
    print(f"Found {len(issues)} issues:")
    for issue in issues:
        print(f"- {issue.title} (ID: {issue.id})")
    
    # Get the specific issue we created
    print(f"\nGetting specific issue (ID: {new_issue.id})...")
    issue = await client.resource(f"linear://issue/{new_issue.id}")
    print(f"Retrieved issue: {issue.title}")
    print(f"Description: {issue.description}")
    
    # Get comments for the issue
    print(f"\nGetting comments for issue (ID: {new_issue.id})...")
    comments = await client.resource(f"linear://issue/{new_issue.id}/comments")
    print(f"Found {len(comments)} comments:")
    for comment in comments:
        print(f"- {comment.body} (ID: {comment.id})")
    
    # Search for issues
    print("\nSearching for issues...")
    search_results = await client.tool("search_issues", {"query_string": "test"})
    print(f"Found {len(search_results)} issues matching 'test':")
    for issue in search_results:
        print(f"- {issue.title} (ID: {issue.id})")
    
    print("\nExample completed successfully!")

if __name__ == "__main__":
    asyncio.run(main()) 