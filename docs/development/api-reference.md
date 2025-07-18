# AI Agent Platform - API Documentation

> **Complete API Reference** - Comprehensive guide to the Generic Agent Framework API

This document provides complete API documentation for the AI Agent Platform v1.0, featuring a fully generic agent framework with dynamic discovery and zero configuration. All endpoints are also available through the interactive documentation at `http://localhost:8000/docs` when the server is running.

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

All API responses follow a consistent `ApiResponse<T>` format for standardized client handling:

### ApiResponse Structure
```typescript
interface ApiResponse<T> {
  success: boolean;           // Whether the request was successful
  result: T | null;          // The response data (null for errors)
  message: string | null;    // Human-readable message
  error: string | null;      // Error message (null for success)
  metadata: object | null;   // Additional response metadata
}
```

### Success Response Example
```json
{
  "success": true,
  "result": {
    "id": "123",
    "status": "completed",
    "data": "..." 
  },
  "message": "Operation completed successfully",
  "error": null,
  "metadata": {
    "timestamp": "2024-01-01T10:00:00Z",
    "version": "1.0",
    "execution_time": 0.123
  }
}
```

### Error Response Example
```json
{
  "success": false,
  "result": null,
  "message": "Operation failed",
  "error": "Invalid input parameters",
  "metadata": {
    "error_code": "VALIDATION_ERROR",
    "timestamp": "2024-01-01T10:00:00Z",
    "request_id": "req_123"
  }
}
```

### Validation Error Response
For input validation failures, the error response includes detailed validation information:

```json
{
  "success": false,
  "result": null,
  "message": "Validation failed with 2 errors",
  "error": "name: field required; email: field required",
  "metadata": {
    "error_type": "validation_error",
    "error_count": 2,
    "validation_errors": [
      {
        "loc": ["name"],
        "msg": "field required",
        "type": "value_error.missing"
      },
      {
        "loc": ["email"],
        "msg": "field required", 
        "type": "value_error.missing"
      }
    ],
    "timestamp": "2024-01-01T10:00:00Z"
  }
}
```

### Agent-Specific Errors
Agent-related errors are wrapped in the same ApiResponse format:

```json
{
  "success": false,
  "result": null,
  "message": "Agent operation failed",
  "error": "Agent 'unknown_agent' not found",
  "metadata": {
    "error_code": "AGENT_NOT_FOUND",
    "agent_identifier": "unknown_agent",
    "suggestion": "Check available agents using GET /agents endpoint",
    "timestamp": "2024-01-01T10:00:00Z"
  }
}
```

```json
{
  "success": false,
  "result": null,
  "message": "Agent unavailable",
  "error": "Agent 'disabled_agent' is disabled and not available for use",
  "metadata": {
    "error_code": "AGENT_DISABLED",
    "agent_identifier": "disabled_agent",
    "lifecycle_state": "disabled",
    "suggestion": "Agent is not enabled or has load errors. Check agent status or contact administrator.",
    "timestamp": "2024-01-01T10:00:00Z"
  }
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
  "success": true,
  "result": {
    "status": "healthy",
    "version": "1.0.0",
    "environment": "development",
    "framework_version": "1.0",
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
  },
  "message": "System health check completed",
  "error": null,
  "metadata": {
    "endpoint": "health_check",
    "response_time_ms": 5
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
  "success": true,
  "result": {
    "message": "AI Agent Platform v1.0 is running",
    "status": "healthy",
    "version": "1.0.0",
    "environment": "development",
    "framework_version": "1.0",
    "agent_framework": "self-contained",
    "timestamp": "2024-01-01T10:00:00Z"
  },
  "message": "Platform status retrieved successfully",
  "error": null,
  "metadata": {
    "endpoint": "root_status"
  }
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
  "success": true,
  "result": {
    "cors_origins": ["http://localhost:5173", "http://localhost:3000"],
    "environment": "development",
    "allow_credentials": true,
    "max_age": 86400,
    "message": "CORS configuration (development mode)"
  },
  "message": "CORS configuration retrieved successfully",
  "error": null,
  "metadata": {
    "endpoint": "cors_info",
    "available_in": "development"
  }
}
```

### 2. Authentication

#### Get Current User Info
```http
GET /auth/user
```

**Description:** Get information about the currently authenticated user.

**Authentication:** Required

