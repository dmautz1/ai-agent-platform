# Agent Development Guide

> **Complete Guide to Building Custom AI Agents** - From basic setup to advanced patterns

This guide teaches you how to create custom AI agents using the Self-Contained Agent Framework v1.0. Perfect for developers who want to build specialized AI functionality for their applications.

## Table of Contents

- [Quick Start](#quick-start)
- [Framework Overview](#framework-overview)
- [Creating Your First Agent](#creating-your-first-agent)
- [Agent Architecture Patterns](#agent-architecture-patterns)
- [Advanced Features](#advanced-features)
- [Testing and Debugging](#testing-and-debugging)
- [Configuration and Deployment](#configuration-and-deployment)
- [Best Practices](#best-practices)
- [Common Patterns](#common-patterns)
- [Troubleshooting](#troubleshooting)

## Quick Start

### Prerequisites

- Python 3.8+
- Basic understanding of Python and FastAPI
- Google AI Studio API key (for AI functionality)
- AI Agent Platform setup (see [README.md](README.md))

### 5-Minute Agent Creation

Create a file `backend/agents/my_first_agent.py`:

```python
"""
My First Agent - A simple example agent
"""

from typing import List, Dict, Any
from pydantic import BaseModel, Field
from agent_framework import SelfContainedAgent, endpoint, job_model, execute_agent_job, validate_job_data
from agent import AgentExecutionResult

@job_model
class MyJobData(BaseModel):
    prompt: str = Field(..., description="Text to process")
    operation: str = Field(default="greet", description="Operation to perform")

class MyFirstAgent(SelfContainedAgent):
    def __init__(self, **kwargs):
        super().__init__(
            name="my_first_agent",  # Explicit name - this is the primary identifier
            description="My first custom agent",
            **kwargs
        )
    
    @endpoint("/my-first-agent/process", methods=["POST"], auth_required=True)
    async def process(self, request_data: dict, user: dict):
        job_data = validate_job_data(request_data, MyJobData)
        return await execute_agent_job(self, job_data, user["id"])
    
    async def _execute_job_logic(self, job_data: MyJobData) -> AgentExecutionResult:
        if job_data.operation == "greet":
            result = f"Hello! You sent: {job_data.prompt}"
        else:
            result = f"Processed '{job_data.prompt}' with operation '{job_data.operation}'"
        
        return AgentExecutionResult(
            success=True,
            result=result,
            metadata={"operation": job_data.operation}
        )
```

**That's it!** Your agent is automatically discovered and available at `/my-first-agent/process`.

## Framework Overview

### Self-Contained Agent Framework v1.0

The platform uses a **dual-agent architecture** with two approaches:

1. **SelfContainedAgent** - Zero-configuration rapid development framework
2. **BaseAgent** - Maximum control for complex custom integrations

The framework is **completely LLM-agnostic**, supporting 6+ AI providers through a unified interface.

#### SelfContainedAgent - Recommended Approach

The **single-file approach** where each agent contains:

1. **Job Data Models** - Define input/output with `@job_model`
2. **API Endpoints** - Create endpoints with `@endpoint`
3. **Business Logic** - Implement core functionality
4. **Configuration** - Agent-specific settings

```python
from services.llm_service import get_unified_llm_service

@job_model
class MyJobData(BaseModel):
    prompt: str = Field(..., description="Text to process")
    provider: Optional[str] = Field(default="google", description="AI provider to use")

class MyAgent(SelfContainedAgent):
    def __init__(self, **kwargs):
        super().__init__(
            name="my_agent",  # Explicit name - this is the primary identifier
            description="My custom agent description",
            **kwargs
        )
        self.llm = get_unified_llm_service()  # LLM-agnostic service
    
    @endpoint("/my-agent/process", methods=["POST"], auth_required=True)
    async def process(self, request_data: dict, user: dict):
        job_data = validate_job_data(request_data, MyJobData)
        return await execute_agent_job(self, job_data, user["id"])
    
    async def _execute_job_logic(self, job_data):
        # Works with any AI provider
        result = await self.llm.query(
            prompt=job_data.prompt,
            provider=job_data.provider  # User's choice
        )
        return AgentExecutionResult(success=True, result=result)

#### BaseAgent - Advanced Use Cases

Use BaseAgent when you need:
- Complex multi-step workflows
- Custom database integrations  
- Manual API endpoint management
- Integration with external services

**→ [Complete Architecture Guide](../architecture/agent-architecture.md)** for detailed comparison.

### Key Benefits

- ✅ **Zero Configuration** - Drop in a file, it works
- ✅ **LLM Provider Agnostic** - Supports Google AI, OpenAI, Anthropic, Grok, DeepSeek, Meta Llama
- ✅ **Type Safety** - Full Pydantic validation
- ✅ **Auto-Discovery** - Automatic registration
- ✅ **Built-in Auth** - JWT authentication support
- ✅ **Self-Documenting** - OpenAPI docs generated automatically

### Framework Components

```
backend/agents/your_agent.py
├── @job_model decorators    # Data models
├── Agent class              # Main implementation
├── @endpoint decorators     # API endpoints
└── Business logic methods   # Your custom code
```

## Creating Your First Agent

### Step 1: Choose Your Agent Type

Decide what your agent will do:

- **Data Processing** - Transform, analyze, or validate data
- **Content Generation** - Create text, summaries, or reports
- **Integration** - Connect to external APIs or services
- **Workflow** - Orchestrate multi-step processes

### Step 2: Design Your Data Model

Define what data your agent needs:

```python
@job_model
class MyAgentJobData(BaseModel):
    # Required fields
    input_data: str = Field(..., min_length=1, description="Data to process")
    
    # Optional fields with defaults
    operation: str = Field(default="process", description="Operation type")
    options: Optional[Dict[str, Any]] = Field(default=None, description="Additional options")
    
    # Validation
    @validator('operation')
    def validate_operation(cls, v):
        allowed = ["process", "analyze", "transform"]
        if v not in allowed:
            raise ValueError(f"Operation must be one of: {allowed}")
        return v
```

### Step 3: Create Your Agent Class

```python
class MyAgent(SelfContainedAgent):
    def __init__(self, **kwargs):
        super().__init__(
            name="my_agent",  # Explicit name - this is the primary identifier
            description="Description of what your agent does",
            **kwargs
        )
        # Initialize any agent-specific settings
        self.supported_operations = ["process", "analyze", "transform"]
```

### Step 4: Add Endpoints

```python
# Public capability endpoint (no auth required)
@endpoint("/my-agent/capabilities", methods=["GET"], auth_required=False)
async def get_capabilities(self):
    return {
        "status": "success",
        "operations": self.supported_operations,
        "description": self.description
    }

# Main processing endpoint (auth required)
@endpoint("/my-agent/process", methods=["POST"], auth_required=True)
async def process_data(self, request_data: dict, user: dict):
    job_data = validate_job_data(request_data, MyAgentJobData)
    return await execute_agent_job(self, job_data, user["id"])
```

### Step 5: Implement Business Logic

```python
async def _execute_job_logic(self, job_data: MyAgentJobData) -> AgentExecutionResult:
    try:
        # Your agent's core logic here
        if job_data.operation == "process":
            result = self._process_data(job_data.input_data)
        elif job_data.operation == "analyze":
            result = self._analyze_data(job_data.input_data)
        else:
            result = self._transform_data(job_data.input_data)
        
        return AgentExecutionResult(
            success=True,
            result=result,
            metadata={
                "operation": job_data.operation,
                "processed_at": datetime.utcnow().isoformat()
            }
        )
    except Exception as e:
        return AgentExecutionResult(
            success=False,
            error_message=str(e)
        )

def _process_data(self, data: str) -> str:
    # Implement your processing logic
    return f"Processed: {data.upper()}"
```

## Agent Architecture Patterns

### Pattern 1: Simple Processor

For straightforward data transformation:

```python
class SimpleProcessorAgent(SelfContainedAgent):
    @endpoint("/simple-processor/transform", methods=["POST"], auth_required=True)
    async def transform(self, request_data: dict, user: dict):
        # Single-purpose endpoint
        input_data = request_data.get("data", "")
        result = input_data.upper()  # Simple transformation
        return {"result": result}
```

### Pattern 2: Multi-Operation Agent

For agents with multiple related functions:

```python
class MultiOperationAgent(SelfContainedAgent):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.operations = {
            "analyze": self._analyze,
            "transform": self._transform,
            "validate": self._validate
        }
    
    async def _execute_job_logic(self, job_data):
        operation = self.operations.get(job_data.operation)
        if not operation:
            raise ValueError(f"Unsupported operation: {job_data.operation}")
        return await operation(job_data)
```

### Pattern 3: AI-Powered Agent

For agents using any AI provider through the unified LLM service:

```python
class AIAgent(SelfContainedAgent):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Option 1: Use the unified LLM service directly
        self.llm_service = get_unified_llm_service()
    
    async def _execute_job_logic(self, job_data):
        # Use any AI provider through the unified interface
        response = await self.llm_service.query(
            prompt=f"Process this text: {job_data.prompt}",
            provider=job_data.preferred_provider,  # User can choose provider
            model=job_data.model,  # Optional specific model
            temperature=job_data.temperature
        )
        
        return AgentExecutionResult(
            success=True,
            result=response,
            metadata={
                "provider": job_data.preferred_provider,
                "model": job_data.model
            }
        )
```

**Alternative: Using BaseAgent's LLM Service Method**

For BaseAgent subclasses, you can use the built-in method:

```python
class CustomBaseAgent(BaseAgent):
    async def _execute_job_logic(self, job_data):
        # Option 2: Use BaseAgent's get_llm_service() method
        llm_service = self.get_llm_service()
        
        response = await llm_service.query(
            prompt=job_data.prompt,
            # Uses configured DEFAULT_LLM_PROVIDER if no provider specified
            provider=job_data.provider if hasattr(job_data, 'provider') else None
        )
        
        return AgentExecutionResult(success=True, result=response)
```

**Key Benefits:**
- **Provider Agnostic** - Works with Google AI, OpenAI, Anthropic, Grok, DeepSeek, Meta Llama
- **Configurable Default** - Uses `DEFAULT_LLM_PROVIDER` from environment config
- **User Choice** - Let users select their preferred AI provider
- **Automatic Fallbacks** - System handles provider failures gracefully
- **Cost Optimization** - Route to most cost-effective provider based on requirements

### Pattern 4: External API Integration

For agents that connect to external services:

```python
import aiohttp

class ExternalAPIAgent(SelfContainedAgent):
    async def _execute_job_logic(self, job_data):
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.example.com/process",
                json={"data": job_data.prompt}
            ) as response:
                result = await response.json()
        
        return AgentExecutionResult(
            success=True,
            result=result,
            metadata={"api_response_time": response.headers.get("response-time")}
        )
```

## Advanced Features

### Custom Validation

Add sophisticated input validation:

```python
@job_model
class AdvancedJobData(BaseModel):
    email: str = Field(..., description="Email to validate")
    data: Dict[str, Any] = Field(..., description="Additional data")
    
    @validator('email')
    def validate_email_format(cls, v):
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, v):
            raise ValueError('Invalid email format')
        return v
    
    @validator('data')
    def validate_required_fields(cls, v):
        required_fields = ['name', 'type']
        for field in required_fields:
            if field not in v:
                raise ValueError(f'Missing required field: {field}')
        return v
```

### Multiple Endpoints

Create specialized endpoints for different use cases:

```python
class AdvancedAgent(SelfContainedAgent):
    # Batch processing endpoint
    @endpoint("/advanced/batch", methods=["POST"], auth_required=True)
    async def batch_process(self, request_data: dict, user: dict):
        items = request_data.get("items", [])
        results = []
        for item in items:
            # Process each item
            result = await self.process_single_item(item)
            results.append(result)
        return {"results": results}
    
    # Status check endpoint
    @endpoint("/advanced/status", methods=["GET"], auth_required=False)
    async def get_status(self):
        return {
            "status": "healthy",
            "last_processed": self.last_execution_time,
            "total_processed": self.execution_count
        }
    
    # Configuration endpoint
    @endpoint("/advanced/config", methods=["GET", "PUT"], auth_required=True)
    async def manage_config(self, request_data: dict = None, user: dict = None):
        if request_data:  # PUT request
            # Update configuration
            self.update_config(request_data)
            return {"message": "Configuration updated"}
        else:  # GET request
            return {"config": self.get_current_config()}
```

### Error Handling and Retry Logic

Implement robust error handling:

```python
import asyncio
from typing import Union

class RobustAgent(SelfContainedAgent):
    async def _execute_job_logic(self, job_data) -> AgentExecutionResult:
        max_retries = 3
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                result = await self._process_with_timeout(job_data)
                return AgentExecutionResult(success=True, result=result)
            
            except asyncio.TimeoutError:
                if attempt == max_retries - 1:
                    return AgentExecutionResult(
                        success=False,
                        error_message="Processing timeout after retries"
                    )
                await asyncio.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
            
            except ValueError as e:
                # Don't retry validation errors
                return AgentExecutionResult(
                    success=False,
                    error_message=f"Validation error: {str(e)}"
                )
            
            except Exception as e:
                if attempt == max_retries - 1:
                    return AgentExecutionResult(
                        success=False,
                        error_message=f"Processing failed: {str(e)}"
                    )
                await asyncio.sleep(retry_delay)
    
    async def _process_with_timeout(self, job_data):
        timeout = self.agent_config.execution.timeout_seconds
        return await asyncio.wait_for(
            self._actual_processing(job_data),
            timeout=timeout
        )
```

### Custom Configuration

Add agent-specific configuration:

```python
class ConfigurableAgent(SelfContainedAgent):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Load custom configuration
        custom_config = self.agent_config.custom_settings
        self.max_items = custom_config.get("max_items", 100)
        self.enable_caching = custom_config.get("enable_caching", True)
        self.api_key = custom_config.get("external_api_key")
        
        if not self.api_key:
            logger.warning("No external API key configured")
    
    @endpoint("/configurable/settings", methods=["GET"], auth_required=True)
    async def get_settings(self):
        return {
            "max_items": self.max_items,
            "enable_caching": self.enable_caching,
            "api_configured": bool(self.api_key)
        }
```

## Testing and Debugging

### Unit Testing Your Agent

Create tests for your agent:

```python
# tests/test_my_agent.py
import pytest
from backend.agents.my_agent import MyAgent, MyJobData

@pytest.fixture
def agent():
    return MyAgent()

@pytest.mark.asyncio
async def test_process_data(agent):
    job_data = MyJobData(
        prompt="test input",
        operation="process"
    )
    
    result = await agent._execute_job_logic(job_data)
    
    assert result.success
    assert "test input" in result.result

@pytest.mark.asyncio
async def test_invalid_operation(agent):
    job_data = MyJobData(
        prompt="test input",
        operation="invalid_operation"
    )
    
    result = await agent._execute_job_logic(job_data)
    
    assert not result.success
    assert "invalid_operation" in result.error_message
```

### Manual Testing

Test your agent via API:

```bash
# Test capabilities endpoint
curl http://localhost:8000/my-agent/capabilities

# Test processing endpoint (with auth)
curl -X POST http://localhost:8000/my-agent/process \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "test", "operation": "process"}'
```

### Debugging

Add comprehensive logging:

```python
from logging_system import get_logger

logger = get_logger(__name__)

class DebuggableAgent(SelfContainedAgent):
    async def _execute_job_logic(self, job_data):
        logger.info(f"Processing job with operation: {job_data.operation}")
        logger.debug(f"Input data: {job_data.prompt[:100]}...")
        
        try:
            result = await self._process_data(job_data)
            logger.info(f"Successfully processed job")
            return result
        except Exception as e:
            logger.error(f"Job processing failed: {str(e)}", exc_info=True)
            raise
```

## Configuration and Deployment

### Agent Configuration

Configure your agent via files or environment variables:

```json
// config/agents/my_agent.json
{
  "name": "my_agent",
  "description": "My custom agent",
  "profile": "balanced",
  "execution": {
    "timeout_seconds": 120,
    "max_retries": 3
  },
  "model": {
    "temperature": 0.7,
    "max_tokens": 2000
  },
  "custom_settings": {
    "max_items": 50,
    "enable_feature_x": true,
    "external_api_url": "https://api.example.com"
  }
}
```