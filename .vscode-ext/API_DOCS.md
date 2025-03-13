# REST API Documentation

This extension provides a REST API that allows programmatic access to VS Code commands and functionality. The API server runs on port 3000 by default.

## Starting and Stopping the API Server

The API server starts automatically when the extension is activated. You can also manage it manually:

- Use the command palette (Ctrl+Shift+P or Cmd+Shift+P) and search for "Start API Server" to start it
- Use the command palette and search for "Stop API Server" to stop it

## API Endpoints

### GET /api/hello

Triggers the "Hello World" message in VS Code.

**Example Request:**
```bash
curl http://localhost:3000/api/hello
```

**Example Response:**
```json
{
  "message": "Hello World command executed successfully",
  "success": true
}
```

### GET /api/commands

Returns a list of all available VS Code commands.

**Example Request:**
```bash
curl http://localhost:3000/api/commands
```

**Example Response:**
```json
{
  "commands": [
    "workbench.action.openGlobalSettings",
    "workbench.action.zoomIn",
    "workbench.action.zoomOut",
    "hello-world.helloWorld",
    "hello-world.listAllCommands",
    "hello-world.startApiServer",
    "hello-world.stopApiServer"
    // ... many more commands
  ],
  "count": 1500,
  "success": true
}
```

## Error Handling

All API endpoints return JSON responses with the following structure:

- Success responses include a `success: true` property and any relevant data
- Error responses include a `success: false` property and an `error` message

## Security Considerations

The API server does not implement authentication or authorization. It should only be used in trusted environments as it allows programmatic access to VS Code commands.

## Extending the API

To add new endpoints, modify the `apiService.js` file in the `services` directory:

1. Add a new route handler in the `handleRequest` method
2. Create a new handler method for your endpoint
3. Implement the functionality using the command service or VS Code API directly 