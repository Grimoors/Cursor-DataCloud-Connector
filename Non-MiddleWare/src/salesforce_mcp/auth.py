"""
Salesforce Data Cloud Authentication Module

Handles the complex OAuth 2.0 JWT Bearer Flow required for authenticating
with Salesforce Data Cloud APIs. This module encapsulates the two-step token
exchange process and provides caching for performance.
"""

import os
import time
import jwt
import requests
from datetime import datetime, timedelta, timezone
from typing import Tuple, Optional


class SalesforceAuth:
    """
    Handles the complex OAuth 2.0 JWT Bearer Flow for Salesforce Data Cloud.
    
    This class manages the two-step authentication process:
    1. JWT for Salesforce Token: Creates and exchanges a signed JWT for a Salesforce access token
    2. Salesforce Token for Data Cloud Token: Exchanges the Salesforce token for a Data Cloud token
    
    The class also handles token caching and automatic renewal.
    """
    
    def __init__(self):
        """Initialize the authentication handler with configuration from environment."""
        self.client_id = os.getenv("SF_CLIENT_ID")
        if not self.client_id:
            raise ValueError("SF_CLIENT_ID environment variable is required")
            
        self.username = os.getenv("SF_USERNAME")
        if not self.username:
            raise ValueError("SF_USERNAME environment variable is required")
            
        self.login_url = os.getenv("SF_LOGIN_URL", "https://login.salesforce.com")
        
        # Load private key for JWT signing
        private_key_path = os.getenv("SF_PRIVATE_KEY_PATH")
        if not private_key_path or not os.path.exists(private_key_path):
            raise ValueError(
                f"Salesforce private key path not found or not set in .env: {private_key_path}"
            )
        
        with open(private_key_path, "r") as f:
            self.private_key = f.read()

        # Token caching
        self._dc_token: Optional[str] = None
        self._dc_token_expiry: Optional[datetime] = None
        self._dc_instance_url: Optional[str] = None

    def _create_jwt(self) -> str:
        """
        Creates a signed JWT for Salesforce authentication.
        
        Returns:
            str: The signed JWT token
        """
        payload = {
            "iss": self.client_id,  # Issuer (Consumer Key)
            "sub": self.username,    # Subject (Username)
            "aud": self.login_url,   # Audience (Login URL)
            "exp": int(time.time()) + 180,  # Expiry (3 minutes)
        }
        return jwt.encode(payload, self.private_key, algorithm="RS256")

    def _get_sf_access_token(self) -> dict:
        """
        First step: Exchanges the JWT for a Salesforce access token.
        
        Returns:
            dict: The Salesforce token response containing access_token and instance_url
            
        Raises:
            requests.exceptions.HTTPError: If the token exchange fails
        """
        assertion = self._create_jwt()
        token_url = f"{self.login_url}/services/oauth2/token"
        
        data = {
            "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
            "assertion": assertion
        }
        
        response = requests.post(token_url, data=data)
        response.raise_for_status()
        return response.json()

    def _exchange_for_dc_token(self, sf_token_response: dict) -> dict:
        """
        Second step: Exchanges the Salesforce token for a Data Cloud token.
        
        Args:
            sf_token_response: The response from the first token exchange
            
        Returns:
            dict: The Data Cloud token response
            
        Raises:
            requests.exceptions.HTTPError: If the token exchange fails
        """
        sf_access_token = sf_token_response["access_token"]
        sf_instance_url = sf_token_response["instance_url"]
        
        exchange_url = f"{sf_instance_url}/services/v1/token-exchange"
        headers = {"Authorization": f"Bearer {sf_access_token}"}
        
        # For Data Spaces, you would add 'dataspace': 'your_space_name' to the payload
        # See: https://help.salesforce.com/s/articleView?id=sf.c360_a_using_data_cloud_apis_with_data_spaces.htm
        payload = {}
        
        response = requests.post(exchange_url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()

    def get_token(self) -> Tuple[str, str]:
        """
        Public method to get a valid Data Cloud token.
        
        Handles caching and refreshing automatically. If a valid cached token
        exists, it returns that. Otherwise, it performs the full authentication
        flow and caches the result.
        
        Returns:
            Tuple[str, str]: (access_token, instance_url)
            
        Raises:
            Exception: If authentication fails at any step
        """
        # Check if we have a valid cached token
        if (self._dc_token and self._dc_token_expiry and 
            datetime.now(timezone.utc) < self._dc_token_expiry):
            print("Using cached Data Cloud token.")
            return self._dc_token, self._dc_instance_url

        print("No valid cached token. Authenticating with Salesforce...")
        
        try:
            # Step 1: Get Salesforce access token
            sf_token_data = self._get_sf_access_token()
            print("✓ Obtained Salesforce access token")
            
            # Step 2: Exchange for Data Cloud token
            dc_token_data = self._exchange_for_dc_token(sf_token_data)
            print("✓ Exchanged for Data Cloud access token")
            
            # Cache the results
            self._dc_token = dc_token_data["access_token"]
            self._dc_instance_url = dc_token_data["instance_url"]
            
            # Set expiry to 1 minute before actual expiry for safety buffer
            expiry_seconds = int(dc_token_data.get("expires_in", 3600))
            self._dc_token_expiry = datetime.now(timezone.utc) + timedelta(seconds=expiry_seconds - 60)
            
            print("Successfully authenticated and cached Data Cloud token.")
            return self._dc_token, self._dc_instance_url
            
        except requests.exceptions.HTTPError as e:
            error_msg = f"Authentication failed: {e.response.status_code} - {e.response.text}"
            print(f"❌ {error_msg}")
            raise Exception(error_msg) from e
        except Exception as e:
            error_msg = f"Unexpected authentication error: {str(e)}"
            print(f"❌ {error_msg}")
            raise Exception(error_msg) from e

    def clear_cache(self):
        """Clear the cached tokens, forcing a fresh authentication on next request."""
        self._dc_token = None
        self._dc_token_expiry = None
        self._dc_instance_url = None
        print("Cleared cached authentication tokens.") 