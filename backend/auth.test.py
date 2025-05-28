"""
Unit tests for Supabase authentication module.
"""

import pytest
import os
from unittest.mock import Mock, patch, AsyncMock
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from auth import (
    SupabaseAuth, 
    get_auth_instance, 
    verify_token, 
    get_current_user,
    get_optional_user,
    require_role,
    require_admin
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
    with patch('auth.create_client') as mock_create:
        mock_client = Mock()
        mock_auth = Mock()
        mock_client.auth = mock_auth
        mock_create.return_value = mock_client
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

class TestSupabaseAuth:
    """Test cases for SupabaseAuth class"""

    def test_init_success(self, mock_env_vars, mock_supabase_client):
        """Test successful initialization"""
        auth = SupabaseAuth()
        assert auth.client is not None
        assert auth.jwt_secret == 'test-jwt-secret'

    def test_init_missing_env_vars(self):
        """Test initialization fails with missing environment variables"""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="SUPABASE_URL and SUPABASE_KEY environment variables are required"):
                SupabaseAuth()

    def test_verify_jwt_token_valid(self, mock_env_vars, mock_supabase_client, valid_jwt_token):
        """Test JWT token verification with valid token"""
        auth = SupabaseAuth()
        result = auth.verify_jwt_token(valid_jwt_token)
        
        assert result is not None
        assert result['sub'] == 'test-user-id'
        assert result['email'] == 'test@example.com'

    def test_verify_jwt_token_expired(self, mock_env_vars, mock_supabase_client, expired_jwt_token):
        """Test JWT token verification with expired token"""
        auth = SupabaseAuth()
        result = auth.verify_jwt_token(expired_jwt_token)
        
        assert result is None

    def test_verify_jwt_token_invalid(self, mock_env_vars, mock_supabase_client):
        """Test JWT token verification with invalid token"""
        auth = SupabaseAuth()
        result = auth.verify_jwt_token("invalid-token")
        
        assert result is None

    def test_get_user_from_token_success(self, mock_env_vars, mock_supabase_client):
        """Test successful user retrieval from token"""
        # Setup mock user response
        mock_user = Mock()
        mock_user.id = 'test-user-id'
        mock_user.email = 'test@example.com'
        mock_user.user_metadata = {'name': 'Test User'}
        mock_user.app_metadata = {'roles': ['user']}
        mock_user.created_at = '2024-01-01T00:00:00Z'
        
        mock_user_response = Mock()
        mock_user_response.user = mock_user
        
        mock_supabase_client.auth.get_user.return_value = mock_user_response
        
        auth = SupabaseAuth()
        result = auth.get_user_from_token('test-token')
        
        assert result is not None
        assert result['id'] == 'test-user-id'
        assert result['email'] == 'test@example.com'
        assert result['metadata'] == {'name': 'Test User'}

    def test_get_user_from_token_no_user(self, mock_env_vars, mock_supabase_client):
        """Test user retrieval when no user found"""
        mock_user_response = Mock()
        mock_user_response.user = None
        
        mock_supabase_client.auth.get_user.return_value = mock_user_response
        
        auth = SupabaseAuth()
        result = auth.get_user_from_token('test-token')
        
        assert result is None

class TestAuthDependencies:
    """Test authentication dependency functions"""

    @pytest.mark.asyncio
    async def test_verify_token_success(self, mock_env_vars, mock_supabase_client, valid_jwt_token):
        """Test successful token verification"""
        # Setup mocks
        mock_user_response = Mock()
        mock_user = Mock()
        mock_user.id = 'test-user-id'
        mock_user.email = 'test@example.com'
        mock_user.user_metadata = {}
        mock_user.app_metadata = {}
        mock_user.created_at = '2024-01-01T00:00:00Z'
        mock_user_response.user = mock_user
        
        mock_supabase_client.auth.get_user.return_value = mock_user_response
        
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=valid_jwt_token)
        
        with patch('auth.get_auth_instance') as mock_get_auth:
            mock_auth = SupabaseAuth()
            mock_get_auth.return_value = mock_auth
            
            result = await verify_token(credentials)
            
            assert result['id'] == 'test-user-id'
            assert result['email'] == 'test@example.com'

    @pytest.mark.asyncio
    async def test_verify_token_invalid(self, mock_env_vars, mock_supabase_client):
        """Test token verification with invalid token"""
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="invalid-token")
        
        with patch('auth.get_auth_instance') as mock_get_auth:
            mock_auth = SupabaseAuth()
            mock_get_auth.return_value = mock_auth
            
            with pytest.raises(HTTPException) as exc_info:
                await verify_token(credentials)
            
            assert exc_info.value.status_code == 401
            assert "Invalid or expired token" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_get_current_user(self):
        """Test get_current_user dependency"""
        user_data = {"id": "test-user", "email": "test@example.com"}
        
        result = await get_current_user(user_data)
        
        assert result == user_data

    @pytest.mark.asyncio
    async def test_get_optional_user_with_token(self, mock_env_vars, mock_supabase_client):
        """Test optional user authentication with valid token"""
        mock_request = Mock()
        mock_request.headers = {"Authorization": "Bearer valid-token"}
        
        with patch('auth.get_auth_instance') as mock_get_auth:
            mock_auth = Mock()
            mock_auth.verify_jwt_token.return_value = {"sub": "test-user"}
            mock_auth.get_user_from_token.return_value = {"id": "test-user"}
            mock_get_auth.return_value = mock_auth
            
            result = await get_optional_user(mock_request)
            
            assert result is not None
            assert result["id"] == "test-user"

    @pytest.mark.asyncio
    async def test_get_optional_user_no_token(self):
        """Test optional user authentication without token"""
        mock_request = Mock()
        mock_request.headers = {}
        
        result = await get_optional_user(mock_request)
        
        assert result is None

class TestRoleBasedAuth:
    """Test role-based authorization"""

    @pytest.mark.asyncio
    async def test_require_role_success(self):
        """Test role requirement with user having required role"""
        user_data = {
            "id": "test-user",
            "app_metadata": {"roles": ["admin", "user"]}
        }
        
        role_checker = require_role("admin")
        result = await role_checker(user_data)
        
        assert result == user_data

    @pytest.mark.asyncio
    async def test_require_role_missing(self):
        """Test role requirement with user missing required role"""
        user_data = {
            "id": "test-user",
            "app_metadata": {"roles": ["user"]}
        }
        
        role_checker = require_role("admin")
        
        with pytest.raises(HTTPException) as exc_info:
            await role_checker(user_data)
        
        assert exc_info.value.status_code == 403
        assert "Required role 'admin' not found" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_require_admin(self):
        """Test admin role requirement"""
        user_data = {
            "id": "test-user",
            "app_metadata": {"roles": ["admin"]}
        }
        
        with patch('auth.require_role') as mock_require_role:
            mock_require_role.return_value = AsyncMock(return_value=user_data)
            
            result = await require_admin(user_data)
            
            assert result == user_data

def test_get_auth_instance():
    """Test singleton auth instance getter"""
    with patch.dict(os.environ, {
        'SUPABASE_URL': 'https://test.supabase.co',
        'SUPABASE_KEY': 'test-key'
    }):
        with patch('auth.create_client'):
            instance1 = get_auth_instance()
            instance2 = get_auth_instance()
            
            # Should return the same instance (singleton pattern)
            assert instance1 is instance2 