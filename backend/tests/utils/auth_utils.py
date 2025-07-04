"""
Authentication mock utilities for schedule route testing.

Provides mock implementations of authentication and authorization
components for testing schedule API routes without dependencies
on external authentication services.
"""

import uuid
import time
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, AsyncMock, patch
from contextlib import asynccontextmanager

import pytest
import jwt
from fastapi import HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials


class MockJWTHandler:
    """Mock JWT token handler for testing."""
    
    def __init__(self, secret_key: str = "test_secret_key"):
        self.secret_key = secret_key
        self.algorithm = "HS256"
        self.access_token_expire_minutes = 30
        self.refresh_token_expire_days = 7
        
    def create_access_token(
        self,
        user_id: str,
        email: str,
        additional_claims: Optional[Dict[str, Any]] = None
    ) -> str:
        """Create a mock access token."""
        now = datetime.utcnow()
        expire = now + timedelta(minutes=self.access_token_expire_minutes)
        
        payload = {
            "sub": user_id,
            "email": email,
            "type": "access",
            "iat": int(now.timestamp()),
            "exp": int(expire.timestamp())
        }
        
        if additional_claims:
            payload.update(additional_claims)
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def create_refresh_token(self, user_id: str, email: str) -> str:
        """Create a mock refresh token."""
        now = datetime.utcnow()
        expire = now + timedelta(days=self.refresh_token_expire_days)
        
        payload = {
            "sub": user_id,
            "email": email,
            "type": "refresh",
            "iat": int(now.timestamp()),
            "exp": int(expire.timestamp())
        }
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def decode_token(self, token: str) -> Dict[str, Any]:
        """Decode and validate a JWT token."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
    
    def create_expired_token(self, user_id: str, email: str) -> str:
        """Create an expired token for testing."""
        past_time = datetime.utcnow() - timedelta(hours=1)
        
        payload = {
            "sub": user_id,
            "email": email,
            "type": "access",
            "iat": int(past_time.timestamp()),
            "exp": int(past_time.timestamp())
        }
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def create_invalid_token(self) -> str:
        """Create an invalid token for testing."""
        return jwt.encode(
            {"invalid": "payload"}, 
            "wrong_secret", 
            algorithm=self.algorithm
        )


class MockUser:
    """Mock user for testing."""
    
    def __init__(
        self,
        user_id: Optional[str] = None,
        email: Optional[str] = None,
        is_active: bool = True,
        is_admin: bool = False,
        **kwargs
    ):
        self.id = user_id or str(uuid.uuid4())
        self.email = email or f"user{self.id[:8]}@test.com"
        self.is_active = is_active
        self.is_admin = is_admin
        self.created_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)
        
        # Additional attributes
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert user to dictionary."""
        return {
            "id": self.id,
            "email": self.email,
            "is_active": self.is_active,
            "is_admin": self.is_admin,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


class MockAuthenticator:
    """Mock authenticator for testing authentication flows."""
    
    def __init__(self):
        self.jwt_handler = MockJWTHandler()
        self.users = {}
        self.current_user = None
        self.should_fail_auth = False
        self.failure_reason = "Authentication failed"
        
    def register_user(
        self,
        user_id: Optional[str] = None,
        email: Optional[str] = None,
        is_active: bool = True,
        is_admin: bool = False,
        **kwargs
    ) -> MockUser:
        """Register a new mock user."""
        user = MockUser(
            user_id=user_id,
            email=email,
            is_active=is_active,
            is_admin=is_admin,
            **kwargs
        )
        self.users[user.id] = user
        return user
    
    def get_user_by_id(self, user_id: str) -> Optional[MockUser]:
        """Get user by ID."""
        return self.users.get(user_id)
    
    def get_user_by_email(self, email: str) -> Optional[MockUser]:
        """Get user by email."""
        for user in self.users.values():
            if user.email == email:
                return user
        return None
    
    def set_current_user(self, user: MockUser):
        """Set the current authenticated user."""
        self.current_user = user
    
    def get_current_user(self) -> Optional[MockUser]:
        """Get the current authenticated user."""
        if self.should_fail_auth:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=self.failure_reason
            )
        return self.current_user
    
    def authenticate_with_token(self, token: str) -> MockUser:
        """Authenticate user with JWT token."""
        if self.should_fail_auth:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=self.failure_reason
            )
        
        try:
            payload = self.jwt_handler.decode_token(token)
            user_id = payload.get("sub")
            
            if not user_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token payload"
                )
            
            user = self.get_user_by_id(user_id)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found"
                )
            
            if not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User account is inactive"
                )
            
            return user
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication failed"
            )
    
    def create_login_tokens(self, user: MockUser) -> Dict[str, str]:
        """Create login tokens for a user."""
        access_token = self.jwt_handler.create_access_token(
            user_id=user.id,
            email=user.email
        )
        refresh_token = self.jwt_handler.create_refresh_token(
            user_id=user.id,
            email=user.email
        )
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
    
    def configure_auth_failure(
        self,
        should_fail: bool = True,
        failure_reason: str = "Authentication failed"
    ):
        """Configure authentication failure behavior."""
        self.should_fail_auth = should_fail
        self.failure_reason = failure_reason
    
    def reset(self):
        """Reset authenticator state."""
        self.users.clear()
        self.current_user = None
        self.should_fail_auth = False
        self.failure_reason = "Authentication failed"


