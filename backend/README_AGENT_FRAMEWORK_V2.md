# AI Agent Template - Self-Contained Agent Framework v2.0

## Overview

The AI Agent Template v2.0 introduces a revolutionary **Self-Contained Agent Framework** that dramatically simplifies agent development and deployment. With this new architecture, adding a new agent requires only creating a single file in the `agents/` directory - no changes to `main.py`, `models.py`, or manual registration required.

## Key Features

### 🚀 **Zero Configuration Agent Development**
- **Single File Agents**: Everything needed for an agent in one file
- **Automatic Discovery**: Agents are automatically found and registered
- **Embedded Models**: Job data models defined within agent files
- **Embedded Endpoints**: API endpoints defined within agent files
- **Auto-Registration**: Endpoints automatically registered with FastAPI

### 🎯 **Developer Experience**
- **No Boilerplate**: Minimal code required for new agents
- **Type Safety**: Full Pydantic validation and type hints
- **Self-Documenting**: Agents include their own documentation
- **Easy Testing**: Each agent is independently testable
- **Plugin Architecture**: Drop-in agent files with zero configuration

### 🔧 **Enterprise Features**
- **Authentication Integration**: Built-in JWT authentication support
- **Performance Monitoring**: Automatic performance logging
- **Error Handling**: Comprehensive error handling and recovery
- **Rate Limiting**: Built-in rate limiting capabilities
- **Validation**: Automatic request/response validation

## Architecture

### Framework Components

```
backend/
├── agent_framework.py          # Core framework with decorators and registration
├── agents/                     # Self-contained agent directory
│   ├── __init__.py            # Auto-discovery system
│   ├── text_processing_agent.py    # Example self-contained agent
│   ├── web_scraping_agent.py       # Example self-contained agent
│   └── your_new_agent.py           # Your new agent (just drop it in!)
├── main.py                     # Simplified main application
└── models.py                   # Core models only (no job data models)
```

### Key Classes

1. **`SelfContainedAgent`**: Base class for all agents
2. **`@job_model`**: Decorator for embedding data models
3. **`@endpoint`**: Decorator for embedding API endpoints
4. **Auto-Discovery System**: Automatically finds and registers agents

## Creating a New Agent

### Step 1: Create Agent File

Create a new file in `agents/your_agent_name_agent.py`:

```python
"""
Your Custom Agent

Description of what your agent does.
All endpoints and models are embedded in this single file.
"""

from typing import Dict, Any, List
from pydantic import BaseModel, Field

from agent_framework import SelfContainedAgent, endpoint, job_model, execute_agent_job, validate_job_data
from models import JobType
from logging_system import get_logger

logger = get_logger(__name__)

# Embedded Job Data Model
@job_model
class YourJobData(BaseModel):
    """Your agent's job data model"""
    input_text: str = Field(..., description="Text to process")
    operation: str = Field(..., description="Operation to perform")
    parameters: Optional[Dict[str, Any]] = Field(default=None)

class YourAgent(SelfContainedAgent):
    """Your custom agent implementation"""
    
    def __init__(self, **kwargs):
        super().__init__(
            description="Your agent description",
            **kwargs
        )
    
    def get_supported_job_types(self) -> List[JobType]:
        return [JobType.custom]  # or your specific job type
    
    # Public Endpoint (no auth required)
    @endpoint("/your-agent/capabilities", methods=["GET"], auth_required=False)
    async def get_capabilities(self):
        """Get agent capabilities"""
        return {
            "status": "success",
            "agent_name": self.name,
            "operations": ["operation1", "operation2"],
            "description": "What your agent does"
        }
    
    # Protected Endpoint (auth required)
    @endpoint("/your-agent/process", methods=["POST"], auth_required=True)
    async def process_data(self, request_data: dict, user: dict):
        """Main processing endpoint"""
        job_data = validate_job_data(request_data, YourJobData)
        return await execute_agent_job(self, job_data, user["id"])
    
    # Agent Business Logic
    async def _execute_job_logic(self, job_data: YourJobData):
        """Implement your agent's core logic here"""
        try:
            # Your processing logic
            result = f"Processed: {job_data.input_text}"
            
            from agent import AgentExecutionResult
            return AgentExecutionResult(
                success=True,
                result=result,
                metadata={"operation": job_data.operation}
            )
        except Exception as e:
            from agent import AgentExecutionResult
            return AgentExecutionResult(
                success=False,
                error_message=str(e)
            )
```

