# Quick Start Guide

Get your Salesforce Data Cloud MCP Server running in 10 minutes!

## Prerequisites

- Python 3.8+ with `uv` package manager
- Cursor code editor
- Salesforce org with Data Cloud enabled
- OpenSSL installed

## 1. Setup (2 minutes)

```bash
# Clone and setup
git clone <repository-url>
cd Cursor-DataCloud-Connector
./scripts/setup.sh
```

## 2. Generate SSL Certificate (1 minute)

```bash
# Generate certificate (if setup script didn't do it)
openssl genrsa -out server.key 2048
openssl req -new -key server.key -out server.csr -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"
openssl x509 -req -sha256 -days 365 -in server.csr -signkey server.key -out server.crt
rm server.csr
```

## 3. Configure Salesforce (3 minutes)

1. **Create Connected App** in Salesforce Setup → App Manager

   - Name: `Cursor MCP Assistant`
   - Enable OAuth Settings
   - Callback URL: `http://localhost:1717/OauthRedirect`
   - Upload `server.crt` for digital signatures
   - Add OAuth Scopes: `cdp_query_api`, `api`, `refresh_token`, `offline_access`, `cdp_profile_api`

2. **Get Consumer Key** from the Connected App

## 4. Configure Environment (1 minute)

Edit `.env` file:

```env
SF_CLIENT_ID="YOUR_CONSUMER_KEY"
SF_USERNAME="your.salesforce.username@example.com"
SF_LOGIN_URL="https://login.salesforce.com"
SF_PRIVATE_KEY_PATH="./server.key"
```

## 5. Test Connection (1 minute)

```bash
python scripts/test_connection.py
```

## 6. Configure Cursor (1 minute)

1. Restart Cursor
2. Open this project
3. Open chat (Ctrl+L)
4. Try: "Test the connection to Salesforce Data Cloud"

## 7. Configure AI (1 minute)

1. Go to Cursor Settings → Models
2. Create/edit your model
3. Click "Edit Prompts"
4. Paste the system prompt from `docs/SYSTEM_PROMPT.md`

## Done! 🎉

Now you can ask questions like:

- "Show me all contacts from California"
- "What objects are available in Data Cloud?"
- "Find opportunities over $50k in the technology industry"

## Troubleshooting

**Connection failed?**

- Check your `.env` file has correct credentials
- Verify Connected App is active
- Run `python scripts/test_connection.py`

**MCP Server not showing?**

- Restart Cursor completely
- Check `.cursor/mcp.json` exists
- Look at MCP Logs (Ctrl+Shift+U → MCP Logs)

**Authentication errors?**

- Verify Consumer Key is correct
- Check username and login URL
- Ensure certificate was uploaded to Connected App

## Next Steps

- Read the full [Setup Guide](docs/SETUP_GUIDE.md)
- Explore [Usage Examples](docs/USAGE_EXAMPLES.md)
- Check out [Development Guide](docs/DEVELOPMENT.md) for extending functionality

## Support

- Check the [troubleshooting section](docs/SETUP_GUIDE.md#troubleshooting)
- Review [MCP Logs](docs/SETUP_GUIDE.md#step-7-verify-mcp-server-status)
- Open an issue on GitHub

Happy querying! 🚀
