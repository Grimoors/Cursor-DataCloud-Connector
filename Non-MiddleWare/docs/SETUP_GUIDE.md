# Salesforce Data Cloud MCP Server Setup Guide

This guide provides detailed step-by-step instructions for setting up the Salesforce Data Cloud MCP Server and configuring it to work with Cursor.

## Prerequisites

Before starting, ensure you have:

- Python 3.8+ installed
- `uv` package manager installed
- OpenSSL installed
- Cursor code editor installed
- Access to a Salesforce org with Data Cloud enabled

## Step 1: Project Setup

### 1.1 Clone and Initialize

```bash
git clone <repository-url>
cd Cursor-DataCloud-Connector
```

### 1.2 Run the Setup Script

```bash
./scripts/setup.sh
```

This script will:

- Check for required dependencies
- Initialize the project with `uv`
- Install Python dependencies
- Generate SSL certificates
- Create a `.env` file from template

## Step 2: Generate SSL Certificate

If the setup script didn't generate the certificate, or if you need to regenerate it:

```bash
# Create private key
openssl genrsa -out server.key 2048

# Create certificate signing request
openssl req -new -key server.key -out server.csr

# Create self-signed certificate
openssl x509 -req -sha256 -days 365 -in server.csr -signkey server.key -out server.crt

# Clean up
rm server.csr
```

## Step 3: Configure Salesforce Connected App

### 3.1 Create Connected App

1. **Navigate to Setup**

   - Log into your Salesforce org
   - Go to Setup → App Manager

2. **Create New Connected App**

   - Click "New Connected App"
   - Fill in the basic information:
     - **Connected App Name**: `Cursor MCP Assistant`
     - **API Name**: `Cursor_MCP_Assistant`
     - **Contact Email**: Your email address

3. **Enable OAuth Settings**

   - Check "Enable OAuth Settings"
   - Set **Callback URL** to: `http://localhost:1717/OauthRedirect`

4. **Configure Digital Signatures**

   - Check "Use digital signatures"
   - Click "Choose File" and upload your `server.crt` file

5. **Add OAuth Scopes**

   - In the "Selected OAuth Scopes" section, add these scopes:
     - `cdp_query_api` - Perform ANSI SQL queries on Data Cloud data
     - `api` - Manage user data via APIs
     - `refresh_token` - Perform requests at any time
     - `offline_access` - Perform requests at any time
     - `cdp_profile_api` - Manage Data Cloud profile data

6. **Save the App**
   - Click "Save"
   - Wait a few minutes for the app to become active

### 3.2 Gather Credentials

After saving the Connected App:

1. **Get Consumer Key**

   - Click "Manage Consumer Details"
   - Note the **Consumer Key** (this is your `SF_CLIENT_ID`)

2. **Note Your Username**
   - Your Salesforce username (usually your email)

## Step 4: Configure Environment Variables

Edit the `.env` file with your actual credentials:

```env
# Salesforce Connected App Consumer Key (Client ID)
SF_CLIENT_ID="YOUR_CONSUMER_KEY_HERE"

# Salesforce Username
SF_USERNAME="your.salesforce.username@example.com"

# Salesforce Login URL
# Use https://login.salesforce.com for production
# Use https://test.salesforce.com for sandbox
SF_LOGIN_URL="https://login.salesforce.com"

# Path to your private key file (relative to project root)
SF_PRIVATE_KEY_PATH="./server.key"
```

## Step 5: Test the Connection

Run the test script to verify everything is working:

```bash
python scripts/test_connection.py
```

You should see output like:

```
🧪 Testing Salesforce Data Cloud Connection
==================================================
✓ Environment variables loaded

🔐 Testing authentication...
✓ Authentication successful
  Instance URL: https://your-instance.my.salesforce.com
  Token: eyJhbGciOiJSUzI1NiIs...

🔗 Testing API connection...
✓ API connection successful
  Message: Successfully connected to Salesforce Data Cloud

📋 Testing metadata retrieval...
✓ Metadata retrieval successful
  Available objects: 15

🎉 All tests passed! Your Salesforce Data Cloud connection is working correctly.
```

## Step 6: Configure Cursor

### 6.1 Verify MCP Configuration

The `.cursor/mcp.json` file should already be created. Verify it contains:

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

### 6.2 Restart Cursor

1. Close Cursor completely
2. Reopen Cursor and navigate to this project
3. Open the chat panel (Ctrl+L)
4. Try a test query: "Test the connection to Salesforce Data Cloud"

## Step 7: Verify MCP Server Status

1. **Check MCP Settings**

   - Go to Cursor Settings → Features → Model Context Protocol
   - You should see "salesforce-data-cloud" with a green dot

2. **Check MCP Logs**
   - Open Output panel (Ctrl+Shift+U)
   - Select "MCP Logs" from the dropdown
   - Look for successful connection messages

## Troubleshooting

### Common Issues

1. **"Missing required environment variables"**

   - Check that your `.env` file exists and has all required variables
   - Ensure no extra spaces or quotes around values

2. **"Salesforce private key path not found"**

   - Verify `server.key` exists in the project root
   - Check the path in `.env` is correct

3. **"Authentication failed"**

   - Verify your Consumer Key is correct
   - Check that the Connected App is active
   - Ensure the certificate was uploaded correctly
   - Verify OAuth scopes are set correctly

4. **"HTTP Error 401"**

   - Check your username is correct
   - Verify the login URL (production vs sandbox)
   - Ensure the Connected App has the correct scopes

5. **MCP Server not showing in Cursor**
   - Restart Cursor completely
   - Check the `.cursor/mcp.json` file exists and is valid JSON
   - Verify the `cwd` path is correct

### Debug Commands

```bash
# Test authentication directly
python -c "
from dotenv import load_dotenv
from src.salesforce_mcp.auth import SalesforceAuth
load_dotenv()
auth = SalesforceAuth()
token, url = auth.get_token()
print(f'Token: {token[:50]}...')
print(f'URL: {url}')
"

# Test MCP server directly
uv run salesforce-mcp
```

## Security Best Practices

1. **Never commit sensitive files**

   - `.env` file is in `.gitignore`
   - `server.key` is in `.gitignore`
   - `server.crt` is in `.gitignore`

2. **Use least privilege**

   - Only grant the OAuth scopes you need
   - Consider using a dedicated user for the Connected App

3. **Rotate credentials regularly**
   - Regenerate SSL certificates periodically
   - Update Connected App settings as needed

## Next Steps

Once setup is complete, you can:

1. **Test basic queries**: "Show me all contacts from California"
2. **Explore metadata**: "What objects are available in Data Cloud?"
3. **Build complex queries**: "Find opportunities over $50k with contacts in the technology industry"

For more advanced usage, see the main README.md file.
