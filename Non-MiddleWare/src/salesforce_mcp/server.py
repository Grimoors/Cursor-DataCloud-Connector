"""
Salesforce Data Cloud MCP Server

Main server implementation that provides tools for querying and interacting
with Salesforce Data Cloud through the Model Context Protocol.
"""

import json
import os
from typing import Dict, Any
from dotenv import load_dotenv

from mcp.server.fastmcp import FastMCP
import requests

from .auth import SalesforceAuth

# Load environment variables
load_dotenv()

# Initialize the MCP server and the authenticator
mcp = FastMCP("Salesforce Data Cloud Server")
sf_auth = SalesforceAuth()


@mcp.tool()
def search_data_cloud(query: str) -> Dict[str, Any]:
    """
    Executes an ANSI SQL query against the Salesforce Data Cloud.
    
    Use this tool to retrieve data from Data Model Objects (DMOs).
    The query should be a valid ANSI SQL string.
    
    Args:
        query: ANSI SQL query string to execute
        
    Returns:
        Dictionary with 'success' status and 'data' or 'error'
        
    Example:
        "SELECT Id__c, Name__c FROM Contact__dlm LIMIT 10"
    """
    print(f"Executing tool 'search_data_cloud' with query: {query}")
    
    try:
        # Get valid access token
        access_token, instance_url = sf_auth.get_token()
        
        # Prepare the API request
        query_api_url = f"{instance_url}/api/v2/query"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        payload = {"sql": query}

        # Execute the query
        response = requests.post(query_api_url, headers=headers, json=payload)
        response.raise_for_status()
        
        result_data = response.json()
        print("✓ Query executed successfully.")
        
        return {
            "success": True, 
            "data": result_data,
            "query": query,
            "record_count": len(result_data.get("records", []))
        }

    except requests.exceptions.HTTPError as e:
        error_message = f"HTTP Error {e.response.status_code}: {e.response.text}"
        print(f"❌ {error_message}")
        return {
            "success": False, 
            "error": error_message,
            "query": query
        }
    except Exception as e:
        error_message = f"Unexpected error: {str(e)}"
        print(f"❌ {error_message}")
        return {
            "success": False, 
            "error": error_message,
            "query": query
        }


@mcp.tool()
def get_object_metadata(object_api_name: str) -> Dict[str, Any]:
    """
    Retrieves the metadata schema for a specific Data Cloud object (DMO or DLO).
    
    Use this to understand the available fields and their types for a given object.
    This is useful for building queries or understanding the data structure.
    
    Args:
        object_api_name: The API name of the object (e.g., "UnifiedIndividual__dlm")
        
    Returns:
        Dictionary with 'success' status and 'data' or 'error'
        
    Example:
        "UnifiedIndividual__dlm"
    """
    print(f"Executing tool 'get_object_metadata' for object: {object_api_name}")
    
    try:
        # Get valid access token
        access_token, instance_url = sf_auth.get_token()

        # Prepare the API request
        metadata_api_url = f"{instance_url}/api/v1/metadata/{object_api_name}"
        headers = {"Authorization": f"Bearer {access_token}"}

        # Retrieve metadata
        response = requests.get(metadata_api_url, headers=headers)
        response.raise_for_status()

        metadata = response.json()
        print(f"✓ Metadata retrieved successfully for {object_api_name}")
        
        return {
            "success": True, 
            "data": metadata,
            "object_name": object_api_name
        }

    except requests.exceptions.HTTPError as e:
        error_message = f"HTTP Error {e.response.status_code}: {e.response.text}"
        print(f"❌ {error_message}")
        return {
            "success": False, 
            "error": error_message,
            "object_name": object_api_name
        }
    except Exception as e:
        error_message = f"Unexpected error: {str(e)}"
        print(f"❌ {error_message}")
        return {
            "success": False, 
            "error": error_message,
            "object_name": object_api_name
        }


@mcp.tool()
def list_available_objects() -> Dict[str, Any]:
    """
    Lists available Data Model Objects (DMOs) in the Data Cloud instance.
    
    This tool helps discover what objects are available for querying.
    It's useful for understanding the data structure and available entities.
    
    Returns:
        Dictionary with 'success' status and 'data' or 'error'
    """
    print("Executing tool 'list_available_objects'")
    
    try:
        # Get valid access token
        access_token, instance_url = sf_auth.get_token()

        # Prepare the API request
        metadata_api_url = f"{instance_url}/api/v1/metadata"
        headers = {"Authorization": f"Bearer {access_token}"}

        # Retrieve available objects
        response = requests.get(metadata_api_url, headers=headers)
        response.raise_for_status()

        objects_data = response.json()
        print("✓ Available objects retrieved successfully")
        
        return {
            "success": True, 
            "data": objects_data,
            "object_count": len(objects_data.get("objects", []))
        }

    except requests.exceptions.HTTPError as e:
        error_message = f"HTTP Error {e.response.status_code}: {e.response.text}"
        print(f"❌ {error_message}")
        return {
            "success": False, 
            "error": error_message
        }
    except Exception as e:
        error_message = f"Unexpected error: {str(e)}"
        print(f"❌ {error_message}")
        return {
            "success": False, 
            "error": error_message
        }


@mcp.tool()
def test_connection() -> Dict[str, Any]:
    """
    Tests the connection to Salesforce Data Cloud.
    
    This tool verifies that authentication is working and the API is accessible.
    It's useful for debugging connection issues.
    
    Returns:
        Dictionary with 'success' status and connection details
    """
    print("Executing tool 'test_connection'")
    
    try:
        # Test authentication
        access_token, instance_url = sf_auth.get_token()
        
        # Test API connectivity with a simple metadata call
        test_url = f"{instance_url}/api/v1/metadata"
        headers = {"Authorization": f"Bearer {access_token}"}
        
        response = requests.get(test_url, headers=headers)
        response.raise_for_status()
        
        print("✓ Connection test successful")
        
        return {
            "success": True,
            "message": "Successfully connected to Salesforce Data Cloud",
            "instance_url": instance_url,
            "token_valid": True
        }

    except Exception as e:
        error_message = f"Connection test failed: {str(e)}"
        print(f"❌ {error_message}")
        return {
            "success": False,
            "error": error_message
        }


def run():
    """
    Main function to run the MCP server.
    
    Configures the server to run using stdio transport, which is
    the standard for MCP servers running as subprocesses.
    """
    print("Starting Salesforce Data Cloud MCP Server...")
    print(f"Server version: {__import__('salesforce_mcp').__version__}")
    
    # Validate environment
    required_env_vars = ["SF_CLIENT_ID", "SF_USERNAME", "SF_PRIVATE_KEY_PATH"]
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("Please check your .env file and ensure all required variables are set.")
        return
    
    print("✓ Environment validation passed")
    print("✓ Server ready to accept connections")
    
    # Run the server
    mcp.run(transport="stdio")


if __name__ == "__main__":
    run() 