### Step 2: That's It!

Your agent is automatically:
- ✅ Discovered and registered
- ✅ Endpoints added to FastAPI
- ✅ Models validated
- ✅ Available via API

No changes needed to `main.py`, `models.py`, or any other files!

## Framework Decorators

### `@job_model`

Embeds a Pydantic model within the agent file:

```python
@job_model
class MyJobData(BaseModel):
    text: str = Field(..., description="Text to process")
    operation: str = Field(..., description="Operation type")
```

**Features:**
- Automatic registration with agent framework
- Full Pydantic validation
- Type safety and documentation
- Accessible via `agent.get_models()`

### `@endpoint`

Embeds API endpoints within the agent:

```python
@endpoint("/my-agent/process", methods=["POST"], auth_required=True)
async def process_data(self, request_data: dict, user: dict):
    """Process data endpoint"""
    return {"status": "success"}
```

**Parameters:**
- `path`: API endpoint path
- `methods`: HTTP methods (default: `["POST"]`)
- `auth_required`: Require JWT authentication (default: `True`)
- `public`: Public endpoint flag (default: `False`)

**Method Signatures:**
- **With Auth**: `async def method(self, request_data: dict, user: dict)`
- **Without Auth**: `async def method(self, request_data: dict)`
- **No Data**: `async def method(self, user: dict)` or `async def method(self)`

## Utility Functions

### `execute_agent_job(agent, job_data, user_id)`

Executes an agent job with proper error handling and response formatting:

```python
@endpoint("/my-agent/process", methods=["POST"], auth_required=True)
async def process_data(self, request_data: dict, user: dict):
    job_data = validate_job_data(request_data, MyJobData)
    return await execute_agent_job(self, job_data, user["id"])
```

### `validate_job_data(data, model_class)`

Validates request data against a Pydantic model:

```python
job_data = validate_job_data(request_data, MyJobData)
```

## Agent Discovery System

### Automatic Discovery

The framework automatically:

1. **Scans** `agents/` directory for `*_agent.py` files
2. **Imports** agent modules
3. **Finds** classes inheriting from `SelfContainedAgent`
4. **Instantiates** agent classes
5. **Registers** agents with the agent registry
6. **Extracts** endpoints and registers with FastAPI

### Discovery Status

Check discovery status via API:

```bash
GET /agents
```

Response:
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
      }
    }
  }
}
```

## API Endpoints

### Framework Management

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/agents` | GET | No | List all registered agents |
| `/agents/{name}` | GET | No | Get specific agent info |
| `/agents/{name}/health` | GET | No | Check agent health |

### Agent Endpoints

Each agent automatically gets endpoints based on their `@endpoint` decorators. For example:

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/text-processing/operations` | GET | No | Get text processing operations |
| `/text-processing/process` | POST | Yes | Process text |
| `/web-scraping/capabilities` | GET | No | Get scraping capabilities |
| `/web-scraping/scrape` | POST | Yes | Scrape website |

## Example Agents

### Text Processing Agent

```python
@job_model
class TextProcessingJobData(BaseModel):
    text: str = Field(..., max_length=50000)
    operation: str = Field(...)
    parameters: Optional[Dict[str, Any]] = None

class TextProcessingAgent(SelfContainedAgent):
    @endpoint("/text-processing/operations", methods=["GET"], auth_required=False)
    async def get_operations(self):
        return {"operations": ["sentiment", "keywords", "classify"]}
    
    @endpoint("/text-processing/process", methods=["POST"], auth_required=True)
    async def process_text(self, request_data: dict, user: dict):
        job_data = validate_job_data(request_data, TextProcessingJobData)
        return await execute_agent_job(self, job_data, user["id"])
