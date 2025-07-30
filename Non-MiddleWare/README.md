# Salesforce Data Cloud Assistant for Cursor

A sophisticated AI-powered assistant that integrates with Salesforce Data Cloud, providing natural language querying capabilities directly within the Cursor code editor. This project implements a custom Model Context Protocol (MCP) server that bridges the gap between Cursor's AI capabilities and Salesforce Data Cloud's powerful data platform.

## 🏗️ Architecture Overview

This system is built on a three-pillar architecture:

1. **Cursor (AI-Native Frontend)**: Provides the chat interface and manages AI agent interactions
2. **Python MCP Server (Intelligent Middleware)**: Handles authentication and business logic execution
3. **Salesforce Data Cloud (Authoritative Backend)**: The data source accessed via REST APIs

## 🚀 Features

- **Natural Language Queries**: Ask questions in plain English and get structured data back
- **ANSI SQL Support**: Leverages Data Cloud's powerful SQL query engine
- **Secure Authentication**: Implements OAuth 2.0 JWT Bearer Flow for enterprise-grade security
- **Human-in-the-Loop**: All tool calls require user approval for safety
- **Real-time Data**: Direct connection to live Salesforce Data Cloud data
- **Metadata Discovery**: Explore available objects and their schemas

## 📋 Prerequisites

- Python 3.8+ with `uv` package manager
- Salesforce org with Data Cloud enabled
- Cursor code editor
- OpenSSL (for certificate generation)

## 🛠️ Installation

### 1. Clone and Setup

```bash
git clone <repository-url>
cd Cursor-DataCloud-Connector
uv init
```

### 2. Install Dependencies

```bash
uv add "mcp[cli]" requests pyjwt cryptography python-dotenv
```

### 3. Generate SSL Certificate

```bash
# Create private key
openssl genrsa -out server.key 2048

# Create certificate signing request
openssl req -new -key server.key -out server.csr

# Create self-signed certificate
openssl x509 -req -sha256 -days 365 -in server.csr -signkey server.key -out server.crt
```

### 4. Configure Salesforce Connected App

1. In Salesforce Setup, navigate to **App Manager** → **New Connected App**
2. Fill in basic information (App Name: "Cursor MCP Assistant")
3. Enable OAuth Settings
4. Set Callback URL to `http://localhost:1717/OauthRedirect`
5. Check "Use digital signatures" and upload `server.crt`
6. Add OAuth Scopes:
   - `cdp_query_api`
   - `api`
   - `refresh_token`
   - `offline_access`
   - `cdp_profile_api`
7. Save and note the Consumer Key

### 5. Configure Environment

Create a `.env` file in the project root:

```env
SF_CLIENT_ID="YOUR_CONSUMER_KEY"
SF_USERNAME="your.salesforce.username@example.com"
SF_LOGIN_URL="https://login.salesforce.com"
SF_PRIVATE_KEY_PATH="./server.key"
```

### 6. Configure Cursor

Create `.cursor/mcp.json` in your project:

```json
{
  "mcpServers": {
    "salesforce-data-cloud": {
      "command": "uv",
      "args": ["run", "salesforce-mcp"],
      "env": {
        "SF_CLIENT_ID": "${env:SF_CLIENT_ID}",
        "SF_USERNAME": "${env:SF_USERNAME}",
        "SF_LOGIN_URL": "${env:SF_LOGIN_URL}",
        "SF_PRIVATE_KEY_PATH": "${env:SF_PRIVATE_KEY_PATH}"
      },
      "cwd": "${workspaceFolder}"
    }
  }
}
```

## 🎯 Usage

### Basic Query Example

1. Open Cursor and navigate to this project
2. Open the chat panel (Ctrl+L)
3. Ask a question like: "Show me all contacts from California with opportunities over $50,000"
4. The AI will generate an SQL query and request approval
5. Approve the tool call to execute the query
6. View the formatted results in the chat

### Available Tools

- **search_data_cloud**: Execute ANSI SQL queries against Data Cloud
- **get_object_metadata**: Retrieve schema information for Data Model Objects

## 🔧 Development

### Project Structure

```
Cursor-DataCloud-Connector/
├── .cursor/
│   └── mcp.json              # Cursor MCP configuration
├── src/
│   └── salesforce_mcp/
│       ├── __init__.py
│       ├── auth.py           # Authentication module
│       └── server.py         # Main MCP server
├── .env                      # Environment variables
├── server.key               # Private key (DO NOT COMMIT)
├── server.crt               # Certificate
├── pyproject.toml          # Project configuration
└── README.md               # This file
```

### Running the Server

```bash
# Development
uv run salesforce-mcp

# Or directly
python -m salesforce_mcp.server
```

### Debugging

- Check Cursor's MCP Logs (Ctrl+Shift+U → MCP Logs)
- Verify server status in Settings → Features → Model Context Protocol
- Monitor authentication flow in server logs

## 🔒 Security Considerations

- **Private Key**: Never commit `server.key` to version control
- **Environment Variables**: Use `.env` for sensitive configuration
- **OAuth Scopes**: Follow principle of least privilege
- **Human-in-the-Loop**: All tool calls require user approval

## 🚀 Future Enhancements

- [ ] CRUD operations via Data Cloud Connect APIs
- [ ] Multi-step agentic workflows
- [ ] Integration with other enterprise APIs
- [ ] Advanced caching strategies
- [ ] Team distribution packaging

## 📚 Resources

- [Model Context Protocol Documentation](https://modelcontextprotocol.io/)
- [Salesforce Data Cloud API Guide](https://developer.salesforce.com/docs/data/data-cloud-ref/)
- [Cursor Documentation](https://docs.cursor.com/)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.
