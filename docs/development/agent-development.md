# Agent Customization Guide

> **Complete Guide to Building Custom AI Agents** - From basic setup to advanced patterns

This guide teaches you how to create custom AI agents using the Self-Contained Agent Framework v2.0. Perfect for developers who want to build specialized AI functionality for their applications.

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
- AI Agent Template setup (see [README.md](README.md))

### 5-Minute Agent Creation

Create a file `backend/agents/my_first_agent.py`:

```python
"""
My First Agent - A simple example agent
"""

from typing import List, Dict, Any
from pydantic import BaseModel, Field
from agent_framework import SelfContainedAgent, endpoint, job_model, execute_agent_job, validate_job_data
from models import JobType
from agent import AgentExecutionResult

@job_model
class MyJobData(BaseModel):
    input_text: str = Field(..., description="Text to process")
    operation: str = Field(default="greet", description="Operation to perform")

class MyFirstAgent(SelfContainedAgent):
    def __init__(self, **kwargs):
        super().__init__(description="My first custom agent", **kwargs)
    
    def get_supported_job_types(self) -> List[JobType]:
        return [JobType.custom]
    
    @endpoint("/my-first-agent/process", methods=["POST"], auth_required=True)
    async def process(self, request_data: dict, user: dict):
        job_data = validate_job_data(request_data, MyJobData)
        return await execute_agent_job(self, job_data, user["id"])
    
    async def _execute_job_logic(self, job_data: MyJobData) -> AgentExecutionResult:
        if job_data.operation == "greet":
            result = f"Hello! You sent: {job_data.input_text}"
        else:
            result = f"Processed '{job_data.input_text}' with operation '{job_data.operation}'"
        
        return AgentExecutionResult(
            success=True,
            result=result,
            metadata={"operation": job_data.operation}
        )
```

**That's it!** Your agent is automatically discovered and available at `/my-first-agent/process`.

## Framework Overview

### Self-Contained Agent Framework v2.0

The framework uses a **single-file approach** where each agent contains:

1. **Job Data Models** - Define input/output with `@job_model`
2. **API Endpoints** - Create endpoints with `@endpoint`
3. **Business Logic** - Implement core functionality
4. **Configuration** - Agent-specific settings

### Key Benefits

- ✅ **Zero Configuration** - Drop in a file, it works
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
            description="Description of what your agent does",
            **kwargs
        )
        # Initialize any agent-specific settings
        self.supported_operations = ["process", "analyze", "transform"]
    
    def get_supported_job_types(self) -> List[JobType]:
        return [JobType.custom]  # or specific type like JobType.text_processing
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

For agents using Google AI/ADK:

```python
class AIAgent(SelfContainedAgent):
    async def _execute_job_logic(self, job_data):
        # Get the ADK agent
        adk_agent = await self.get_adk_agent()
        
        # Create prompt
        prompt = f"Process this text: {job_data.input_text}"
        
        # Query AI model
        response = await adk_agent.query(prompt)
        
        return AgentExecutionResult(
            success=True,
            result=response,
            metadata={"model_used": self.agent_config.model.model_name}
        )
```

### Pattern 4: External API Integration

For agents that connect to external services:

```python
import aiohttp

class ExternalAPIAgent(SelfContainedAgent):
    async def _execute_job_logic(self, job_data):
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.example.com/process",
                json={"data": job_data.input_data}
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
        input_text="test input",
        operation="process"
    )
    
    result = await agent._execute_job_logic(job_data)
    
    assert result.success
    assert "test input" in result.result

@pytest.mark.asyncio
async def test_invalid_operation(agent):
    job_data = MyJobData(
        input_text="test input",
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
  -d '{"input_text": "test", "operation": "process"}'
```

### Debugging

Add comprehensive logging:

```python
from logging_system import get_logger

logger = get_logger(__name__)

class DebuggableAgent(SelfContainedAgent):
    async def _execute_job_logic(self, job_data):
        logger.info(f"Processing job with operation: {job_data.operation}")
        logger.debug(f"Input data: {job_data.input_text[:100]}...")
        
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

Or use environment variables:

```bash
export AGENT_MY_AGENT_EXECUTION_TIMEOUT_SECONDS=180
export AGENT_MY_AGENT_CUSTOM_SETTINGS_MAX_ITEMS=100
```

### Deployment Checklist

Before deploying your agent:

- [ ] Test all endpoints manually
- [ ] Write unit tests for core logic
- [ ] Configure production settings
- [ ] Set up monitoring and logging
- [ ] Document API endpoints
- [ ] Validate error handling
- [ ] Check authentication requirements
- [ ] Test with realistic data volumes

## Best Practices

### 1. Agent Design

**Keep It Focused**
```python
# Good: Single responsibility
class EmailValidatorAgent(SelfContainedAgent):
    """Validates email addresses only"""
    pass

