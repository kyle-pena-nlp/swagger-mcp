const vscode = require('vscode');

/**
 * Service class for handling VSCode extension commands
 */
class CommandService {
    /**
     * Display a "Hello World!" message
     */
    helloWorld() {
        vscode.window.showInformationMessage('Hello World!');
    }
    

    
    /**
     * List all available VSCode commands in a QuickPick menu
     */
    async listAllCommands() {
        try {
            // Get all registered commands
            const commands = await vscode.commands.getCommands(true);
            
            // Sort commands alphabetically for better readability
            const sortedCommands = commands.sort();
            
            // Create a QuickPick to display the commands
            const quickPick = vscode.window.createQuickPick();
            quickPick.items = sortedCommands.map(cmd => ({ label: cmd }));
            quickPick.placeholder = `${sortedCommands.length} commands found`;
            
            // Show the QuickPick
            quickPick.show();
            
            // Optional: allow users to copy a command id when selected
            quickPick.onDidAccept(() => {
                const selectedCommand = quickPick.selectedItems[0]?.label;
                if (selectedCommand) {
                    vscode.env.clipboard.writeText(selectedCommand);
                    vscode.window.showInformationMessage(`Copied command: ${selectedCommand}`);
                }
                quickPick.hide();
            });
        } catch (error) {
            vscode.window.showErrorMessage(`Error listing commands: ${error.message}`);
        }
    }
}

// Export the command service
module.exports = new CommandService(); 