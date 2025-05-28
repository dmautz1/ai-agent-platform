"""
Supabase authentication middleware for FastAPI.
Provides user authentication and authorization with comprehensive logging.
"""

from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, Any, Optional
import jwt
from database import get_supabase_client
from config import get_settings
from logging_system import get_security_logger, get_logger

# Initialize loggers
security_logger = get_security_logger()
logger = get_logger(__name__)

# Initialize settings and security
settings = get_settings()
security = HTTPBearer()

async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """
    Verify Supabase JWT token and return user information.
    
    Args:
        credentials: HTTP Bearer token credentials
        
    Returns:
        User information from token payload
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    token = credentials.credentials
    
    try:
        # Get Supabase client
        supabase = get_supabase_client()
        
        # Verify token with Supabase
        response = supabase.auth.get_user(token)
        
        if response.user is None:
            logger.warning("Token verification failed - no user found", token_prefix=token[:10])
            security_logger.log_auth_failure(
                reason="invalid_token",
                method="supabase_jwt"
            )
            raise HTTPException(
                status_code=401,
                detail="Invalid authentication token"
            )
        
        user_data = {
            "id": response.user.id,
            "email": response.user.email,
            "created_at": response.user.created_at,
            "last_sign_in_at": response.user.last_sign_in_at,
            "app_metadata": response.user.app_metadata,
            "user_metadata": response.user.user_metadata
        }
        
        logger.debug("Token verified successfully", user_id=response.user.id)
        security_logger.log_auth_success(
            user_id=response.user.id,
            method="supabase_jwt"
        )
        
        return user_data
        
    except jwt.ExpiredSignatureError:
        logger.warning("Token verification failed - expired token", token_prefix=token[:10])
        security_logger.log_auth_failure(
            reason="expired_token",
            method="supabase_jwt"
        )
        raise HTTPException(
            status_code=401,
            detail="Token has expired"
        )
    except jwt.InvalidTokenError as e:
        logger.warning("Token verification failed - invalid token", error=str(e), token_prefix=token[:10])
        security_logger.log_auth_failure(
            reason="malformed_token",
            method="supabase_jwt"
        )
        raise HTTPException(
            status_code=401,
            detail="Invalid token format"
        )
    except Exception as e:
        logger.error("Token verification failed - unexpected error", exception=e, token_prefix=token[:10])
        security_logger.log_auth_failure(
            reason="verification_error",
            method="supabase_jwt"
        )
        raise HTTPException(
            status_code=401,
            detail="Authentication failed"
        )

async def get_current_user(user_data: Dict[str, Any] = Depends(verify_token)) -> Dict[str, Any]:
    """
    Get current authenticated user with comprehensive logging.
    
    Args:
        user_data: Verified user data from token
        
    Returns:
        Current user information
    """
    logger.debug("Current user retrieved", user_id=user_data["id"])
    return user_data

async def get_optional_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))) -> Optional[Dict[str, Any]]:
    """
    Get current user if authenticated, None if not (optional authentication).
    
    Args:
        credentials: Optional HTTP Bearer token credentials
        
    Returns:
        User information if authenticated, None otherwise
    """
    if credentials is None:
        logger.debug("No authentication credentials provided")
        return None
    
    try:
        # Verify token manually since auto_error=False
        token = credentials.credentials
        
        # Get Supabase client
        supabase = get_supabase_client()
        
        # Verify token with Supabase
        response = supabase.auth.get_user(token)
        
        if response.user is None:
            logger.debug("Optional auth failed - no user found", token_prefix=token[:10])
            return None
        
        user_data = {
            "id": response.user.id,
            "email": response.user.email,
            "created_at": response.user.created_at,
            "last_sign_in_at": response.user.last_sign_in_at,
            "app_metadata": response.user.app_metadata,
            "user_metadata": response.user.user_metadata
        }
        
        logger.debug("Optional auth successful", user_id=response.user.id)
        security_logger.log_auth_success(
            user_id=response.user.id,
            method="supabase_jwt_optional"
        )
        
        return user_data
        
    except Exception as e:
        logger.debug("Optional auth failed", exception=e, token_prefix=credentials.credentials[:10] if credentials else "none")
        return None

def require_user_access(resource_user_id: str, current_user: Dict[str, Any]) -> None:
    """
    Ensure current user has access to a specific user's resources.
    
    Args:
        resource_user_id: ID of the user whose resource is being accessed
        current_user: Current authenticated user
        
    Raises:
        HTTPException: If user doesn't have access to the resource
    """
    if current_user["id"] != resource_user_id:
        logger.warning(
            "Unauthorized resource access attempted",
            current_user_id=current_user["id"],
            requested_user_id=resource_user_id
        )
        security_logger.log_authorization_failure(
            user_id=current_user["id"],
            resource=f"user:{resource_user_id}",
            action="access"
        )
        raise HTTPException(
            status_code=403,
            detail="Access denied: You can only access your own resources"
        )
    
    logger.debug("User access verified", user_id=current_user["id"], resource_user_id=resource_user_id)

def require_admin_access(current_user: Dict[str, Any]) -> None:
    """
    Ensure current user has admin access.
    
    Args:
        current_user: Current authenticated user
        
    Raises:
        HTTPException: If user doesn't have admin access
    """
    is_admin = current_user.get("app_metadata", {}).get("role") == "admin"
    
    if not is_admin:
        logger.warning("Admin access denied", user_id=current_user["id"])
        security_logger.log_authorization_failure(
            user_id=current_user["id"],
            resource="admin",
            action="access"
        )
        raise HTTPException(
            status_code=403,
            detail="Access denied: Admin privileges required"
        )
    
    logger.info("Admin access granted", user_id=current_user["id"])

def check_rate_limiting(user_id: str, action: str, limit_per_minute: int = 60) -> None:
    """
    Check if user is within rate limits for a specific action.
    
    Note: This is a placeholder implementation. In production, you would
    use Redis or similar for distributed rate limiting.
    
    Args:
        user_id: ID of the user
        action: Action being performed
        limit_per_minute: Maximum actions allowed per minute
        
    Raises:
        HTTPException: If rate limit is exceeded
    """
    # TODO: Implement actual rate limiting with Redis
    # For now, just log the rate limit check
    logger.debug(
        "Rate limit check",
        user_id=user_id,
        action=action,
        limit_per_minute=limit_per_minute
    )
    
    # Simulate rate limit exceeded for demonstration
    # In real implementation, check against Redis/cache
    # if rate_limit_exceeded:
    #     security_logger.log_rate_limit_exceeded(
    #         identifier=user_id,
    #         limit=f"{limit_per_minute}/minute"
    #     )
    #     raise HTTPException(
    #         status_code=429,
    #         detail=f"Rate limit exceeded: {limit_per_minute} requests per minute"
    #     ) 