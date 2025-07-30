# Setup Instructions

This guide provides step-by-step instructions for setting up the Salesforce Data Cloud-Integrated IDE Assistant, including both the middleware server and the VS Code/Cursor extension.

## Prerequisites

Before beginning the setup, ensure you have the following:

- **Python 3.8+** installed on your system
- **Node.js 16+** installed on your system
- **VS Code** or **Cursor** IDE
- **Salesforce Data Cloud** instance with API access
- **Salesforce Connected App** configured (see Salesforce Setup section)

## Step 1: Salesforce Setup

### 1.1 Create a Connected App

1. **Log into Salesforce Setup**

   - Navigate to your Salesforce instance
   - Go to Setup → App Manager

2. **Create New Connected App**

   - Click "New Connected App"
   - Fill in the basic information:
     - **Connected App Name**: `Data Cloud IDE Assistant`
     - **API Name**: `Data_Cloud_IDE_Assistant`
     - **Contact Email**: Your email address

3. **Enable OAuth Settings**

   - Check "Enable OAuth Settings"
   - Set **Callback URL**: `https://login.salesforce.com/services/oauth2/success`
   - Select the following **OAuth Scopes**:
     - `Manage user data via APIs (api)`
     - `Perform requests at any time (refresh_token, offline_access)`
     - `Perform ANSI SQL queries on Data Cloud data (cdp_query_api)`
     - `Manage Data Cloud profile data (cdp_profile_api)`

4. **Configure Digital Signatures**

   - Check "Use digital signatures"
   - Generate a certificate and key pair (see Certificate Generation section)
   - Upload the public certificate (.crt file)

5. **Save and Retrieve Credentials**
   - Save the Connected App
   - Note down the **Consumer Key** (Client ID)
   - Store the private key securely

### 1.2 Generate Certificate and Key Pair

#### Option A: Using OpenSSL (Recommended)

```bash
# Generate private key
openssl genrsa -out server.key 2048

# Generate certificate signing request
openssl req -new -key server.key -out server.csr -subj "/C=US/ST=State/L=City/O=Organization/CN=DataCloudIDE"

# Generate self-signed certificate (valid for 1 year)
openssl x509 -req -days 365 -in server.csr -signkey server.key -out server.crt

# Clean up CSR file
rm server.csr
```

#### Option B: Using Online Tools

1. Visit a certificate generation service
2. Generate a 2048-bit RSA key pair
3. Download both the private key (.key) and certificate (.crt) files

### 1.3 Data Cloud Configuration

1. **Identify Your Data Cloud Instance**

   - Note your Data Cloud dataspace name
   - Verify API access permissions

2. **Test API Access**
   - Use Salesforce Workbench or Postman to test Data Cloud API access
   - Ensure your user has the necessary permissions

## Step 2: Middleware Setup

### 2.1 Clone and Navigate

```bash
# Clone the repository (if not already done)
git clone <repository-url>
cd With-Middleware
```

### 2.2 Python Environment Setup

```bash
# Navigate to middleware directory
cd middleware

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2.3 Configuration Setup

```bash
# Copy example configuration
cp config/example.env config/.env

# Edit the configuration file
# On Windows:
notepad config\.env
# On macOS/Linux:
nano config/.env
```

### 2.4 Update Configuration

Edit `config/.env` with your actual values:

```env
# Required: Update these with your actual values
SALESFORCE_USERNAME=your_actual_username@yourdomain.com
SALESFORCE_CONSUMER_KEY=your_actual_consumer_key
SALESFORCE_PRIVATE_KEY_PATH=config/server.key
DATA_CLOUD_DATASPACE=your_actual_dataspace_name

# Optional: Generate a secure API key
ALLOWED_API_KEYS=your_secure_api_key_here
```

### 2.5 Place Certificate Files

```bash
# Copy your certificate files to the config directory
cp /path/to/your/server.key config/
cp /path/to/your/server.crt config/

# Set proper permissions (on macOS/Linux)
chmod 600 config/server.key
chmod 644 config/server.crt
```

### 2.6 Test Middleware

```bash
# Start the middleware server
python -m src.main

# In another terminal, test the health endpoint
curl http://localhost:8000/health
```

Expected response:

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "environment": "development"
}
```

## Step 3: Extension Setup

### 3.1 Install Dependencies

```bash
# Navigate to extension directory
cd ../extension

# Install Node.js dependencies
npm install
```

### 3.2 Build Extension

```bash
# Compile TypeScript
npm run compile

# Build webview assets
npm run build:webview
```

### 3.3 Install Extension in VS Code

1. **Open VS Code**
2. **Open Command Palette** (`Ctrl+Shift+P` or `Cmd+Shift+P`)
3. **Type**: "Extensions: Install from VSIX"
4. **Select**: The generated `.vsix` file from the extension directory

### 3.4 Configure Extension