```

### Web Scraping Agent

```python
@job_model
class WebScrapingJobData(BaseModel):
    url: str = Field(...)
    selectors: Optional[Dict[str, str]] = None
    options: Optional[Dict[str, Any]] = None

class WebScrapingAgent(SelfContainedAgent):
    @endpoint("/web-scraping/capabilities", methods=["GET"], auth_required=False)
    async def get_capabilities(self):
        return {"operations": ["extract_text", "extract_links"]}
    
    @endpoint("/web-scraping/scrape", methods=["POST"], auth_required=True)
    async def scrape_website(self, request_data: dict, user: dict):
        job_data = validate_job_data(request_data, WebScrapingJobData)
        return await execute_agent_job(self, job_data, user["id"])
```

## Testing Agents

### Unit Testing

Each agent can be tested independently:

```python
import pytest
from agents.my_agent import MyAgent, MyJobData

@pytest.fixture
def agent():
    return MyAgent()

@pytest.mark.asyncio
async def test_agent_processing(agent):
    job_data = MyJobData(
        input_text="test text",
        operation="test_op"
    )
    
    result = await agent._execute_job_logic(job_data)
    assert result.success
    assert "test text" in result.result
```

### Integration Testing

Test endpoints via FastAPI test client:

```python
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_agent_endpoint():
    response = client.post(
        "/my-agent/process",
        json={"input_text": "test", "operation": "test_op"},
        headers={"Authorization": "Bearer valid_token"}
    )
    assert response.status_code == 200
```

## Migration Guide

### From v1.0 to v2.0

1. **Move Agent Files**: Move agents to `agents/` directory
2. **Refactor Agents**: Convert to `SelfContainedAgent` format
3. **Embed Models**: Add `@job_model` decorators
4. **Embed Endpoints**: Add `@endpoint` decorators
5. **Remove Manual Registration**: Delete from `main.py`
6. **Clean Models**: Remove job data models from `models.py`

### Example Migration

**Before (v1.0):**
```python
# models.py
class MyJobData(BaseModel):
    text: str

# my_agent.py
class MyAgent(BaseAgent):
    pass

# main.py
@app.post("/my-agent/process")
async def process_data(data: MyJobData, user=Depends(get_current_user)):
    # endpoint logic
```

**After (v2.0):**
```python
# agents/my_agent.py
@job_model
class MyJobData(BaseModel):
    text: str

class MyAgent(SelfContainedAgent):
    @endpoint("/my-agent/process", methods=["POST"])
    async def process_data(self, request_data: dict, user: dict):
        job_data = validate_job_data(request_data, MyJobData)
        return await execute_agent_job(self, job_data, user["id"])
```

## Best Practices

### 1. Agent Organization

```python
"""
Agent File Structure:

1. Docstring with agent description
2. Imports
3. Job data models with @job_model
4. Agent class with SelfContainedAgent
5. Public endpoints (auth_required=False)
6. Protected endpoints (auth_required=True)
7. Business logic methods
8. Helper methods
"""
```

### 2. Error Handling

```python
async def _execute_job_logic(self, job_data):
    try:
        # Your logic here
        result = process_data(job_data)
        
        return AgentExecutionResult(
            success=True,
            result=result,
            metadata={"processed_at": time.time()}
        )
    except ValidationError as e:
        return AgentExecutionResult(
            success=False,
            error_message=f"Validation error: {str(e)}"
        )
    except Exception as e:
        logger.error("Unexpected error", exception=e)
        return AgentExecutionResult(
            success=False,
            error_message=f"Processing failed: {str(e)}"
        )
```

### 3. Endpoint Design

```python
# Public discovery endpoint
@endpoint("/my-agent/capabilities", methods=["GET"], auth_required=False)
async def get_capabilities(self):
    return {"operations": self.supported_operations}

