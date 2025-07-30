"""
OAuth authentication module for Salesforce Data Cloud.

This module handles the OAuth 2.0 JWT Bearer flow for authenticating
with Salesforce and managing access tokens.
"""

import datetime
import time
from typing import Dict, Optional, Tuple

import httpx
import structlog
from pydantic import BaseModel

from src.auth.jwt import get_jwt_authenticator
from src.config.settings import get_settings
from src.utils.logging import get_logger

logger = get_logger(__name__)


class TokenResponse(BaseModel):
    """Response model for OAuth token requests."""
    
    access_token: str
    token_type: str
    expires_in: int
    refresh_token: Optional[str] = None
    scope: Optional[str] = None
    instance_url: Optional[str] = None
    id: Optional[str] = None


class SalesforceAuthenticator:
    """
    Salesforce OAuth authenticator for Data Cloud integration.
    
    This class handles the OAuth 2.0 JWT Bearer flow for authenticating
    with Salesforce and managing access tokens for Data Cloud APIs.
    """
    
    def __init__(self):
        """Initialize the Salesforce authenticator."""
        self.settings = get_settings()
        self.jwt_authenticator = get_jwt_authenticator()
        self._platform_token: Optional[TokenResponse] = None
        self._data_cloud_token: Optional[TokenResponse] = None
        self._last_token_refresh: Optional[datetime.datetime] = None
    
    async def get_platform_access_token(self) -> str:
        """
        Get a Salesforce platform access token using JWT Bearer flow.
        
        Returns:
            str: The platform access token
            
        Raises:
            ValueError: If authentication fails
        """
        # Check if we have a valid cached token
        if self._platform_token and not self._should_refresh_token(self._platform_token):
            logger.debug("Using cached platform access token")
            return self._platform_token.access_token
        
        try:
            # Create JWT assertion
            jwt_assertion = self.jwt_authenticator.create_jwt_assertion()
            
            # Prepare token request
            token_url = f"{self.settings.salesforce_instance_url}/services/oauth2/token"
            token_data = {
                'grant_type': 'urn:ietf:params:oauth:grant-type:jwt-bearer',
                'assertion': jwt_assertion
            }
            
            logger.info("Requesting Salesforce platform access token",
                       token_url=token_url,
                       grant_type=token_data['grant_type'])
            
            # Make token request
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(token_url, data=token_data)
                
                if response.status_code != 200:
                    logger.error("Failed to get platform access token",
                               status_code=response.status_code,
                               response_text=response.text)
                    raise ValueError(f"Token request failed: {response.status_code}")
                
                # Parse response
                token_data = response.json()
                self._platform_token = TokenResponse(**token_data)
                self._last_token_refresh = datetime.datetime.now(datetime.timezone.utc)
                
                logger.info("Successfully obtained platform access token",
                           expires_in=self._platform_token.expires_in,
                           instance_url=self._platform_token.instance_url)
                
                return self._platform_token.access_token
                
        except Exception as e:
            logger.error("Failed to get platform access token", error=str(e))
            raise ValueError(f"Platform authentication failed: {str(e)}")
    
    async def get_data_cloud_access_token(self, dataspace: Optional[str] = None) -> str:
        """
        Get a Data Cloud access token by exchanging the platform token.
        
        Args:
            dataspace: The Data Cloud dataspace to access (optional)
            
        Returns:
            str: The Data Cloud access token
            
        Raises:
            ValueError: If token exchange fails
        """
        # Check if we have a valid cached token
        if self._data_cloud_token and not self._should_refresh_token(self._data_cloud_token):
            logger.debug("Using cached Data Cloud access token")
            return self._data_cloud_token.access_token
        
        try:
            # Get platform token first
            platform_token = await self.get_platform_access_token()
            
            # Prepare token exchange request
            if self._platform_token and self._platform_token.instance_url:
                instance_url = self._platform_token.instance_url
            else:
                instance_url = self.settings.salesforce_instance_url
            
            exchange_url = f"{instance_url}/services/oauth2/token"
            exchange_data = {
                'grant_type': 'urn:ietf:params:oauth:grant-type:jwt-bearer',
                'assertion': platform_token
            }
            
            # Add dataspace if specified
            if dataspace:
                exchange_data['dataspace'] = dataspace
            elif self.settings.data_cloud_dataspace:
                exchange_data['dataspace'] = self.settings.data_cloud_dataspace
            
            logger.info("Exchanging platform token for Data Cloud access token",
                       exchange_url=exchange_url,
                       dataspace=exchange_data.get('dataspace'))
            
            # Make token exchange request
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(exchange_url, data=exchange_data)
                
                if response.status_code != 200:
                    logger.error("Failed to exchange token for Data Cloud access",
                               status_code=response.status_code,
                               response_text=response.text)
                    raise ValueError(f"Token exchange failed: {response.status_code}")
                
                # Parse response
                token_data = response.json()
                self._data_cloud_token = TokenResponse(**token_data)
                self._last_token_refresh = datetime.datetime.now(datetime.timezone.utc)
                
                logger.info("Successfully obtained Data Cloud access token",
                           expires_in=self._data_cloud_token.expires_in)
                
                return self._data_cloud_token.access_token
                
        except Exception as e:
            logger.error("Failed to get Data Cloud access token", error=str(e))
            raise ValueError(f"Data Cloud authentication failed: {str(e)}")
    
    def _should_refresh_token(self, token_response: TokenResponse) -> bool:
        """
        Check if a token should be refreshed.
        
        Args:
            token_response: The token response to check
            
        Returns:
            bool: True if the token should be refreshed
        """
        if not token_response or not self._last_token_refresh:
            return True
        
        # Check if token is close to expiring
        time_since_refresh = datetime.datetime.now(datetime.timezone.utc) - self._last_token_refresh
        threshold_seconds = self.settings.token_refresh_threshold_minutes * 60
        
        return time_since_refresh.total_seconds() >= (token_response.expires_in - threshold_seconds)
    
    async def get_valid_access_token(self, for_data_cloud: bool = True) -> str:
        """
        Get a valid access token for the specified service.
        
        Args:
            for_data_cloud: Whether to get a Data Cloud token (True) or platform token (False)
            
        Returns:
            str: The valid access token
        """
        if for_data_cloud:
            return await self.get_data_cloud_access_token()
        else:
            return await self.get_platform_access_token()
    
    def clear_cached_tokens(self) -> None:
        """Clear all cached tokens."""
        self._platform_token = None
        self._data_cloud_token = None
        self._last_token_refresh = None
        logger.info("Cleared cached authentication tokens")
    
    def get_token_info(self) -> Dict:
        """
        Get information about the current tokens.
        
        Returns:
            Dict: Token information
        """
        info = {
            'platform_token': {
                'has_token': self._platform_token is not None,
                'expires_in': self._platform_token.expires_in if self._platform_token else None,
                'last_refresh': self._last_token_refresh.isoformat() if self._last_token_refresh else None,
            },
            'data_cloud_token': {
                'has_token': self._data_cloud_token is not None,
                'expires_in': self._data_cloud_token.expires_in if self._data_cloud_token else None,
            }
        }
        
        return info


# Global authenticator instance
_authenticator: Optional[SalesforceAuthenticator] = None


def get_salesforce_authenticator() -> SalesforceAuthenticator:
    """
    Get the global Salesforce authenticator instance.
    
    Returns:
        SalesforceAuthenticator: The authenticator instance
    """
    global _authenticator
    if _authenticator is None:
        _authenticator = SalesforceAuthenticator()
    return _authenticator


async def authenticate_with_salesforce() -> str:
    """
    Authenticate with Salesforce and get a Data Cloud access token.
    
    Returns:
        str: The Data Cloud access token
        
    Raises:
        ValueError: If authentication fails
    """
    authenticator = get_salesforce_authenticator()
    return await authenticator.get_data_cloud_access_token()


async def get_salesforce_headers(for_data_cloud: bool = True) -> Dict[str, str]:
    """
    Get HTTP headers for Salesforce API requests.
    
    Args:
        for_data_cloud: Whether to get headers for Data Cloud (True) or platform (False)
        
    Returns:
        Dict[str, str]: Headers for API requests
    """
    authenticator = get_salesforce_authenticator()
    access_token = await authenticator.get_valid_access_token(for_data_cloud)
    
    return {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    } 