1. **Open VS Code Settings** (`Ctrl+,` or `Cmd+,`)
2. **Search for**: "Salesforce Data Cloud"
3. **Configure**:
   - **Middleware URL**: `http://localhost:8000`
   - **API Key**: Your secure API key
   - **Enable Debug**: `false` (set to `true` for troubleshooting)

## Step 4: MCP Setup (Cursor Only)

### 4.1 Create MCP Configuration

Create `.cursor/mcp.json` in your project root:

```json
{
  "mcpServers": {
    "salesforce-data-tools": {
      "command": "python",
      "args": ["-m", "src.mcp.server"],
      "env": {
        "SALESFORCE_USERNAME": "${env:SF_USER}",
        "SALESFORCE_CONSUMER_KEY": "${env:SF_CONSUMER_KEY}",
        "SALESFORCE_PRIVATE_KEY_PATH": "${workspaceFolder}/middleware/config/server.key",
        "DATA_CLOUD_DATASPACE": "${env:DATA_CLOUD_DATASPACE}"
      }
    }
  }
}
```

### 4.2 Set Environment Variables

```bash
# Set environment variables for MCP
export SF_USER=your_username@yourdomain.com
export SF_CONSUMER_KEY=your_consumer_key
export DATA_CLOUD_DATASPACE=your_dataspace_name
```

## Step 5: Verification

### 5.1 Test REST API

```bash
# Test query endpoint
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your_api_key" \
  -d '{
    "query": "Show me recent cases for user@example.com",
    "query_type": "natural_language"
  }'
```

### 5.2 Test VS Code Extension

1. **Open VS Code**
2. **Click the Salesforce Data Cloud icon** in the Activity Bar
3. **Type a test query**: "Show me user profile for user@example.com"
4. **Verify response** appears in the chat interface

### 5.3 Test MCP (Cursor)

1. **Open Cursor**
2. **Open Chat** (`Ctrl+L`)
3. **Type**: "@SalesforceTools get user profile for user@example.com"
4. **Verify tool execution** and response

## Troubleshooting

### Common Issues

#### 1. Authentication Errors

**Symptoms**: 401/403 errors, "Invalid JWT" messages

**Solutions**:

- Verify certificate files are in the correct location
- Check certificate permissions (600 for private key)
- Ensure Consumer Key matches Connected App
- Verify username is correct

#### 2. Data Cloud Access Errors

**Symptoms**: "Data Cloud not found" or "Permission denied"

**Solutions**:

- Verify Data Cloud dataspace name
- Check user permissions in Data Cloud
- Ensure Connected App has correct OAuth scopes
- Test API access directly in Salesforce

#### 3. Extension Connection Issues

**Symptoms**: "Failed to communicate with middleware"

**Solutions**:

- Verify middleware is running on correct port
- Check API key configuration
- Ensure CORS settings allow VS Code origin
- Check firewall settings

#### 4. MCP Tool Errors

**Symptoms**: Tools not appearing or failing to execute

**Solutions**:

- Verify MCP configuration file location
- Check environment variables are set
- Ensure Python path is correct
- Test MCP server independently

### Debug Mode

Enable debug logging:

```bash
# Middleware debug
LOG_LEVEL=DEBUG python -m src.main

# Extension debug
# Set "salesforceDataCloud.enableDebug": true in VS Code settings
```

### Logs

Check logs for detailed error information:

- **Middleware logs**: Printed to console when running
- **Extension logs**: View in VS Code Output panel (Salesforce Data Cloud Assistant)
- **MCP logs**: Printed to console when tools are executed

## Security Considerations

### 1. Certificate Security

- Store private keys securely
- Use file permissions (600) for private keys
- Rotate certificates regularly
- Never commit certificates to version control

### 2. API Key Security

- Use strong, unique API keys
- Rotate keys regularly
- Store keys in secure credential managers
- Use environment variables in production

### 3. Network Security

- Use HTTPS in production
- Configure firewalls appropriately
- Implement rate limiting
- Monitor access logs

## Production Deployment

### 1. Environment Configuration

```env
ENVIRONMENT=production
DEBUG=false
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=INFO
ENABLE_DOCS=false
```

### 2. Process Management

Use a process manager like `systemd` or `supervisord`:

```ini
[program:salesforce-middleware]
command=/path/to/venv/bin/python -m src.main
directory=/path/to/middleware
user=www-data
autostart=true
autorestart=true
```

### 3. Reverse Proxy

Configure nginx or Apache as a reverse proxy:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 4. SSL/TLS

- Obtain SSL certificates (Let's Encrypt recommended)
- Configure HTTPS in reverse proxy
- Update extension configuration to use HTTPS

## Support

For additional help:

1. **Check the logs** for detailed error messages
2. **Review the architecture documentation** for system understanding
3. **Test individual components** to isolate issues
4. **Create an issue** in the repository with detailed information

Remember to never share sensitive information like private keys or API keys when seeking support.
