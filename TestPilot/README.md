# TestPilot frontend

This directory contains code for the TestPilot Visual Studio Code extension written in Typescript. This extension communicates with a backend Python Flask server through a RESTful API to generate tests. The Python Flask server must be running at localhost (http://127.0.0.1:8000) for the Visual Studio Code extension to access it.

# How to run this extension locally
1. Run `npm run watch` to monitor changes in files as you develop.
2. Press `F5` while on extension.ts to run the extension in a new Visual Studio Code window through the "Extension Development Host".

# User interface elements used
- [Visual Studio Code Extension API](https://code.visualstudio.com/api)
- [Fluent UI](https://learn.microsoft.com/en-us/fluent-ui/web-components/components/overview)
- [Visual Studio Code sample styling](https://github.com/microsoft/vscode-extension-samples/tree/main/webview-sample)