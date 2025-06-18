"""
Authentication routes for the AI Agent Platform.

Contains endpoints for:
- User authentication and session management
- User profile information
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any

from auth import get_current_user
from logging_system import get_logger, get_security_logger

logger = get_logger(__name__)
security_logger = get_security_logger()

router = APIRouter(prefix="/auth", tags=["authentication"])

@router.get("/user")
async def get_user_info(user: Dict[str, Any] = Depends(get_current_user)):
    """Get current user information"""
    logger.info("User info requested", user_id=user["id"])
    
    try:
        # Return Supabase-aligned user information
        return {
            "success": True,
            "message": "User information retrieved successfully",
            "data": {
                "user": {
                    "id": user["id"],
                    "email": user["email"],
                    "user_metadata": user.get("user_metadata", {}),
                    "app_metadata": user.get("app_metadata", {})
                }
            }
        }
    except Exception as e:
        logger.error("Failed to get user info", exception=e, user_id=user["id"])
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve user information"
        ) 