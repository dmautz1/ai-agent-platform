# API Response Patterns

This document describes the unified `ApiResponse` pattern implemented across the AI Agent Platform backend.

## Overview

All endpoints in the AI Agent Platform now return responses in a consistent `ApiResponse<T>` format, providing:
- Uniform response structure across all endpoints
- Standardized error handling and metadata
- Type-safe generic responses
- Rich debugging and monitoring information

## ApiResponse Structure

```typescript
interface ApiResponse<T> {
    success: boolean;           // Operation success status
    result: T | null;          // Response data (null on error)
    message: string | null;    // Human-readable message
    error: string | null;      // Error description (null on success)
    metadata: object | null;   // Additional context and debugging info
}
```

## Core Utility Functions

### `create_success_response<T>(result, message?, metadata?)`

Creates a successful response with optional message and metadata:

```python
from utils.responses import create_success_response

response = create_success_response(
    result={"id": "job_123", "status": "completed"},
    message="Job completed successfully",
    metadata={
        "execution_time": 2.5,
        "timestamp": "2024-01-15T10:30:00Z"
    }
)
```

### `create_error_response(error_message, message?, metadata?)`

Creates an error response with descriptive error information:

```python
from utils.responses import create_error_response

response = create_error_response(
    error_message="Invalid job configuration: missing required field 'agent_name'",
    message="Job creation failed",
    metadata={
        "error_code": "VALIDATION_ERROR",
        "field": "agent_name",
        "timestamp": "2024-01-15T10:30:00Z"
    }
)
```

### `create_validation_error_response(validation_errors, message?)`

Creates a response for Pydantic validation errors:

```python
from utils.responses import create_validation_error_response

try:
    job_data = JobModel(**request_data)
except ValidationError as e:
    return create_validation_error_response(
        validation_errors=e.errors(),
        message="Invalid job data format"
    )
```

## Response Type Patterns

### Distributed Response Types

Each route module defines its own response types locally, providing better cohesion and maintainability:

```python
# In routes/jobs/management.py
JobListResponse = Dict[str, Union[List[Dict[str, Any]], int, str]]
JobDetailResponse = Dict[str, Any]
JobStatusResponse = Dict[str, Union[str, Dict[str, Any]]]

@router.get("/jobs/list", response_model=ApiResponse[JobListResponse])
@api_response_validator(result_type=JobListResponse)
async def list_jobs():
    # Implementation
    return create_success_response(result=jobs_data)
```

### Agent Framework Integration

Agent endpoints use helper methods from the `SelfContainedAgent` base class:

```python
class MyAgent(SelfContainedAgent):
    @endpoint("/my-agent/process", methods=["POST"])
    async def process_data(self, request_data: dict, user: dict):
        try:
            result = await self._process(request_data)
            return self.success_response(
                result=result,
                message="Processing completed successfully",
                endpoint="/my-agent/process"
            )
        except Exception as e:
            return self.error_response(
                error_message=str(e),
                message="Processing failed",
                endpoint="/my-agent/process"
            )
```

## Validation and Monitoring

### Response Validation Decorator

The `@api_response_validator` decorator ensures endpoints return proper `ApiResponse` format:

```python
from utils.responses import api_response_validator

@router.get("/jobs/{job_id}", response_model=ApiResponse[JobDetailResponse])
@api_response_validator(result_type=JobDetailResponse)
async def get_job(job_id: str):
    return create_success_response(result=job_data)
```

### Metadata Standards

All responses include rich metadata for debugging and monitoring:

```python
# Standard metadata fields
{
    "endpoint": "/jobs/create",
    "user_id": "user_123",
    "execution_time": 1.234,
    "timestamp": "2024-01-15T10:30:00Z",
    "operation": "job_creation"
}

# Error-specific metadata
{
    "error_code": "VALIDATION_ERROR",
    "error_type": "ValidationError",
    "field": "agent_name",
    "provided_value": null
}

# Agent-specific metadata
{
    "agent_name": "simple_prompt",
    "agent_framework": "self_contained",
    "provider": "google",
    "model": "gemini-2.0-flash"
}
```

## Error Handling Patterns

### Standard Error Codes

Common error codes used throughout the platform:

- `VALIDATION_ERROR` - Input validation failures
- `NOT_FOUND` - Resource not found
- `UNAUTHORIZED` - Authentication/authorization failures
- `RATE_LIMIT_EXCEEDED` - API rate limiting
- `INTERNAL_ERROR` - Unexpected server errors
- `AGENT_ERROR` - Agent-specific errors
- `INVALID_RESPONSE_TYPE` - Framework validation errors

### Error Response Examples

#### Validation Error
```json
{
    "success": false,
    "result": null,
    "message": "Invalid job data format",
    "error": "agent_name: field required; data: field required",
    "metadata": {
        "error_type": "validation_error",
        "error_count": 2,
        "validation_errors": [...],
        "timestamp": "2024-01-15T10:30:00Z"
    }
}
```

#### Resource Not Found
```json
{
    "success": false,
    "result": null,
    "message": "Job not found",
    "error": "Job with ID 'job_123' not found or access denied",
    "metadata": {
        "error_code": "JOB_NOT_FOUND",
        "job_id": "job_123",
        "user_id": "user_456",
        "timestamp": "2024-01-15T10:30:00Z"
    }
}
```

#### Agent Error
```json
{
    "success": false,
    "result": null,
    "message": "Agent operation failed",
    "error": "Failed to process prompt: API rate limit exceeded",
    "metadata": {
        "agent_name": "simple_prompt",
        "error_type": "RateLimitError",
        "endpoint": "/simple-prompt/process",
        "execution_time": 0.5,
        "timestamp": "2024-01-15T10:30:00Z"
    }
}
```