# Avoid: Multiple unrelated responsibilities
class EverythingAgent(SelfContainedAgent):
    """Validates emails, processes images, sends notifications..."""
    pass
```

**Use Clear Naming**
```python
# Good: Descriptive names
class DocumentSummarizerAgent(SelfContainedAgent):
    @endpoint("/document-summarizer/summarize", ...)
    async def summarize_document(self, ...):
        pass

# Avoid: Generic names
class ProcessorAgent(SelfContainedAgent):
    @endpoint("/processor/do", ...)
    async def do_stuff(self, ...):
        pass
```

### 2. Data Validation

**Comprehensive Validation**
```python
@job_model
class WellValidatedJobData(BaseModel):
    # Field validation
    text: str = Field(..., min_length=1, max_length=10000)
    priority: int = Field(default=5, ge=1, le=10)
    
    # Custom validation
    @validator('text')
    def validate_text_content(cls, v):
        if any(word in v.lower() for word in ['spam', 'malicious']):
            raise ValueError('Text contains prohibited content')
        return v
    
    # Configuration example
    class Config:
        schema_extra = {
            "example": {
                "text": "Sample text to process",
                "priority": 5
            }
        }
```

### 3. Error Handling

**Graceful Degradation**
```python
async def _execute_job_logic(self, job_data):
    try:
        # Primary processing method
        return await self._primary_process(job_data)
    except ExternalAPIError:
        # Fallback to secondary method
        logger.warning("Primary API failed, using fallback")
        return await self._fallback_process(job_data)
    except ValidationError as e:
        # Clear error for client
        return AgentExecutionResult(
            success=False,
            error_message=f"Invalid input: {str(e)}"
        )
    except Exception as e:
        # Log details, return generic error
        logger.error("Unexpected error", exc_info=True)
        return AgentExecutionResult(
            success=False,
            error_message="Processing failed due to internal error"
        )
```

### 4. Performance

**Efficient Processing**
```python
class EfficientAgent(SelfContainedAgent):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Initialize expensive resources once
        self.model = self._load_model()
        self.cache = {}
    
    async def _execute_job_logic(self, job_data):
        # Check cache first
        cache_key = self._get_cache_key(job_data)
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        # Process and cache result
        result = await self._actual_process(job_data)
        self.cache[cache_key] = result
        return result
```

### 5. Security

**Input Sanitization**
```python
class SecureAgent(SelfContainedAgent):
    async def _execute_job_logic(self, job_data):
        # Sanitize inputs
        clean_text = self._sanitize_input(job_data.input_text)
        
        # Validate size limits
        if len(clean_text) > self.agent_config.security.max_input_size_bytes:
            raise ValueError("Input too large")
        
        # Process safely
        result = await self._safe_process(clean_text)
        
        # Sanitize output
        clean_result = self._sanitize_output(result)
        return AgentExecutionResult(success=True, result=clean_result)
    
    def _sanitize_input(self, text: str) -> str:
        # Remove/escape potentially dangerous content
        import html
        return html.escape(text.strip())
```

## Common Patterns

### Pattern: Workflow Agent

For multi-step processes:

```python
class WorkflowAgent(SelfContainedAgent):
    async def _execute_job_logic(self, job_data):
        workflow_id = f"wf_{uuid.uuid4().hex[:8]}"
        
        try:
            # Step 1: Validate input
            await self._step_validate(job_data, workflow_id)
            
            # Step 2: Pre-process
            preprocessed = await self._step_preprocess(job_data, workflow_id)
            
            # Step 3: Main processing
            result = await self._step_main_process(preprocessed, workflow_id)
            
            # Step 4: Post-process
            final_result = await self._step_postprocess(result, workflow_id)
            
            return AgentExecutionResult(
                success=True,
                result=final_result,
                metadata={"workflow_id": workflow_id}
            )
        except Exception as e:
            logger.error(f"Workflow {workflow_id} failed at step", exc_info=True)
            raise
