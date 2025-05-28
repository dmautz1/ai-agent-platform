"""
Pydantic models for request/response validation and serialization.
This module will be implemented in task 1.6.
"""

from pydantic import BaseModel, Field, validator, EmailStr
from typing import Optional, Any, Dict, List, Union
from datetime import datetime
from enum import Enum
import uuid

# Placeholder - will be implemented in task 1.6
class JobStatus(str, Enum):
    """Job status enumeration"""
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"

# Additional models will be added in task 1.6 

# Enums
class JobType(str, Enum):
    """Job type enumeration"""
    text_processing = "text_processing"
    text_summarization = "text_summarization"
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

# Job Data Models
class JobDataBase(BaseModel):
    """Base model for job data"""
    job_type: JobType
    agent_type: AgentType = AgentType.google_adk
    metadata: Optional[Dict[str, Any]] = None

class TextProcessingJobData(JobDataBase):
    """Text processing job data model"""
    job_type: JobType = Field(default=JobType.text_processing, const=True)
    text: str = Field(..., min_length=1, max_length=50000, description="Text to process")
    operation: str = Field(..., description="Processing operation to perform")
    parameters: Optional[Dict[str, Any]] = Field(default=None, description="Additional parameters")
    
    class Config:
        schema_extra = {
            "example": {
                "job_type": "text_processing",
                "text": "This is a sample text to process",
                "operation": "analyze_sentiment",
                "parameters": {"language": "en"}
            }
        }

class TextSummarizationJobData(JobDataBase):
    """Text summarization job data model"""
    job_type: JobType = Field(default=JobType.text_summarization, const=True)
    text: str = Field(..., min_length=1, max_length=100000, description="Text to summarize")
    max_length: Optional[int] = Field(default=150, ge=50, le=1000, description="Maximum summary length")
    min_length: Optional[int] = Field(default=30, ge=10, le=500, description="Minimum summary length")
    style: Optional[str] = Field(default="neutral", description="Summary style")
    
    @validator('min_length')
    def validate_min_length(cls, v, values):
        if 'max_length' in values and v >= values['max_length']:
            raise ValueError('min_length must be less than max_length')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "job_type": "text_summarization",
                "text": "Long article text to summarize...",
                "max_length": 150,
                "min_length": 50,
                "style": "neutral"
            }
        }

class WebScrapingJobData(JobDataBase):
    """Web scraping job data model"""
    job_type: JobType = Field(default=JobType.web_scraping, const=True)
    url: str = Field(..., description="URL to scrape")
    selectors: Optional[Dict[str, str]] = Field(default=None, description="CSS selectors for specific elements")
    options: Optional[Dict[str, Any]] = Field(default=None, description="Scraping options")
    
    @validator('url')
    def validate_url(cls, v):
        if not v.startswith(('http://', 'https://')):
            raise ValueError('URL must start with http:// or https://')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "job_type": "web_scraping",
                "url": "https://example.com",
                "selectors": {"title": "h1", "content": ".main-content"},
                "options": {"timeout": 30, "wait_for": "networkidle"}
            }
        }

class CustomJobData(JobDataBase):
    """Custom job data model"""
    job_type: JobType = Field(default=JobType.custom, const=True)
    custom_data: Dict[str, Any] = Field(..., description="Custom job data")
    
    class Config:
        schema_extra = {
            "example": {
                "job_type": "custom",
                "custom_data": {"operation": "custom_task", "parameters": {"key": "value"}}
            }
        }

# Union type for all job data types
JobData = Union[TextProcessingJobData, TextSummarizationJobData, WebScrapingJobData, CustomJobData]

# Job Request/Response Models
class JobCreateRequest(BaseModel):
    """Job creation request model"""
    data: JobData = Field(..., description="Job data based on job type")
    priority: Optional[int] = Field(default=0, ge=0, le=10, description="Job priority (0-10)")
    tags: Optional[List[str]] = Field(default=None, description="Job tags for organization")
    
    class Config:
        schema_extra = {
            "example": {
                "data": {
                    "job_type": "text_processing",
                    "text": "Sample text",
                    "operation": "analyze"
                },
                "priority": 1,
                "tags": ["analysis", "text"]
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
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "status": "completed",
                "data": {"job_type": "text_processing", "text": "Sample text"},
                "result": "Processing completed successfully",
                "error_message": None,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:01:00Z"
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
                "job_id": "123e4567-e89b-12d3-a456-426614174000"
            }
        }

class JobDetailResponse(BaseResponse):
    """Job detail response model"""
    job: JobResponse = Field(..., description="Job details")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "message": "Job retrieved successfully",
                "job": {
                    "id": "123e4567-e89b-12d3-a456-426614174000",
                    "status": "completed",
                    "data": {},
                    "result": "Job completed",
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-01T00:01:00Z"
                }
            }
        }

# Job Update Models
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

# Statistics Models
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
                "message": "Statistics retrieved successfully",
                "stats": {
                    "total_jobs": 100,
                    "completed_jobs": 85,
                    "failed_jobs": 8,
                    "success_rate": 91.4
                }
            }
        }

# Authentication Models
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
                    "email": "user@example.com"
                }
            }
        }

# Health Check Models
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
                "version": "1.0.0",
                "environment": "development",
                "cors_origins": 5,
                "timestamp": "2024-01-01T00:00:00Z"
            }
        } 