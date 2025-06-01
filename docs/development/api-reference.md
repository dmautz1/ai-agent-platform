# AI Agent Template - API Documentation

> **Complete API Reference** - Comprehensive guide to all API endpoints with request/response examples

This document provides complete API documentation for the AI Agent Template. All endpoints are also available through the interactive documentation at `http://localhost:8000/docs` when the server is running.

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
    "total_endpoints": 15,
    "agents": {
      "text_processing": {
        "class_name": "TextProcessingAgent",
        "endpoints": 7,
        "models": 1,
        "status": "registered"
      }
    }
  },
  "timestamp": "2024-01-01T10:00:00Z",
  "performance_metrics": {
    "request_count": 100,
    "average_response_time": 0.25,
    "error_rate": 0.01
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
  "success": true,
  "message": "User information retrieved",
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
  "timestamp": "2024-01-01T10:00:00Z"
}
```

### 3. Agent Management

#### List All Agents
```http
GET /agents
```

**Description:** Get information about all registered agents and their capabilities.

**Authentication:** None required

**Response:**
```json
{
  "status": "success",
  "framework_version": "2.0",
  "discovery_status": {
    "total_agents": 3,
    "total_endpoints": 15,
    "agents": {
      "text_processing": {
        "class_name": "TextProcessingAgent",
        "endpoints": 7,
        "models": 1,
        "status": "registered"
      },
      "summarization": {
        "class_name": "SummarizationAgent", 
        "endpoints": 4,
        "models": 3,
        "status": "registered"
      },
      "web_scraping": {
        "class_name": "WebScrapingAgent",
        "endpoints": 6,
        "models": 1,
        "status": "registered"
      }
    }
  }
}
```

#### Get Specific Agent Info
```http
GET /agents/{agent_name}
```

**Description:** Get detailed information about a specific agent.

**Authentication:** None required

**Path Parameters:**
- `agent_name` (string): Name of the agent (e.g., "text_processing")

**Response:**
```json
{
  "agent_name": "text_processing",
  "class_name": "TextProcessingAgent",
  "description": "Advanced text processing agent with multiple analysis operations",
  "endpoints": [
    {
      "path": "/text-processing/process",
      "methods": ["POST"],
      "auth_required": true,
      "description": "Main text processing endpoint"
    },
    {
      "path": "/text-processing/capabilities",
      "methods": ["GET"], 
      "auth_required": false,
      "description": "Get text processing capabilities"
    }
  ],
  "models": {
    "TextProcessingJobData": {
      "fields": {
        "text": "string (required)",
        "operation": "string (required)",
        "parameters": "object (optional)"
      }
    }
  },
  "supported_operations": [
    "analyze_sentiment",
    "extract_keywords", 
    "classify_text",
    "analyze_tone",
    "extract_entities"
  ]
}
```

#### Get Agent Health
```http
GET /agents/{agent_name}/health
```

**Description:** Check the health status of a specific agent.

**Authentication:** None required

**Path Parameters:**
- `agent_name` (string): Name of the agent

**Response:**
```json
{
  "agent_name": "text_processing",
  "status": "healthy",
  "last_check": "2024-01-01T10:00:00Z",
  "response_time_ms": 45,
  "capabilities_available": true,
  "endpoints_registered": 7,
  "models_loaded": 1
}
```

### 4. Job Management

#### Create Job
```http
POST /jobs
```

**Description:** Create a new job for processing by an AI agent.

**Authentication:** Required

**Request Body:**
```json
{
  "data": {
    "text": "Sample text to analyze",
    "operation": "analyze_sentiment",
    "parameters": {
      "confidence_threshold": 0.8
    }
  },
  "priority": 5,
  "tags": ["sentiment", "analysis"]
}
```

**Response:**
```json
{
  "success": true,
  "message": "Job created successfully",
  "job_id": "job_abc123",
  "timestamp": "2024-01-01T10:00:00Z"
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
      "id": "job_abc123",
      "status": "completed",
      "data": {
        "text": "Sample text",
        "operation": "analyze_sentiment"
      },
      "result": "{\"sentiment\": \"positive\", \"confidence\": 0.95}",
      "error_message": null,
      "created_at": "2024-01-01T10:00:00Z",
      "updated_at": "2024-01-01T10:01:00Z"
    }
  ],
  "total_count": 1,
  "timestamp": "2024-01-01T10:00:00Z"
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
    "id": "job_abc123",
    "status": "running",
    "data": {
      "text": "Sample text to process",
      "operation": "analyze_sentiment"
    },
    "result": null,
    "error_message": null,
    "created_at": "2024-01-01T10:00:00Z",
    "updated_at": "2024-01-01T10:00:30Z"
  },
  "timestamp": "2024-01-01T10:00:00Z"
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
  "job_id": "job_abc123",
  "timestamp": "2024-01-01T10:00:00Z"
}
```

### 5. Pipeline Management

#### Get Pipeline Status
```http
GET /pipeline/status
```

**Description:** Get current status of the job processing pipeline.

**Authentication:** Required

**Response:**
```json
{
  "success": true,
  "message": "Pipeline status retrieved",
  "status": {
    "is_running": true,
    "queue_size": 5,
    "scheduled_jobs": 2,
    "active_jobs": 3,
    "max_concurrent_jobs": 5,
    "worker_count": 6,
    "metrics": {
      "active_jobs": 3,
      "completed_jobs": 150,
      "failed_jobs": 5,
      "retried_jobs": 8,
      "total_processed": 155,
      "success_rate": 96.8,
      "uptime_seconds": 3600,
      "jobs_per_minute": 2.6
    }
  },
  "timestamp": "2024-01-01T11:00:00Z"
}
```

#### Get Pipeline Metrics
```http
GET /pipeline/metrics
```

**Description:** Get performance metrics for the job processing pipeline.

**Authentication:** Required

**Response:**
```json
{
  "success": true,
  "message": "Pipeline metrics retrieved",
  "metrics": {
    "completed_jobs": 150,
    "failed_jobs": 5,
    "success_rate": 96.8,
    "jobs_per_minute": 2.6,
    "average_processing_time": 45.2,
    "peak_concurrent_jobs": 8
  },
  "pipeline_info": {
    "is_running": true,
    "worker_count": 6,
    "max_concurrent_jobs": 5
  },
  "timestamp": "2024-01-01T11:00:00Z"
}
```

### 6. Google ADK Integration

#### Validate ADK Setup
```http
GET /adk/validate
```

**Description:** Validate Google ADK configuration and connectivity.

**Authentication:** None required

**Response:**
```json
{
  "status": "success",
  "configuration": {
    "adk_available": true,
    "authentication_method": "google_ai_studio",
    "default_model": "gemini-2.0-flash",
    "project_configured": true
  },
  "validation_results": {
    "environment_variables": "valid",
    "authentication": "valid",
    "model_access": "valid"
  },
  "timestamp": "2024-01-01T10:00:00Z"
}
```

#### Get Available Models
```http
GET /adk/models
```

**Description:** Get list of available Google AI models.

**Authentication:** None required

**Response:**
```json
{
  "status": "success",
  "available_models": [
    {
      "name": "gemini-2.0-flash",
      "description": "Latest Gemini model, fastest performance",
      "default": true
    },
    {
      "name": "gemini-1.5-pro",
      "description": "Most capable Gemini model",
      "default": false
    }
  ],
  "default_model": "gemini-2.0-flash",
  "total_models": 2
}
```

#### Test ADK Connection
```http
GET /adk/connection-test
```

**Description:** Test connection to Google AI services.

**Authentication:** None required

**Response:**
```json
{
  "status": "success",
  "connection_test": {
    "google_ai_reachable": true,
    "authentication_valid": true,
    "model_accessible": true,
    "response_time_ms": 234
  },
  "test_timestamp": "2024-01-01T10:00:00Z"
}
```

### 7. Agent Configuration

#### List Agent Configurations
```http
GET /config/agents
```

**Description:** Get configuration settings for all agents.

**Authentication:** Required

**Response:**
```json
{
  "success": true,
  "message": "Agent configurations retrieved",
  "configs": {
    "text_processing_agent": {
      "name": "text_processing_agent",
      "description": "Advanced text processing agent",
      "profile": "balanced",
      "performance_mode": "balanced",
      "enabled": true,
      "execution": {
        "timeout_seconds": 300,
        "max_retries": 3,
        "enable_caching": true
      },
      "model": {
        "temperature": 0.7,
        "max_tokens": 2000
      }
    }
  },
  "total_count": 1,
  "timestamp": "2024-01-01T10:00:00Z"
}
```

#### Get Agent Configuration
```http
GET /config/agents/{agent_name}
```

**Description:** Get configuration settings for a specific agent.

**Authentication:** Required

**Path Parameters:**
- `agent_name` (string): Name of the agent

**Response:**
```json
{
  "success": true,
  "message": "Configuration retrieved for agent: text_processing_agent",
  "config": {
    "name": "text_processing_agent",
    "description": "Advanced text processing agent",
    "profile": "balanced",
    "execution": {
      "timeout_seconds": 300,
      "max_retries": 3,
      "enable_caching": true
    },
    "model": {
      "temperature": 0.7,
      "max_tokens": 2000
    },
    "custom_settings": {}
  },
  "timestamp": "2024-01-01T10:00:00Z"
}
```

#### Update Agent Configuration
```http
PUT /config/agents/{agent_name}
```

**Description:** Update configuration settings for a specific agent.

**Authentication:** Required

**Path Parameters:**
- `agent_name` (string): Name of the agent

**Request Body:**
```json
{
  "execution": {
    "timeout_seconds": 180,
    "max_retries": 2
  },
  "model": {
    "temperature": 0.8
  },
  "custom_settings": {
    "special_mode": true
  }
}
```

**Response:**
```json
{
  "success": true,
  "message": "Configuration updated for agent: text_processing_agent",
  "config": {
    "name": "text_processing_agent",
    "description": "Advanced text processing agent",
    "execution": {
      "timeout_seconds": 180,
      "max_retries": 2,
      "enable_caching": true
    },
    "model": {
      "temperature": 0.8,
      "max_tokens": 2000
    },
    "custom_settings": {
      "special_mode": true
    }
  },
  "timestamp": "2024-01-01T10:00:00Z"
}
```

#### Get Available Profiles
```http
GET /config/profiles
```

**Description:** Get list of available agent configuration profiles.

**Authentication:** Required

**Response:**
```json
{
  "success": true,
  "message": "Agent profiles retrieved",
  "profiles": {
    "fast": {
      "description": "Optimized for speed",
      "execution": {
        "timeout_seconds": 60,
        "max_retries": 1
      },
      "model": {
        "temperature": 0.3,
        "max_tokens": 1000
      }
    },
    "balanced": {
      "description": "Balanced speed and quality",
      "execution": {
        "timeout_seconds": 300,
        "max_retries": 3
      },
      "model": {
        "temperature": 0.7,
        "max_tokens": 2000
      }
    },
    "quality": {
      "description": "Optimized for quality",
      "execution": {
        "timeout_seconds": 600,
        "max_retries": 5
      },
      "model": {
        "temperature": 0.9,
        "max_tokens": 4000
      }
    }
  },
  "timestamp": "2024-01-01T10:00:00Z"
}
```

#### Set Agent Profile
```http
POST /config/agents/{agent_name}/profile
```

**Description:** Set a predefined configuration profile for an agent.

**Authentication:** Required

**Path Parameters:**
- `agent_name` (string): Name of the agent

**Request Body:**
```json
{
  "profile": "fast",
  "performance_mode": "speed"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Profile set for agent: text_processing_agent",
  "profile": "fast",
  "performance_mode": "speed",
  "applied_config": {
    "execution": {
      "timeout_seconds": 60,
      "max_retries": 1
    },
    "model": {
      "temperature": 0.3,
      "max_tokens": 1000
    }
  },
  "timestamp": "2024-01-01T10:00:00Z"
}
```

## Agent-Specific Endpoints

The following endpoints are automatically generated for each agent. Replace `{agent_type}` with the actual agent name (e.g., `text-processing`, `summarization`, `web-scraping`).

### Text Processing Agent

#### Get Capabilities
```http
GET /text-processing/capabilities
```

**Authentication:** None required

**Response:**
```json
{
  "status": "success",
  "agent_name": "text_processing",
  "operations": [
    "analyze_sentiment",
    "extract_keywords",
    "classify_text",
    "analyze_tone",
    "extract_entities",
    "summarize_brief",
    "translate",
    "grammar_check",
    "readability_score",
    "custom"
  ],
  "description": "Advanced text processing with multiple analysis operations",
  "supported_job_types": ["text_processing"],
  "framework_version": "2.0"
}
```

#### Process Text
```http
POST /text-processing/process
```

**Authentication:** Required

**Request Body:**
```json
{
  "text": "I love this new AI agent template! It's incredibly well-designed and easy to use.",
  "operation": "analyze_sentiment",
  "parameters": {
    "confidence_threshold": 0.8
  }
}
```

**Response:**
```json
{
  "success": true,
  "result": {
    "sentiment": "positive",
    "confidence": 0.95,
    "emotions": ["joy", "satisfaction"],
    "explanation": "The text expresses strong positive sentiment with words like 'love', 'incredibly', and 'easy'."
  },
  "processing_time": 1.23,
  "timestamp": "2024-01-01T10:00:00Z"
}
```

#### Direct Operation Endpoints
```http
POST /text-processing/analyze-sentiment
POST /text-processing/extract-keywords
POST /text-processing/classify-text
```

**Authentication:** Required

These endpoints automatically set the operation parameter for convenience.

### Summarization Agent

#### Get Capabilities
```http
GET /summarization/capabilities
```

**Authentication:** None required

**Response:**
```json
{
  "status": "success",
  "agent_name": "summarization",
  "supported_media_types": ["text", "audio", "video"],
  "supported_job_types": ["text_summarization", "audio_summarization", "video_summarization"],
  "text_summary_types": ["brief", "detailed", "key_points", "executive"],
  "audio_summary_types": ["transcript", "key_points", "speaker_analysis"],
  "video_summary_types": ["visual_narrative", "key_moments", "full_analysis"],
  "framework_version": "2.0"
}
```

#### Summarize Text
```http
POST /summarization/text
```

**Authentication:** Required

**Request Body:**
```json
{
  "content": "Long text content to summarize...",
  "summary_type": "brief",
  "max_length": 100,
  "style": "bullet_points"
}
```

**Response:**
```json
{
  "success": true,
  "result": {
    "summary": "• Key point 1\n• Key point 2\n• Key point 3",
    "original_length": 1500,
    "summary_length": 87,
    "compression_ratio": 0.058,
    "key_topics": ["topic1", "topic2"]
  },
  "processing_time": 2.15,
  "timestamp": "2024-01-01T10:00:00Z"
}
```

### Web Scraping Agent

#### Get Capabilities
```http
GET /web-scraping/capabilities
```

**Authentication:** None required

**Response:**
```json
{
  "status": "success",
  "agent_name": "web_scraping",
  "supported_operations": [
    "extract_text",
    "extract_links",
    "extract_metadata",
    "full_page",
    "structured_data",
    "monitor_changes"
  ],
  "features": {
    "rate_limiting": true,
    "error_recovery": true,
    "custom_selectors": true,
    "structured_data": true,
    "content_validation": true,
    "robots_txt_compliance": true
  },
  "max_page_size": 5242880,
  "supported_formats": ["html", "xml", "json-ld", "microdata"]
}
```

#### Scrape Website
```http
POST /web-scraping/scrape
```

**Authentication:** Required

**Request Body:**
```json
{
  "url": "https://example.com",
  "options": {
    "operation": "extract_text",
    "max_page_size": 1048576,
    "custom_selectors": {
      "title": "h1",
      "content": ".main-content"
    },
    "follow_robots_txt": true
  }
}
```

**Response:**
```json
{
  "success": true,
  "result": {
    "url": "https://example.com",
    "title": "Example Page Title",
    "content": "Extracted page content...",
    "metadata": {
      "page_size": 45678,
      "load_time": 1.23,
      "last_modified": "2024-01-01T09:00:00Z"
    },
    "extracted_data": {
      "title": "Custom title content",
      "content": "Custom content selection"
    }
  },
  "processing_time": 3.45,
  "timestamp": "2024-01-01T10:00:00Z"
}
```

## Error Codes

| Code | Description | Solution |
|------|-------------|-----------|
| `AUTHENTICATION_FAILED` | Invalid or missing JWT token | Provide valid authorization header |
| `VALIDATION_ERROR` | Request validation failed | Check request body format and required fields |
| `AGENT_NOT_FOUND` | Specified agent doesn't exist | Verify agent name and availability |
| `JOB_NOT_FOUND` | Job ID doesn't exist or access denied | Check job ID and user permissions |
| `RATE_LIMITED` | Too many requests | Wait before retrying |
| `INTERNAL_ERROR` | Server processing error | Check server logs or contact support |
| `ADK_CONNECTION_ERROR` | Google ADK connectivity issue | Verify ADK configuration |
| `AGENT_TIMEOUT` | Agent processing timeout | Try again or adjust timeout settings |

## Rate Limiting

- **Default Limit:** 100 requests per minute per user
- **Burst Limit:** 20 requests per 10 seconds
- **Headers:** Rate limit information is included in response headers:
  - `X-RateLimit-Limit`: Requests allowed per window
  - `X-RateLimit-Remaining`: Requests remaining in current window
  - `X-RateLimit-Reset`: Time when the rate limit resets

## Status Codes

| Code | Description |
|------|-------------|
| `200` | Success |
| `201` | Created |
| `400` | Bad Request |
| `401` | Unauthorized |
| `403` | Forbidden |
| `404` | Not Found |
| `422` | Validation Error |
| `429` | Rate Limited |
| `500` | Internal Server Error |

## Testing the API

### Using curl
```bash
# Get health status
curl http://localhost:8000/health

# List agents
curl http://localhost:8000/agents

# Create a job (with authentication)
curl -X POST http://localhost:8000/jobs \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"data": {"text": "Test text", "operation": "analyze_sentiment"}}'
```

### Using the Interactive Documentation
Visit `http://localhost:8000/docs` for a complete interactive API explorer with:
- Live endpoint testing
- Request/response examples
- Schema validation
- Authentication testing

## SDK and Client Libraries

For easier integration, consider using the frontend's API client:
- **Location:** `frontend/src/lib/api.ts`
- **Features:** Automatic authentication, error handling, TypeScript types
- **Usage:** Import and use the pre-configured Axios client

---

**Need Help?** 
- Interactive docs: `http://localhost:8000/docs`
- API health: `http://localhost:8000/health`
- Agent info: `http://localhost:8000/agents` 