```

### Pattern: Batch Processor

For handling multiple items:

```python
class BatchAgent(SelfContainedAgent):
    @endpoint("/batch/process", methods=["POST"], auth_required=True)
    async def batch_process(self, request_data: dict, user: dict):
        items = request_data.get("items", [])
        max_batch_size = self.agent_config.custom_settings.get("max_batch_size", 100)
        
        if len(items) > max_batch_size:
            raise ValueError(f"Batch size {len(items)} exceeds limit {max_batch_size}")
        
        results = []
        for i, item in enumerate(items):
            try:
                result = await self._process_single_item(item)
                results.append({"index": i, "success": True, "result": result})
            except Exception as e:
                results.append({"index": i, "success": False, "error": str(e)})
        
        return {
            "total_items": len(items),
            "successful": sum(1 for r in results if r["success"]),
            "failed": sum(1 for r in results if not r["success"]),
            "results": results
        }
```

### Pattern: Event-Driven Agent

For reactive processing:

```python
class EventDrivenAgent(SelfContainedAgent):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.event_handlers = {
            "user_action": self._handle_user_action,
            "system_alert": self._handle_system_alert,
            "data_update": self._handle_data_update
        }
    
    @endpoint("/events/handle", methods=["POST"], auth_required=True)
    async def handle_event(self, request_data: dict, user: dict):
        event_type = request_data.get("event_type")
        event_data = request_data.get("data", {})
        
        handler = self.event_handlers.get(event_type)
        if not handler:
            raise ValueError(f"Unknown event type: {event_type}")
        
        result = await handler(event_data, user)
        return {
            "event_type": event_type,
            "processed_at": datetime.utcnow().isoformat(),
            "result": result
        }
```

## Troubleshooting

### Agent Not Discovered

**Problem**: Agent file exists but doesn't appear in `/agents` endpoint

**Solutions**:
1. Check file naming: Must end with `_agent.py`
2. Ensure class inherits from `SelfContainedAgent`
3. Check for import errors in agent file
4. Restart the server

```bash
# Debug discovery
curl http://localhost:8000/agents
# Check logs for errors
tail -f logs/app.log | grep agent
```

### Endpoints Not Working

**Problem**: Agent discovered but endpoints return 404

**Solutions**:
1. Verify `@endpoint` decorator syntax
2. Check method signature matches auth requirements
3. Ensure agent class is properly instantiated

```python
# Correct endpoint signature
@endpoint("/my-agent/process", methods=["POST"], auth_required=True)
async def process(self, request_data: dict, user: dict):  # Note: both parameters
    pass

# For no-auth endpoints
@endpoint("/my-agent/info", methods=["GET"], auth_required=False)
async def get_info(self):  # Note: no user parameter
    pass
```

### Validation Errors

**Problem**: Request fails with validation errors

**Solutions**:
1. Check `@job_model` decorator is applied
2. Verify request data matches model schema
3. Test model validation independently

```python
# Test your model
try:
    data = MyJobData(input_text="test", operation="process")
    print("Model validation passed")
except ValidationError as e:
    print(f"Validation failed: {e}")
```

### Performance Issues

**Problem**: Agent responses are slow

**Solutions**:
1. Profile your code to find bottlenecks
2. Implement caching for repeated operations
3. Use async/await properly
4. Optimize Google ADK calls

```python
import time

async def _execute_job_logic(self, job_data):
    start_time = time.time()
    
    try:
        result = await self._process_data(job_data)
        processing_time = time.time() - start_time
        
        logger.info(f"Processing completed in {processing_time:.2f}s")
        return result
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"Processing failed after {processing_time:.2f}s: {e}")
        raise
```

### Memory Issues

**Problem**: Agent consumes too much memory

**Solutions**:
1. Use generators for large datasets
2. Process data in chunks
3. Clear caches periodically
4. Monitor memory usage

```python
class MemoryEfficientAgent(SelfContainedAgent):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.max_cache_size = 1000
        self.cache = {}
    
    def _manage_cache(self):
        if len(self.cache) > self.max_cache_size:
            # Remove oldest entries
            items = list(self.cache.items())
            for key, _ in items[:len(items)//2]:
                del self.cache[key]
```

## Next Steps

### Learn More

- **[API Documentation](API_DOCUMENTATION.md)** - Complete API reference
- **[Agent Framework Details](backend/README_AGENT_FRAMEWORK_V2.md)** - Technical deep dive
- **[Configuration Guide](backend/README_AGENT_CONFIG.md)** - Advanced configuration
- **[Examples](backend/agents/)** - Study existing agent implementations

### Contribute

- Create agents for common use cases
- Improve framework features
- Add testing utilities
- Write documentation

### Get Help

- Check existing agent implementations for patterns
- Review the API documentation for endpoint details
- Test your agents thoroughly before deployment
- Use the interactive docs at `http://localhost:8000/docs`

---

**Ready to build amazing AI agents?** Start with the quick start example and gradually add more sophisticated features as you learn the framework! 