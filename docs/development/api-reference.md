# AI Agent Template - API Documentation

> **Complete API Reference** - Comprehensive guide to the Generic Agent Framework API

This document provides complete API documentation for the AI Agent Template v2.0, featuring a fully generic agent framework with dynamic discovery and zero configuration. All endpoints are also available through the interactive documentation at `http://localhost:8000/docs` when the server is running.

## Base URL

```
http://localhost:8000
```

## Authentication

Most endpoints require JWT authentication. Include the token in the Authorization header:

```http
Authorization: Bearer <your-jwt-token>
```

**Getting a Token:** Use the Supabase authentication system via the frontend or directly through Supabase APIs.

## Response Format

All API responses follow a consistent format:

### Success Response
```json
{
  "success": true,
  "message": "Operation successful",
  "timestamp": "2024-01-01T10:00:00Z",
  // ... additional response data
}
```

### Error Response
```json
{
  "success": false,
  "message": "Error description",
  "error_code": "ERROR_CODE",
  "details": {
    "field": ["Validation error message"]
  },
  "timestamp": "2024-01-01T10:00:00Z"
}
```

### Agent-Specific Errors
The framework includes specialized error handling for agent-related issues:

```json
{
  "error": "AgentNotFoundError",
  "message": "Agent 'unknown_agent' not found",
  "status_code": 404,
  "agent_identifier": "unknown_agent",
  "suggestion": "Check available agents using GET /agents endpoint"
}
```

```json
{
  "error": "AgentDisabledError", 
  "message": "Agent 'disabled_agent' is disabled and not available for use",
  "status_code": 400,
  "agent_identifier": "disabled_agent",
  "lifecycle_state": "disabled",
  "suggestion": "Agent is not enabled or has load errors. Check agent status or contact administrator."
}
```

## Key Framework Features

### Dynamic Agent Discovery
- **Zero Configuration:** Agents are automatically discovered by dropping Python files in the `agents/` directory
- **No Hardcoding:** No need to modify framework code when adding new agents
- **Metadata Extraction:** Agent information is extracted automatically using Python introspection
- **Schema Discovery:** Job data schemas are dynamically extracted from Pydantic models

### Generic Job Processing
- **Any Agent Type:** Create jobs for any discovered agent using string identifiers
- **Dynamic Validation:** Job data is validated against agent-specific Pydantic schemas
- **Flexible Data:** Job data structure is determined by individual agents, not the framework

### Consistent Error Handling
- **Standardized Responses:** All agent-related errors follow the same format
- **Helpful Messages:** Errors include suggestions for resolution
- **Proper HTTP Codes:** 404 for not found, 400 for disabled, 503 for not loaded

## API Endpoints

### 1. System Health & Information

#### Get Health Status
```http
GET /health
```

**Description:** Comprehensive health check with system information.

**Authentication:** None required

**Response:**
```json
{
  "status": "healthy",
  "version": "2.0.0",
  "environment": "development",
  "framework_version": "2.0",
  "cors_origins": 3,
  "debug": true,
  "agent_status": {
    "total_agents": 3,
    "enabled_agents": 2,
    "disabled_agents": 1,
    "current_environment": "dev"
  },
  "timestamp": "2024-01-01T10:00:00Z",
  "performance_metrics": {
    "total_operations": 1250,
    "average_response_time": 0.25
  }
}
```

#### Get Basic Status
```http
GET /
```

**Description:** Simple health check endpoint.

**Authentication:** None required

**Response:**
```json
{
  "message": "AI Agent Template v2.0 is running",
  "status": "healthy",
  "version": "2.0.0",
  "environment": "development",
  "framework_version": "2.0",
  "agent_framework": "self-contained",
  "timestamp": "2024-01-01T10:00:00Z"
}
```

#### Get CORS Information
```http
GET /cors-info
```

**Description:** CORS configuration details (development only).

**Authentication:** None required

**Response:**
```json
{
  "cors_origins": ["http://localhost:5173", "http://localhost:3000"],
  "environment": "development",
  "allow_credentials": true,
  "max_age": 86400,
  "message": "CORS configuration (development mode)"
}
```

### 2. Authentication

#### Get Current User Info
```http
GET /auth/me
```

**Description:** Get information about the currently authenticated user.

**Authentication:** Required

