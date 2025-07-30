# Salesforce Data Cloud-Integrated IDE Assistant

A comprehensive Visual Studio Code and Cursor extension that provides developers with seamless access to enriched Salesforce Data Cloud data directly within their IDE. This system implements both a standard REST API architecture and an advanced Model Context Protocol (MCP) architecture for intelligent, agentic workflows.

## 🏗️ Architecture Overview

This system follows a three-tier architecture designed for security, scalability, and maintainability:

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   IDE Extension │◄──►│  Middleware API  │◄──►│ Salesforce Data │
│   (VS Code/     │    │   (Python/FastAPI│    │     Cloud       │
│    Cursor)      │    │    or MCP Server)│    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### Components

1. **IDE Extension**: TypeScript-based VS Code/Cursor extension with React UI
2. **Middleware API**: Python backend handling authentication and data enrichment
3. **Salesforce Data Cloud**: Authoritative data source (read-only access)

## 🚀 Features

### Standard REST API Architecture

- Secure OAuth 2.0 JWT Bearer authentication with Salesforce
- Custom sidebar with React-based chat interface
- Real-time data querying and enrichment
- Secure credential management using VS Code SecretStorage

### Advanced MCP Architecture

- Model Context Protocol server integration
- AI agent-driven workflows in Cursor
- Natural language query processing
- Tool-based data access patterns

## 📁 Project Structure

```
With-Middleware/
├── README.md                           # This file
├── docs/                              # Comprehensive documentation
│   ├── architecture.md                # Detailed architecture guide
│   ├── setup.md                       # Setup instructions
│   ├── api-reference.md               # API documentation
│   └── mcp-guide.md                   # MCP implementation guide
├── extension/                         # VS Code/Cursor Extension
│   ├── src/
│   │   ├── extension.ts              # Main extension logic
│   │   ├── webview/                  # React webview components
│   │   └── types/                    # TypeScript type definitions
│   ├── package.json                  # Extension manifest
│   └── webpack.config.js             # Build configuration
├── middleware/                        # Python Backend
│   ├── src/
│   │   ├── api/                      # REST API implementation
│   │   ├── mcp/                      # MCP server implementation
│   │   ├── auth/                     # Authentication logic
│   │   ├── models/                   # Data models
│   │   └── utils/                    # Utility functions
│   ├── requirements.txt              # Python dependencies
│   ├── config/                       # Configuration files
│   └── tests/                        # Test suite
├── examples/                         # Usage examples
└── scripts/                          # Development scripts
```

## 🛠️ Quick Start

### Prerequisites

- Python 3.8+
- Node.js 16+
- VS Code or Cursor IDE
- Salesforce Data Cloud instance
- Salesforce Connected App configured

### Installation

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd With-Middleware
   ```

2. **Setup the Middleware**

   ```bash
   cd middleware
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Configure Salesforce Authentication**

   ```bash
   cp config/example.env config/.env
   # Edit config/.env with your Salesforce credentials
   ```

4. **Install the Extension**

   ```bash
   cd ../extension
   npm install
   npm run compile
   ```

5. **Start the Middleware Server**

   ```bash
   cd ../middleware
   python -m src.main
   ```

6. **Install Extension in VS Code**
   - Open VS Code
   - Press `Ctrl+Shift+P` (or `Cmd+Shift+P` on Mac)
   - Type "Extensions: Install from VSIX"
   - Select the generated `.vsix` file

## 🔧 Configuration

### Salesforce Connected App Setup

1. Navigate to Salesforce Setup → App Manager
2. Create a new Connected App
3. Enable OAuth Settings
4. Upload your public certificate
5. Set required OAuth scopes:
   - `api` (Manage user data via APIs)
   - `refresh_token` (Perform requests at any time)
   - `offline_access` (Perform requests at any time)
   - `cdp_query_api` (Perform ANSI SQL queries on Data Cloud data)
   - `cdp_profile_api` (Manage Data Cloud profile data)

### Environment Variables

Create `middleware/config/.env`:

```env
# Salesforce Configuration
SALESFORCE_USERNAME=your_username@yourdomain.com
SALESFORCE_CONSUMER_KEY=your_connected_app_consumer_key
SALESFORCE_PRIVATE_KEY_PATH=config/server.key
SALESFORCE_INSTANCE_URL=https://login.salesforce.com

# Middleware Configuration
MIDDLEWARE_API_KEY=your_secure_api_key
MIDDLEWARE_HOST=localhost
MIDDLEWARE_PORT=8000

# Data Cloud Configuration
DATA_CLOUD_DATASPACE=your_dataspace_name
```

## 📖 Usage

### Standard REST API Mode

1. Open VS Code/Cursor
2. Click the Salesforce Data Cloud icon in the Activity Bar
3. Type your query in the chat interface
4. View enriched data results

### MCP Mode (Cursor Only)

1. Configure MCP server in `.cursor/mcp.json`
2. Open Cursor chat (`Ctrl+L`)
3. Use natural language queries like:
   - "Show me recent cases for user@example.com"
   - "What's the loyalty status for customer@domain.com"

## 🔒 Security Features

- OAuth 2.0 JWT Bearer authentication
- Secure credential storage using VS Code SecretStorage
- Input sanitization and validation
- Content Security Policy (CSP) for webviews
- Rate limiting and API quota management

## 🧪 Testing

```bash
# Run middleware tests
cd middleware
python -m pytest tests/

# Run extension tests
cd extension
npm test
```

## 📚 Documentation

- [Architecture Guide](docs/architecture.md) - Detailed system design
- [Setup Instructions](docs/setup.md) - Step-by-step installation
- [API Reference](docs/api-reference.md) - REST API documentation
- [MCP Guide](docs/mcp-guide.md) - Model Context Protocol implementation

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For issues and questions:

- Check the [documentation](docs/)
- Review [common issues](docs/troubleshooting.md)
- Create an issue in the repository

---

**Note**: This implementation provides both standard REST API functionality and advanced MCP integration, allowing developers to choose the architecture that best fits their workflow and requirements.
