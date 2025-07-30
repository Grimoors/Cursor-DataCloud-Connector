#!/bin/bash

# Salesforce Data Cloud MCP Server Setup Script
# This script automates the initial setup process

set -e  # Exit on any error

echo "🚀 Setting up Salesforce Data Cloud MCP Server..."

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "❌ uv is not installed. Please install it first:"
    echo "   curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# Check if OpenSSL is installed
if ! command -v openssl &> /dev/null; then
    echo "❌ OpenSSL is not installed. Please install it first."
    exit 1
fi

echo "✓ Dependencies check passed"

# Create necessary directories
mkdir -p scripts

# Initialize the project with uv
echo "📦 Initializing project with uv..."
uv init --no-readme

# Install dependencies
echo "📦 Installing dependencies..."
uv add "mcp[cli]" requests pyjwt cryptography python-dotenv

# Generate SSL certificate if it doesn't exist
if [ ! -f "server.key" ]; then
    echo "🔐 Generating SSL certificate..."
    openssl genrsa -out server.key 2048
    openssl req -new -key server.key -out server.csr -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"
    openssl x509 -req -sha256 -days 365 -in server.csr -signkey server.key -out server.crt
    rm server.csr
    echo "✓ SSL certificate generated"
else
    echo "✓ SSL certificate already exists"
fi

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file..."
    cp env.example .env
    echo "✓ .env file created from template"
    echo "⚠️  Please edit .env file with your Salesforce credentials"
else
    echo "✓ .env file already exists"
fi

echo ""
echo "🎉 Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your Salesforce credentials"
echo "2. Configure your Salesforce Connected App"
echo "3. Restart Cursor to load the MCP server"
echo ""
echo "For detailed instructions, see README.md" 