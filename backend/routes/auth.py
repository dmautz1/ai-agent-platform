"""
Authentication routes for the AI Agent Platform.

Contains endpoints for:
- User authentication and session management
- User profile information
"""

from fastapi import APIRouter, Depends
from typing import Dict, Any

from auth import get_current_user
from logging_system import get_logger, get_performance_logger, get_security_logger

logger = get_logger(__name__)
perf_logger = get_performance_logger()
security_logger = get_security_logger()

router = APIRouter(prefix="/auth", tags=["authentication"])

@router.get("/me")
async def get_current_user_info(user: Dict[str, Any] = Depends(get_current_user)):
    """Get current authenticated user info"""
    with perf_logger.time_operation("auth_get_user_info", user_id=user["id"]):
        logger.info("User info requested", user_id=user["id"])
        
        security_logger.log_auth_success(
            user_id=user["id"],
            method="jwt"
        )
        
        return {
            "user": user,
            "message": "Authentication successful"
        } 