**Response:**
```json
{
  "user": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "email": "user@example.com",
    "metadata": {
      "name": "John Doe"
    },
    "app_metadata": {
      "roles": ["user"]
    },
    "created_at": "2024-01-01T00:00:00Z"
  },
  "message": "Authentication successful"
}
```

### 3. Agent Discovery & Management

The Generic Agent Framework automatically discovers agents from the `agents/` directory and provides dynamic access to their capabilities.

#### List All Agents
```http
GET /agents
```

**Description:** Get information about all discovered agents and their metadata.

**Authentication:** None required

**Response:**
```json
{
  "status": "success",
  "framework_version": "2.0",
  "discovery_system": "agent_discovery",
  "discovery_stats": {
    "total_scanned": 3,
    "total_loaded": 2,
    "total_failed": 1,
    "last_scan": "2024-01-01T10:00:00Z",
    "scan_duration": 0.123
  },
  "agents": {
    "simple_example": {
      "identifier": "simple_example",
      "name": "Simple Example Agent",
      "description": "Simple prompt processing agent",
      "class_name": "SimplePromptAgent",
      "lifecycle_state": "enabled",
      "supported_environments": ["all"],
      "version": "1.0.0",
      "enabled": true,
      "has_error": false,
      "error_message": null,
      "created_at": "2024-01-01T09:00:00Z",
      "last_updated": "2024-01-01T09:00:00Z"
    },
    "my_custom_agent": {
      "identifier": "my_custom_agent",
      "name": "My Custom Agent",
      "description": "Custom business logic agent",
      "class_name": "MyCustomAgent",
      "lifecycle_state": "enabled",
      "supported_environments": ["dev", "prod"],
      "version": "2.1.0",
      "enabled": true,
      "has_error": false,
      "error_message": null,
      "created_at": "2024-01-01T08:30:00Z",
      "last_updated": "2024-01-01T09:15:00Z"
    }
  },
  "summary": {
    "total_agents": 2,
    "enabled_agents": 2,
    "disabled_agents": 0,
    "current_environment": "dev"
  }
}
```

#### Get Specific Agent Info
```http
GET /agents/{agent_identifier}
```

**Description:** Get detailed information about a specific agent, including runtime status.

**Authentication:** None required

**Path Parameters:**
- `agent_identifier` (string): Identifier of the agent (e.g., "simple_example")

**Response:**
```json
{
  "status": "success",
  "agent": {
    "identifier": "simple_example",
    "name": "Simple Example Agent",
    "description": "Simple prompt processing agent",
    "class_name": "SimplePromptAgent",
    "module_path": "agents.simple_example_agent",
    "lifecycle_state": "enabled",
    "supported_environments": ["all"],
    "version": "1.0.0",
    "enabled": true,
    "has_error": false,
    "error_message": null,
    "created_at": "2024-01-01T09:00:00Z",
    "last_updated": "2024-01-01T09:00:00Z",
    "metadata_extras": {},
    "instance_available": true,
    "runtime_info": {
      "endpoints": [
        {
          "path": "/simple-prompt/process",
          "methods": ["POST"],
          "auth_required": true,
          "public": false
        }
      ],
      "models": ["PromptJobData"],
      "framework_version": "2.0",
      "self_contained": true,
      "google_ai_integration": true,
      "google_ai_stats": {
        "total_requests": 42,
        "success_rate": 0.95,
        "average_response_time": 1.23
      },
      "google_ai_connection": "active"
    }
  }
}
```

#### Get Agent Health
```http
GET /agents/{agent_identifier}/health
```

**Description:** Check the health status of a specific agent (requires agent to be loaded).

**Authentication:** None required

**Path Parameters:**
- `agent_identifier` (string): Identifier of the agent

**Response:**
```json
{
  "status": "success",
  "health": {
    "status": "healthy",
    "agent_identifier": "simple_example",
    "instance_loaded": true,
    "last_check": "2024-01-01T10:00:00Z",
    "response_time_ms": 45,
    "endpoints_registered": 1,
    "models_available": 1,
    "google_ai_connection": "active"
  }
}
```

#### Get Agent Schema
```http
GET /agents/{agent_identifier}/schema
```

**Description:** Get job data schema for an agent to enable dynamic form generation.

**Authentication:** None required

**Path Parameters:**
- `agent_identifier` (string): Identifier of the agent

