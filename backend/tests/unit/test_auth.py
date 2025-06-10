"""
Unit tests for Supabase authentication module.
"""

import pytest
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import os
from unittest.mock import Mock, patch, AsyncMock
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from auth import (
    verify_token, 
    get_current_user,
    get_optional_user,
    require_user_access,
    require_admin_access,
    check_rate_limiting
)
from datetime import datetime, timedelta
import jwt

@pytest.fixture
def mock_env_vars():
    """Mock environment variables for testing"""
    with patch.dict(os.environ, {
        'SUPABASE_URL': 'https://test.supabase.co',
        'SUPABASE_KEY': 'test-key',
        'SUPABASE_JWT_SECRET': 'test-jwt-secret'
    }):
        yield

@pytest.fixture
def mock_supabase_client():
    """Mock Supabase client for testing"""
    with patch('auth.get_supabase_client') as mock_get_client:
        mock_client = Mock()
        mock_auth = Mock()
        mock_client.auth = mock_auth
        mock_get_client.return_value = mock_client
        yield mock_client

@pytest.fixture
def valid_jwt_token():
    """Create a valid JWT token for testing"""
    payload = {
        'sub': 'test-user-id',
        'email': 'test@example.com',
        'exp': (datetime.utcnow() + timedelta(hours=1)).timestamp(),
        'iat': datetime.utcnow().timestamp()
    }
    return jwt.encode(payload, 'test-jwt-secret', algorithm='HS256')

@pytest.fixture
def expired_jwt_token():
    """Create an expired JWT token for testing"""
    payload = {
        'sub': 'test-user-id',
        'email': 'test@example.com',
        'exp': (datetime.utcnow() - timedelta(hours=1)).timestamp(),
        'iat': datetime.utcnow().timestamp()
    }
    return jwt.encode(payload, 'test-jwt-secret', algorithm='HS256')

@pytest.fixture
def mock_user_data():
    """Mock user data for testing"""
    return {
        "id": "test-user-id",
        "email": "test@example.com",
        "created_at": "2024-01-01T00:00:00Z",
        "last_sign_in_at": "2024-01-01T00:00:00Z",
        "app_metadata": {"role": "user"},
        "user_metadata": {"name": "Test User"}
    }

@pytest.fixture
def mock_admin_user_data():
    """Mock admin user data for testing"""
    return {
        "id": "admin-user-id",
        "email": "admin@example.com",
        "created_at": "2024-01-01T00:00:00Z",
        "last_sign_in_at": "2024-01-01T00:00:00Z",
        "app_metadata": {"role": "admin"},
        "user_metadata": {"name": "Admin User"}
    }

class TestVerifyToken:
    """Test cases for verify_token function"""

    @pytest.mark.asyncio
    async def test_verify_token_success(self, mock_supabase_client):
        """Test successful token verification"""
        # Setup mock user response
        mock_user = Mock()
        mock_user.id = 'test-user-id'
        mock_user.email = 'test@example.com'
        mock_user.created_at = '2024-01-01T00:00:00Z'
        mock_user.last_sign_in_at = '2024-01-01T00:00:00Z'
        mock_user.app_metadata = {"role": "user"}
        mock_user.user_metadata = {"name": "Test User"}
        
        mock_user_response = Mock()
        mock_user_response.user = mock_user
        mock_supabase_client.auth.get_user.return_value = mock_user_response
        
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="valid-token")
        
        result = await verify_token(credentials)
        
        assert result['id'] == 'test-user-id'
        assert result['email'] == 'test@example.com'
        assert result['app_metadata'] == {"role": "user"}
        mock_supabase_client.auth.get_user.assert_called_once_with("valid-token")

    @pytest.mark.asyncio
    async def test_verify_token_no_user(self, mock_supabase_client):
        """Test token verification when no user found"""
        mock_user_response = Mock()
        mock_user_response.user = None
        mock_supabase_client.auth.get_user.return_value = mock_user_response
        
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="invalid-token")
        
        with pytest.raises(HTTPException) as exc_info:
            await verify_token(credentials)
        
        assert exc_info.value.status_code == 401
        assert "Authentication failed" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_verify_token_expired(self, mock_supabase_client):
        """Test token verification with expired token"""
        mock_supabase_client.auth.get_user.side_effect = jwt.ExpiredSignatureError("Token expired")
        
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="expired-token")
        
        with pytest.raises(HTTPException) as exc_info:
            await verify_token(credentials)
        
        assert exc_info.value.status_code == 401
        assert "Token has expired" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_verify_token_invalid_format(self, mock_supabase_client):
        """Test token verification with invalid token format"""
        mock_supabase_client.auth.get_user.side_effect = jwt.InvalidTokenError("Invalid token")
        
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="malformed-token")
        
        with pytest.raises(HTTPException) as exc_info:
            await verify_token(credentials)
        
        assert exc_info.value.status_code == 401
        assert "Invalid token format" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_verify_token_unexpected_error(self, mock_supabase_client):
        """Test token verification with unexpected error"""
        mock_supabase_client.auth.get_user.side_effect = Exception("Unexpected error")
        
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="error-token")
        
        with pytest.raises(HTTPException) as exc_info:
            await verify_token(credentials)
        
        assert exc_info.value.status_code == 401
        assert "Authentication failed" in exc_info.value.detail

