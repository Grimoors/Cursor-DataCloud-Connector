/**
 * Main extension entry point for Salesforce Data Cloud Assistant.
 * 
 * This module handles the extension activation, webview management,
 * and communication with the middleware API.
 */

import * as vscode from 'vscode';
import * as path from 'path';
import fetch from 'node-fetch';

interface QueryRequest {
    query: string;
    query_type?: string;
    limit?: number;
    include_metadata?: boolean;
    enrich_data?: boolean;
    correlation_id?: string;
}

interface QueryResponse {
    status: string;
    data?: {
        records: any[];
        total_size: number;
        execution_time_ms?: number;
    };
    error?: {
        code: string;
        message: string;
        details?: string;
    };
    correlation_id?: string;
    processing_time_ms?: number;
}

class SalesforceDataCloudProvider implements vscode.WebviewViewProvider {
    public static readonly viewType = 'salesforceDataCloudView';

    private _view?: vscode.WebviewView;
    private _outputChannel: vscode.OutputChannel;

    constructor(private readonly _extensionUri: vscode.Uri) {
        this._outputChannel = vscode.window.createOutputChannel('Salesforce Data Cloud Assistant');
    }

    public resolveWebviewView(
        webviewView: vscode.WebviewView,
        context: vscode.WebviewViewResolveContext,
        _token: vscode.CancellationToken,
    ) {
        this._view = webviewView;

        webviewView.webview.options = {
            enableScripts: true,
            localResourceRoots: [
                vscode.Uri.joinPath(this._extensionUri, 'out', 'webview')
            ]
        };

        webviewView.webview.html = this._getHtmlForWebview(webviewView.webview);

        // Handle messages from the webview
        webviewView.webview.onDidReceiveMessage(async (data) => {
            switch (data.type) {
                case 'query':
                    await this._handleQuery(data.query);
                    break;
                case 'clear':
                    this._clearChat();
                    break;
                case 'settings':
                    await this._openSettings();
                    break;
            }
        });

        // Handle view visibility changes
        webviewView.onDidChangeVisibility(() => {
            if (webviewView.visible) {
                this._log('Webview became visible');
            }
        });

        this._log('Webview provider initialized');
    }

    private async _handleQuery(query: string) {
        try {
            this._log(`Processing query: ${query}`);

            // Get configuration
            const config = vscode.workspace.getConfiguration('salesforceDataCloud');
            const middlewareUrl = config.get<string>('middlewareUrl', 'http://localhost:8000');
            const apiKey = await this._getApiKey();

            if (!apiKey) {
                this._showError('API key not configured. Please set the API key in settings.');
                return;
            }

            // Prepare request
            const request: QueryRequest = {
                query: query,
                query_type: 'natural_language',
                limit: 100,
                include_metadata: true,
                enrich_data: true,
                correlation_id: this._generateCorrelationId()
            };

            // Send request to middleware
            const response = await fetch(`${middlewareUrl}/api/v1/query`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-API-Key': apiKey,
                    'X-Correlation-ID': request.correlation_id!
                },
                body: JSON.stringify(request)
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const result: QueryResponse = await response.json();

            // Send response to webview
            this._view?.webview.postMessage({
                type: 'queryResponse',
                success: result.status === 'success',
                data: result.data,
                error: result.error,
                processingTime: result.processing_time_ms
            });

            this._log(`Query completed in ${result.processing_time_ms}ms`);

        } catch (error) {
            this._log(`Query failed: ${error}`);
            this._showError(`Query failed: ${error}`);
            
            // Send error to webview
            this._view?.webview.postMessage({
                type: 'queryResponse',
                success: false,
                error: {
                    code: 'NETWORK_ERROR',
                    message: 'Failed to communicate with middleware',
                    details: error instanceof Error ? error.message : String(error)
                }
            });
        }
    }

    private _clearChat() {
        this._view?.webview.postMessage({
            type: 'clearChat'
        });
        this._log('Chat cleared');
    }

    private async _openSettings() {
        await vscode.commands.executeCommand('workbench.action.openSettings', 'salesforceDataCloud');
    }

    private async _getApiKey(): Promise<string | undefined> {
        // Try to get from secrets first
        const secrets = vscode.context.secrets;
        let apiKey = await secrets.get('salesforceDataCloud.apiKey');

        if (!apiKey) {
            // Prompt user for API key
            apiKey = await vscode.window.showInputBox({
                prompt: 'Enter your Salesforce Data Cloud API key',
                password: true,
                placeHolder: 'API Key'
            });

            if (apiKey) {
                // Store in secrets
                await secrets.store('salesforceDataCloud.apiKey', apiKey);
            }
        }

        return apiKey;
    }

    private _generateCorrelationId(): string {
        return `req-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    }

    private _getHtmlForWebview(webview: vscode.Webview) {
        const scriptUri = webview.asWebviewUri(vscode.Uri.joinPath(this._extensionUri, 'out', 'webview', 'webview.js'));
        const styleUri = webview.asWebviewUri(vscode.Uri.joinPath(this._extensionUri, 'out', 'webview', 'webview.css'));

        return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src ${webview.cspSource} 'unsafe-inline'; script-src ${webview.cspSource} 'unsafe-inline';">
    <title>Salesforce Data Cloud Assistant</title>
    <link rel="stylesheet" href="${styleUri}">
</head>
<body>
    <div id="app">
        <div class="header">
            <h2>Salesforce Data Cloud Assistant</h2>
            <div class="status" id="status">Ready</div>
        </div>
        
        <div class="chat-container">
            <div class="messages" id="messages">
                <div class="message system">
                    <div class="message-content">
                        Welcome to Salesforce Data Cloud Assistant! 
                        Ask me anything about your customer data.
                    </div>
                </div>
            </div>
            
            <div class="input-container">
                <div class="input-wrapper">
                    <input type="text" id="queryInput" placeholder="Ask about customer data..." />
                    <button id="sendButton">Send</button>
                </div>
            </div>
        </div>
    </div>
    
    <script src="${scriptUri}"></script>
</body>
</html>`;
    }

    private _log(message: string) {
        this._outputChannel.appendLine(`[${new Date().toISOString()}] ${message}`);
    }

    private _showError(message: string) {
        vscode.window.showErrorMessage(`Salesforce Data Cloud: ${message}`);
    }
}

export function activate(context: vscode.ExtensionContext) {
    const provider = new SalesforceDataCloudProvider(context.extensionUri);

    context.subscriptions.push(
        vscode.window.registerWebviewViewProvider(
            SalesforceDataCloudProvider.viewType,
            provider
        )
    );

    // Register commands
    context.subscriptions.push(
        vscode.commands.registerCommand('salesforceDataCloud.refresh', () => {
            vscode.window.showInformationMessage('Salesforce Data Cloud: Refresh requested');
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('salesforceDataCloud.clear', () => {
            vscode.window.showInformationMessage('Salesforce Data Cloud: Clear chat requested');
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('salesforceDataCloud.settings', async () => {
            await vscode.commands.executeCommand('workbench.action.openSettings', 'salesforceDataCloud');
        })
    );

    console.log('Salesforce Data Cloud Assistant extension is now active!');
}

export function deactivate() {
    console.log('Salesforce Data Cloud Assistant extension is now deactivated!');
} 