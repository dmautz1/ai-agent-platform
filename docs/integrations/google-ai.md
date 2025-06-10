# Google AI Services Integration

> **AI/ML service configuration** - Complete setup for Google AI Studio integration

## Overview

The AI Agent Platform integrates with Google AI services to provide powerful AI capabilities:

- **Google AI Studio** - Easy-to-use AI development platform
- **Direct Google AI API** - Clean integration with Google's AI services
- **Gemini Models** - Access to Google's latest AI models
- **Vertex AI Support** - Optional enterprise-grade AI platform
- **Cost-Effective** - Pay-per-use pricing with generous free tier
- **Simple Configuration** - Minimal setup required

## Quick Setup

### 1. Create Google AI Studio Account

1. Go to [Google AI Studio](https://aistudio.google.com)
2. Sign in with your Google account
3. Accept the terms of service
4. Choose your country/region

### 2. Generate API Key

1. In Google AI Studio, click **"Get API Key"** in the top menu
2. Click **"Create API Key"**
3. Choose **"Create API key in new project"** (recommended for new users)
4. Copy the generated API key

```bash
# Your API key will look like this
GOOGLE_API_KEY=AIzaSyBxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

⚠️ **Security Note**: Keep this key secret! It provides access to Google AI services.

### 3. Configure Environment

Add your API key to the backend environment:

**Backend** (`backend/.env`):
```bash
# Google AI Configuration
GOOGLE_API_KEY=your-api-key-here
GOOGLE_AI_MODEL=gemini-2.0-flash  # Default model
VERTEX_AI_PROJECT_ID=your-project-id  # Optional: for Vertex AI
VERTEX_AI_LOCATION=us-central1  # Optional: for Vertex AI
```

### 4. Test Connection

Test your setup with the unified LLM service:

```bash
# Start your backend
cd backend && python main.py

# Test the connection
curl -X POST http://localhost:8000/ai/test \
  -H "Content-Type: application/json" \
  -d '{"provider": "google", "prompt": "Hello, world!"}'
```

Expected response:
```json
{
  "success": true,
  "result": "Hello! How can I help you today?",
  "provider": "google",
  "model": "gemini-2.0-flash"
}
```

## Available Models

### Gemini 2.0 Flash (Recommended)
- **Best for**: Fast responses, general tasks
- **Strengths**: Speed, cost-effective, good quality
- **Use cases**: Text processing, content generation, analysis

### Gemini 1.5 Pro
- **Best for**: Complex reasoning, high-quality output
- **Strengths**: Advanced reasoning, detailed responses
- **Use cases**: Complex analysis, research, detailed content

### Model Configuration

Set the model in your environment:

```bash
# Fast and cost-effective (default)
GOOGLE_AI_MODEL=gemini-2.0-flash

# Higher quality for complex tasks
GOOGLE_AI_MODEL=gemini-1.5-pro
```

## Backend Integration

### Google AI Client Setup

The template includes a pre-configured Google AI integration:

```python
# backend/config/google_ai.py (simplified example)
import google.generativeai as genai
import os

def get_google_ai_config():
    """Initialize Google AI configuration"""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not configured")
    
    genai.configure(api_key=api_key)
    
    return {
        "api_key": api_key,
        "default_model": os.getenv("GOOGLE_AI_MODEL", "gemini-2.0-flash"),
        "use_vertex_ai": os.getenv("USE_VERTEX_AI", "false").lower() == "true",
        "project_id": os.getenv("VERTEX_AI_PROJECT_ID"),
        "location": os.getenv("VERTEX_AI_LOCATION", "us-central1")
    }

def create_model(model_name: str = None):
    """Create a Google AI model instance"""
    config = get_google_ai_config()
    model_name = model_name or config["default_model"]
    
    return genai.GenerativeModel(model_name)
```

### Using Google AI in Agents

Example agent integration using direct Google AI:

```python
# agents/my_ai_agent.py
from typing import Dict, Any
import google.generativeai as genai
from agent_framework import SelfContainedAgent, endpoint, job_model
from config.google_ai import create_model

@job_model
class AIJobData(BaseModel):
    prompt: str = Field(..., description="Text prompt for AI")
    max_tokens: int = Field(default=1000, description="Maximum response length")

class MyAIAgent(SelfContainedAgent):
    def __init__(self, **kwargs):
        super().__init__(
            description="AI-powered text processing using Google AI",
            agent_type="llm",
            **kwargs
        )
        self.model = create_model()
    
    @endpoint("/ai-agent/generate", methods=["POST"], auth_required=True)
    async def generate_text(self, request_data: dict, user: dict):
        job_data = validate_job_data(request_data, AIJobData)
        return await execute_agent_job(self, job_data, user["id"])
    
    async def _execute_job_logic(self, job_data: AIJobData):
        try:
            # Generate content using Google AI
            response = await self.model.generate_content_async(job_data.prompt)
            
            return AgentExecutionResult(
                success=True,
                result=response.text,
                metadata={
                    "model": self.model.model_name,
                    "prompt_length": len(job_data.prompt),
                    "response_length": len(response.text),
                    "service": "Google AI Studio"
                }
            )
        except Exception as e:
            return AgentExecutionResult(
                success=False,
                error_message=f"Google AI generation failed: {str(e)}"
            )
```

## Built-in AI Agents

The template includes several pre-built agents that use Google AI:

### Simple Prompt Agent
- **Endpoint**: `/simple-prompt/process`
- **Features**: Text generation using Google AI, conversation, analysis
- **Use cases**: Content generation, Q&A, text processing

### Workflow Agents
- **Sequential Agent**: `/workflow/sequential`
- **Parallel Agent**: `/workflow/parallel` 
- **Loop Agent**: `/workflow/loop`
- **Features**: Multi-step AI workflows using Google AI
- **Use cases**: Complex task automation, multi-stage processing

### Multi-Agent Coordinator
- **Endpoint**: `/multi-agent/coordinate`
- **Features**: Agent delegation and coordination using Google AI
- **Use cases**: Complex task distribution, specialized agent teams

## Advanced Configuration

### Function Tools Integration

Add custom tools to agents using Google AI:

```python
import google.generativeai as genai

def calculate_total(items: list, tax_rate: float = 0.1) -> dict:
    """Calculate total with tax for a list of items"""
    subtotal = sum(item.get('price', 0) for item in items)
    tax = subtotal * tax_rate
    total = subtotal + tax
    return {
        "subtotal": subtotal,
        "tax": tax,
        "total": total
    }

class BusinessAgent(SelfContainedAgent):
    def _get_google_ai_tools(self):
        """Return Google AI FunctionTools for this agent"""
        return [
            genai.FunctionTool(
                name="calculate_total",
                description="Calculate order total with tax",
                func=calculate_total
            )
        ]
    
    def _create_google_ai_agent(self):
        return create_model(self.name)
```

### Workflow Agent Creation

Create complex workflows using Google AI:

```python
from google.generativeai import Sequential, Parallel, Loop
from config.google_ai import create_workflow_agent

class WorkflowAgent(SelfContainedAgent):
    def __init__(self, **kwargs):
        super().__init__(agent_type="sequential", **kwargs)
    
    def _create_google_ai_agent(self):
        # Create sub-agents for the workflow
        analyzer = create_model("analyzer")
        
        processor = create_model("processor")
        
        summarizer = create_model("summarizer")
        
        # Create Sequential workflow
        return create_workflow_agent(
            agent_type="sequential",
            name=f"{self.name}_workflow",
            agents=[analyzer, processor, summarizer]
        )
```

### Multi-Agent Coordination

Coordinate multiple agents using Google AI:

```python
class CoordinatorAgent(SelfContainedAgent):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.specialist_agents = []
    
    def add_specialist_agent(self, agent):
        """Add a specialist agent to coordinate"""
        self.specialist_agents.append(agent)
    
    async def coordinate_task(self, task_description: str):
        """Coordinate task execution across multiple agents"""
        coordination_result = await self.coordinate_agents(
            agents=self.specialist_agents,
            coordinator_prompt=f"""
            Analyze this task and distribute it among available specialist agents:
            Task: {task_description}
            
            Plan the optimal task distribution and execution order.
            """
        )
        
        return coordination_result
```

## Cost Management

### Understanding Pricing

Google AI Studio offers:
- **Free Tier**: Generous limits for development and testing
- **Pay-per-use**: Only pay for what you use in production
- **Token-based pricing**: Charged per input/output tokens

### Monitoring Usage

Track AI usage through Google AI:

```python
class GoogleAIAUsageTracker:
    def __init__(self):
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
    
    async def track_google_ai_request(self, agent, prompt: str):
        """Track Google AI agent usage"""
        self.total_requests += 1
        
        try:
            response = await agent.model.generate_content_async(prompt)
            self.successful_requests += 1
        
            logger.info(f"Google AI Usage - Total: {self.total_requests}, "
                       f"Success: {self.successful_requests}, "
                       f"Failed: {self.failed_requests}")
            
            return response
        except Exception as e:
            self.failed_requests += 1
            logger.error(f"Google AI request failed: {e}")
            raise
```

### Cost Optimization Tips

1. **Choose the right agent type**: Use Google AI for simple tasks, workflows for complex ones
2. **Optimize instructions**: Clear, concise system instructions = better efficiency
3. **Use agent caching**: Google AI agents cache responses automatically
4. **Leverage workflow agents**: Avoid redundant processing with proper workflows
5. **Monitor agent performance**: Track usage patterns and optimize

## Troubleshooting

### Common Issues

**Google AI Configuration Problems:**
```bash
# Check if Google AI is properly configured
echo $GOOGLE_API_KEY

# Test Google AI connection
curl http://localhost:8000/google-ai/connection-test
```

**Agent Creation Issues:**
```python
# Test Google AI agent creation
from config.google_ai import create_model

try:
    agent = create_model("test_agent")
    response = agent.model.generate_content_async("Hello, test!")
    print("Google AI agent working correctly")
except Exception as e:
    print(f"Google AI agent error: {e}")
```

**Workflow Agent Problems:**
```python
# Check workflow agent creation
from config.google_ai import create_workflow_agent

try:
    agents = [create_model("agent1"), create_model("agent2")]
    workflow = create_workflow_agent("sequential", "test_workflow", agents)
    print("Workflow agent created successfully")
except Exception as e:
    print(f"Workflow creation error: {e}")
```

### Performance Optimization

1. **Agent reuse**: Reuse agent instances instead of creating new ones
2. **Proper workflow design**: Design efficient Sequential/Parallel workflows
3. **Tool optimization**: Use efficient function tools
4. **Async patterns**: Use async/await for concurrent operations

### Security Best Practices

1. **API Key Protection**: Never commit API keys to version control
2. **Environment Variables**: Use secure environment variable storage
3. **Agent Validation**: Validate agent responses before processing
4. **Tool Security**: Ensure function tools are secure and validated
5. **Multi-agent Security**: Secure communication between agents

---

**Next Steps:**
- **[Authentication Setup](authentication.md)** - User management integration
- **[Agent Development Guide](../development/agent-development.md)** - Build Google AI-powered agents
- **[API Reference](../development/api-reference.md)** - Google AI agent endpoints 