**Response:**
```json
{
  "success": true,
  "result": {
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
    }
  },
  "message": "User information retrieved successfully",
  "error": null,
  "metadata": {
    "endpoint": "user_info",
    "authenticated": true
  }
}
```

**Error Response (Unauthorized):**
```json
{
  "success": false,
  "result": null,
  "message": "Authentication required",
  "error": "Missing or invalid authentication token",
  "metadata": {
    "error_code": "AUTHENTICATION_REQUIRED",
    "status_code": 401,
    "timestamp": "2024-01-01T10:00:00Z"
  }
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

**Response Example:**
```json
{
  "success": true,
  "result": {
    "agents": [
      {
        "identifier": "simple_prompt",
        "name": "Simple Prompt Agent",
        "description": "A simple agent that processes text prompts using any available LLM provider",
        "class_name": "SimplePromptAgent",
        "lifecycle_state": "enabled",
        "supported_environments": ["dev", "prod"],
        "version": "1.0.0",
        "enabled": true,
        "has_error": false,
        "created_at": "2024-01-01T00:00:00Z",
        "last_updated": "2024-01-01T00:00:00Z"
      }
    ],
    "summary": {
      "total_agents": 2,
      "enabled_agents": 2,
      "disabled_agents": 0,
      "current_environment": "development"
    },
    "framework_version": "1.0",
    "discovery_system": "agent_discovery"
  },
  "message": "Agents retrieved successfully",
  "error": null,
  "metadata": {
    "endpoint": "agent_list",
    "total_count": 2,
    "loaded_count": 2
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
- `agent_identifier` (string): Identifier of the agent (e.g., "simple_prompt")

**Response Example:**
```json
{
  "success": true,
  "result": {
    "agent_name": "simple_prompt",
    "display_name": "Simple Prompt Agent",
    "description": "A simple agent that processes text prompts using any available LLM provider",
    "class_name": "SimplePromptAgent",
    "lifecycle_state": "enabled",
    "supported_environments": ["dev", "prod"],
    "version": "1.0.0",
    "enabled": true,
    "has_error": false,
    "runtime_info": {
      "loaded": true,
      "last_execution": "2024-01-01T09:30:00Z",
      "total_executions": 125
    },
    "created_at": "2024-01-01T00:00:00Z",
    "last_updated": "2024-01-01T00:00:00Z"
  },
  "message": "Agent information retrieved successfully", 
  "error": null,
  "metadata": {
    "endpoint": "agent_info",
    "agent_identifier": "simple_prompt"
  }
}
```

**Error Response (Agent Not Found):**
```json
{
  "success": false,
  "result": null,
  "message": "Agent not found",
  "error": "Agent 'unknown_agent' not found",
  "metadata": {
    "error_code": "AGENT_NOT_FOUND",
    "agent_identifier": "unknown_agent",
    "suggestion": "Check available agents using GET /agents endpoint",
    "timestamp": "2024-01-01T10:00:00Z"
  }
}
```

#### Get Agent Schema
```http
GET /agents/{agent_identifier}/schema
```

**Description:** Get the Pydantic schema for the agent's job data structure.

**Authentication:** None required

**Path Parameters:**
- `agent_identifier` (string): Identifier of the agent

**Response Example:**
```json
{
  "success": true,
  "result": {
    "schema": {
      "type": "object",
      "properties": {
        "prompt": {
          "type": "string",
          "title": "Prompt",
          "description": "The text prompt to process"
        },
        "max_tokens": {
          "type": "integer",
          "title": "Max Tokens",
          "default": 1000,
          "minimum": 1,
          "maximum": 4000
        },
        "temperature": {
          "type": "number",
          "title": "Temperature",
          "default": 0.7,
          "minimum": 0.0,
          "maximum": 2.0
        }
      },
      "required": ["prompt"]
    },
    "ui_schema": {
      "prompt": {
        "ui:widget": "textarea",
        "ui:placeholder": "Enter your prompt here..."
      }
    },
    "agent_identifier": "simple_prompt"
  },
  "message": "Agent schema retrieved successfully",
  "error": null,
  "metadata": {
    "endpoint": "agent_schema",
    "agent_identifier": "simple_prompt",
    "schema_version": "1.0"
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
  "agent_identifier": "simple_prompt",
  "data": {
    "prompt": "Hello, how are you?",
    "temperature": 0.7
  },
  "priority": 5,
  "tags": ["test", "example"]
}
```

**Response Example:**
```json
{
  "success": true,
  "message": "Job created successfully",
  "job_id": "123e4567-e89b-12d3-a456-426614174000",
  "job": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "status": "pending",
    "agent_identifier": "simple_prompt",
    "data": {
      "prompt": "Hello, how are you?",
      "temperature": 0.7
    },
    "priority": 5,
    "tags": ["test", "example"],
    "created_at": "2024-01-01T12:00:00Z",
    "updated_at": "2024-01-01T12:00:00Z"
  }
}
```

**Error Response (Validation Failed):**
```json
{
  "message": "Job data validation failed",
  "agent_identifier": "simple_prompt",
  "validation_errors": [
    {
      "field": "prompt",
      "message": "field required",
      "type": "value_error.missing"
    }
  ],
  "expected_schema": {
    "model_name": "SimplePromptJobData",
    "available_models": ["SimplePromptJobData"],
    "schema": {
      "type": "object",
      "properties": {
        "prompt": {"type": "string"},
        "temperature": {"type": "number", "default": 0.7}
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
  "agent_identifier": "simple_prompt",
  "data": {
    "prompt": "Hello, how are you?",
    "temperature": 0.7
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
    "agent_identifier": "simple_prompt",
    "model_used": "SimplePromptJobData",
    "errors": [],
    "warnings": [],
    "schema_info": {
      "model_name": "SimplePromptJobData",
      "available_models": ["SimplePromptJobData"]
    },
    "validated_data": {
      "prompt": "Hello, how are you?",
      "temperature": 0.7
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

**Response Example:**
```json
{
  "success": true,
  "message": "Jobs retrieved successfully",
  "jobs": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "status": "completed",
      "agent_identifier": "simple_prompt",
      "data": {
        "prompt": "Hello, how are you?",
        "temperature": 0.7
      },
      "result": {
        "success": true,
        "result": "Hello! I'm doing well, thank you for asking...",
        "metadata": {
          "execution_time": 1.23,
          "model_used": "gemini-1.5-flash"
        }
      },
      "created_at": "2024-01-01T12:00:00Z",
      "updated_at": "2024-01-01T12:01:23Z"
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

**Response Example:**
```json
{
  "success": true,
  "message": "Job retrieved successfully",
  "job": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "status": "completed",
    "agent_identifier": "simple_prompt",
    "data": {
      "prompt": "Hello, how are you?",
      "temperature": 0.7
    },
    "result": {
      "success": true,
      "result": "Hello! I'm doing well, thank you for asking...",
      "metadata": {
        "execution_time": 1.23,
        "model_used": "gemini-1.5-flash"
      }
    },
    "created_at": "2024-01-01T12:00:00Z",
    "updated_at": "2024-01-01T12:01:23Z"
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

**Response Example:**
```json
{
  "success": true,
  "message": "Job retried successfully",
  "data": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "status": "pending",
    "agent_identifier": "simple_prompt",
    "data": {
      "prompt": "Hello, how are you?",
      "temperature": 0.7
    },
    "created_at": "2024-01-01T12:00:00Z",
    "updated_at": "2024-01-01T12:05:00Z"
  }
}
```

**Error Response (Schema Changed):**
```json
{
  "message": "Cannot retry job - existing job data no longer meets agent requirements",
  "job_id": "123e4567-e89b-12d3-a456-426614174000", 
  "agent_identifier": "simple_prompt",
  "validation_errors": [
    {
      "field": "new_required_field",
      "message": "field required",
      "type": "value_error.missing"
    }
  ],
  "expected_schema": {
    "model_name": "SimplePromptJobData",
    "available_models": ["SimplePromptJobData"]
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
  "job_id": "123e4567-e89b-12d3-a456-426614174000"
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
    "status": "completed"
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
    "123e4567-e89b-12d3-a456-426614174000",
    "456e7890-e89b-12d3-a456-426614174111"
  ]
}
```

**Response:**
```json
{
  "success": true,
  "message": "Batch job status retrieved",
  "data": {
    "123e4567-e89b-12d3-a456-426614174000": {
      "status": "completed",
      "updated_at": "2024-01-01T12:01:23Z"
    },
    "456e7890-e89b-12d3-a456-426614174111": {
      "status": "running",
      "updated_at": "2024-01-01T12:00:45Z"
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
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "status": "completed",
      "updated_at": "2024-01-01T12:01:23Z"
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
    "Job 123e4567-e89b-12d3-a456-426614174000 created at 2024-01-01T12:00:00Z",
    "Current status: completed",
    "Last updated: 2024-01-01T12:01:23Z",
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
    "simple_prompt": {
      "name": "Simple Prompt Agent",
      "description": "A simple agent that processes text prompts using any available LLM provider",
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
  "message": "Configuration retrieved for agent: simple_prompt",
  "config": {
    "name": "Simple Prompt Agent",
    "description": "A simple agent that processes text prompts using any available LLM provider",
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
  "message": "Configuration updated for agent: simple_prompt",
  "config": {
    "name": "Simple Prompt Agent",
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

## Schedule Management

> **Automated Agent Execution** - Schedule agents to run automatically using cron expressions

The Schedule Management API enables automated execution of agents at specified intervals using cron expressions. Each schedule stores complete agent configuration and job data, ensuring consistent execution parameters over time.

### Key Features
- **Cron-based Scheduling:** Standard cron expressions with human-readable descriptions
- **Complete Configuration Storage:** Full agent settings and job data stored with each schedule
- **Timezone Support:** Schedule execution times with timezone awareness
- **Status Management:** Enable, disable, and monitor schedule states
- **Execution History:** Track schedule performance and troubleshoot issues
- **Dashboard Integration:** View upcoming jobs and manage schedules

### Data Models

#### Schedule Object
```typescript
interface Schedule {
  id: string;                          // Schedule UUID
  user_id: string;                     // Owner user ID
  title: string;                       // Schedule title
  description?: string;                // Schedule description
  agent_name: string;                  // Target agent identifier
  cron_expression: string;             // Cron expression for scheduling
  enabled: boolean;                    // Whether schedule is enabled
  status: "enabled" | "disabled" | "paused" | "error";
  next_run?: string;                   // Next scheduled execution time (ISO 8601)
  last_run?: string;                   // Last execution time (ISO 8601)
  created_at: string;                  // Creation timestamp (ISO 8601)
  updated_at: string;                  // Last update timestamp (ISO 8601)
  total_executions: number;            // Total number of executions
  successful_executions: number;       // Number of successful executions
  failed_executions: number;           // Number of failed executions
  agent_config_data: AgentConfiguration; // Complete agent configuration
}
```

#### Agent Configuration Object
```typescript
interface AgentConfiguration {
  name: string;                        // Agent name
  description?: string;                // Agent description
  profile: "fast" | "balanced" | "quality" | "custom";
  performance_mode: "speed" | "quality" | "balanced" | "power_save";
  enabled: boolean;                    // Whether agent is enabled
  result_format?: string;              // Expected result format
  execution: ExecutionConfig;          // Execution configuration
  model: ModelConfig;                  // Model configuration
  logging: LoggingConfig;              // Logging configuration
  security: SecurityConfig;            // Security configuration
  job_data: Record<string, any>;       // Job data to be passed to the agent
  custom_settings: Record<string, any>; // Custom configuration settings
}
```

### Create Schedule
```http
POST /schedules
```

**Description:** Create a new schedule with agent configuration and cron expression.

**Authentication:** Required

**Request Body:**
```json
{
  "title": "Daily Data Processing",
  "description": "Process daily analytics data at 9 AM",
  "agent_name": "simple_prompt",
  "cron_expression": "0 9 * * *",
  "enabled": true,
  "agent_config_data": {
    "name": "simple_prompt",
    "description": "Daily processing agent",
    "profile": "balanced",
    "performance_mode": "balanced",
    "enabled": true,
    "result_format": "json",
    "execution": {
      "timeout_seconds": 300,
      "max_retries": 3,
      "enable_caching": true
    },
    "model": {
      "temperature": 0.7,
      "max_tokens": 2000
    },
    "logging": {
      "log_level": "INFO",
      "enable_performance_logging": true
    },
    "security": {
      "enable_input_validation": true,
      "rate_limit_per_minute": 60
    },
    "job_data": {
      "prompt": "Process today's analytics data",
      "max_tokens": 1500
    },
    "custom_settings": {}
  }
}
```

**Response:**
```json
{
  "success": true,
  "result": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "user_id": "user-123",
    "title": "Daily Data Processing",
    "description": "Process daily analytics data at 9 AM",
    "agent_name": "simple_prompt",
    "cron_expression": "0 9 * * *",
    "enabled": true,
    "status": "enabled",
    "next_run": "2024-01-15T09:00:00Z",
    "last_run": null,
    "created_at": "2024-01-10T08:30:00Z",
    "updated_at": "2024-01-10T08:30:00Z",
    "total_executions": 0,
    "successful_executions": 0,
    "failed_executions": 0,
    "agent_config_data": { /* Full configuration object */ }
  },
  "message": "Schedule 'Daily Data Processing' created successfully",
  "error": null,
  "metadata": {
    "schedule_id": "550e8400-e29b-41d4-a716-446655440000",
    "next_run": "2024-01-15T09:00:00Z",
    "cron_description": "At 09:00 every day",
    "endpoint": "create_schedule"
  }
}
```

### List Schedules
```http
GET /schedules
```

**Description:** List user's schedules with optional filtering and pagination.

**Authentication:** Required

**Query Parameters:**
- `enabled` (boolean, optional): Filter by enabled status
- `agent_name` (string, optional): Filter by agent name
- `limit` (integer, optional): Maximum number of schedules to return (1-100, default: 50)
- `offset` (integer, optional): Number of schedules to skip (default: 0)

**Response:**
```json
{
  "success": true,
  "result": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "title": "Daily Data Processing",
      "agent_name": "simple_prompt",
      "cron_expression": "0 9 * * *",
      "enabled": true,
      "status": "enabled",
      "next_run": "2024-01-15T09:00:00Z",
      "total_executions": 12,
      "successful_executions": 11,
      "failed_executions": 1,
      "created_at": "2024-01-10T08:30:00Z"
    }
  ],
  "message": "Schedules retrieved successfully",
  "error": null,
  "metadata": {
    "total_count": 1,
    "limit": 50,
    "offset": 0,
    "has_more": false,
    "endpoint": "list_schedules"
  }
}
```

### Get Schedule
```http
GET /schedules/{schedule_id}
```

**Description:** Get detailed information about a specific schedule.

**Authentication:** Required

**Path Parameters:**
- `schedule_id` (string): Schedule UUID

**Response:**
```json
{
  "success": true,
  "result": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "user_id": "user-123",
    "title": "Daily Data Processing",
    "description": "Process daily analytics data at 9 AM",
    "agent_name": "simple_prompt",
    "cron_expression": "0 9 * * *",
    "enabled": true,
    "status": "enabled",
    "next_run": "2024-01-15T09:00:00Z",
    "last_run": "2024-01-14T09:00:00Z",
    "created_at": "2024-01-10T08:30:00Z",
    "updated_at": "2024-01-14T09:05:00Z",
    "total_executions": 12,
    "successful_executions": 11,
    "failed_executions": 1,
    "agent_config_data": { /* Full configuration object */ }
  },
  "message": "Schedule retrieved successfully",
  "error": null,
  "metadata": {
    "cron_description": "At 09:00 every day",
    "success_rate": 91.67,
    "endpoint": "get_schedule"
  }
}
```

### Update Schedule
```http
PUT /schedules/{schedule_id}
```

**Description:** Update an existing schedule. Only provided fields will be updated.

**Authentication:** Required

**Path Parameters:**
- `schedule_id` (string): Schedule UUID

**Request Body (all fields optional):**
```json
{
  "title": "Updated Daily Processing",
  "description": "Updated description",
  "cron_expression": "0 10 * * *",
  "enabled": false,
  "agent_config_data": {
    "job_data": {
      "prompt": "Updated prompt",
      "max_tokens": 2000
    }
  }
}
```

**Response:**
```json
{
  "success": true,
  "result": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "title": "Updated Daily Processing",
    "cron_expression": "0 10 * * *",
    "enabled": false,
    "status": "disabled",
    "next_run": null,
    "updated_at": "2024-01-15T10:30:00Z"
    /* ... other fields ... */
  },
  "message": "Schedule updated successfully",
  "error": null,
  "metadata": {
    "updated_fields": ["title", "cron_expression", "enabled"],
    "cron_description": "At 10:00 every day",
    "endpoint": "update_schedule"
  }
}
```

### Delete Schedule
```http
DELETE /schedules/{schedule_id}
```

**Description:** Permanently delete a schedule. This action cannot be undone.

**Authentication:** Required

**Path Parameters:**
- `schedule_id` (string): Schedule UUID

**Response:**
```json
{
  "success": true,
  "result": {
    "message": "Schedule deleted successfully",
    "schedule_id": "550e8400-e29b-41d4-a716-446655440000"
  },
  "message": "Schedule 'Daily Data Processing' deleted successfully",
  "error": null,
  "metadata": {
    "schedule_id": "550e8400-e29b-41d4-a716-446655440000",
    "endpoint": "delete_schedule"
  }
}
```

### Enable Schedule
```http
POST /schedules/{schedule_id}/enable
```

**Description:** Enable a disabled schedule and calculate next run time.

**Authentication:** Required

**Path Parameters:**
- `schedule_id` (string): Schedule UUID

**Response:**
```json
{
  "success": true,
  "result": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "enabled": true,
    "status": "enabled",
    "next_run": "2024-01-16T09:00:00Z",
    "updated_at": "2024-01-15T14:30:00Z"
    /* ... other fields ... */
  },
  "message": "Schedule enabled successfully",
  "error": null,
  "metadata": {
    "next_run": "2024-01-16T09:00:00Z",
    "endpoint": "enable_schedule"
  }
}
```

### Disable Schedule
```http
POST /schedules/{schedule_id}/disable
```

**Description:** Disable an enabled schedule and clear next run time.

**Authentication:** Required

**Path Parameters:**
- `schedule_id` (string): Schedule UUID

**Response:**
```json
{
  "success": true,
  "result": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "enabled": false,
    "status": "disabled",
    "next_run": null,
    "updated_at": "2024-01-15T14:30:00Z"
    /* ... other fields ... */
  },
  "message": "Schedule disabled successfully",
  "error": null,
  "metadata": {
    "endpoint": "disable_schedule"
  }
}
```

### Get Upcoming Jobs
```http
GET /schedules/upcoming-jobs
```

**Description:** Get upcoming scheduled jobs for dashboard display.

**Authentication:** Required

**Query Parameters:**
- `limit` (integer, optional): Maximum number of upcoming jobs to return (1-50, default: 10)
- `hours_ahead` (integer, optional): Hours ahead to look for upcoming jobs (1-168, default: 24)

**Response:**
```json
{
  "success": true,
  "result": [
    {
      "schedule_id": "550e8400-e29b-41d4-a716-446655440000",
      "title": "Daily Data Processing",
      "agent_name": "simple_prompt",
      "cron_expression": "0 9 * * *",
      "next_run": "2024-01-16T09:00:00Z",
      "enabled": true,
      "time_until_run": "in 18 hours",
      "description": "Process daily analytics data at 9 AM"
    }
  ],
  "message": "Upcoming jobs retrieved successfully",
  "error": null,
  "metadata": {
    "total_upcoming": 1,
    "hours_ahead": 24,
    "endpoint": "get_upcoming_jobs"
  }
}
```

### Get Schedule History
```http
GET /schedules/{schedule_id}/history
```

**Description:** Get execution history for a specific schedule.

**Authentication:** Required

**Path Parameters:**
- `schedule_id` (string): Schedule UUID

**Query Parameters:**
- `limit` (integer, optional): Maximum number of history records to return (1-200, default: 50)
- `offset` (integer, optional): Number of records to skip (default: 0)
- `status` (string, optional): Filter by job status (completed, failed, running, pending)

**Response:**
```json
{
  "success": true,
  "result": [
    {
      "schedule_id": "550e8400-e29b-41d4-a716-446655440000",
      "job_id": "job-456",
      "execution_time": "2024-01-14T09:00:00Z",
      "status": "completed",
      "duration_seconds": 45.2,
      "error_message": null,
      "result_preview": "Successfully processed 1,234 records..."
    },
    {
      "schedule_id": "550e8400-e29b-41d4-a716-446655440000",
      "job_id": "job-455",
      "execution_time": "2024-01-13T09:00:00Z",
      "status": "failed",
      "duration_seconds": 12.8,
      "error_message": "API timeout after 300 seconds",
      "result_preview": null
    }
  ],
  "message": "Schedule history retrieved successfully",
  "error": null,
  "metadata": {
    "total_count": 12,
    "limit": 50,
    "offset": 0,
    "has_more": false,
    "schedule_title": "Daily Data Processing",
    "endpoint": "get_schedule_history"
  }
}
```

### Cron Expression Examples

Common cron expressions for scheduling:

| Expression | Description | Next Run (Example) |
|------------|-------------|-------------------|
| `0 9 * * *` | Every day at 9:00 AM | Daily at 09:00 |
| `0 */6 * * *` | Every 6 hours | Every 6 hours |
| `0 9 * * 1` | Every Monday at 9:00 AM | Mondays at 09:00 |
| `0 9 1 * *` | First day of every month at 9:00 AM | Monthly on 1st at 09:00 |
| `0 9 * * 1-5` | Every weekday at 9:00 AM | Weekdays at 09:00 |
| `*/15 * * * *` | Every 15 minutes | Every 15 minutes |
| `0 0 * * 0` | Every Sunday at midnight | Sundays at 00:00 |

### Schedule Error Handling

#### Validation Errors
```json
{
  "success": false,
  "result": null,
  "message": "Validation failed with 2 errors",
  "error": "cron_expression: Invalid cron expression format; title: field required",
  "metadata": {
    "error_type": "validation_error",
    "validation_errors": [
      {
        "loc": ["cron_expression"],
        "msg": "Invalid cron expression format",
        "type": "value_error.invalid_cron"
      }
    ]
  }
}
```

#### Schedule Not Found
```json
{
  "success": false,
  "result": null,
  "message": "Schedule not found",
  "error": "Schedule with ID '550e8400-e29b-41d4-a716-446655440000' not found",
  "metadata": {
    "error_code": "SCHEDULE_NOT_FOUND",
    "schedule_id": "550e8400-e29b-41d4-a716-446655440000",
    "suggestion": "Check schedule ID or use GET /schedules to list available schedules"
  }
}
```

#### Agent Configuration Errors
```json
{
  "success": false,
  "result": null,
  "message": "Agent configuration invalid",
  "error": "Agent 'unknown_agent' not found in system",
  "metadata": {
    "error_code": "AGENT_NOT_FOUND",
    "agent_name": "unknown_agent",
    "suggestion": "Check available agents using GET /agents endpoint"
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
| `404` | `ScheduleNotFoundError` | Schedule doesn't exist | Schedule with ID 'xyz' not found |
| `400` | `CronValidationError` | Invalid cron expression | Invalid cron expression format |
| `401` | `AuthenticationError` | Invalid or missing token | Authorization header required |
| `403` | `AuthorizationError` | Access denied | User not authorized for this operation |
| `429` | `RateLimitError` | Too many requests | Rate limit exceeded |
| `500` | `InternalError` | Server processing error | Unexpected server error |

### Agent Error Suggestions

Each agent error includes helpful suggestions:
- **AgentNotFoundError:** "Check available agents using GET /agents endpoint"
- **AgentDisabledError:** "Agent is not enabled or has load errors. Check agent status or contact administrator."
- **AgentNotLoadedError:** "Agent exists but is not currently loaded. Try again later or contact administrator."

### Schedule Error Suggestions

Each schedule error includes helpful suggestions:
- **ScheduleNotFoundError:** "Check schedule ID or use GET /schedules to list available schedules"
- **CronValidationError:** "Use standard cron format (minute hour day month weekday) or check cron expression syntax"
- **AgentConfigurationError:** "Verify agent exists and configuration data matches agent requirements"

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
curl http://localhost:8000/agents/simple_prompt/schema

# Create a schedule
curl -X POST http://localhost:8000/schedules \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Schedule",
    "agent_name": "simple_prompt",
    "cron_expression": "0 9 * * *",
    "agent_config_data": {
      "name": "simple_prompt",
      "job_data": {"prompt": "Hello world", "max_tokens": 100}
    }
  }'

# List schedules
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/schedules

# Get upcoming jobs
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/schedules/upcoming-jobs

# Validate job data
curl -X POST http://localhost:8000/jobs/validate \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_identifier": "simple_prompt",
    "data": {"prompt": "Test prompt", "max_tokens": 500}
  }'

# Create a job
curl -X POST http://localhost:8000/jobs \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_identifier": "simple_prompt",
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