"""
Pydantic models for request/response validation and serialization.
Core models for the AI Agent Platform framework v1.0.

Job data models are now embedded in individual agent files using the @job_model decorator.
Updated to use generic string fields instead of hardcoded agent/job type enums.
"""

from pydantic import BaseModel, Field, validator, EmailStr, field_validator, ConfigDict, model_validator
from typing import Optional, Any, Dict, List, Union, Generic, TypeVar
from datetime import datetime
from enum import Enum
import uuid
import re

# TypeVar for generic ApiResponse typing
T = TypeVar('T')

# Unified API Response Model
class ApiResponse(BaseModel, Generic[T]):
    """
    Unified API response wrapper for all endpoints.
    
    Provides consistent response structure across the platform with:
    - success: Boolean indicating if the request was successful
    - result: The actual response data (generic type T)
    - message: Optional human-readable message
    - error: Optional error message for failed requests
    - metadata: Optional additional information about the response
    """
    success: bool = Field(..., description="Whether the request was successful")
    result: Optional[T] = Field(default=None, description="The response data")
    message: Optional[str] = Field(default=None, description="Human-readable message")
    error: Optional[str] = Field(default=None, description="Error message if request failed")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional response metadata")
    
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "description": "Successful response with result",
                    "value": {
                        "success": True,
                        "result": {"id": "123", "name": "Example"},
                        "message": "Operation completed successfully",
                        "error": None,
                        "metadata": {"timestamp": "2024-01-01T10:00:00Z", "version": "1.0"}
                    }
                },
                {
                    "description": "Error response",
                    "value": {
                        "success": False,
                        "result": None,
                        "message": "Operation failed",
                        "error": "Invalid input parameters",
                        "metadata": {"error_code": "VALIDATION_ERROR", "timestamp": "2024-01-01T10:00:00Z"}
                    }
                }
            ]
        }
    )

# Enums
class JobStatus(str, Enum):
    """Job status enumeration"""
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"

# User Models
class UserInfo(BaseModel):
    """User information model"""
    id: str
    email: EmailStr
    metadata: Optional[Dict[str, Any]] = None
    app_metadata: Optional[Dict[str, Any]] = None
    created_at: Optional[str] = None
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "email": "user@example.com",
                "metadata": {"name": "John Doe"},
                "app_metadata": {"role": "user"},
                "created_at": "2024-01-01T10:00:00Z"
            }
        }
    )

# Job Models (Generic - specific job data models are now in agent files)
class JobDataBase(BaseModel):
    """Base model for job data - uses generic string fields"""
    agent_identifier: str = Field(..., description="Agent identifier for processing this job")
    metadata: Optional[Dict[str, Any]] = None

# Union type for job data - will be dynamically populated by agent framework
JobData = Union[JobDataBase]  # This will be extended by the agent framework

class JobCreateRequest(BaseModel):
    """Job creation request model"""
    agent_identifier: str = Field(..., description="Identifier of the agent to process this job")
    data: Dict[str, Any] = Field(..., description="Job data (validated by specific agent)")
    title: str = Field(..., description="Job title for identification and organization")
    priority: Optional[int] = Field(default=0, ge=0, le=10, description="Job priority (0-10)")
    tags: Optional[List[str]] = Field(default=None, description="Job tags for organization")
    
    @field_validator('agent_identifier')
    @classmethod
    def validate_agent_identifier(cls, v):
        """Validate agent identifier is not empty"""
        if not v or not v.strip():
            raise ValueError('Agent identifier cannot be empty')
        return v.strip()
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "agent_identifier": "simple_prompt",
                "title": "Simple Prompt Job",
                "data": {
                    "prompt": "Hello, how are you?",
                    "max_tokens": 1000
                },
                "priority": 5,
                "tags": ["prompt", "simple"]
            }
        }
    )

class JobResponse(BaseModel):
    """Job response model"""
    id: str = Field(..., description="Job ID")
    status: JobStatus = Field(..., description="Current job status")
    agent_identifier: str = Field(..., description="Agent identifier that processed/will process this job")
    data: Dict[str, Any] = Field(..., description="Job input data")
    title: Optional[str] = Field(None, description="Human-readable job title")
    result: Optional[str] = Field(None, description="Job result")
    result_format: Optional[str] = Field(None, description="Format of the result data")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    created_at: datetime = Field(..., description="Job creation timestamp")
    updated_at: datetime = Field(..., description="Job last update timestamp")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "job_123",
                "status": "completed",
                "agent_identifier": "simple_prompt",
                "data": {"prompt": "Hello, how are you?", "max_tokens": 1000},
                "title": "Simple Prompt Job",
                "result": "Hello! I'm doing well, thank you for asking. How can I help you today?",
                "result_format": "markdown",
                "error_message": None,
                "created_at": "2024-01-01T10:00:00Z",
                "updated_at": "2024-01-01T10:01:00Z"
            }
        }
    )

class JobStatusUpdate(BaseModel):
    """Job status update model"""
    status: JobStatus = Field(..., description="New job status")
    result: Optional[str] = Field(None, description="Job result")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    
    @model_validator(mode='after')
    def validate_status_requirements(self):
        """Validate that required fields are present for specific statuses"""
        if self.status == JobStatus.completed and not self.result:
            raise ValueError('Result is required when status is completed')
        if self.status == JobStatus.failed and not self.error_message:
            raise ValueError('Error message is required when status is failed')
        return self

class JobStats(BaseModel):
    """Job statistics model"""
    total_jobs: int = Field(..., description="Total number of jobs")
    pending_jobs: int = Field(..., description="Number of pending jobs")
    running_jobs: int = Field(..., description="Number of running jobs")
    completed_jobs: int = Field(..., description="Number of completed jobs")
    failed_jobs: int = Field(..., description="Number of failed jobs")
    success_rate: float = Field(..., description="Job success rate percentage")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total_jobs": 100,
                "pending_jobs": 5,
                "running_jobs": 2,
                "completed_jobs": 85,
                "failed_jobs": 8,
                "success_rate": 91.4
            }
        }
    )

class HealthResponse(BaseModel):
    """Health check response model"""
    status: str = Field(..., description="API health status")
    version: str = Field(..., description="API version")
    environment: str = Field(..., description="Environment name")
    cors_origins: int = Field(..., description="Number of CORS origins configured")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "healthy",
                "version": "1.0.0",
                "environment": "development",
                "cors_origins": 3,
                "timestamp": "2024-01-01T10:00:00Z"
            }
        }
    ) 