"""
Unit tests for authentication module.

This module tests the JWT authentication and OAuth flow
for Salesforce Data Cloud integration.
"""

import pytest
import tempfile
import os
from unittest.mock import Mock, patch, mock_open
from datetime import datetime, timedelta

from src.auth.jwt import JWTAuthenticator, get_jwt_authenticator
from src.auth.oauth import SalesforceAuthenticator, get_salesforce_authenticator
from src.config.settings import get_settings


class TestJWTAuthenticator:
    """Test cases for JWT authentication."""

    @pytest.fixture
    def authenticator(self):
        """Create a JWT authenticator instance."""
        return JWTAuthenticator()

    @pytest.fixture
    def mock_settings(self):
        """Mock settings for testing."""
        with patch('src.auth.jwt.get_settings') as mock_get_settings:
            settings = Mock()
            settings.salesforce_username = 'test@example.com'
            settings.salesforce_consumer_key = 'test_consumer_key'
            settings.salesforce_private_key_path = '/path/to/private.key'
            settings.jwt_algorithm = 'RS256'
            settings.jwt_expiration_minutes = 5
            settings.token_refresh_threshold_minutes = 10
            mock_get_settings.return_value = settings
            yield settings

    def test_authenticator_initialization(self, authenticator):
        """Test JWT authenticator initialization."""
        assert authenticator.settings is not None
        assert authenticator._private_key is None
        assert authenticator._public_key is None

    def test_load_private_key_file_not_found(self, authenticator, mock_settings):
        """Test loading private key when file doesn't exist."""
        mock_settings.salesforce_private_key_path = '/nonexistent/path'
        
        with pytest.raises(FileNotFoundError):
            authenticator._load_private_key()

    @patch('builtins.open', new_callable=mock_open, read_data=b'private_key_content')
    def test_load_private_key_success(self, mock_file, authenticator, mock_settings):
        """Test successful private key loading."""
        result = authenticator._load_private_key()
        assert result == b'private_key_content'
        assert authenticator._private_key == b'private_key_content'

    def test_load_public_key_file_not_found(self, authenticator, mock_settings):
        """Test loading public key when file doesn't exist."""
        with patch('pathlib.Path.exists', return_value=False):
            with pytest.raises(FileNotFoundError):
                authenticator._load_public_key()

    @patch('builtins.open', new_callable=mock_open, read_data=b'public_key_content')
    def test_load_public_key_success(self, mock_file, authenticator, mock_settings):
        """Test successful public key loading."""
        with patch('pathlib.Path.exists', return_value=True):
            result = authenticator._load_public_key()
            assert result == b'public_key_content'
            assert authenticator._public_key == b'public_key_content'

    @patch('src.auth.jwt.jwt.encode')
    def test_create_jwt_assertion_success(self, mock_jwt_encode, authenticator, mock_settings):
        """Test successful JWT assertion creation."""
        mock_jwt_encode.return_value = 'test_jwt_token'
        
        with patch.object(authenticator, '_load_private_key', return_value=b'private_key'):
            with patch('cryptography.hazmat.primitives.serialization.load_pem_private_key') as mock_load_key:
                mock_key = Mock()
                mock_load_key.return_value = mock_key
                
                result = authenticator.create_jwt_assertion()
                
                assert result == 'test_jwt_token'
                mock_jwt_encode.assert_called_once()

    def test_create_jwt_assertion_failure(self, authenticator, mock_settings):
        """Test JWT assertion creation failure."""
        with patch.object(authenticator, '_load_private_key', side_effect=Exception('Key error')):
            with pytest.raises(ValueError, match='JWT creation failed'):
                authenticator.create_jwt_assertion()

    @patch('src.auth.jwt.jwt.decode')
    def test_verify_jwt_token_success(self, mock_jwt_decode, authenticator, mock_settings):
        """Test successful JWT token verification."""
        mock_jwt_decode.return_value = {
            'iss': 'test_consumer_key',
            'sub': 'test@example.com',
            'aud': 'https://login.salesforce.com'
        }
        
        with patch.object(authenticator, '_load_public_key', return_value=b'public_key'):
            with patch('cryptography.hazmat.primitives.serialization.load_pem_public_key') as mock_load_key:
                mock_key = Mock()
                mock_load_key.return_value = mock_key
                
                result = authenticator.verify_jwt_token('test_token')
                
                assert result['iss'] == 'test_consumer_key'
                mock_jwt_decode.assert_called_once()

    def test_verify_jwt_token_invalid(self, authenticator, mock_settings):
        """Test JWT token verification with invalid token."""
        with patch.object(authenticator, '_load_public_key', return_value=b'public_key'):
            with patch('cryptography.hazmat.primitives.serialization.load_pem_public_key') as mock_load_key:
                mock_key = Mock()
                mock_load_key.return_value = mock_key
                
                with patch('src.auth.jwt.jwt.decode', side_effect=Exception('Invalid token')):
                    with pytest.raises(Exception):
                        authenticator.verify_jwt_token('invalid_token')

    def test_is_token_expired_true(self, authenticator):
        """Test token expiration check when token is expired."""
        with patch('src.auth.jwt.jwt.decode') as mock_decode:
            mock_decode.return_value = {'exp': datetime.now().timestamp() - 3600}  # Expired 1 hour ago
            
            result = authenticator.is_token_expired('expired_token')
            assert result is True

    def test_is_token_expired_false(self, authenticator):
        """Test token expiration check when token is not expired."""
        with patch('src.auth.jwt.jwt.decode') as mock_decode:
            mock_decode.return_value = {'exp': datetime.now().timestamp() + 3600}  # Expires in 1 hour
            
            result = authenticator.is_token_expired('valid_token')
            assert result is False

    def test_get_token_expiration_time(self, authenticator):
        """Test getting token expiration time."""
        future_time = datetime.now() + timedelta(hours=1)
        with patch('src.auth.jwt.jwt.decode') as mock_decode:
            mock_decode.return_value = {'exp': future_time.timestamp()}
            
            result = authenticator.get_token_expiration_time('test_token')
            assert result is not None
            assert abs((result - future_time).total_seconds()) < 1

    def test_should_refresh_token_true(self, authenticator, mock_settings):
        """Test token refresh check when refresh is needed."""
        with patch.object(authenticator, 'get_token_expiration_time') as mock_get_exp:
            mock_get_exp.return_value = datetime.now() + timedelta(minutes=2)  # Expires soon
            
            result = authenticator.should_refresh_token('test_token')
            assert result is True

    def test_should_refresh_token_false(self, authenticator, mock_settings):
        """Test token refresh check when refresh is not needed."""
        with patch.object(authenticator, 'get_token_expiration_time') as mock_get_exp:
            mock_get_exp.return_value = datetime.now() + timedelta(hours=1)  # Expires later
            
            result = authenticator.should_refresh_token('test_token')
            assert result is False


