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
        this._previousEditor = editor;
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
                    case 'saveSwitchSelection':
                        this.saveSwitchSelection(message.menuSelection);
                    case 'saveMenuSelection':
                        this.saveMenuSelection(message.menuSelection);
                    case 'populateTestFile':
                        this.populateTestFile(message.tests);
                        return;
                    case 'saveDetails':
                        this.saveDetails(message.tests, message.testFunctionNames, message.testDescriptions);
                        return;
                    case 'saveIndicesOfDescriptionsFromNovice':
                        this.saveIndicesOfDescriptionsFromNovice(message.indicesOfDescriptionsFromNovice);
                        return;
                    case 'saveCoverage':
                        this.saveCoverage(message.codeCoverage, message.caseCoverage, message.vectorDatabaseCoverage);
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

    public saveMenuSelection(menuSelection: string) {
        this._context.globalState.update('testpilot-menu-selection', menuSelection);
    }

    public saveSwitchSelection(switchSelection: string) {
        this._context.globalState.update('testpilot-switch-selection', switchSelection);
    }

    public saveIndicesOfDescriptionsFromNovice(indicesOfDescriptionsFromNovice: string) {
        this._context.globalState.update('testpilot-indices-of-descriptions-from-novice', indicesOfDescriptionsFromNovice);
    }

    public saveCoverage(codeCoverage: string, caseCoverage: string, vectorDatabaseCoverage: string) {
        this._context.globalState.update('testpilot-code-coverage', codeCoverage);
        this._context.globalState.update('testpilot-case-coverage', caseCoverage);
        this._context.globalState.update('testpilot-vector-database-coverage', vectorDatabaseCoverage);
        if (this._view && this._view.webview) {
            const text = this._previousEditor ? this._previousEditor.document.getText() : undefined;
            this._view.webview.html = this._getHtmlForWebview(this._view.webview, this.editor, text);
        }
    }

    public runTests(): Promise<void> {
        return new Promise((resolve, reject) => {
            const pathToJUnitStandaloneJar = this._context.extensionUri.fsPath + "/junit-jars/junit-platform-console-standalone-1.8.2.jar";
            const directoryWhereJavaFilesExist = this.pathOfInputFile?.fsPath.substring(0, this.pathOfInputFile.fsPath.lastIndexOf('/'));
            const pathRepresentingAllJavaFiles = `${directoryWhereJavaFilesExist}/*.java`;   
            const compileCommand = `javac -cp ".:${pathToJUnitStandaloneJar}" ${pathRepresentingAllJavaFiles}`;
            this.executeCommand(compileCommand, "compile")
                .then(() => {
                    let indexWhereSrcBegins = pathRepresentingAllJavaFiles.indexOf("/src");
                    let srcFolder = pathRepresentingAllJavaFiles.substring(0, indexWhereSrcBegins + 4);
                    const runTestsCommand = `java -cp "${srcFolder}:${pathToJUnitStandaloneJar}" org.junit.platform.console.ConsoleLauncher --scan-classpath`;
                    return this.executeCommand(runTestsCommand, "test");
                })
                .then(() => {
                    resolve();
                })
                .catch(error => {
                    console.error(error.message);
                    resolve();
                });
        });
    }

    private executeCommand(command: string, action: string): Promise<void> {
        return new Promise<void>((resolve, reject) => {
            exec(command, (error, stdout, stderr) => {
                if (error) {
                    if (action === "test") {
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
                        // Update webview content after tests are executed
                        if (this._view) {
                            const text = this._previousEditor ? this._previousEditor.document.getText() : undefined;
                            this._view.webview.html = this._getHtmlForWebview(this._view.webview, this.editor, text);
                        }
                    }
                    resolve();
                } else {
                    // Update webview content after tests are executed
                    this._context.globalState.update('testpilot-failed-test-function-names', []);
                    if (this._view && action === "test") {
                        const text = this._previousEditor ? this._previousEditor.document.getText() : undefined;
                        this._view.webview.html = this._getHtmlForWebview(this._view.webview, this.editor, text);
                    }
                    resolve();
                }
            });
        });
    }

    public populateTestFile(tests: string | undefined) {
        if (!tests) {
            return;
        }
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
        this._context.globalState.update('testpilot-test-file-content', tests);
        // Your logic to generate tests
        vscode.workspace.fs.writeFile(pathOfTestFile, Buffer.from(tests, 'utf-8'));
    }

    private ifMakingTestsOnTestFile() {
        this.pathOfInputFile = vscode.window.activeTextEditor?.document.uri;
        this.inputFileContent = vscode.window.activeTextEditor?.document.getText();
        if (!this.pathOfInputFile?.fsPath.includes("/src/test") && !this.pathOfInputFile?.fsPath.includes("Test.java") && !this.inputFileContent?.includes("@Test")) {
            return false;
        } else {
            return true;
        }
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

    // Expose the saveDetails function to the webview
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

    // Expose the saveUserDescription function to the webview
    private callSaveUserDescription = `
    function saveUserDescription(userDescription) {
        tsvscode.postMessage({
            command: 'saveUserDescription',
            userDescription: userDescription
        });
    }
    `;

    // Expose the saveSwitchSelection function to the webview
    private callSaveSwitchSelection = `
    function saveSwitchSelection(menuSelection) {
        tsvscode.postMessage({
            command: 'saveSwitchSelection',
            menuSelection: menuSelection
        });
    }
    `;

    // Expose the saveMenuSelection function to the webview
    private callSaveMenuSelection = `
    function saveMenuSelection(menuSelection) {
        tsvscode.postMessage({
            command: 'saveMenuSelection',
            menuSelection: menuSelection
        });
    }
    `;

    // Expose the saveIndicesOfDescriptionsFromNovice function to the webview
    private callSaveIndicesOfDescriptionsFromNovice = `
    function saveIndicesOfDescriptionsFromNovice(indicesOfDescriptionsFromNovice) {
        tsvscode.postMessage({
            command: 'saveIndicesOfDescriptionsFromNovice',
            indicesOfDescriptionsFromNovice: indicesOfDescriptionsFromNovice
        });
    }
    `;

    // Expose the saveCoverage function to the webview
    private callSaveCoverage = `
    function saveCoverage(codeCoverage, caseCoverage, vectorDatabaseCoverage) {
        tsvscode.postMessage({
            command: 'saveCoverage',
            codeCoverage: codeCoverage,
            caseCoverage: caseCoverage,
            vectorDatabaseCoverage: vectorDatabaseCoverage
        });
    }
    `;

    private _getHtmlForWebview(webview: vscode.Webview, editor: boolean, code: string | undefined) {
        // Gather CSS files
        const styleResetUri = webview.asWebviewUri(
            vscode.Uri.joinPath(this._context.extensionUri, "media", "reset.css")
        );
        const styleVSCodeUri = webview.asWebviewUri(
            vscode.Uri.joinPath(this._context.extensionUri, "media", "vscode.css")
        );
        const nonce = this.getNonce();
        // Inline HTML for the sidebar using the CSS files
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
                        ${this.callSaveSwitchSelection}
                        ${this.callSaveMenuSelection}
                        ${this.callSaveIndicesOfDescriptionsFromNovice}
                        ${this.callSaveCoverage}
                        ${this.callPopulateTestFile}
                        ${this.callSaveDetails}
                        ${this.callRunTests}
                    </script>
                    <script nonce="${nonce}" type="module" src="https://cdnjs.cloudflare.com/ajax/libs/axios/1.5.1/axios.min.js"></script>
                    <script nonce="${nonce}" type="module" src="https://unpkg.com/@fluentui/web-components"></script>
                </head>
                <body>
                    <h1>TestPilot</h1>
                    <div class="switchDiv" id="mode-of-operation">
                        <fluent-switch class="switch">
                            <span slot="checked-message"><b>Testing mode</b></span>
                            <span slot="unchecked-message"><b>Discovery mode</b></span>
                            <label for="cap-switch"><b>Mode of operation</b></label>
                        </fluent-switch>
                    </div>
                    <textarea name="text" placeholder="What is a test case in your code?" rows="2" cols="10" wrap="soft" maxlength="196" style="overflow:hidden; resize:none;" id="myTextField"></textarea>
                    <fluent-select title="Select a test case exploration method" class="select" id="test-case-exploration-method">
                        <fluent-option value="1">Explore new test suite</fluent-option>
                        <fluent-option value="2">Explore current test suite</fluent-option>
                    </fluent-select>
                    <button id="generateButton">Generate</button>
                    <fluent-tooltip id="tooltip" anchor="anchor-default">
                        A similar solution ${(JSON.stringify(this._context.globalState.get('testpilot-vector-database-coverage')) !== undefined && JSON.stringify(this._context.globalState.get('testpilot-vector-database-coverage')) !== 'null') ? "had " + JSON.stringify(this._context.globalState.get('testpilot-vector-database-coverage')) + "% code coverage" : "is unavailable."}
                    </fluent-tooltip>
                    <div id='anchor-default'>
                        <div style="display: flex; align-items: center;">
                            <span>Code coverage&nbsp;&nbsp;</span>
                            <fluent-progress id="codeCoverageProgress" value="${JSON.stringify(this._context.globalState.get('testpilot-code-coverage')) || '?'}" style="flex: 1; width=200px"></fluent-progress>
                            &nbsp;&nbsp;<span id="codeCoverageProgressValue">${JSON.stringify(this._context.globalState.get('testpilot-code-coverage')) || '?'}</span>%
                        </div>
                        <!-- Conditional rendering for case coverage progress bar -->
                        <div style="display: flex; align-items: center;" id="caseCoverageProgressBarContainer">
                            <span>Case coverage&nbsp;&nbsp;</span>
                            <fluent-progress id="caseCoverageProgress" value="${JSON.stringify(this._context.globalState.get('testpilot-case-coverage')) || '?'}" style="flex: 1; width=200px"></fluent-progress>
                            &nbsp;&nbsp;<span id="caseCoverageProgressValue">${JSON.stringify(this._context.globalState.get('testpilot-case-coverage')) || '?'}</span>%
                        </div>
                    </div>
                    <div id="response"></div>
                    <script nonce="${nonce}">
                    const textField = document.getElementById('myTextField');
                    textField.value = ${JSON.stringify(this._context.globalState.get('testpilot-user-input') || "")};
                    textField.addEventListener('input', (event) => {
                        saveUserDescription(event.target.value);
                      });
                    document.addEventListener("DOMContentLoaded", function() {
                        if (${JSON.stringify(this._context.globalState.get('testpilot-menu-selection'))} == "testing") {
                            var switchElement = document.getElementById("mode-of-operation").querySelector(".switch");
                            switchElement.setAttribute("checked", "");
                        }    
                    });
                    const menu = document.getElementById('test-case-exploration-method');
                    var optionElements = menu.getElementsByTagName('fluent-option');
                    let testCaseExplorationMethod = ${JSON.stringify(this._context.globalState.get('testpilot-menu-selection') || "-1")};
                    for (var i = 0; i < optionElements.length; i++) {
                        if (optionElements[i].getAttribute('value') == testCaseExplorationMethod) {
                            optionElements[i].setAttribute('selected', 'selected');
                        } else {
                            optionElements[i].removeAttribute('selected');
                        }
                    }
                    menu.addEventListener('change', function(event) {
                        saveMenuSelection(event.target.value);
                    });
                    const switchElement = document.querySelector('.switch');
                    const caseCoverageProgressBarContainer = document.getElementById('caseCoverageProgressBarContainer');
                    switchElement.addEventListener('change', function(event) {
                        const isChecked = event.target.checked;
                        const message = isChecked ? event.target.querySelector('[slot="checked-message"]').textContent.replace(" mode", "").toLowerCase() : event.target.querySelector('[slot="unchecked-message"]').textContent.replace(" mode", "").toLowerCase();
                        saveSwitchSelection(message);
                        var switchElement = document.querySelector(' .switch');
                        var ariaChecked = switchElement.getAttribute('aria-checked');
                        if(ariaChecked == 'true') {
                            caseCoverageProgressBarContainer.style.display = 'flex';
                        } else {
                            caseCoverageProgressBarContainer.style.display = 'none';
                        }
                    });
                    var ariaChecked = switchElement.getAttribute('aria-checked');
                    if(ariaChecked == 'true') {
                        caseCoverageProgressBarContainer.style.display = 'flex';
                    } else {
                        caseCoverageProgressBarContainer.style.display = 'none';
                    }
                    if(${JSON.stringify(this._context.globalState.get('testpilot-test-function-names'))} && ${JSON.stringify(this._context.globalState.get('testpilot-test-descriptions'))}) {
                        renderPreviousBoxes(${JSON.stringify(this._context.globalState.get('testpilot-test-function-names'))}, ${JSON.stringify(this._context.globalState.get('testpilot-test-descriptions'))}, ${JSON.stringify(this._context.globalState.get('testpilot-indices-of-descriptions-from-novice'))});
                    }
                    document.getElementById('generateButton').addEventListener('click', () => {
                        const testFileOpen = ${JSON.stringify(this.ifMakingTestsOnTestFile())}
                        if(${JSON.stringify(this.ifMakingTestsOnTestFile())}) {
                            textField.value = "";
                            textField.placeholder = "You can't make tests on a test file! ❌";
                            return;
                        } else {
                            if (${!vscode.window.activeTextEditor}) {
                                textField.value = "";
                                textField.placeholder = "Open a window with code so I can help! ❌";
                                return;
                            }
                        }
                        const explorationMethod = document.getElementById('test-case-exploration-method');
                        var switchElement = document.querySelector(' .switch');
                        var ariaChecked = switchElement.getAttribute('aria-checked');
                        if(ariaChecked === 'true') {
                            var endpoint = "http://127.0.0.1:8000/testpilot/testing";
                        } else {
                            var endpoint = "http://127.0.0.1:8000/testpilot/discovery";
                        }
                        if (explorationMethod.value === "1") {
                            if (endpoint == 'http://127.0.0.1:8000/testpilot/discovery') {
                                let progressElement = document.getElementById('codeCoverageProgress');
                                let progressValueElement = document.getElementById('codeCoverageProgressValue');
                                progressElement.setAttribute('value', "0");
                                progressValueElement.textContent = "?";
                                progressElement = document.getElementById('caseCoverageProgress');
                                progressValueElement = document.getElementById('caseCoverageProgressValue');
                                progressElement.setAttribute('value', "0");
                                progressValueElement.textContent = "?";
                            }
                            const container = document.getElementById('response');
                            while (container.firstChild) {
                                container.removeChild(container.firstChild);
                            }
                            explorationMethod.value = "2";
                            saveMenuSelection("2");
                            const loadingIcon = document.createElement('fluent-progress-ring');
                            loadingIcon.size = 'large';
                            loadingIcon.className = 'loader';
                            container.appendChild(loadingIcon);
                            let testFunctionNames = "undefined";
                            let testDescriptions = "undefined";
                            let tests = "undefined";
                            let indexOfDescriptionFromNovice = "0";
                            let codeCoverage = "undefined"
                            let vectorDatabaseCoverage = "undefined"
                            axios.get(endpoint, {
                                params: {
                                    description: textField.value, 
                                    code: ${JSON.stringify(code)?.toString()}
                                }
                            })
                            .then(response => {
                                container.removeChild(loadingIcon);
                                testFunctionNames = response.data.testFunctionNames;
                                testDescriptions = response.data.descriptions;
                                indexOfDescriptionFromNovice = response.data.indexOfDescriptionFromNovice ?? undefined;
                                if(indexOfDescriptionFromNovice != undefined){
                                    saveIndicesOfDescriptionsFromNovice(indexOfDescriptionFromNovice);
                                }
                                let tests = response.data.tests;
                                let codeCoverage = response.data.codeCoverage;
                                let caseCoverage = response.data.caseCoverage ?? undefined;
                                let vectorDatabaseCoverage = response.data.vectorDatabaseCoverage;
                                let progressElement = document.getElementById('codeCoverageProgress');
                                let progressValueElement = document.getElementById('codeCoverageProgressValue');
                                progressElement.setAttribute('value', codeCoverage.toString());
                                progressValueElement.textContent = codeCoverage.toString();
                                saveCoverage(codeCoverage, caseCoverage, vectorDatabaseCoverage);
                                saveDetails(tests, testFunctionNames, testDescriptions);
                                populateTestFile(tests);
                                runTests();
                                if (caseCoverage != 0 && endpoint == "http://127.0.0.1:8000/testpilot/discovery") {
                                    progressElement = document.getElementById('caseCoverageProgress');
                                    progressValueElement = document.getElementById('caseCoverageProgressValue');
                                    progressElement.setAttribute('value', caseCoverage.toString());
                                    progressValueElement.textContent = caseCoverage.toString();
                                    generateBoxes(testFunctionNames, testDescriptions);
                                    let previousIndicesOfDescriptionsFromNovices = ${JSON.stringify(this._context.globalState.get('testpilot-indices-of-descriptions-from-novice'))} + "," + indexOfDescriptionFromNovice;
                                    renderPreviousBoxes(testFunctionNames, testDescriptions, previousIndicesOfDescriptionsFromNovices);
                                }
                            })
                            .catch(error => {
                                if (error.response && error.response.status === 400) {
                                    container.removeChild(loadingIcon);
                                    document.querySelector('input').placeholder = 'Error: Enter a valid description here! ❌';
                                }
                                console.error('API Error:', error);
                            });
                        } else {
                            let progressElement = document.getElementById('caseCoverageProgress');
                            let progressValueElement = document.getElementById('caseCoverageProgressValue');
                            progressElement.setAttribute('value', "0");
                            progressValueElement.textContent = "?";
                            let indexOfDescriptionFromNovice = "0";
                            let testDescriptions = ${JSON.stringify(this._context.globalState.get('testpilot-test-descriptions'))};
                            let testFunctionNames = ${JSON.stringify(this._context.globalState.get('testpilot-test-function-names'))};
                            let formattedDescription = ""
                            for (let i = 1; i < testDescriptions.length+1; i++) {
                                formattedDescription = formattedDescription + i + ". " + testDescriptions[i-1] + "\\n";
                            }
                            let previousIndicesOfDescriptionsFromNovices = "undefined";
                            const container = document.getElementById('response');
                            var cards = container.children;
                            for (var i = 0; i < cards.length; i++) {
                                var card = cards[i];
                                if (card.style.opacity === '0.5') {
                                    const loadingIcon = document.createElement('fluent-progress-ring');
                                    loadingIcon.size = 'large';
                                    loadingIcon.className = 'responseLoader'
                                    card.appendChild(loadingIcon);
                                }
                            }
                            axios.get('endpoint', {
                                params: {
                                    code: ${JSON.stringify(code)?.toString()},
                                    description: textField.value,
                                    testCode: ${JSON.stringify(this._context.globalState.get('testpilot-test-file-content'))},
                                    testCases: formattedDescription,
                                    knownTestCaseIndices: ${JSON.stringify(this._context.globalState.get('testpilot-indices-of-descriptions-from-novice'))}
                                }
                            })
                            .then(response => {
                                indexOfDescriptionFromNovice = response.data.indexOfDescriptionFromNovice;
                                caseCoverage = response.data.caseCoverage;
                            })
                            .then(() => {
                                previousIndicesOfDescriptionsFromNovices = ${JSON.stringify(this._context.globalState.get('testpilot-indices-of-descriptions-from-novice'))} + "," + indexOfDescriptionFromNovice;
                                saveIndicesOfDescriptionsFromNovice(previousIndicesOfDescriptionsFromNovices);
                                codeCoverage = ${JSON.stringify(this._context.globalState.get('testpilot-code-coverage'))};
                                vectorDatabaseCoverage = ${JSON.stringify(this._context.globalState.get('testpilot-vector-database-coverage'))};
                                const progressElement = document.getElementById('caseCoverageProgress');
                                const progressValueElement = document.getElementById('caseCoverageProgressValue');
                                progressElement.setAttribute('value', codeCoverage.toString());
                                progressValueElement.textContent = codeCoverage.toString();
                                saveCoverage(codeCoverage, caseCoverage, vectorDatabaseCoverage);
                                const container = document.getElementById('response');
                                while (container.firstChild) {
                                    container.removeChild(container.firstChild);
                                }
                                renderPreviousBoxes(testFunctionNames, testDescriptions, previousIndicesOfDescriptionsFromNovices);
                            })
                            .catch(error => {
                                if (error.response && error.response.status === 400) {
                                    container.removeChild(loadingIcon);
                                    document.querySelector('input').placeholder = 'Error: Enter a valid description here! ❌';
                                }
                                console.error('API Error:', error);
                            });
                        }
                    });
                        
                    function renderPreviousBoxes(testFunctionNames, testDescriptions, previousIndicesOfDescriptionsFromNovices) {
                        const container = document.getElementById('response');
                        for (let i = 1; i < testFunctionNames.length+1; i++) {
                            const card = document.createElement('fluent-card');
                            card.className = 'responseBox';
                            const checkbox = document.createElement('fluent-checkbox');
                            checkbox.className = 'checkbox';
                            const loadingIcon = document.createElement('fluent-progress-ring');
                            loadingIcon.size = 'large';
                            loadingIcon.className = 'responseLoader'
                            if(${JSON.stringify(this._context.globalState.get('testpilot-failed-test-function-names'))}.includes(testFunctionNames[i-1][0])) {
                                const paragraph = document.createElement('p');
                                paragraph.textContent = testDescriptions[i-1];
                                card.appendChild(paragraph);
                                checkbox.id = 'redCheckbox';
                                checkbox.checked = false;
                            } else {
                                const existingLoadingIcon = card.querySelector('.responseLoader');
                                if (existingLoadingIcon) {
                                    card.removeChild(existingLoadingIcon);
                                }
                                const paragraph = document.createElement('p');
                                paragraph.textContent = testDescriptions[i-1];
                                if(!String(previousIndicesOfDescriptionsFromNovices).includes(i-1)) {
                                    card.style.opacity = '0.5';
                                    card.style.filter = 'blur(3px)';
                                }
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

    private getNonce() {
        let text = '';
        const possible = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
        for (let i = 0; i < 32; i++) {
            text += possible.charAt(Math.floor(Math.random() * possible.length));
        }
        return text;
    }
}
