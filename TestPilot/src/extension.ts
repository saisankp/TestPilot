import * as vscode from 'vscode';

export function activate(context: vscode.ExtensionContext) {
    // Register command to show the side panel
    let disposable = vscode.commands.registerCommand('extension.showHelloWorldPanel', () => {
        // Create and show a WebviewPanel
        const panel = vscode.window.createWebviewPanel(
            'helloWorldPanel',
            'Hello World',
            vscode.ViewColumn.One,
            {
                enableScripts: true
            }
        );

        // Set the HTML content for the WebviewPanel
        panel.webview.html = getWebviewContent();
    });

    // Add the command to the context subscriptions
    context.subscriptions.push(disposable);
}

function getWebviewContent() {
    return `
        <h1>Hello World!</h1>
    `;
}

export function deactivate() {}
