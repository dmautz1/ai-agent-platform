# OpenAI Integration

> **OpenAI (GPT) Setup** - Configure OpenAI's GPT models for your AI agents

## Overview

OpenAI integration provides access to powerful language models including GPT-4, GPT-4 Turbo, and GPT-3.5 Turbo. Known for reliability, strong code generation capabilities, and consistent performance.

**Key Features:**
- **Industry Standard**: Most widely used commercial LLM
- **Code Generation**: Excellent at programming tasks
- **Function Calling**: Advanced tool integration
- **JSON Mode**: Structured output generation
- **Reliable**: High uptime and consistent performance

## Quick Setup

### 1. Create OpenAI Account

1. Go to [OpenAI Platform](https://platform.openai.com)
2. Sign up or log in with your account
3. Complete account verification if required
4. Add billing information (required for API access)

### 2. Generate API Key

1. Navigate to **API Keys** in your dashboard
2. Click **"Create new secret key"**
3. Give it a descriptive name (e.g., "AI Agent Platform")
4. Copy the generated key immediately (it won't be shown again)

```bash
# Your OpenAI API key
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

⚠️ **Security Warning**: Never share or commit this key. It provides billing access to your OpenAI account.

### 3. Configure Environment

Add your OpenAI configuration to `backend/.env`:

```bash
# OpenAI Configuration
OPENAI_API_KEY=sk-proj-your-key-here
OPENAI_MODEL=gpt-4-turbo-preview  # Default model
OPENAI_MAX_TOKENS=4000           # Response length limit
OPENAI_TEMPERATURE=0.7           # Creativity level (0-2)
```

### 4. Test Connection

```bash
# Start backend
cd backend && python main.py

# Test OpenAI connection
curl -X POST http://localhost:8000/ai/test \
  -H "Content-Type: application/json" \
  -d '{"provider": "openai", "prompt": "Hello, world!"}'
```

Expected response:
```json
{
  "success": true,
  "result": "Hello! How can I assist you today?",
  "provider": "openai",
  "model": "gpt-4-turbo-preview"
}
```

## Available Models

### GPT-4 Turbo (Recommended)
- **Model**: `gpt-4-turbo-preview`
- **Context**: 128K tokens
- **Best for**: Complex reasoning, analysis, coding
- **Cost**: $0.01/1K input, $0.03/1K output tokens

### GPT-4
- **Model**: `gpt-4`
- **Context**: 8K tokens
- **Best for**: High-quality responses, complex tasks
- **Cost**: $0.03/1K input, $0.06/1K output tokens

### GPT-3.5 Turbo (Cost-Effective)
- **Model**: `gpt-3.5-turbo`
- **Context**: 16K tokens
- **Best for**: General tasks, high-volume applications
- **Cost**: $0.0005/1K input, $0.0015/1K output tokens

### Model Configuration

```bash
# High-quality, expensive
OPENAI_MODEL=gpt-4-turbo-preview

# Balanced quality and cost
OPENAI_MODEL=gpt-4

# Cost-effective for simple tasks
OPENAI_MODEL=gpt-3.5-turbo
```

## Using OpenAI in Agents

### Basic Usage

```python
from services.llm_service import get_unified_llm_service

class MyOpenAIAgent(SelfContainedAgent):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.llm = get_unified_llm_service()
    
    async def _execute_job_logic(self, job_data):
        result = await self.llm.query(
            prompt=job_data.prompt,
            provider="openai",
            model="gpt-4-turbo-preview"
        )
        
        return AgentExecutionResult(
            success=True,
            result=result,
            metadata={"provider": "openai"}
        )
```

### Advanced Configuration

```python
@job_model
class OpenAIJobData(BaseModel):
    prompt: str = Field(..., description="Text prompt")
    model: str = Field(default="gpt-4-turbo-preview", description="OpenAI model")
    temperature: float = Field(default=0.7, ge=0, le=2, description="Creativity level")
    max_tokens: int = Field(default=4000, description="Maximum response length")
    response_format: str = Field(default="text", description="Response format (text|json)")

class AdvancedOpenAIAgent(SelfContainedAgent):
    async def _execute_job_logic(self, job_data: OpenAIJobData):
        result = await self.llm.query(
            prompt=job_data.prompt,
            provider="openai",
            model=job_data.model,
            temperature=job_data.temperature,
            max_tokens=job_data.max_tokens,
            response_format=job_data.response_format
        )
        
        return AgentExecutionResult(
            success=True,
            result=result,
            metadata={
                "provider": "openai",
                "model": job_data.model,
                "temperature": job_data.temperature
            }
        )
```

## OpenAI-Specific Features

### 1. JSON Mode

Force structured JSON output:

```python
result = await self.llm.query(
    prompt="Extract person details: John Smith, age 30, engineer",
    provider="openai",
    response_format="json",
    extra_instructions="Return as JSON with fields: name, age, profession"
)

# Result: {"name": "John Smith", "age": 30, "profession": "engineer"}
```

### 2. Function Calling

Define functions for the model to use:

```python
functions = [
    {
        "name": "get_weather",
        "description": "Get weather for a location",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {"type": "string"},
                "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]}
            },
            "required": ["location"]
        }
    }
]

