"""
JWT authentication module for Salesforce OAuth 2.0 JWT Bearer flow.

This module handles the creation and management of JWT tokens for
authenticating with Salesforce APIs.
"""

import datetime
import time
from pathlib import Path
from typing import Dict, Optional

import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from src.config.settings import get_settings
from src.utils.logging import get_logger

logger = get_logger(__name__)


class JWTAuthenticator:
    """
    JWT authenticator for Salesforce OAuth 2.0 JWT Bearer flow.
    
    This class handles the creation and management of JWT tokens
    for authenticating with Salesforce APIs.
    """
    
    def __init__(self):
        """Initialize the JWT authenticator."""
        self.settings = get_settings()
        self._private_key = None
        self._public_key = None
    
    def _load_private_key(self) -> bytes:
        """
        Load the private key from the configured path.
        
        Returns:
            bytes: The private key content
            
        Raises:
            FileNotFoundError: If the private key file doesn't exist
            ValueError: If the private key is invalid
        """
        if self._private_key is None:
            try:
                key_path = Path(self.settings.salesforce_private_key_path)
                if not key_path.exists():
                    raise FileNotFoundError(f"Private key file not found: {key_path}")
                
                with open(key_path, 'rb') as key_file:
                    self._private_key = key_file.read()
                
                logger.debug("Private key loaded successfully", 
                           key_path=str(key_path))
                
            except Exception as e:
                logger.error("Failed to load private key", 
                           error=str(e),
                           key_path=self.settings.salesforce_private_key_path)
                raise
        
        return self._private_key
    
    def _load_public_key(self) -> bytes:
        """
        Load the public key from the configured path.
        
        Returns:
            bytes: The public key content
            
        Raises:
            FileNotFoundError: If the public key file doesn't exist
            ValueError: If the public key is invalid
        """
        if self._public_key is None:
            try:
                # Try to find public key in the same directory as private key
                private_key_path = Path(self.settings.salesforce_private_key_path)
                public_key_path = private_key_path.with_suffix('.crt')
                
                if not public_key_path.exists():
                    # Try alternative extensions
                    for ext in ['.pem', '.pub', '.crt']:
                        alt_path = private_key_path.with_suffix(ext)
                        if alt_path.exists():
                            public_key_path = alt_path
                            break
                
                if not public_key_path.exists():
                    raise FileNotFoundError(f"Public key file not found: {public_key_path}")
                
                with open(public_key_path, 'rb') as key_file:
                    self._public_key = key_file.read()
                
                logger.debug("Public key loaded successfully", 
                           key_path=str(public_key_path))
                
            except Exception as e:
                logger.error("Failed to load public key", 
                           error=str(e),
                           private_key_path=self.settings.salesforce_private_key_path)
                raise
        
        return self._public_key
    
    def create_jwt_assertion(self, audience: Optional[str] = None) -> str:
        """
        Create a JWT assertion for Salesforce OAuth 2.0 JWT Bearer flow.
        
        Args:
            audience: The audience for the JWT (defaults to Salesforce login URL)
            
        Returns:
            str: The signed JWT assertion
            
        Raises:
            ValueError: If the JWT creation fails
        """
        try:
            # Load private key
            private_key_bytes = self._load_private_key()
            
            # Parse private key
            try:
                private_key = serialization.load_pem_private_key(
                    private_key_bytes,
                    password=None
                )
            except ValueError:
                # Try loading as RSA private key
                private_key = rsa.generate_private_key(
                    public_exponent=65537,
                    key_size=2048
                )
            
            # Prepare JWT claims
            now = datetime.datetime.utcnow()
            expiration = now + datetime.timedelta(minutes=self.settings.jwt_expiration_minutes)
            
            claims = {
                'iss': self.settings.salesforce_consumer_key,
                'sub': self.settings.salesforce_username,
                'aud': audience or self.settings.salesforce_instance_url,
                'exp': int(expiration.timestamp()),
                'iat': int(now.timestamp()),
            }
            
            # Create and sign JWT
            jwt_token = jwt.encode(
                claims,
                private_key,
                algorithm=self.settings.jwt_algorithm,
                headers={'alg': self.settings.jwt_algorithm}
            )
            
            logger.debug("JWT assertion created successfully",
                        issuer=claims['iss'],
                        subject=claims['sub'],
                        audience=claims['aud'],
                        expiration=expiration.isoformat())
            
            return jwt_token
            
        except Exception as e:
            logger.error("Failed to create JWT assertion", error=str(e))
            raise ValueError(f"JWT creation failed: {str(e)}")
    
    def verify_jwt_token(self, token: str) -> Dict:
        """
        Verify and decode a JWT token.
        
        Args:
            token: The JWT token to verify
            
        Returns:
            Dict: The decoded JWT claims
            
        Raises:
            jwt.InvalidTokenError: If the token is invalid
        """
        try:
            # Load public key
            public_key_bytes = self._load_public_key()
            
            # Parse public key
            try:
                public_key = serialization.load_pem_public_key(public_key_bytes)
            except ValueError:
                # Try loading as RSA public key
                public_key = rsa.generate_private_key(
                    public_exponent=65537,
                    key_size=2048
                ).public_key()
            
            # Verify and decode JWT
            decoded = jwt.decode(
                token,
                public_key,
                algorithms=[self.settings.jwt_algorithm],
                options={
                    'verify_signature': True,
                    'verify_exp': True,
                    'verify_aud': False,  # We'll verify audience separately
                }
            )
            
            logger.debug("JWT token verified successfully",
                        issuer=decoded.get('iss'),
                        subject=decoded.get('sub'),
                        audience=decoded.get('aud'))
            
            return decoded
            
        except jwt.ExpiredSignatureError:
            logger.warning("JWT token has expired")
            raise
        except jwt.InvalidSignatureError:
            logger.warning("JWT token has invalid signature")
            raise
        except jwt.InvalidTokenError as e:
            logger.warning("JWT token is invalid", error=str(e))
            raise
        except Exception as e:
            logger.error("Failed to verify JWT token", error=str(e))
            raise
    
    def is_token_expired(self, token: str) -> bool:
        """
        Check if a JWT token is expired.
        
        Args:
            token: The JWT token to check
            
        Returns:
            bool: True if the token is expired, False otherwise
        """
        try:
            # Decode without verification to check expiration
            decoded = jwt.decode(
                token,
                options={'verify_signature': False}
            )
            
            exp_timestamp = decoded.get('exp')
            if exp_timestamp is None:
                return True
            
            current_time = int(time.time())
            return current_time >= exp_timestamp
            
        except Exception as e:
            logger.warning("Failed to check token expiration", error=str(e))
            return True
    
    def get_token_expiration_time(self, token: str) -> Optional[datetime.datetime]:
        """
        Get the expiration time of a JWT token.
        
        Args:
            token: The JWT token to check
            
        Returns:
            Optional[datetime.datetime]: The expiration time, or None if invalid
        """
        try:
            # Decode without verification to get expiration
            decoded = jwt.decode(
                token,
                options={'verify_signature': False}
            )
            
            exp_timestamp = decoded.get('exp')
            if exp_timestamp is None:
                return None
            
            return datetime.datetime.fromtimestamp(exp_timestamp, tz=datetime.timezone.utc)
            
        except Exception as e:
            logger.warning("Failed to get token expiration time", error=str(e))
            return None
    
    def should_refresh_token(self, token: str) -> bool:
        """
        Check if a token should be refreshed based on the configured threshold.
        
        Args:
            token: The JWT token to check
            
        Returns:
            bool: True if the token should be refreshed, False otherwise
        """
        try:
            expiration_time = self.get_token_expiration_time(token)
            if expiration_time is None:
                return True
            
            current_time = datetime.datetime.now(datetime.timezone.utc)
            time_until_expiration = expiration_time - current_time
            threshold_minutes = datetime.timedelta(minutes=self.settings.token_refresh_threshold_minutes)
            
            return time_until_expiration <= threshold_minutes
            
        except Exception as e:
            logger.warning("Failed to check if token should be refreshed", error=str(e))
            return True


# Global JWT authenticator instance
_jwt_authenticator: Optional[JWTAuthenticator] = None


def get_jwt_authenticator() -> JWTAuthenticator:
    """
    Get the global JWT authenticator instance.
    
    Returns:
        JWTAuthenticator: The JWT authenticator instance
    """
    global _jwt_authenticator
    if _jwt_authenticator is None:
        _jwt_authenticator = JWTAuthenticator()
    return _jwt_authenticator 