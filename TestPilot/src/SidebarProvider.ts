import * as vscode from "vscode";
import { exec } from 'child_process';
import axios, { AxiosResponse, AxiosError } from 'axios';

// SidebarProvider class for viewing the extension
export class SidebarProvider implements vscode.WebviewViewProvider {
    inputFileContent: string|undefined = undefined;
    pathOfInputFile: vscode.Uri|undefined = undefined;
    private _view?: vscode.WebviewView;
    private _previousEditor: vscode.TextEditor | undefined;
    private editor = true;


    constructor(private readonly _context: vscode.ExtensionContext) {
        vscode.window.onDidChangeActiveTextEditor(this.onDidChangeActiveTextEditor, this);
        this._previousEditor = vscode.window.activeTextEditor;
    }

    // Upon the user changing the file open in the editor, update the webview content accordingly.
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
            if(!editor || this._previousEditor){
                this._view.webview.html = this._getHtmlForWebview(this._view.webview, this.editor, text);
            }
        }
    }

    // Upon extension startup, check if an editor is open and show the correct webview
    public resolveWebviewView(webviewView: vscode.WebviewView) {
        this._view = webviewView;
        webviewView.webview.options = {
            enableScripts: true,
            localResourceRoots: [this._context.extensionUri],
        };

         // Set up a message listener for the webview
        const disposable = webviewView.webview.onDidReceiveMessage(
            message => {
                switch (message.command) {
                    case 'saveUserDescription':
                        this.saveUserDescription(message.userDescription);
                        return;
                    case 'populateTestFile':
                        this.populateTestFile(message.tests);
                        return;
                    case 'saveDetails':
                        this.saveDetails(message.tests, message.testFunctionNames, message.testDescriptions);
                        return;
                    case 'runTests':
                        this.runTests();
                        return;
                }
            }
        );

        this._view.onDidChangeVisibility(() => {
            if (vscode.window.activeTextEditor) {
                this.editor = true;
                webviewView.webview.html = this._getHtmlForWebview(webviewView.webview, this.editor, vscode.window.activeTextEditor.document.getText());
            }
            else {
                this.editor = false;
                webviewView.webview.html = this._getHtmlForWebview(webviewView.webview, this.editor, "");
            }
        });

        this._view.onDidDispose(() => {
            disposable.dispose();
        });
    
        if (vscode.window.activeTextEditor) {
            this.editor = true;
            webviewView.webview.html = this._getHtmlForWebview(webviewView.webview, this.editor, vscode.window.activeTextEditor.document.getText());
        }
        else {
            this.editor = false;
            this._view.webview.html = this._getHtmlForWebview(this._view.webview, this.editor, "");
        }
    }

    public saveDetails(tests: string, testFunctionNames: string[], testDescriptions: string[]) {
        this._context.globalState.update('testpilot-tests', tests);
        this._context.globalState.update('testpilot-test-function-names', testFunctionNames);
        this._context.globalState.update('testpilot-test-descriptions', testDescriptions);
    }

    public saveUserDescription(userDescription: string) {
        this._context.globalState.update('testpilot-user-input', userDescription);
    }

    public runTests(): Promise<void> {
        return new Promise((resolve, reject) => {
            const pathToJUnitStandaloneJar = this._context.extensionUri.fsPath + "/junit-jars/junit-platform-console-standalone-1.8.2.jar";
            const directoryWhereJavaFilesExist = this.pathOfInputFile?.fsPath.substring(0, this.pathOfInputFile.fsPath.lastIndexOf('/'));
            const pathRepresentingAllJavaFiles = `${directoryWhereJavaFilesExist}/*.java`;   
            
            // STEP 1: Compile java files
            const compileCommand = `javac -cp ".:${pathToJUnitStandaloneJar}" ${pathRepresentingAllJavaFiles}`;
            console.log(compileCommand);
    
            this.executeCommand(compileCommand, "compile")
                .then(() => {
                    console.log("Compilation finished");
                    // STEP 2: Run the tests
                    let indexWhereSrcBegins = pathRepresentingAllJavaFiles.indexOf("/src");
                    // Adding 4 to include the length of "/src"
                    let srcFolder = pathRepresentingAllJavaFiles.substring(0, indexWhereSrcBegins + 4);
    
                    const runTestsCommand = `java -cp "${srcFolder}:${pathToJUnitStandaloneJar}" org.junit.platform.console.ConsoleLauncher --scan-classpath`;
                    console.log(runTestsCommand);
    
                    return this.executeCommand(runTestsCommand, "test");
                })
                .then(() => {
                    console.log("Tests finished");
                    resolve(); // Resolve the promise when tests are successfully executed
                })
                .catch(error => {
                    console.error(error.message);
                    // reject(error); // Reject the promise if an error occurs
                    resolve();
                });
        });
    }

    private executeCommand(command: string, action: string): Promise<void> {
        return new Promise<void>((resolve, reject) => {
            exec(command, (error, stdout, stderr) => {
                if (error) {
                    if (action === "compile") {
                        //TODO Implement call to GPT correction endpoint, use code to write to test file again and re-run compilation + tests
                        this._context.globalState.update('testpilot-failed-test-function-names', this._context.globalState.get('testpilot-test-function-names'));
                        console.log("Making API call to corrective GPT endpoint");
                        //Call GPT correction endpoint
                        axios.get("http://127.0.0.1:8000/testpilot-correction", {
                            params: {
                            code: this.inputFileContent,
                            tests: this._context.globalState.get('testpilot-tests'),
                            errors: `${stdout} ${error.message} ${stderr}`,
                            model: "gpt-3.5-turbo-1106"
                            },
                        })
                            .then((response: AxiosResponse) => {
                            // Handle the successful response
                            console.log('NEW Compilation Response:', response.data);
                            this._context.globalState.update('testpilot-tests', response.data.tests);
                            this._context.globalState.update('testpilot-test-function-names', response.data.testFunctionNames);
                            this._context.globalState.update('testpilot-test-descriptions', response.data.descriptions);
                            this.populateTestFile(response.data.tests);
                            console.log("Running tests with updated code");
                            this.runTests();
                            })
                            .catch((error: AxiosError) => {
                            // Handle errors
                            if (error.response) {
                                // The request was made and the server responded with a status code
                                // that falls out of the range of 2xx
                                console.error('Server responded with non-2xx status:', error.response.status);
                                console.log(error.message);
                            } else if (error.request) {
                                // The request was made but no response was received
                                console.error('No response received from the server');
                                console.log(error.message);
                            } else {
                                // Something happened in setting up the request that triggered an Error
                                console.error('Error setting up the request:', error.message);
                                console.log(error.message);
                            }
                            });
    
                    } else if (action === "test") {
                        const regex = /─\s*(.*?)\s*✘/g;
                        let match;

                        let failedTestFunctionNames = [];
                        this._context.globalState.update('testpilot-failed-test-function-names', []);
                        // Iterate over matches in the input string
                        while ((match = regex.exec(`${stdout}`)) !== null) {
                            const failedTest = match[1].replaceAll("\u001b[0m \u001b[31m", "").replaceAll("()", ""); // Remove ANSI escape codes and function brackets from JUnit output
                            failedTestFunctionNames.push(failedTest);
                        }
                        this._context.globalState.update('testpilot-failed-test-function-names', failedTestFunctionNames);
                        console.log(failedTestFunctionNames);
                        console.log("Making API call to corrective GPT endpoint");
                        axios.get("http://127.0.0.1:8000/testpilot-correction", {
                            params: {
                            code: this.inputFileContent,
                            tests: this._context.globalState.get('testpilot-tests'),
                            errors: `${stdout} ${error.message} ${stderr}`,
                            model: "gpt-3.5-turbo-1106"
                            },
                        })
                            .then((response: AxiosResponse) => {
                            // Handle the successful response
                            console.log('NEW tests Response:', response.data);
                            this._context.globalState.update('testpilot-tests', response.data.tests);
                            this._context.globalState.update('testpilot-test-function-names', response.data.testFunctionNames);
                            this._context.globalState.update('testpilot-test-descriptions', response.data.descriptions);
                            this.populateTestFile(response.data.tests);
                            console.log("Running tests with updated tests");
                            this.runTests();
                            })
                            .catch((error: AxiosError) => {
                            // Handle errors
                            if (error.response) {
                                // The request was made and the server responded with a status code
                                // that falls out of the range of 2xx
                                console.error('Server responded with non-2xx status:', error.response.status);
                            } else if (error.request) {
                                // The request was made but no response was received
                                console.error('No response received from the server');
                            } else {
                                // Something happened in setting up the request that triggered an Error
                                console.error('Error setting up the request:', error.message);
                            }
                            });

                        // Update webview content after tests are executed
                        if (this._view && action === "test") {
                            const text = this._previousEditor ? this._previousEditor.document.getText() : undefined;
                            this._view.webview.html = this._getHtmlForWebview(this._view.webview, this.editor, text);
                        }
                    }
                    
                    //TODO: Make compilation error hold loading icon (only test error does so far)
                    console.log(`Output: ${stdout}`);
                    console.log(`Error executing command: ${error.message}\n${stderr}`);
                    // reject();
                    resolve();
                } else {
                    this._context.globalState.update('testpilot-failed-test-function-names', []);
                    // Update webview content after tests are executed
                    if (this._view && action === "test") {
                        const text = this._previousEditor ? this._previousEditor.document.getText() : undefined;
                        this._view.webview.html = this._getHtmlForWebview(this._view.webview, this.editor, text);
                    }
                    resolve();
                }
            });
        });
    }

    public populateTestFile(tests: string) {
        let originalPath = this.pathOfInputFile?.fsPath || "";

        if(this.pathOfInputFile?.fsPath.includes("/src/main")){
            originalPath = this.pathOfInputFile?.fsPath.replace(/\/src(\/main)?\//, '/src/test/') || "";
        }  

        //Get the active filename 
        const currentOpenFilename = originalPath?.split('/').pop() || "";;
    
        // Append "Test" to the active filename
        const testFilename = currentOpenFilename.replace(/\.java$/, 'Test.java');
    
        // Construct the final path with the updated file name
        const pathOfTestFile = vscode.Uri.file(originalPath?.replace(currentOpenFilename, testFilename));
    
        // Your logic to generate tests
        vscode.workspace.fs.writeFile(pathOfTestFile, Buffer.from(tests, 'utf-8'));
    }

    // Expose the populateTestFile function to the webview
    private callPopulateTestFile = `
        function populateTestFile(tests) {
            tsvscode.postMessage({
                command: 'populateTestFile',
                tests: tests
            });
        }
    `;

    // Expose the callSaveDetails function to the webview
    private callSaveDetails = `
        function saveDetails(tests, testFunctionNames, testDescriptions) {
            tsvscode.postMessage({
                command: 'saveDetails',
                tests: tests,
                testFunctionNames: testFunctionNames,
                testDescriptions: testDescriptions
            });
        }
    `;

    // Expose the runTests function to the webview
    private callRunTests = `
        function runTests() {
            tsvscode.postMessage({
                command: 'runTests',
            });
        }
    `;

    private callSaveUserDescription = `
    function saveUserDescription(userDescription) {
        tsvscode.postMessage({
            command: 'saveUserDescription',
            userDescription: userDescription
        });
    }
    `;

    private ifMakingTestsOnTestFile() {
        this.pathOfInputFile = vscode.window.activeTextEditor?.document.uri;
        this.inputFileContent = vscode.window.activeTextEditor?.document.getText();
        if (!this.pathOfInputFile?.fsPath.includes("/src/test") && !this.pathOfInputFile?.fsPath.includes("Test.java") && !this.inputFileContent?.includes("@Test")) {
            return false;
        } else {
            return true;
        }
    }

    private _getHtmlForWebview(webview: vscode.Webview, editor: boolean, code: string | undefined) {
        // Gather css files
        const styleResetUri = webview.asWebviewUri(
            vscode.Uri.joinPath(this._context.extensionUri, "media", "reset.css")
        );
        const styleVSCodeUri = webview.asWebviewUri(
            vscode.Uri.joinPath(this._context.extensionUri, "media", "vscode.css")
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
                        ${this.callSaveUserDescription}
                        ${this.callPopulateTestFile}
                        ${this.callSaveDetails}
                        ${this.callRunTests}
                    </script>
                    <script nonce="${nonce}" type="module" src="https://cdnjs.cloudflare.com/ajax/libs/axios/1.5.1/axios.min.js"></script>
                    <script nonce="${nonce}" type="module" src="https://unpkg.com/@fluentui/web-components"></script>
                </head>
                <body>
                    <h1>TestPilot</h1>
                    <input placeholder="What should your code do?"/ id="myTextField">
                    <button id="generateButton">Generate tests</button>
                    <div id="response"></div>
                    <script nonce="${nonce}"> 
                    console.log(${JSON.stringify(this._context.globalState.get('testpilot-user-input'))});
                    console.log(${JSON.stringify(this._context.globalState.get('testpilot-tests'))});
                    const textField = document.getElementById('myTextField');
                    textField.value = ${JSON.stringify(this._context.globalState.get('testpilot-user-input') || "")};
                    textField.addEventListener('input', (event) => {
                        saveUserDescription(event.target.value);
                      });
                    console.log(${JSON.stringify(this._context.globalState.get('testpilot-test-function-names'))})
                    console.log(${JSON.stringify(this._context.globalState.get('testpilot-test-descriptions'))})
                    console.log(${JSON.stringify(this._context.globalState.get('testpilot-failed-test-function-names'))})
                    if(${JSON.stringify(this._context.globalState.get('testpilot-test-function-names'))} && ${JSON.stringify(this._context.globalState.get('testpilot-test-descriptions'))}) {
                        renderPreviousBoxes(${JSON.stringify(this._context.globalState.get('testpilot-test-function-names'))}, ${JSON.stringify(this._context.globalState.get('testpilot-test-descriptions'))});
                    }
                        document.getElementById('generateButton').addEventListener('click', () => {
                            const testFileOpen = ${JSON.stringify(this.ifMakingTestsOnTestFile())}
                            if(${JSON.stringify(this.ifMakingTestsOnTestFile())}) {
                                document.querySelector('input').value = "";
                                document.querySelector('input').placeholder = "You can't make tests on a test file! ❌";
                                return;
                            } else {
                                if (${!vscode.window.activeTextEditor}) {
                                    document.querySelector('input').value = "";
                                    document.querySelector('input').placeholder = "Open a window with code so I can help! ❌";
                                    return;
                                }
                            }
                            console.log(${JSON.stringify(code)?.toString()});
                            const container = document.getElementById('response');
                            while (container.firstChild) {
                                container.removeChild(container.firstChild);
                            }
                            const loadingIcon = document.createElement('fluent-progress-ring');
                            loadingIcon.size = 'large';
                            loadingIcon.className = 'loader';
                            container.appendChild(loadingIcon);
                            let testFunctionNames = "undefined";
                            let testDescriptions = "undefined";
                            axios.get('http://127.0.0.1:8000/testpilot', {
                                params: {
                                    description: document.querySelector('input').value, 
                                    code: ${JSON.stringify(code)?.toString()}
                                }
                            })
                            .then(response => {
                                console.log(response);
                                container.removeChild(loadingIcon);
                                testFunctionNames = response.data.testFunctionNames;
                                testDescriptions = response.data.descriptions;
                                const tests = response.data.tests;
                                saveDetails(tests, testFunctionNames, testDescriptions);
                                console.log(tests);
                                populateTestFile(tests);
                                runTests();
                            })
                            .then(() => {
                                generateBoxes(testFunctionNames, testDescriptions);
                            })
                            .catch(error => {
                                //container.removeChild(loadingIcon);
                                if (error.response && error.response.status === 400) {
                                    container.removeChild(loadingIcon);
                                    document.querySelector('input').placeholder = 'Error: Enter a valid description here! ❌';
                                }
                                console.error('API Error:', error);
                            });
                        });
                        
                        function renderPreviousBoxes(testFunctionNames, testDescriptions) {
                            const container = document.getElementById('response');
                            for (let i = 1; i < testFunctionNames.length+1; i++) {
                                const card = document.createElement('fluent-card');
                                card.className = 'responseBox';
                                const checkbox = document.createElement('fluent-checkbox');
                                checkbox.className = 'checkbox';
                                const loadingIcon = document.createElement('fluent-progress-ring');
                                loadingIcon.size = 'large';
                                loadingIcon.className = 'responseLoader'
                                if(${JSON.stringify(this._context.globalState.get('testpilot-failed-test-function-names') || [])}.includes(testFunctionNames[i-1])) {
                                    card.appendChild(loadingIcon);
                                    checkbox.id = 'redCheckbox';
                                    checkbox.checked = false;
                                } else {
                                    const existingLoadingIcon = card.querySelector('.responseLoader');
                                    if (existingLoadingIcon) {
                                        card.removeChild(existingLoadingIcon);
                                    }
                                    const paragraph = document.createElement('p');
                                    paragraph.textContent = testDescriptions[i];
                                    card.appendChild(paragraph);
                                    checkbox.id = 'greenCheckbox';
                                    checkbox.checked = true;
                                }
                                card.appendChild(checkbox);
                                container.appendChild(card);
                            }
                        }
                        
                        function generateBoxes(testFunctionNames, testDescriptions) {
                            const container = document.getElementById('response');
                            for (let i = 1; i < testFunctionNames.length+1; i++) {
                                const card = document.createElement('fluent-card');
                                card.className = 'responseBox';
                                const checkbox = document.createElement('fluent-checkbox');
                                checkbox.className = 'checkbox';
                                checkbox.id = 'redCheckbox';
                                const loadingIcon = document.createElement('fluent-progress-ring');
                                loadingIcon.size = 'large';
                                loadingIcon.className = 'responseLoader'
                                card.appendChild(loadingIcon);
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