result = await self.llm.query(
    prompt="What's the weather in San Francisco?",
    provider="openai",
    functions=functions
)
```

### 3. System Messages

Use system messages for behavior control:

```python
result = await self.llm.query(
    prompt="Hello there!",
    provider="openai",
    system_message="You are a helpful assistant that responds in pirate speak."
)

# Result: "Ahoy there, matey! How can this old sea dog help ye today?"
```

### 4. Token Optimization

```python
# Count tokens before making request
from tiktoken import encoding_for_model

encoder = encoding_for_model("gpt-4")
token_count = len(encoder.encode(prompt))

if token_count > 8000:  # GPT-4 limit
    # Use GPT-4 Turbo instead
    model = "gpt-4-turbo-preview"
else:
    model = "gpt-4"

result = await self.llm.query(prompt, provider="openai", model=model)
```

## Cost Management

### Pricing (as of Dec 2024)

| Model | Input (1K tokens) | Output (1K tokens) | Context Window |
|-------|-------------------|-------------------|----------------|
| GPT-4 Turbo | $0.01 | $0.03 | 128K |
| GPT-4 | $0.03 | $0.06 | 8K |
| GPT-3.5 Turbo | $0.0005 | $0.0015 | 16K |

### Cost Optimization Strategies

```python
# 1. Model selection based on complexity
def select_model(task_complexity: str) -> str:
    if task_complexity == "simple":
        return "gpt-3.5-turbo"  # 60x cheaper than GPT-4
    elif task_complexity == "medium":
        return "gpt-4"
    else:
        return "gpt-4-turbo-preview"  # Best for complex tasks

# 2. Token limit management
async def cost_aware_query(prompt: str) -> str:
    # Estimate cost before request
    estimated_input_tokens = len(prompt.split()) * 1.3  # Rough estimate
    max_output_tokens = min(4000, 8000 - estimated_input_tokens)
    
    if estimated_input_tokens > 6000:  # Switch to Turbo for long prompts
        model = "gpt-4-turbo-preview"
    else:
        model = "gpt-4"
    
    return await self.llm.query(
        prompt=prompt,
        provider="openai",
        model=model,
        max_tokens=max_output_tokens
    )
```

### Usage Monitoring

```bash
# Check OpenAI usage in dashboard
# Visit: https://platform.openai.com/usage

# Or via API
curl https://api.openai.com/v1/usage \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -H "Content-Type: application/json"
```

## Error Handling

### Common Error Codes

```python
from openai import OpenAIError, RateLimitError, AuthenticationError