class TestGetCurrentUser:
    """Test cases for get_current_user function"""

    @pytest.mark.asyncio
    async def test_get_current_user_success(self, mock_user_data):
        """Test successful get_current_user"""
        result = await get_current_user(mock_user_data)
        assert result == mock_user_data

class TestGetOptionalUser:
    """Test cases for get_optional_user function"""

    @pytest.mark.asyncio
    async def test_get_optional_user_success(self, mock_supabase_client):
        """Test successful optional user authentication"""
        # Setup mock user response
        mock_user = Mock()
        mock_user.id = 'test-user-id'
        mock_user.email = 'test@example.com'
        mock_user.created_at = '2024-01-01T00:00:00Z'
        mock_user.last_sign_in_at = '2024-01-01T00:00:00Z'
        mock_user.app_metadata = {"role": "user"}
        mock_user.user_metadata = {"name": "Test User"}
        
        mock_user_response = Mock()
        mock_user_response.user = mock_user
        mock_supabase_client.auth.get_user.return_value = mock_user_response
        
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="valid-token")
        
        result = await get_optional_user(credentials)
        
        assert result is not None
        assert result['id'] == 'test-user-id'
        assert result['email'] == 'test@example.com'

    @pytest.mark.asyncio
    async def test_get_optional_user_no_credentials(self):
        """Test optional user authentication without credentials"""
        result = await get_optional_user(None)
        assert result is None

    @pytest.mark.asyncio
    async def test_get_optional_user_no_user(self, mock_supabase_client):
        """Test optional user authentication when no user found"""
        mock_user_response = Mock()
        mock_user_response.user = None
        mock_supabase_client.auth.get_user.return_value = mock_user_response
        
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="invalid-token")
        
        result = await get_optional_user(credentials)
        assert result is None

    @pytest.mark.asyncio
    async def test_get_optional_user_error(self, mock_supabase_client):
        """Test optional user authentication with error"""
        mock_supabase_client.auth.get_user.side_effect = Exception("Auth error")
        
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="error-token")
        
        result = await get_optional_user(credentials)
        assert result is None

class TestAccessControl:
    """Test cases for access control functions"""

    def test_require_user_access_success(self, mock_user_data):
        """Test successful user access verification"""
        # Should not raise exception when user accesses their own resource
        require_user_access("test-user-id", mock_user_data)

    def test_require_user_access_denied(self, mock_user_data):
        """Test user access denied for different user's resource"""
        with pytest.raises(HTTPException) as exc_info:
            require_user_access("other-user-id", mock_user_data)
        
        assert exc_info.value.status_code == 403
        assert "Access denied" in exc_info.value.detail

    def test_require_admin_access_success(self, mock_admin_user_data):
        """Test successful admin access verification"""
        # Should not raise exception when admin user accesses admin resource
        require_admin_access(mock_admin_user_data)

    def test_require_admin_access_denied(self, mock_user_data):
        """Test admin access denied for regular user"""
        with pytest.raises(HTTPException) as exc_info:
            require_admin_access(mock_user_data)
        
        assert exc_info.value.status_code == 403
        assert "Admin privileges required" in exc_info.value.detail

    def test_check_rate_limiting_success(self):
        """Test rate limiting check (currently a placeholder)"""
        # Should not raise exception - this is currently a placeholder implementation
        check_rate_limiting("test-user-id", "test-action", 60) 