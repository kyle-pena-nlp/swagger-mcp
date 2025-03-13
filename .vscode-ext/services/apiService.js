const http = require('http');
const url = require('url');
const commandService = require('./commandService');
const vscode = require('vscode');

/**
 * Service that exposes VS Code command functionality via a REST API
 */
class ApiService {
    constructor() {
        this.server = null;
        this.port = 3000; // Default port
    }

    /**
     * Start the API server
     * @param {number} port - Port to listen on (optional)
     * @returns {Promise<void>}
     */
    start(port) {
        if (this.server) {
            return Promise.resolve(); // Server already running
        }

        if (port) {
            this.port = port;
        }

        return new Promise((resolve, reject) => {
            try {
                this.server = http.createServer((req, res) => {
                    this.handleRequest(req, res);
                });

                this.server.listen(this.port, () => {
                    vscode.window.showInformationMessage(`API server running on port ${this.port}`);
                    resolve();
                });

                this.server.on('error', (err) => {
                    vscode.window.showErrorMessage(`Failed to start API server: ${err.message}`);
                    this.server = null;
                    reject(err);
                });
            } catch (err) {
                vscode.window.showErrorMessage(`Error starting API server: ${err.message}`);
                reject(err);
            }
        });
    }

    /**
     * Stop the API server
     * @returns {Promise<void>}
     */
    stop() {
        return new Promise((resolve) => {
            if (!this.server) {
                resolve();
                return;
            }

            this.server.close(() => {
                vscode.window.showInformationMessage('API server stopped');
                this.server = null;
                resolve();
            });
        });
    }

    /**
     * Handle incoming HTTP requests
     * @param {http.IncomingMessage} req - The request object
     * @param {http.ServerResponse} res - The response object
     */
    handleRequest(req, res) {
        // Set CORS headers
        res.setHeader('Access-Control-Allow-Origin', '*');
        res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
        res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

        // Handle preflight requests
        if (req.method === 'OPTIONS') {
            res.writeHead(204);
            res.end();
            return;
        }

        // Parse the URL and route the request
        const parsedUrl = url.parse(req.url, true);
        const path = parsedUrl.pathname;

        // Basic routing
        if (req.method === 'GET') {
            if (path === '/api/hello') {
                this.handleHelloWorld(req, res);
            } else if (path === '/api/commands') {
                this.handleListCommands(req, res);
            } else {
                this.sendResponse(res, 404, { error: 'Not found' });
            }
        } else {
            this.sendResponse(res, 405, { error: 'Method not allowed' });
        }
    }

    /**
     * Handle the hello world endpoint
     * @param {http.IncomingMessage} req - The request object
     * @param {http.ServerResponse} res - The response object
     */
    handleHelloWorld(req, res) {
        try {
            // Call the command service method
            commandService.helloWorld();
            
            // Send a success response
            this.sendResponse(res, 200, { 
                message: 'Hello World command executed successfully',
                success: true
            });
        } catch (error) {
            this.sendResponse(res, 500, { 
                error: `Failed to execute Hello World command: ${error.message}`,
                success: false
            });
        }
    }

    /**
     * Handle the list commands endpoint
     * @param {http.IncomingMessage} req - The request object
     * @param {http.ServerResponse} res - The response object
     */
    async handleListCommands(req, res) {
        try {
            // Get all VS Code commands using the VSCode API directly
            // since we need to return the result rather than show the UI
            const commands = await vscode.commands.getCommands(true);
            const sortedCommands = commands.sort();
            
            // Send the commands as the response
            this.sendResponse(res, 200, { 
                commands: sortedCommands,
                count: sortedCommands.length,
                success: true
            });
        } catch (error) {
            this.sendResponse(res, 500, { 
                error: `Failed to retrieve commands: ${error.message}`,
                success: false
            });
        }
    }

    /**
     * Send an HTTP response
     * @param {http.ServerResponse} res - The response object
     * @param {number} statusCode - The HTTP status code
     * @param {Object} data - The response data
     */
    sendResponse(res, statusCode, data) {
        res.writeHead(statusCode, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify(data, null, 2));
    }
}

// Export a singleton instance of the API service
module.exports = new ApiService(); 