#!/usr/bin/env python3
"""
Simple test script to verify the Linear MCP server is working correctly.
"""

import asyncio
from mcp.client import MCPClient

async def main():
    # Connect to the MCP server
    client = MCPClient("http://localhost:8000")
    
    # Test listing tools
    print("Listing available tools...")
    tools = await client.list_tools()
    print(f"Found {len(tools)} tools:")
    for tool in tools:
        print(f"- {tool.name}: {tool.description}")
    
    # Test listing resources
    print("\nListing available resources...")
    resources = await client.list_resources()
    print(f"Found {len(resources)} resources:")
    for resource in resources:
        print(f"- {resource.uri}: {resource.description}")
    
    # Test getting teams
    print("\nTesting get_teams...")
    try:
        teams = await client.tool("get_teams")
        print(f"Success! Found {len(teams)} teams.")
        if teams:
            print(f"First team: {teams[0]['name']} (ID: {teams[0]['id']})")
    except Exception as e:
        print(f"Exception: {e}")
    
    # Test getting issues
    print("\nTesting get_issues...")
    try:
        issues = await client.resource("linear://issues")
        print(f"Success! Found {len(issues)} issues.")
        if issues:
            print(f"First issue: {issues[0].title} (ID: {issues[0].id})")
    except Exception as e:
        print(f"Exception: {e}")
    
    print("\nTests completed.")

if __name__ == "__main__":
    asyncio.run(main()) 