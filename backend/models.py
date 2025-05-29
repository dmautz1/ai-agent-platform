"""
Pydantic models for request/response validation and serialization.
Core models for the AI Agent Template framework v2.0.

Job data models are now embedded in individual agent files using the @job_model decorator.
"""

from pydantic import BaseModel, Field, validator, EmailStr
from typing import Optional, Any, Dict, List, Union
from datetime import datetime
from enum import Enum
import uuid

# Enums
class JobStatus(str, Enum):
    """Job status enumeration"""
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"

class JobType(str, Enum):
    """Job type enumeration"""
    text_processing = "text_processing"
    text_summarization = "text_summarization"
    audio_summarization = "audio_summarization"
    video_summarization = "video_summarization"
    web_scraping = "web_scraping"
    custom = "custom"

class AgentType(str, Enum):
    """AI agent type enumeration"""
    google_adk = "google_adk"
    openai = "openai"
    custom = "custom"

# Base Models
class BaseResponse(BaseModel):
    """Base response model"""
    success: bool = True
    message: str = "Operation successful"
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ErrorResponse(BaseResponse):
    """Error response model"""
    success: bool = False
    error_code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

# User Models
class UserInfo(BaseModel):
    """User information model"""
    id: str
    email: EmailStr
    metadata: Optional[Dict[str, Any]] = None
    app_metadata: Optional[Dict[str, Any]] = None
    created_at: Optional[str] = None
    
    class Config:
        schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "email": "user@example.com",
                "metadata": {"name": "John Doe"},
                "app_metadata": {"roles": ["user"]},
                "created_at": "2024-01-01T00:00:00Z"
            }
        }

# Job Models (Generic - specific job data models are now in agent files)
class JobDataBase(BaseModel):
    """Base model for job data"""
    job_type: JobType
    agent_type: AgentType = AgentType.google_adk
    metadata: Optional[Dict[str, Any]] = None

# Union type for job data - will be dynamically populated by agent framework
JobData = Union[JobDataBase]  # This will be extended by the agent framework

class JobCreateRequest(BaseModel):
    """Job creation request model"""
    data: Dict[str, Any] = Field(..., description="Job data (validated by specific agent)")
    priority: Optional[int] = Field(default=0, ge=0, le=10, description="Job priority (0-10)")
    tags: Optional[List[str]] = Field(default=None, description="Job tags for organization")
    
    class Config:
        schema_extra = {
            "example": {
                "data": {
                    "text": "Sample text to process",
                    "operation": "analyze_sentiment"
                },
                "priority": 5,
                "tags": ["sentiment", "analysis"]
            }
        }

class JobResponse(BaseModel):
    """Job response model"""
    id: str = Field(..., description="Job ID")
    status: JobStatus = Field(..., description="Current job status")
    data: Dict[str, Any] = Field(..., description="Job input data")
    result: Optional[str] = Field(None, description="Job result")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    created_at: datetime = Field(..., description="Job creation timestamp")
    updated_at: datetime = Field(..., description="Job last update timestamp")
    
    class Config:
        schema_extra = {
            "example": {
                "id": "job_123",
                "status": "completed",
                "data": {"text": "Sample text", "operation": "analyze_sentiment"},
                "result": '{"sentiment": "positive", "confidence": 0.95}',
                "error_message": None,
                "created_at": "2024-01-01T10:00:00Z",
                "updated_at": "2024-01-01T10:01:00Z"
            }
        }

class JobListResponse(BaseResponse):
    """Job list response model"""
    jobs: List[JobResponse] = Field(..., description="List of jobs")
    total_count: int = Field(..., description="Total number of jobs")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "message": "Jobs retrieved successfully",
                "jobs": [],
                "total_count": 0
            }
        }

class JobCreateResponse(BaseResponse):
    """Job creation response model"""
    job_id: str = Field(..., description="Created job ID")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "message": "Job created successfully",
                "job_id": "job_123"
            }
        }

class JobDetailResponse(BaseResponse):
    """Job detail response model"""
    job: JobResponse = Field(..., description="Job details")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "message": "Job details retrieved successfully",
                "job": {
                    "id": "job_123",
                    "status": "completed",
                    "data": {"text": "Sample text"},
                    "result": '{"processed": true}',
                    "error_message": None,
                    "created_at": "2024-01-01T10:00:00Z",
                    "updated_at": "2024-01-01T10:01:00Z"
                }
            }
        }

class JobStatusUpdate(BaseModel):
    """Job status update model"""
    status: JobStatus = Field(..., description="New job status")
    result: Optional[str] = Field(None, description="Job result")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    
    @validator('result')
    def validate_result_with_status(cls, v, values):
        if values.get('status') == JobStatus.completed and not v:
            raise ValueError('Result is required when status is completed')
        return v
    
    @validator('error_message')
    def validate_error_with_status(cls, v, values):
        if values.get('status') == JobStatus.failed and not v:
            raise ValueError('Error message is required when status is failed')
        return v

class JobStats(BaseModel):
    """Job statistics model"""
    total_jobs: int = Field(..., description="Total number of jobs")
    pending_jobs: int = Field(..., description="Number of pending jobs")
    running_jobs: int = Field(..., description="Number of running jobs")
    completed_jobs: int = Field(..., description="Number of completed jobs")
    failed_jobs: int = Field(..., description="Number of failed jobs")
    success_rate: float = Field(..., description="Job success rate percentage")
    
    class Config:
        schema_extra = {
            "example": {
                "total_jobs": 100,
                "pending_jobs": 5,
                "running_jobs": 2,
                "completed_jobs": 85,
                "failed_jobs": 8,
                "success_rate": 91.4
            }
        }

class JobStatsResponse(BaseResponse):
    """Job statistics response model"""
    stats: JobStats = Field(..., description="Job statistics")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "message": "Job statistics retrieved successfully",
                "stats": {
                    "total_jobs": 100,
                    "pending_jobs": 5,
                    "running_jobs": 2,
                    "completed_jobs": 85,
                    "failed_jobs": 8,
                    "success_rate": 91.4
                }
            }
        }

class AuthResponse(BaseResponse):
    """Authentication response model"""
    user: UserInfo = Field(..., description="User information")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "message": "Authentication successful",
                "user": {
                    "id": "123e4567-e89b-12d3-a456-426614174000",
                    "email": "user@example.com",
                    "metadata": {"name": "John Doe"}
                }
            }
        }

class HealthResponse(BaseModel):
    """Health check response model"""
    status: str = Field(..., description="API health status")
    version: str = Field(..., description="API version")
    environment: str = Field(..., description="Environment name")
    cors_origins: int = Field(..., description="Number of CORS origins configured")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        schema_extra = {
            "example": {
                "status": "healthy",
                "version": "2.0.0",
                "environment": "development",
                "cors_origins": 3,
                "timestamp": "2024-01-01T10:00:00Z"
            }
        } 