class MockAuthorizer:
    """Mock authorizer for testing authorization flows."""
    
    def __init__(self):
        self.access_rules = {}
        self.should_fail_auth = False
        self.failure_reason = "Access denied"
    
    def set_user_permissions(
        self,
        user_id: str,
        permissions: List[str]
    ):
        """Set permissions for a user."""
        self.access_rules[user_id] = permissions
    
    def check_permission(
        self,
        user: MockUser,
        permission: str,
        resource_id: Optional[str] = None
    ) -> bool:
        """Check if user has permission."""
        if self.should_fail_auth:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=self.failure_reason
            )
        
        # Admin users have all permissions
        if user.is_admin:
            return True
        
        # Check user-specific permissions
        user_permissions = self.access_rules.get(user.id, [])
        
        # Check for exact permission match
        if permission in user_permissions:
            return True
        
        # Check for wildcard permissions
        if "all" in user_permissions:
            return True
        
        # Check for resource-specific permissions
        if resource_id and f"{permission}:{resource_id}" in user_permissions:
            return True
        
        return False
    
    def require_permission(
        self,
        user: MockUser,
        permission: str,
        resource_id: Optional[str] = None
    ):
        """Require permission or raise exception."""
        if not self.check_permission(user, permission, resource_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{permission}' required"
            )
    
    def check_resource_access(
        self,
        user: MockUser,
        resource_type: str,
        resource_user_id: str
    ) -> bool:
        """Check if user can access a resource owned by another user."""
        # Users can always access their own resources
        if user.id == resource_user_id:
            return True
        
        # Admin users can access all resources
        if user.is_admin:
            return True
        
        # Check for specific permissions
        return self.check_permission(user, f"access_{resource_type}_all")
    
    def require_resource_access(
        self,
        user: MockUser,
        resource_type: str,
        resource_user_id: str
    ):
        """Require resource access or raise exception."""
        if not self.check_resource_access(user, resource_type, resource_user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied to {resource_type}"
            )
    
    def configure_auth_failure(
        self,
        should_fail: bool = True,
        failure_reason: str = "Access denied"
    ):
        """Configure authorization failure behavior."""
        self.should_fail_auth = should_fail
        self.failure_reason = failure_reason
    
    def reset(self):
        """Reset authorizer state."""
        self.access_rules.clear()
        self.should_fail_auth = False
        self.failure_reason = "Access denied"


