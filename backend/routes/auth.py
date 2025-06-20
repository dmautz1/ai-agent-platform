"""
Authentication routes for the AI Agent Platform.

Contains endpoints for:
- User authentication and session management
- User profile information
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
from datetime import datetime, timezone

from auth import get_current_user
from logging_system import get_logger, get_security_logger
from models import ApiResponse
from utils.responses import (
    create_success_response,
    create_error_response,
    api_response_validator
)

logger = get_logger(__name__)
security_logger = get_security_logger()

router = APIRouter(prefix="/auth", tags=["authentication"])

# Auth Response Types
UserInfoResponse = Dict[str, Any]

@router.get("/user", response_model=ApiResponse[UserInfoResponse])
@api_response_validator(result_type=UserInfoResponse)
async def get_user_info(user: Dict[str, Any] = Depends(get_current_user)):
    """Get current user information"""
    logger.info("User info requested", user_id=user["id"])
    
    try:
        # Return Supabase-aligned user information
        user_data = {
            "user": {
                "id": user["id"],
                "email": user["email"],
                "user_metadata": user.get("user_metadata", {}),
                "app_metadata": user.get("app_metadata", {})
            }
        }
        
        return create_success_response(
            result=user_data,
            message="User information retrieved successfully",
            metadata={
                "endpoint": "user_info",
                "user_id": user["id"],
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
    except Exception as e:
        logger.error("Failed to get user info", exception=e, user_id=user["id"])
        return create_error_response(
            error_message=str(e),
            message="Failed to retrieve user information",
            metadata={
                "error_code": "USER_INFO_ERROR",
                "user_id": user["id"],
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        ) 