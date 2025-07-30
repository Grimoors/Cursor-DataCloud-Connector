#!/usr/bin/env python3
"""
Test script for Salesforce Data Cloud MCP Server

This script tests the connection to Salesforce Data Cloud and verifies
that authentication and basic API calls are working correctly.
"""

import os
import sys
from dotenv import load_dotenv

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from salesforce_mcp.auth import SalesforceAuth
from salesforce_mcp.server import test_connection, list_available_objects

def main():
    """Main test function."""
    print("🧪 Testing Salesforce Data Cloud Connection")
    print("=" * 50)
    
    # Load environment variables
    load_dotenv()
    
    # Check required environment variables
    required_vars = ["SF_CLIENT_ID", "SF_USERNAME", "SF_PRIVATE_KEY_PATH"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("Please check your .env file and ensure all required variables are set.")
        return False
    
    print("✓ Environment variables loaded")
    
    try:
        # Test authentication
        print("\n🔐 Testing authentication...")
        auth = SalesforceAuth()
        access_token, instance_url = auth.get_token()
        print(f"✓ Authentication successful")
        print(f"  Instance URL: {instance_url}")
        print(f"  Token: {access_token[:20]}...")
        
        # Test connection
        print("\n🔗 Testing API connection...")
        result = test_connection()
        if result["success"]:
            print("✓ API connection successful")
            print(f"  Message: {result['message']}")
        else:
            print(f"❌ API connection failed: {result['error']}")
            return False
        
        # Test metadata retrieval
        print("\n📋 Testing metadata retrieval...")
        result = list_available_objects()
        if result["success"]:
            print("✓ Metadata retrieval successful")
            print(f"  Available objects: {result['object_count']}")
        else:
            print(f"❌ Metadata retrieval failed: {result['error']}")
            return False
        
        print("\n🎉 All tests passed! Your Salesforce Data Cloud connection is working correctly.")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 