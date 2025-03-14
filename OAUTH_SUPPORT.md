# OAuth Support for OpenAPI MCP Server

This document describes the OAuth 2.0 support integrated into the OpenAPI MCP Server. The server now supports the OAuth 2.0 authorization code flow for APIs that require OAuth-based authentication.

## Overview

The OpenAPI MCP Server can now handle OAuth 2.0 authentication alongside the previously supported bearer token authentication. The implementation:

1. Detects OAuth security schemes in OpenAPI specifications (both 2.0/Swagger and 3.0)
2. Extracts authorization URLs, token URLs, and scopes from these schemes
3. Allows you to provide OAuth client credentials (client ID and client secret) when starting the server
4. Automatically handles the OAuth flow for endpoints that require it

## Usage

To use the OAuth support in the MCP Server, you need to:

1. Start the server with the `--client-id` and `--client-secret` parameters
2. The server will automatically detect endpoints requiring OAuth and use these credentials

### Example Command

```bash
python openapi_mcp_server.py \
  https://raw.githubusercontent.com/slackapi/slack-api-specs/refs/heads/master/web-api/slack_web_openapi_v2_without_examples.json \
  --name "Slack-API-MCP-Server" \
  --url "https://slack.com/api" \
  --client-id "YOUR_CLIENT_ID" \
  --client-secret "YOUR_CLIENT_SECRET" \
  --exclude-pattern "(admin)|(workflows)|(audit)|(files)|(event)|(call)"
```

### Test Script

For convenience, a test script has been included to demonstrate the OAuth support with the Slack API:

```bash
python test_slack_oauth_server.py --client-id YOUR_CLIENT_ID --client-secret YOUR_CLIENT_SECRET
```

## How It Works

1. When the server starts, it parses the OpenAPI spec and identifies security schemes
2. For each tool call, the server:
   - Checks if the endpoint requires OAuth authentication
   - If OAuth is required and client credentials are provided, it extracts the necessary OAuth URLs and scopes
   - Initializes the OAuthHandler with these details
   - Handles the authorization flow to obtain an access token
   - Uses the access token to authenticate API requests

## OAuth Flow Process

1. When an endpoint requiring OAuth is invoked, the server checks for client credentials
2. If credentials are available, the OAuthHandler is initialized with:
   - Client ID and Client Secret
   - Authorization URL and Token URL (extracted from the OpenAPI spec)
   - Scopes required for the endpoint (extracted from the OpenAPI spec)
3. The OAuthHandler manages:
   - Opening a browser for user authorization (first time only)
   - Obtaining an authorization code via a redirect
   - Exchanging the code for an access token
   - Storing the token for future use
   - Refreshing the token when necessary

## Required OAuth Parameters

The following OAuth parameters are now supported:

- `client_id`: Your OAuth client ID (required for OAuth flow)
- `client_secret`: Your OAuth client secret (required for OAuth flow)

The following are extracted automatically from the OpenAPI specification:

- Authorization URL
- Token URL
- Required scopes

## Supported API Providers

This OAuth implementation has been tested with:

- Slack API (OpenAPI 2.0 format)

It should work with any API provider that correctly documents their OAuth security schemes in the OpenAPI specification (versions 2.0 or 3.0).

## Notes

- OAuth tokens are stored locally and reused for subsequent requests to avoid repeated authorization flows
- If the token expires, the handler automatically initiates a refresh
- For APIs requiring specific OAuth scopes, the server extracts these from the OpenAPI security schemes 