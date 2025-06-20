"""
API Response Utility Functions

Helper functions for creating consistent ApiResponse instances across all endpoints.
These utilities ensure uniform response patterns throughout the AI Agent Platform.
"""

from typing import Optional, Any, Dict, List, Type, TypeVar, Union
from datetime import datetime
from pydantic import ValidationError, BaseModel
from functools import wraps
from fastapi import HTTPException

from models import ApiResponse, T


def create_success_response(
    result: Optional[T] = None,
    message: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> ApiResponse[T]:
    """
    Create a successful ApiResponse instance.
    
    Args:
        result: The response data to include
        message: Optional success message
        metadata: Optional additional metadata
        
    Returns:
        ApiResponse instance with success=True and provided data
        
    Example:
        response = create_success_response(
            result={"id": "123", "status": "completed"},
            message="Operation completed successfully",
            metadata={"timestamp": datetime.utcnow().isoformat()}
        )
    """
    return ApiResponse[T](
        success=True,
        result=result,
        message=message,
        error=None,
        metadata=metadata
    )


def create_error_response(
    error_message: str,
    message: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> ApiResponse[None]:
    """
    Create an error ApiResponse instance.
    
    Args:
        error_message: The error description
        message: Optional human-readable message
        metadata: Optional additional error metadata (e.g., error_code, timestamp)
        
    Returns:
        ApiResponse instance with success=False and error details
        
    Example:
        response = create_error_response(
            error_message="Invalid input parameters",
            message="Validation failed",
            metadata={"error_code": "VALIDATION_ERROR", "timestamp": datetime.utcnow().isoformat()}
        )
    """
    return ApiResponse[None](
        success=False,
        result=None,
        message=message,
        error=error_message,
        metadata=metadata
    )


def create_validation_error_response(
    validation_errors: List[Dict[str, Any]],
    message: Optional[str] = None
) -> ApiResponse[None]:
    """
    Create an ApiResponse for Pydantic validation errors.
    
    Args:
        validation_errors: List of validation error details from Pydantic
        message: Optional custom message (defaults to validation summary)
        
    Returns:
        ApiResponse instance with formatted validation errors
        
    Example:
        try:
            model = SomeModel(**data)
        except ValidationError as e:
            return create_validation_error_response(
                validation_errors=e.errors(),
                message="Input validation failed"
            )
    """
    if message is None:
        error_count = len(validation_errors)
        message = f"Validation failed with {error_count} error{'s' if error_count != 1 else ''}"
    
    # Format validation errors for the error message
    error_summary = "; ".join([
        f"{err.get('loc', ['unknown'])[0] if err.get('loc') else 'unknown'}: {err.get('msg', 'validation error')}"
        for err in validation_errors[:3]  # Show first 3 errors
    ])
    
    if len(validation_errors) > 3:
        error_summary += f" (and {len(validation_errors) - 3} more)"
    
    return ApiResponse[None](
        success=False,
        result=None,
        message=message,
        error=error_summary,
        metadata={
            "error_type": "validation_error",
            "error_count": len(validation_errors),
            "validation_errors": validation_errors,
            "timestamp": datetime.utcnow().isoformat()
        }
    )


# Response Model Validation Utilities

def validate_api_response_format(response_data: Any, expected_result_type: Optional[Type] = None) -> bool:
    """
    Validate that response data follows ApiResponse format.
    
    Args:
        response_data: The response data to validate
        expected_result_type: Optional expected type for the result field
        
    Returns:
        True if valid ApiResponse format, False otherwise
    """
    if not isinstance(response_data, dict):
        return False
    
    required_fields = {"success", "result", "message", "error", "metadata"}
    if not required_fields.issubset(response_data.keys()):
        return False
    
    # Validate field types
    if not isinstance(response_data["success"], bool):
        return False
    
    if response_data["message"] is not None and not isinstance(response_data["message"], str):
        return False
    
    if response_data["error"] is not None and not isinstance(response_data["error"], str):
        return False
    
    if response_data["metadata"] is not None and not isinstance(response_data["metadata"], dict):
        return False
    
    # Validate result type if specified
    if expected_result_type and response_data["result"] is not None:
        try:
            if issubclass(expected_result_type, BaseModel):
                expected_result_type(**response_data["result"])
            else:
                # For non-Pydantic types, basic type checking
                if not isinstance(response_data["result"], expected_result_type):
                    return False
        except (TypeError, ValidationError):
            return False
    
    return True


def api_response_validator(result_type: Optional[Type] = None):
    """
    Decorator to validate that endpoint returns proper ApiResponse format.
    
    Args:
        result_type: Expected type for the result field
        
    Usage:
        @api_response_validator(result_type=JobResponse)
        @router.get("/jobs/{job_id}")
        async def get_job(job_id: str):
            return create_success_response(result=job_data)
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                response = await func(*args, **kwargs)
                
                # If response is already an ApiResponse instance, validate it
                if isinstance(response, ApiResponse):
                    return response
                
                # If response is a dict, validate format
                if isinstance(response, dict):
                    if validate_api_response_format(response, result_type):
                        return response
                    else:
                        # Response doesn't match ApiResponse format
                        return create_error_response(
                            error_message="Response format validation failed",
                            message="Internal server error",
                            metadata={
                                "error_code": "RESPONSE_FORMAT_ERROR",
                                "timestamp": datetime.utcnow().isoformat()
                            }
                        )
                
                # Response is not in expected format
                return create_error_response(
                    error_message="Unexpected response format",
                    message="Internal server error", 
                    metadata={
                        "error_code": "UNEXPECTED_RESPONSE_FORMAT",
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
                
            except Exception as e:
                # Handle any exceptions during validation
                return create_error_response(
                    error_message=str(e),
                    message="Response validation error",
                    metadata={
                        "error_code": "RESPONSE_VALIDATION_ERROR",
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
        
        return wrapper
    return decorator 