class AuthMockManager:
    """Manager for coordinating all authentication mocks."""
    
    def __init__(self):
        self.authenticator = MockAuthenticator()
        self.authorizer = MockAuthorizer()
        self.jwt_handler = MockJWTHandler()
        self._active_patches = []
    
    def setup_mocks(self) -> Dict[str, Mock]:
        """Set up all authentication mocks."""
        mocks = {}
        
        # Mock get_current_user dependency
        get_current_user_mock = Mock(side_effect=self.authenticator.get_current_user)
        mocks["get_current_user"] = get_current_user_mock
        
        # Mock JWT authentication
        jwt_auth_mock = Mock()
        jwt_auth_mock.authenticate = Mock(side_effect=self.authenticator.authenticate_with_token)
        jwt_auth_mock.create_tokens = Mock(side_effect=self.authenticator.create_login_tokens)
        mocks["jwt_auth"] = jwt_auth_mock
        
        # Mock authorization checks
        auth_check_mock = Mock()
        auth_check_mock.check_permission = Mock(side_effect=self.authorizer.check_permission)
        auth_check_mock.require_permission = Mock(side_effect=self.authorizer.require_permission)
        auth_check_mock.require_resource_access = Mock(side_effect=self.authorizer.require_resource_access)
        mocks["auth_check"] = auth_check_mock
        
        return mocks
    
    def create_test_user(
        self,
        email: Optional[str] = None,
        is_admin: bool = False,
        permissions: Optional[List[str]] = None,
        **kwargs
    ) -> MockUser:
        """Create a test user with optional permissions."""
        user = self.authenticator.register_user(
            email=email,
            is_admin=is_admin,
            **kwargs
        )
        
        if permissions:
            self.authorizer.set_user_permissions(user.id, permissions)
        
        return user
    
    def authenticate_user(self, user: MockUser) -> str:
        """Authenticate a user and return access token."""
        self.authenticator.set_current_user(user)
        tokens = self.authenticator.create_login_tokens(user)
        return tokens["access_token"]
    
    def create_authenticated_headers(self, user: MockUser) -> Dict[str, str]:
        """Create headers with authentication token."""
        token = self.authenticate_user(user)
        return {"Authorization": f"Bearer {token}"}
    
    def configure_auth_failure(
        self,
        should_fail: bool = True,
        failure_reason: str = "Authentication failed"
    ):
        """Configure authentication failure."""
        self.authenticator.configure_auth_failure(should_fail, failure_reason)
    
    def configure_authz_failure(
        self,
        should_fail: bool = True,
        failure_reason: str = "Access denied"
    ):
        """Configure authorization failure."""
        self.authorizer.configure_auth_failure(should_fail, failure_reason)
    
    def reset_all(self):
        """Reset all authentication state."""
        self.authenticator.reset()
        self.authorizer.reset()
    
    @asynccontextmanager
    async def patch_auth_dependencies(self, target_modules: List[str]):
        """Context manager to patch authentication dependencies."""
        mocks = self.setup_mocks()
        patches = []
        
        try:
            for module in target_modules:
                if "get_current_user" in module:
                    patch_obj = patch(module, mocks["get_current_user"])
                elif "jwt_auth" in module:
                    patch_obj = patch(module, mocks["jwt_auth"])
                elif "auth_check" in module:
                    patch_obj = patch(module, mocks["auth_check"])
                else:
                    continue
                
                patches.append(patch_obj)
                patch_obj.start()
            
            yield mocks
            
        finally:
            for patch_obj in patches:
                patch_obj.stop()