**Response:**
```json
{
  "status": "success",
  "agent_id": "simple_example",
  "agent_name": "Simple Example Agent",
  "description": "Simple prompt processing agent",
  "available_models": ["PromptJobData"],
  "schemas": {
    "PromptJobData": {
      "model_name": "PromptJobData",
      "model_class": "PromptJobData",
      "title": "PromptJobData",
      "description": "Simple prompt job data model",
      "type": "object",
      "properties": {
        "prompt": {
          "type": "string",
          "description": "Text prompt to send to LLM",
          "form_field_type": "textarea"
        },
        "max_tokens": {
          "type": "integer",
          "default": 1000,
          "description": "Maximum tokens in response",
          "form_field_type": "number"
        }
      },
      "required": ["prompt"],
      "definitions": {}
    }
  }
}
```

### 4. Job Management

#### Create Job
```http
POST /jobs
```

**Description:** Create a new job for processing by any available agent. Job data is automatically validated against the agent's schema.

**Authentication:** Required

**Request Body:**
```json
{
  "agent_identifier": "simple_example",
  "data": {
    "prompt": "Write a short story about a robot learning to paint",
    "max_tokens": 1500
  },
  "priority": 5,
  "tags": ["creative", "story"]
}
```

**Response:**
```json
{
  "success": true,
  "message": "Job created and queued for processing",
  "job_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Error Response (Validation Failed):**
```json
{
  "message": "Job data validation failed",
  "agent_identifier": "simple_example",
  "validation_errors": [
    {
      "field": "prompt",
      "message": "field required",
      "type": "value_error.missing"
    }
  ],
  "expected_schema": {
    "model_name": "PromptJobData",
    "available_models": ["PromptJobData"],
    "schema": {
      "type": "object",
      "properties": {
        "prompt": {"type": "string"},
        "max_tokens": {"type": "integer", "default": 1000}
      },
      "required": ["prompt"]
    }
  }
}
```

#### Validate Job Data
```http
POST /jobs/validate
```

**Description:** Validate job data against an agent's schema without creating a job.

**Authentication:** Required

**Request Body:**
```json
{
  "agent_identifier": "simple_example",
  "data": {
    "prompt": "Test prompt",
    "max_tokens": 500
  }
}
```

**Response:**
```json
{
  "success": true,
  "message": "Job data validation completed",
  "validation_result": {
    "valid": true,
    "agent_identifier": "simple_example",
    "model_used": "PromptJobData",
    "errors": [],
    "warnings": [],
    "schema_info": {
      "model_name": "PromptJobData",
      "available_models": ["PromptJobData"]
    },
    "validated_data": {
      "prompt": "Test prompt",
      "max_tokens": 500
    }
  }
}
```

#### List Jobs
```http
GET /jobs?limit=50&offset=0
```

**Description:** Get a paginated list of jobs for the authenticated user.

**Authentication:** Required

**Query Parameters:**
- `limit` (integer, optional): Number of jobs to return (default: 50, max: 100)
- `offset` (integer, optional): Number of jobs to skip (default: 0)

**Response:**
```json
{
  "success": true,
  "message": "Jobs retrieved successfully",
  "jobs": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "status": "completed",
      "agent_identifier": "simple_example",
      "data": {
        "prompt": "Write a short story",
        "max_tokens": 1500
      },
      "result": "Once upon a time, in a world where artificial intelligence...",
      "error_message": null,
      "created_at": "2024-01-01T10:00:00Z",
      "updated_at": "2024-01-01T10:01:30Z"
    }
  ],
  "total_count": 1
}
```

#### Get Job Details
```http
GET /jobs/{job_id}
```

**Description:** Get detailed information about a specific job.

**Authentication:** Required

**Path Parameters:**
- `job_id` (string): Unique job identifier

**Response:**
```json
{
  "success": true,
  "message": "Job details retrieved successfully",
  "job": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "running",
    "agent_identifier": "simple_example",
    "data": {
      "prompt": "Write a short story about a robot learning to paint",
      "max_tokens": 1500
    },
    "result": null,
    "error_message": null,
    "created_at": "2024-01-01T10:00:00Z",
    "updated_at": "2024-01-01T10:00:30Z"
  }
}
```

#### Retry Job
```http
POST /jobs/{job_id}/retry
```

**Description:** Retry a failed job. Validates that the agent is still available and job data still meets current schema requirements.

**Authentication:** Required

**Path Parameters:**
- `job_id` (string): Unique job identifier

**Response:**
```json
{
  "success": true,
  "message": "Job retried successfully",
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "pending",
    "agent_identifier": "simple_example",
    "data": {
      "prompt": "Write a short story",
      "max_tokens": 1500
    },
    "result": null,
    "error_message": null,
    "created_at": "2024-01-01T10:00:00Z",
    "updated_at": "2024-01-01T10:05:00Z"
  }
}
```

**Error Response (Schema Changed):**
```json
{
  "message": "Cannot retry job - existing job data no longer meets agent requirements",
  "job_id": "550e8400-e29b-41d4-a716-446655440000", 
  "agent_identifier": "simple_example",
  "validation_errors": [
    {
      "field": "new_required_field",
      "message": "field required",
      "type": "value_error.missing"
    }
  ],
  "expected_schema": {
    "model_name": "PromptJobData",
    "available_models": ["PromptJobData"]
  },
  "suggestion": "The agent schema may have changed since this job was created. Please create a new job with updated data."
}
```

#### Delete Job
```http
DELETE /jobs/{job_id}
```

**Description:** Delete a specific job.

**Authentication:** Required

**Path Parameters:**
- `job_id` (string): Unique job identifier

**Response:**
```json
{
  "success": true,
  "message": "Job deleted successfully",
  "job_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

#### Get Job Status
```http
GET /jobs/{job_id}/status
```

**Description:** Get just the status of a specific job (lightweight endpoint).

**Authentication:** Required

**Path Parameters:**
- `job_id` (string): Unique job identifier

**Response:**
```json
{
  "success": true,
  "message": "Job status retrieved",
  "data": {
    "status": "running"
  }
}
```

#### Get Batch Job Status
```http
POST /jobs/batch/status
```

**Description:** Get status of multiple jobs in a single request.

**Authentication:** Required

**Request Body:**
```json
{
  "job_ids": [
    "550e8400-e29b-41d4-a716-446655440000",
    "550e8400-e29b-41d4-a716-446655440001"
  ]
}
```

**Response:**
```json
{
  "success": true,
  "message": "Batch job status retrieved",
  "data": {
    "550e8400-e29b-41d4-a716-446655440000": {
      "status": "completed",
      "updated_at": "2024-01-01T10:01:30Z"
    },
    "550e8400-e29b-41d4-a716-446655440001": {
      "status": "running",
      "updated_at": "2024-01-01T10:00:45Z"
    }
  }
}
```

#### Get Minimal Jobs
```http
GET /jobs/minimal?limit=50&offset=0
```

**Description:** Get minimal job data for polling (lighter weight than full job list).

**Authentication:** Required

**Query Parameters:**
- `limit` (integer, optional): Number of jobs to return (default: 50)
- `offset` (integer, optional): Number of jobs to skip (default: 0)

**Response:**
```json
{
  "success": true,
  "message": "Minimal jobs retrieved",
  "data": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "status": "completed",
      "updated_at": "2024-01-01T10:01:30Z"
    }
  ]
}
```

#### Get Job Logs
```http
GET /jobs/{job_id}/logs
```

**Description:** Get execution logs for a specific job.

**Authentication:** Required

**Path Parameters:**
- `job_id` (string): Unique job identifier

**Response:**
```json
{
  "success": true,
  "message": "Job logs retrieved",
  "data": [
    "Job 550e8400-e29b-41d4-a716-446655440000 created at 2024-01-01T10:00:00Z",
    "Current status: completed",
    "Last updated: 2024-01-01T10:01:30Z",
    "Result available: 284 characters"
  ]
}
```

### 5. Job Pipeline Management

#### Get Pipeline Status
```http
GET /pipeline/status
```

**Description:** Get current status and metrics of the job processing pipeline.

**Authentication:** Required

**Response:**
```json
{
  "success": true,
  "message": "Pipeline status retrieved",
  "status": {
    "is_running": true,
    "worker_count": 4,
    "queue_size": 12,
    "processing_jobs": 3,
    "total_processed": 1247,
    "success_rate": 0.97,
    "average_processing_time": 2.34,
    "last_activity": "2024-01-01T10:00:00Z"
  },
  "timestamp": "2024-01-01T10:00:00Z"
}
```

#### Get Pipeline Metrics
```http
GET /pipeline/metrics
```

**Description:** Get detailed pipeline performance metrics.

**Authentication:** Required

**Response:**
```json
{
  "success": true,
  "message": "Pipeline metrics retrieved",
  "status": {
    "is_running": true,
    "performance": {
      "jobs_per_minute": 15.7,
      "average_queue_time": 0.45,
      "average_processing_time": 2.34,
      "peak_throughput": 25.2,
      "success_rate": 0.97
    },
    "resource_usage": {
      "cpu_percent": 34.2,
      "memory_mb": 512,
      "active_workers": 4,
      "max_workers": 8
    }
  },
  "timestamp": "2024-01-01T10:00:00Z"
}
```

## Dynamic Agent Endpoints

The Generic Agent Framework automatically generates endpoints for each discovered agent based on their `@endpoint` decorators. These endpoints are agent-specific and provide direct access to agent functionality.

### Pattern
```http
GET|POST /agent-identifier/endpoint-path
```

### Example: Simple Example Agent
```http
POST /simple-prompt/process
```

**Authentication:** Varies by agent (most require authentication)

**Request Body:**
```json
{
  "prompt": "Write a haiku about artificial intelligence",
  "max_tokens": 100
}
```

**Response:**
```json
{
  "success": true,
  "result": {
    "response": "Silicon minds think\nIn patterns beyond our scope\nWisdom made of code",
    "metadata": {
      "prompt_length": 46,
      "response_tokens": 18,
      "processing_time": 1.23
    }
  },
  "processing_time": 1.23,
  "timestamp": "2024-01-01T10:00:00Z"
}
```

### Discovering Agent Endpoints
Use the agent info endpoint to discover available endpoints for any agent:

```http
GET /agents/{agent_identifier}
```

The response includes runtime information with available endpoints:
```json
{
  "agent": {
    "runtime_info": {
      "endpoints": [
        {
          "path": "/simple-prompt/process",
          "methods": ["POST"],
          "auth_required": true,
          "public": false
        }
      ]
    }
  }
}
```

## Google AI Integration

### Validate Google AI Setup
```http
GET /google-ai/validate
```

**Description:** Validate Google AI configuration.

**Authentication:** None required

**Response:**
```json
{
  "status": "valid",
  "message": "Google AI is properly configured",
  "config": {
    "service": "Google AI Studio",
    "default_model": "gemini-2.0-flash",
    "use_vertex_ai": false
  }
}
```

### Get Available Models
```http
GET /google-ai/models
```

**Description:** Get list of available Google AI models.

**Authentication:** None required

**Response:**
```json
{
  "status": "success",
  "available_models": [
    "gemini-2.0-flash",
    "gemini-1.5-pro",
    "gemini-1.5-flash"
  ],
  "default_model": "gemini-2.0-flash",
  "service": "Google AI Studio"
}
```

### Test Google AI Connection
```http
GET /google-ai/connection-test
```

**Description:** Test connection to Google AI services.

**Authentication:** None required

**Response:**
```json
{
  "status": "success",
  "message": "Successfully connected to Google AI services",
  "service": "Google AI Studio",
  "model": "gemini-2.0-flash"
}
```

## Agent Configuration Management

### List Agent Configs
```http
GET /config/agents
```

**Description:** Get list of all agent configurations.

**Authentication:** Required

**Response:**
```json
{
  "success": true,
  "message": "Agent configurations retrieved",
  "configs": {
    "simple_example": {
      "name": "Simple Example Agent",
      "description": "Simple prompt processing agent",
      "profile": "balanced",
      "performance_mode": "balanced",
      "enabled": true
    }
  },
  "total_count": 1
}
```

### Get Agent Config
```http
GET /config/agents/{agent_name}
```

**Description:** Get detailed configuration for a specific agent.

**Authentication:** Required

**Response:**
```json
{
  "success": true,
  "message": "Configuration retrieved for agent: simple_example",
  "config": {
    "name": "Simple Example Agent",
    "description": "Simple prompt processing agent",
    "profile": "balanced",
    "performance_mode": "balanced",
    "enabled": true,
    "timeout_seconds": 300,
    "max_retries": 3,
    "model_settings": {
      "temperature": 0.7,
      "max_tokens": 2000
    }
  }
}
```

### Update Agent Config
```http
PUT /config/agents/{agent_name}
```

**Description:** Update configuration for a specific agent.

**Authentication:** Required

**Request Body:**
```json
{
  "profile": "fast",
  "performance_mode": "speed",
  "timeout_seconds": 60
}
```

**Response:**
```json
{
  "success": true,
  "message": "Configuration updated for agent: simple_example",
  "config": {
    "name": "Simple Example Agent",
    "profile": "fast",
    "performance_mode": "speed",
    "timeout_seconds": 60,
    "max_retries": 1,
    "model_settings": {
      "temperature": 0.3,
      "max_tokens": 1000
    }
  }
}
```

## Error Codes & HTTP Status Codes

| HTTP Code | Error Type | Description | Example |
|-----------|------------|-------------|---------|
| `404` | `AgentNotFoundError` | Agent doesn't exist | Agent 'unknown_agent' not found |
| `400` | `AgentDisabledError` | Agent is disabled or has errors | Agent 'my_agent' is disabled |
| `503` | `AgentNotLoadedError` | Agent exists but not loaded | Agent 'my_agent' is not currently loaded |
| `400` | `ValidationError` | Job data validation failed | Required field 'prompt' missing |
| `401` | `AuthenticationError` | Invalid or missing token | Authorization header required |
| `403` | `AuthorizationError` | Access denied | User not authorized for this operation |
| `429` | `RateLimitError` | Too many requests | Rate limit exceeded |
| `500` | `InternalError` | Server processing error | Unexpected server error |

### Agent Error Suggestions

Each agent error includes helpful suggestions:
- **AgentNotFoundError:** "Check available agents using GET /agents endpoint"
- **AgentDisabledError:** "Agent is not enabled or has load errors. Check agent status or contact administrator."
- **AgentNotLoadedError:** "Agent exists but is not currently loaded. Try again later or contact administrator."

## Rate Limiting

- **Default Limit:** 100 requests per minute per user
- **Burst Limit:** 20 requests per 10 seconds
- **Headers:** Rate limit information is included in response headers:
  - `X-RateLimit-Limit`: Requests allowed per window
  - `X-RateLimit-Remaining`: Requests remaining in current window
  - `X-RateLimit-Reset`: Time when the rate limit resets

## Development & Testing

### Using curl
```bash
# Get health status
curl http://localhost:8000/health

# List discovered agents
curl http://localhost:8000/agents

# Get agent schema for form generation
curl http://localhost:8000/agents/simple_example/schema

# Validate job data
curl -X POST http://localhost:8000/jobs/validate \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_identifier": "simple_example",
    "data": {"prompt": "Test prompt", "max_tokens": 500}
  }'

# Create a job
curl -X POST http://localhost:8000/jobs \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_identifier": "simple_example",
    "data": {"prompt": "Write a story", "max_tokens": 1500},
    "priority": 5,
    "tags": ["creative"]
  }'
```

### Interactive Documentation
Visit `http://localhost:8000/docs` for a complete interactive API explorer with:
- Live endpoint testing
- Request/response examples
- Schema validation
- Authentication testing
- Real-time agent discovery

### Adding New Agents

1. **Create Agent File:** Drop a new Python file in `backend/agents/`
2. **Define Schema:** Use `@job_model` decorator on Pydantic models
3. **Add Endpoints:** Use `@endpoint` decorator on methods
4. **Inherit Framework:** Extend `SelfContainedAgent` class
5. **Zero Configuration:** Agent is automatically discovered and available

Example:
```python
# backend/agents/my_new_agent.py
from agent_framework import SelfContainedAgent, endpoint, job_model
from pydantic import BaseModel, Field

@job_model  
class MyJobData(BaseModel):
    prompt: str = Field(..., description="Text to process")
    option: str = Field("default", description="Processing option")

class MyNewAgent(SelfContainedAgent):
    def __init__(self, **kwargs):
        super().__init__(description="My custom agent", **kwargs)
    
    @endpoint("/my-new-agent/process", methods=["POST"], auth_required=True)
    async def process(self, request_data: dict, user: dict):
        job_data = validate_job_data(request_data, MyJobData)
        return await execute_agent_job(self, job_data, user["id"])
        
    async def _execute_job_logic(self, job_data: MyJobData):
        # Your custom logic here
        result = f"Processed: {job_data.prompt}"
        return AgentExecutionResult(success=True, result=result)
```