/**
 * Webview script for Salesforce Data Cloud Assistant.
 * 
 * This module handles the chat interface, message handling,
 * and communication with the VS Code extension.
 */

interface Message {
    type: string;
    content?: string;
    timestamp?: Date;
    isUser?: boolean;
    data?: any;
    error?: any;
    processingTime?: number;
}

interface QueryResponse {
    success: boolean;
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
    processingTime?: number;
}

class ChatInterface {
    private messagesContainer: HTMLElement;
    private queryInput: HTMLInputElement;
    private sendButton: HTMLButtonElement;
    private statusElement: HTMLElement;
    private isProcessing = false;

    constructor() {
        this.messagesContainer = document.getElementById('messages') as HTMLElement;
        this.queryInput = document.getElementById('queryInput') as HTMLInputElement;
        this.sendButton = document.getElementById('sendButton') as HTMLButtonElement;
        this.statusElement = document.getElementById('status') as HTMLElement;

        this.initializeEventListeners();
        this.setupMessageListener();
    }

    private initializeEventListeners(): void {
        // Send button click
        this.sendButton.addEventListener('click', () => {
            this.sendQuery();
        });

        // Enter key in input
        this.queryInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendQuery();
            }
        });

        // Input focus
        this.queryInput.addEventListener('focus', () => {
            this.queryInput.placeholder = 'Ask about customer data...';
        });
    }

    private setupMessageListener(): void {
        // Listen for messages from the extension
        window.addEventListener('message', (event) => {
            const message = event.data;
            
            switch (message.type) {
                case 'queryResponse':
                    this.handleQueryResponse(message);
                    break;
                case 'clearChat':
                    this.clearChat();
                    break;
            }
        });
    }

    private sendQuery(): void {
        const query = this.queryInput.value.trim();
        if (!query || this.isProcessing) {
            return;
        }

        // Add user message
        this.addMessage({
            type: 'user',
            content: query,
            timestamp: new Date(),
            isUser: true
        });

        // Clear input and disable
        this.queryInput.value = '';
        this.setProcessing(true);

        // Send to extension
        this.sendMessageToExtension({
            type: 'query',
            query: query
        });
    }

    private handleQueryResponse(response: QueryResponse): void {
        this.setProcessing(false);

        if (response.success && response.data) {
            this.addMessage({
                type: 'assistant',
                content: this.formatQueryResponse(response.data),
                timestamp: new Date(),
                isUser: false,
                data: response.data,
                processingTime: response.processingTime
            });
        } else {
            this.addMessage({
                type: 'error',
                content: this.formatErrorMessage(response.error),
                timestamp: new Date(),
                isUser: false,
                error: response.error
            });
        }
    }

    private formatQueryResponse(data: any): string {
        const records = data.records || [];
        const totalSize = data.total_size || 0;
        const executionTime = data.execution_time_ms;

        if (records.length === 0) {
            return 'No records found matching your query.';
        }

        let result = `Found ${totalSize} record(s):\n\n`;

        records.forEach((record: any, index: number) => {
            result += `**Record ${index + 1}:**\n`;
            
            // Format record data
            Object.entries(record).forEach(([key, value]) => {
                if (value !== null && value !== undefined) {
                    result += `- ${key}: ${value}\n`;
                }
            });
            
            result += '\n';
        });

        if (executionTime) {
            result += `*Query executed in ${executionTime}ms*`;
        }

        return result;
    }

    private formatErrorMessage(error: any): string {
        if (!error) {
            return 'An unknown error occurred.';
        }

        let message = `**Error:** ${error.message || 'Unknown error'}`;
        
        if (error.code) {
            message += `\n**Code:** ${error.code}`;
        }
        
        if (error.details) {
            message += `\n**Details:** ${error.details}`;
        }

        return message;
    }

    private addMessage(message: Message): void {
        const messageElement = document.createElement('div');
        messageElement.className = `message ${message.type}`;

        const contentElement = document.createElement('div');
        contentElement.className = 'message-content';

        // Format content
        if (message.content) {
            contentElement.innerHTML = this.formatContent(message.content);
        }

        // Add timestamp
        if (message.timestamp) {
            const timestampElement = document.createElement('div');
            timestampElement.className = 'message-timestamp';
            timestampElement.textContent = message.timestamp.toLocaleTimeString();
            messageElement.appendChild(timestampElement);
        }

        messageElement.appendChild(contentElement);
        this.messagesContainer.appendChild(messageElement);

        // Scroll to bottom
        this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
    }

    private formatContent(content: string): string {
        // Convert markdown-like formatting to HTML
        return content
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/\n/g, '<br>');
    }

    private clearChat(): void {
        this.messagesContainer.innerHTML = `
            <div class="message system">
                <div class="message-content">
                    Welcome to Salesforce Data Cloud Assistant! 
                    Ask me anything about your customer data.
                </div>
            </div>
        `;
    }

    private setProcessing(processing: boolean): void {
        this.isProcessing = processing;
        this.sendButton.disabled = processing;
        this.queryInput.disabled = processing;
        
        if (processing) {
            this.statusElement.textContent = 'Processing...';
            this.statusElement.className = 'status processing';
        } else {
            this.statusElement.textContent = 'Ready';
            this.statusElement.className = 'status';
        }
    }

    private sendMessageToExtension(message: any): void {
        // Send message to VS Code extension
        if (window.vscode) {
            window.vscode.postMessage(message);
        }
    }
}

// Initialize the chat interface when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new ChatInterface();
});

// Declare global vscode object for TypeScript
declare global {
    interface Window {
        vscode?: {
            postMessage(message: any): void;
        };
    }
} 