import * as vscode from 'vscode';
import { SidebarProvider } from './SidebarProvider';

/**
 * Activates the extension by registering the sidebar provider and initializing necessary subscriptions.
 * 
 * @param context - The `vscode.ExtensionContext` representing the context of the extension.
 */
export function activate(context: vscode.ExtensionContext) {
	const sidebar = new SidebarProvider(context);
	context.subscriptions.push(
		vscode.window.registerWebviewViewProvider(
			"testpilot-sidebar",
			sidebar
		)
	);
}