# Main processing endpoint
@endpoint("/my-agent/process", methods=["POST"], auth_required=True)
async def process_data(self, request_data: dict, user: dict):
    job_data = validate_job_data(request_data, MyJobData)
    return await execute_agent_job(self, job_data, user["id"])

# Convenience endpoints
@endpoint("/my-agent/quick-process", methods=["POST"], auth_required=True)
async def quick_process(self, request_data: dict, user: dict):
    request_data["operation"] = "quick"
    return await self.process_data(request_data, user)
```

### 4. Model Design

```python
@job_model
class MyJobData(BaseModel):
    """Well-documented job data model"""
    
    # Required fields with validation
    text: str = Field(..., min_length=1, max_length=10000, description="Text to process")
    operation: str = Field(..., description="Processing operation")
    
    # Optional fields with defaults
    parameters: Optional[Dict[str, Any]] = Field(default=None, description="Additional parameters")
    timeout: Optional[int] = Field(default=30, ge=1, le=300, description="Processing timeout")
    
    # Custom validation
    @validator('operation')
    def validate_operation(cls, v):
        allowed = ["analyze", "process", "transform"]
        if v not in allowed:
            raise ValueError(f"Operation must be one of: {allowed}")
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "text": "Sample text to process",
                "operation": "analyze",
                "parameters": {"language": "en"},
                "timeout": 30
            }
        }
```

## Performance Considerations

### 1. Agent Loading

- Agents are loaded once at startup
- Lazy loading for heavy dependencies
- Graceful error handling for failed agents

### 2. Endpoint Registration

- Endpoints registered once at startup
- Minimal runtime overhead
- Automatic route optimization

### 3. Memory Usage

- Shared agent instances
- Efficient model validation
- Garbage collection friendly

## Security Features

### 1. Authentication

```python
# Public endpoint (no auth)
@endpoint("/agent/info", auth_required=False)
async def get_info(self):
    return {"info": "public"}

# Protected endpoint (JWT required)
@endpoint("/agent/process", auth_required=True)
async def process(self, request_data: dict, user: dict):
    # user contains validated JWT claims
    return {"user_id": user["id"]}
```

### 2. Input Validation

- Automatic Pydantic validation
- Type safety enforcement
- SQL injection prevention
- XSS protection

### 3. Rate Limiting

Built-in rate limiting support:

```python
class MyAgent(SelfContainedAgent):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rate_limiter = RateLimiter(requests_per_minute=60)
```

## Troubleshooting

### Common Issues

1. **Agent Not Discovered**
   - Check file naming: `*_agent.py`
   - Ensure class inherits from `SelfContainedAgent`
   - Check for import errors

2. **Endpoint Not Registered**
   - Verify `@endpoint` decorator syntax
   - Check method signature
   - Ensure agent is discovered

3. **Model Validation Errors**
   - Check `@job_model` decorator
   - Verify Pydantic model syntax
   - Test model independently

### Debug Commands

```bash
# Check agent discovery status
curl http://localhost:8000/agents

# Check specific agent
curl http://localhost:8000/agents/my_agent

# Check agent health
curl http://localhost:8000/agents/my_agent/health
```

### Logging

Enable debug logging:

```python
import logging
logging.getLogger("agent_framework").setLevel(logging.DEBUG)
```

## Conclusion

The Self-Contained Agent Framework v2.0 represents a paradigm shift in agent development:

- **Zero Configuration**: Drop in agent files, no setup required
- **Self-Contained**: Everything in one file
- **Type Safe**: Full Pydantic validation
- **Auto-Discovery**: Automatic registration
- **Enterprise Ready**: Built-in auth, logging, monitoring

This architecture makes adding new agents as simple as creating a single file, dramatically reducing development time and complexity while maintaining enterprise-grade features and reliability.

## Next Steps

1. **Create Your First Agent**: Follow the quick start guide
2. **Explore Examples**: Study the included text processing and web scraping agents
3. **Read the API Docs**: Check the auto-generated OpenAPI documentation
4. **Join the Community**: Contribute to the framework development

Happy coding! 🚀 