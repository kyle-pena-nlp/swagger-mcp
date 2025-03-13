// The module 'vscode' contains the VS Code extensibility API
const vscode = require('vscode');
// Import the command service
const commandService = require('./services/commandService');
// Import the API service
const apiService = require('./services/apiService');

/**
 * @param {vscode.ExtensionContext} context
 */
function activate(context) {
    console.log('Extension "hello-world" is now active!');

    // Start the API server
    apiService.start()
        .then(() => {
            console.log('API server started successfully');
        })
        .catch(err => {
            console.error('Failed to start API server:', err);
        });

    // Register a command to start/restart the API server
    let startApiServerDisposable = vscode.commands.registerCommand('hello-world.startApiServer', async function () {
        try {
            await apiService.stop(); // Stop if already running
            await apiService.start();
            vscode.window.showInformationMessage('API server started successfully');
        } catch (error) {
            vscode.window.showErrorMessage(`Failed to start API server: ${error.message}`);
        }
    });

    // Register a command to stop the API server
    let stopApiServerDisposable = vscode.commands.registerCommand('hello-world.stopApiServer', async function () {
        try {
            await apiService.stop();
            vscode.window.showInformationMessage('API server stopped successfully');
        } catch (error) {
            vscode.window.showErrorMessage(`Failed to stop API server: ${error.message}`);
        }
    });

    // Register the command handler for hello-world.helloWorld
    let helloWorldDisposable = vscode.commands.registerCommand('hello-world.helloWorld', function () {
        // Use the command service to handle the hello world command
        commandService.helloWorld();
    });

    // Register the command handler for listing all commands
    let listCommandsDisposable = vscode.commands.registerCommand('hello-world.listAllCommands', function () {
        // Use the command service to handle listing all commands
        commandService.listAllCommands();
    });

    // Add the commands to the extension's subscriptions
    context.subscriptions.push(helloWorldDisposable);
    context.subscriptions.push(listCommandsDisposable);
    context.subscriptions.push(startApiServerDisposable);
    context.subscriptions.push(stopApiServerDisposable);
}

// This method is called when your extension is deactivated
function deactivate() {
    // Stop the API server when the extension is deactivated
    return apiService.stop();
}

// Export the activate and deactivate functions
module.exports = {
    activate,
    deactivate
}; 