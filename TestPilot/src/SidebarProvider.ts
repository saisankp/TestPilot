import * as vscode from "vscode";

// SidebarProvider class for viewing the extension
export class SidebarProvider implements vscode.WebviewViewProvider {
    _view?: vscode.WebviewView;
    private _previousEditor: vscode.TextEditor | undefined;
    private editor = true;

    // Constructor to dynamically check if an open editor is present
    constructor(private readonly _extensionUri: vscode.Uri) {
        vscode.window.onDidChangeActiveTextEditor(this.onDidChangeActiveTextEditor, this);
        this._previousEditor = vscode.window.activeTextEditor;
    }

    // Update the greyOut boolean when there is a change between an active and inactive editor
    private onDidChangeActiveTextEditor(editor: vscode.TextEditor | undefined) {
        if (editor) {
            this.editor = true;
        } else {
            if (this._previousEditor) {
                this.editor = false;
            }
        }

        // Update the previous editor to know if we close this later
        this._previousEditor = editor;

        // Update webview content with the new editor boolean
        if (this._view) {
            const text = editor ? editor.document.getText() : undefined;
            this._view.webview.html = this._getHtmlForWebview(this._view.webview, this.editor, text);
        }
    }

    // Upon extension startup, check if an editor is open and show the correct webview
    public resolveWebviewView(webviewView: vscode.WebviewView) {
        this._view = webviewView;
        webviewView.webview.options = {
            enableScripts: true,
            localResourceRoots: [this._extensionUri],
        };

        if (vscode.window.activeTextEditor) {
            this.editor = true;
            webviewView.webview.html = this._getHtmlForWebview(webviewView.webview, this.editor, vscode.window.activeTextEditor.document.getText());
        }
        else {
            this.editor = false;
            this._view.webview.html = this._getHtmlForWebview(this._view.webview, this.editor, "");
        }
    }

    private _getHtmlForWebview(webview: vscode.Webview, editor: boolean, code: string | undefined) {
        // Add greyed out css if no editor is present
        let inactive = undefined;
        if (!editor) {
            inactive = 'body { opacity: 0.5; pointer-events: none; }';
        }
        // Gather css files
        const styleResetUri = webview.asWebviewUri(
            vscode.Uri.joinPath(this._extensionUri, "media", "reset.css")
        );
        const styleVSCodeUri = webview.asWebviewUri(
            vscode.Uri.joinPath(this._extensionUri, "media", "vscode.css")
        );

        // Generate cryptographic nonce for security
        const nonce = this.getNonce();
        const responses = 3;

        // Inline HTML for the sidebar using the css files
        return `<!DOCTYPE html>
                <html lang="en">
                <head>
                    <meta charset="UTF-8">
                    <meta http-equiv="Content-Security-Policy" content="img-src https: data:; style-src 'unsafe-inline' ${webview.cspSource}; script-src 'nonce-${nonce}' https://unpkg.com;">
                    <link href="${styleResetUri}" rel="stylesheet">
                    <link href="${styleVSCodeUri}" rel="stylesheet">
                    <script nonce="${nonce}">
                        const tsvscode = acquireVsCodeApi();
                    </script>
                    <script nonce="${nonce}" type="module" src="https://cdnjs.cloudflare.com/ajax/libs/axios/1.5.1/axios.min.js"></script>
                    <script nonce="${nonce}" type="module" src="https://unpkg.com/@fluentui/web-components"></script>
                    <style nonce="${nonce}">
                        ${inactive}
                    </style>
                </head>
                <body>
                    <h1>TestPilot</h1>
                    <input placeholder="What should your code do?"/>
                    <button id="generateButton">Generate tests</button>
                    <div id="response"></div>
                    <script nonce="${nonce}">
                        document.getElementById('generateButton').addEventListener('click', () => {
                            const container = document.getElementById('response');
                            while (container.firstChild) {
                                container.removeChild(container.firstChild);
                            }
                            const loadingIcon = document.createElement('fluent-progress-ring');
                            loadingIcon.size = 'large';
                            loadingIcon.className = 'loader';
                            container.appendChild(loadingIcon);
                            axios.get('http://127.0.0.1:5000/gpt', {
                                params: {
                                    description: document.querySelector('input').value, 
                                    code: ${JSON.stringify(code)?.toString()}
                                }
                            })
                            .then(response => {
                                container.removeChild(loadingIcon);
                                const numberOfTests = JSON.parse(response.data.choices[0].message.content).numberOfTests
                                const descriptions = Object.values(JSON.parse(response.data.choices[0].message.content).descriptions);
                                generateBoxes(numberOfTests, descriptions);
                            })
                            .catch(error => {
                                container.removeChild(loadingIcon);
                                if (error.response && error.response.status === 400) {
                                    document.querySelector('input').placeholder = 'Error: Enter a valid description here!';
                                }
                                console.error('API Error:', error);
                            });
                        });
                        
                        function generateBoxes(numberOfTests, descriptions) {
                            const container = document.getElementById('response');
                            for (let i = 0; i < numberOfTests; i++) {
                                const card = document.createElement('fluent-card');
                                card.className = 'responseBox';
                                const checkbox = document.createElement('fluent-checkbox');
                                checkbox.className = 'checkbox';
                                checkbox.id = 'redCheckbox';
                                const loadingIcon = document.createElement('fluent-progress-ring');
                                loadingIcon.size = 'large';
                                loadingIcon.className = 'responseLoader'
                                card.appendChild(loadingIcon);

                                // Wait 1 second for animation to turn green (this will be the time it takes to add tests in the code soon)
                                setTimeout(() => {
                                    checkbox.checked = true;
                                }, 1000);

                                // Once the checkbox turns green, we update the responses in each box
                                checkbox.addEventListener('change', function() {
                                    if (checkbox.checked) {
                                        card.removeChild(loadingIcon);
                                        checkbox.id = 'greenCheckbox';
                                        const paragraph = document.createElement('p');
                                        paragraph.textContent = descriptions[i];
                                        card.appendChild(paragraph);
                                    } else {
                                        checkbox.id = 'redCheckbox';
                                    }
                                });
                                card.appendChild(checkbox);
                                container.appendChild(card);
                            }
                        }
                    </script>
                </body>
                </html>`;
    }

    // Create crpytographic nonce for security
    private getNonce() {
        let text = '';
        const possible = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
        for (let i = 0; i < 32; i++) {
            text += possible.charAt(Math.floor(Math.random() * possible.length));
        }
        return text;
    }
}