async def robust_openai_query(prompt: str):
    try:
        result = await self.llm.query(prompt, provider="openai")
        return result
    except AuthenticationError:
        # Invalid API key
        logger.error("OpenAI authentication failed - check API key")
        raise
    except RateLimitError as e:
        # Rate limit exceeded
        logger.warning(f"OpenAI rate limit hit: {e}")
        # Wait and retry or use fallback provider
        await asyncio.sleep(60)
        return await self.llm.query(prompt, provider="google")  # Fallback
    except OpenAIError as e:
        # Other OpenAI errors
        logger.error(f"OpenAI error: {e}")
        return await self.llm.query(prompt, provider="anthropic")  # Fallback
```

### Rate Limiting

OpenAI has rate limits based on your usage tier:

| Tier | GPT-4 (RPM) | GPT-3.5 (RPM) | Monthly Spend |
|------|-------------|---------------|---------------|
| Free | 3 | 3 | $0 |
| Tier 1 | 10,000 | 10,000 | $5+ |
| Tier 2 | 50,000 | 50,000 | $50+ |
| Tier 3 | 100,000 | 100,000 | $1,000+ |

```python
# Handle rate limits gracefully
import time

async def rate_limited_query(prompt: str, max_retries: int = 3):
    for attempt in range(max_retries):
        try:
            return await self.llm.query(prompt, provider="openai")
        except RateLimitError as e:
            if attempt == max_retries - 1:
                raise
            
            # Exponential backoff
            wait_time = 2 ** attempt
            logger.info(f"Rate limited, waiting {wait_time}s...")
            await asyncio.sleep(wait_time)
```

## Best Practices

### 1. Prompt Engineering

```python
# Good: Clear, specific instructions
prompt = """
Analyze the following text and extract key information:

Text: "John Smith is a 30-year-old software engineer living in San Francisco."

Extract:
- Name
- Age  
- Profession
- Location

Format as JSON.
"""

# Better: Include examples
prompt = """
Extract person details from text. Format as JSON.

Example:
Input: "Sarah Jones, 25, teacher from Boston"
Output: {"name": "Sarah Jones", "age": 25, "profession": "teacher", "location": "Boston"}

Input: "John Smith is a 30-year-old software engineer living in San Francisco."
Output:
"""
```

### 2. Model Selection

```python
# Choose model based on task requirements
task_to_model = {
    "simple_qa": "gpt-3.5-turbo",
    "code_generation": "gpt-4",
    "complex_reasoning": "gpt-4-turbo-preview",
    "data_extraction": "gpt-3.5-turbo",
    "creative_writing": "gpt-4"
}
```

### 3. Security

```bash
# Never log API keys
OPENAI_API_KEY=sk-proj-...  # Keep this secret!

# Use environment variables, not hardcoded keys
# ❌ Bad
api_key = "sk-proj-..."

# ✅ Good
api_key = os.getenv("OPENAI_API_KEY")
```

### 4. Monitoring

```python
# Track usage in agent metadata
return AgentExecutionResult(
    success=True,
    result=result,
    metadata={
        "provider": "openai",
        "model": model_used,
        "input_tokens": prompt_tokens,
        "output_tokens": completion_tokens,
        "total_tokens": total_tokens,
        "estimated_cost": total_tokens * price_per_token
    }
)
```

## Troubleshooting

### Authentication Issues

```bash
# Test API key
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"

# Check billing status
curl https://api.openai.com/v1/usage \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

### Common Problems

**"Invalid API Key"**
- Check key format (starts with `sk-proj-` or `sk-`)
- Verify key hasn't been revoked
- Ensure billing is set up

**"Rate Limit Exceeded"**
- Check your usage tier limits
- Implement exponential backoff
- Consider upgrading tier or using fallback providers

**"Context Length Exceeded"**
- Switch to GPT-4 Turbo (128K context)
- Truncate long prompts
- Split large documents into chunks

**High Costs**
- Monitor token usage
- Use GPT-3.5 for simple tasks
- Implement prompt optimization
- Set maximum token limits

---

**Next Steps**: Explore [Anthropic Integration](anthropic.md) or return to [Multi-Provider Setup](ai-providers.md) 