# Test scenario builders
class AuthTestScenarios:
    """Pre-built authentication test scenarios."""
    
    @staticmethod
    def authenticated_user(
        email: str = "test@example.com",
        is_admin: bool = False,
        permissions: Optional[List[str]] = None
    ) -> tuple[AuthMockManager, MockUser, str]:
        """Scenario: Authenticated user with optional permissions."""
        auth_manager = AuthMockManager()
        user = auth_manager.create_test_user(
            email=email,
            is_admin=is_admin,
            permissions=permissions or ["schedule_read", "schedule_write"]
        )
        token = auth_manager.authenticate_user(user)
        return auth_manager, user, token
    
    @staticmethod
    def admin_user(email: str = "admin@example.com") -> tuple[AuthMockManager, MockUser, str]:
        """Scenario: Admin user with full permissions."""
        auth_manager = AuthMockManager()
        user = auth_manager.create_test_user(email=email, is_admin=True)
        token = auth_manager.authenticate_user(user)
        return auth_manager, user, token
    
    @staticmethod
    def unauthenticated_request() -> AuthMockManager:
        """Scenario: Unauthenticated request."""
        auth_manager = AuthMockManager()
        auth_manager.configure_auth_failure(should_fail=True)
        return auth_manager
    
    @staticmethod
    def unauthorized_user(
        email: str = "unauthorized@example.com"
    ) -> tuple[AuthMockManager, MockUser, str]:
        """Scenario: Authenticated but unauthorized user."""
        auth_manager = AuthMockManager()
        user = auth_manager.create_test_user(email=email, permissions=[])
        token = auth_manager.authenticate_user(user)
        return auth_manager, user, token


# Pytest fixtures
@pytest.fixture
def mock_jwt_handler():
    """Pytest fixture providing MockJWTHandler."""
    return MockJWTHandler()


@pytest.fixture
def mock_authenticator():
    """Pytest fixture providing MockAuthenticator."""
    authenticator = MockAuthenticator()
    yield authenticator
    authenticator.reset()


@pytest.fixture
def mock_authorizer():
    """Pytest fixture providing MockAuthorizer."""
    authorizer = MockAuthorizer()
    yield authorizer
    authorizer.reset()


@pytest.fixture
def auth_manager():
    """Pytest fixture providing AuthMockManager."""
    manager = AuthMockManager()
    yield manager
    manager.reset_all()


@pytest.fixture
def authenticated_user(auth_manager):
    """Pytest fixture providing authenticated test user."""
    user = auth_manager.create_test_user(
        email="test@example.com",
        permissions=["schedule_read", "schedule_write"]
    )
    token = auth_manager.authenticate_user(user)
    return user, token, auth_manager.create_authenticated_headers(user)


@pytest.fixture
def admin_user(auth_manager):
    """Pytest fixture providing authenticated admin user."""
    user = auth_manager.create_test_user(
        email="admin@example.com",
        is_admin=True
    )
    token = auth_manager.authenticate_user(user)
    return user, token, auth_manager.create_authenticated_headers(user)


@pytest.fixture
def unauthorized_user(auth_manager):
    """Pytest fixture providing authenticated but unauthorized user."""
    user = auth_manager.create_test_user(
        email="unauthorized@example.com",
        permissions=[]
    )
    token = auth_manager.authenticate_user(user)
    return user, token, auth_manager.create_authenticated_headers(user)


# Helper functions
def create_test_token(
    user_id: Optional[str] = None,
    email: Optional[str] = None,
    is_expired: bool = False,
    is_invalid: bool = False
) -> str:
    """Create a test JWT token."""
    jwt_handler = MockJWTHandler()
    
    user_id = user_id or str(uuid.uuid4())
    email = email or f"test{user_id[:8]}@example.com"
    
    if is_expired:
        return jwt_handler.create_expired_token(user_id, email)
    elif is_invalid:
        return jwt_handler.create_invalid_token()
    else:
        return jwt_handler.create_access_token(user_id, email)


def create_auth_headers(token: str) -> Dict[str, str]:
    """Create authorization headers with token."""
    return {"Authorization": f"Bearer {token}"}


def mock_get_current_user_dependency(user: MockUser):
    """Create a mock for the get_current_user dependency."""
    return Mock(return_value=user) 