#!/usr/bin/env python3
"""
Test script for the openapi_mcp_server with Slack's OpenAPI and OAuth credentials.

This script sets up an MCP server with the Slack OpenAPI spec and appropriate OAuth credentials.
It demonstrates how to pass client_id and client_secret to the server for OAuth-based endpoints.

Usage: 
    python test_slack_oauth_server.py --client-id YOUR_CLIENT_ID --client-secret YOUR_CLIENT_SECRET
"""

import sys
import os
import logging
from openapi_mcp_server import run_server

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Slack OpenAPI spec URL
SLACK_OPENAPI_URL = "https://raw.githubusercontent.com/slackapi/slack-api-specs/refs/heads/master/web-api/slack_web_openapi_v2_without_examples.json"

def main():
    """Run the MCP server with Slack OpenAPI and OAuth credentials."""
    
    # Check if we have the spec file locally, otherwise use the remote URL
    spec_path = "slack_openapi.json"
    if os.path.exists(spec_path):
        logger.info(f"Using local Slack OpenAPI spec: {spec_path}")
        spec = spec_path
    else:
        logger.info(f"Using remote Slack OpenAPI spec URL")
        spec = SLACK_OPENAPI_URL
    
    # Default values
    server_name = "Slack-API-MCP-Server"
    server_url = "https://slack.com/api"
    
    # Exclude patterns to filter out endpoints that we don't want to expose
    # You can adjust this based on what you want to test
    exclude_pattern = "(admin)|(workflows)|(audit)|(files)|(event)|(call)"
    
    # Parse command line arguments for client_id and client_secret
    client_id = None
    client_secret = None
    
    for i, arg in enumerate(sys.argv[1:], 1):
        if arg == "--client-id" and i < len(sys.argv):
            client_id = sys.argv[i + 1]
        elif arg == "--client-secret" and i < len(sys.argv):
            client_secret = sys.argv[i + 1]
    
    if not client_id or not client_secret:
        logger.warning("OAuth client_id and client_secret are not provided.")
        logger.warning("OAuth-based endpoints will not work without these credentials.")
        logger.warning("Usage: python test_slack_oauth_server.py --client-id YOUR_CLIENT_ID --client-secret YOUR_CLIENT_SECRET")
    else:
        logger.info("OAuth credentials provided, OAuth-based endpoints should work correctly.")
    
    # Run the server with the Slack spec and OAuth credentials
    run_server(
        openapi_spec=spec,
        server_name=server_name,
        server_url=server_url,
        exclude_pattern=exclude_pattern,
        client_id=client_id,
        client_secret=client_secret
    )

if __name__ == "__main__":
    main() 