class TestSalesforceAuthenticator:
    """Test cases for Salesforce OAuth authentication."""

    @pytest.fixture
    def authenticator(self):
        """Create a Salesforce authenticator instance."""
        return SalesforceAuthenticator()

    @pytest.fixture
    def mock_settings(self):
        """Mock settings for testing."""
        with patch('src.auth.oauth.get_settings') as mock_get_settings:
            settings = Mock()
            settings.salesforce_username = 'test@example.com'
            settings.salesforce_consumer_key = 'test_consumer_key'
            settings.salesforce_instance_url = 'https://login.salesforce.com'
            settings.data_cloud_dataspace = 'test_dataspace'
            settings.token_refresh_threshold_minutes = 10
            mock_get_settings.return_value = settings
            yield settings

    @pytest.fixture
    def mock_jwt_authenticator(self):
        """Mock JWT authenticator."""
        with patch('src.auth.oauth.get_jwt_authenticator') as mock_get_jwt:
            jwt_auth = Mock()
            jwt_auth.create_jwt_assertion.return_value = 'test_jwt_assertion'
            mock_get_jwt.return_value = jwt_auth
            yield jwt_auth

    @pytest.mark.asyncio
    async def test_get_platform_access_token_success(self, authenticator, mock_settings, mock_jwt_authenticator):
        """Test successful platform access token retrieval."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'access_token': 'test_access_token',
            'token_type': 'Bearer',
            'expires_in': 7200,
            'instance_url': 'https://test.salesforce.com'
        }
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
            
            result = await authenticator.get_platform_access_token()
            
            assert result == 'test_access_token'
            assert authenticator._platform_token is not None
            assert authenticator._platform_token.access_token == 'test_access_token'

    @pytest.mark.asyncio
    async def test_get_platform_access_token_failure(self, authenticator, mock_settings, mock_jwt_authenticator):
        """Test platform access token retrieval failure."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.text = 'Unauthorized'
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
            
            with pytest.raises(ValueError, match='Token request failed'):
                await authenticator.get_platform_access_token()

    @pytest.mark.asyncio
    async def test_get_data_cloud_access_token_success(self, authenticator, mock_settings, mock_jwt_authenticator):
        """Test successful Data Cloud access token retrieval."""
        # Mock platform token
        authenticator._platform_token = Mock()
        authenticator._platform_token.access_token = 'platform_token'
        authenticator._platform_token.instance_url = 'https://test.salesforce.com'
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'access_token': 'data_cloud_token',
            'token_type': 'Bearer',
            'expires_in': 3600
        }
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
            
            result = await authenticator.get_data_cloud_access_token()
            
            assert result == 'data_cloud_token'
            assert authenticator._data_cloud_token is not None
            assert authenticator._data_cloud_token.access_token == 'data_cloud_token'

    @pytest.mark.asyncio
    async def test_get_data_cloud_access_token_failure(self, authenticator, mock_settings, mock_jwt_authenticator):
        """Test Data Cloud access token retrieval failure."""
        # Mock platform token
        authenticator._platform_token = Mock()
        authenticator._platform_token.access_token = 'platform_token'
        authenticator._platform_token.instance_url = 'https://test.salesforce.com'
        
        mock_response = Mock()
        mock_response.status_code = 403
        mock_response.text = 'Forbidden'
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
            
            with pytest.raises(ValueError, match='Token exchange failed'):
                await authenticator.get_data_cloud_access_token()

    def test_should_refresh_token_true(self, authenticator, mock_settings):
        """Test token refresh check when refresh is needed."""
        authenticator._last_token_refresh = datetime.now() - timedelta(minutes=5)
        token_response = Mock()
        token_response.expires_in = 600  # 10 minutes
        
        result = authenticator._should_refresh_token(token_response)
        assert result is True

    def test_should_refresh_token_false(self, authenticator, mock_settings):
        """Test token refresh check when refresh is not needed."""
        authenticator._last_token_refresh = datetime.now() - timedelta(minutes=1)
        token_response = Mock()
        token_response.expires_in = 600  # 10 minutes
        
        result = authenticator._should_refresh_token(token_response)
        assert result is False

    @pytest.mark.asyncio
    async def test_get_valid_access_token_data_cloud(self, authenticator, mock_settings, mock_jwt_authenticator):
        """Test getting valid access token for Data Cloud."""
        with patch.object(authenticator, 'get_data_cloud_access_token', return_value='data_cloud_token'):
            result = await authenticator.get_valid_access_token(for_data_cloud=True)
            assert result == 'data_cloud_token'

    @pytest.mark.asyncio
    async def test_get_valid_access_token_platform(self, authenticator, mock_settings, mock_jwt_authenticator):
        """Test getting valid access token for platform."""
        with patch.object(authenticator, 'get_platform_access_token', return_value='platform_token'):
            result = await authenticator.get_valid_access_token(for_data_cloud=False)
            assert result == 'platform_token'

    def test_clear_cached_tokens(self, authenticator):
        """Test clearing cached tokens."""
        authenticator._platform_token = Mock()
        authenticator._data_cloud_token = Mock()
        authenticator._last_token_refresh = datetime.now()
        
        authenticator.clear_cached_tokens()
        
        assert authenticator._platform_token is None
        assert authenticator._data_cloud_token is None
        assert authenticator._last_token_refresh is None

    def test_get_token_info(self, authenticator):
        """Test getting token information."""
        authenticator._platform_token = Mock()
        authenticator._platform_token.expires_in = 7200
        authenticator._data_cloud_token = Mock()
        authenticator._data_cloud_token.expires_in = 3600
        authenticator._last_token_refresh = datetime.now()
        
        info = authenticator.get_token_info()
        
        assert info['platform_token']['has_token'] is True
        assert info['platform_token']['expires_in'] == 7200
        assert info['data_cloud_token']['has_token'] is True
        assert info['data_cloud_token']['expires_in'] == 3600


class TestGlobalFunctions:
    """Test cases for global authentication functions."""

    @pytest.mark.asyncio
    async def test_authenticate_with_salesforce(self):
        """Test global authenticate function."""
        with patch('src.auth.oauth.get_salesforce_authenticator') as mock_get_auth:
            mock_authenticator = Mock()
            mock_authenticator.get_data_cloud_access_token.return_value = 'test_token'
            mock_get_auth.return_value = mock_authenticator
            
            result = await authenticate_with_salesforce()
            assert result == 'test_token'

    @pytest.mark.asyncio
    async def test_get_salesforce_headers(self):
        """Test getting Salesforce headers."""
        with patch('src.auth.oauth.get_salesforce_authenticator') as mock_get_auth:
            mock_authenticator = Mock()
            mock_authenticator.get_valid_access_token.return_value = 'test_token'
            mock_get_auth.return_value = mock_authenticator
            
            headers = await get_salesforce_headers(for_data_cloud=True)
            
            assert headers['Authorization'] == 'Bearer test_token'
            assert headers['Content-Type'] == 'application/json'
            assert headers['Accept'] == 'application/json'


if __name__ == '__main__':
    pytest.main([__file__]) 