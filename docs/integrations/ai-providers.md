# Multi-Provider AI Setup

> **Unified AI Integration** - Configure and use multiple AI providers seamlessly

## Overview

AI Agent Platform supports 6 major AI providers through a unified interface, allowing you to choose the best AI model for your specific use case or switch between providers as needed.

## Supported Providers

### 🚀 Google AI (Gemini)
- **Models**: Gemini Pro, Gemini Flash
- **Strengths**: Fast, multimodal, general-purpose
- **Best for**: Quick responses, content generation, analysis
- **Free tier**: Yes (generous limits)
- **Setup**: [Google AI Integration](google-ai.md)

### 🧠 OpenAI (GPT)
- **Models**: GPT-4, GPT-4 Turbo, GPT-3.5 Turbo
- **Strengths**: Popular, reliable, strong code generation
- **Best for**: Code generation, complex reasoning, creative writing
- **Free tier**: Limited ($5 free credit)
- **Setup**: [OpenAI Integration](openai.md)

### ⚡ Grok (xAI)
- **Models**: Grok-1, Grok-2
- **Strengths**: Real-time data access, web search capabilities
- **Best for**: Current events, real-time information, research
- **Free tier**: Limited (subscription model)
- **Setup**: [Additional Providers](additional-providers.md#grok-xai)

### 🎯 Anthropic (Claude)
- **Models**: Claude 3 Opus, Claude 3 Sonnet, Claude 3 Haiku
- **Strengths**: Superior reasoning, large context windows, safety
- **Best for**: Complex analysis, document processing, reasoning tasks
- **Free tier**: Limited ($5 free credit)
- **Setup**: [Anthropic Integration](anthropic.md)

### 💎 DeepSeek
- **Models**: DeepSeek Chat, DeepSeek Code
- **Strengths**: Competitive performance, cost-effective
- **Best for**: Cost-sensitive applications, code generation
- **Free tier**: Yes (limited)
- **Setup**: [Additional Providers](additional-providers.md#deepseek)

### 🦙 Meta Llama
- **Models**: Llama 2, Code Llama, Llama 2-Chat
- **Strengths**: Open-source excellence, specialized models
- **Best for**: Code generation, chat applications, custom fine-tuning
- **Free tier**: Via Together AI and other providers
- **Setup**: [Additional Providers](additional-providers.md#meta-llama)

## Quick Setup Guide

### 1. Choose Your Providers

You can configure one or multiple providers. We recommend starting with:
- **Google AI** (free, reliable)
- **OpenAI** (industry standard)

### 2. Get API Keys

Follow the setup guides for each provider:

```bash
# Google AI Studio (free)
GOOGLE_API_KEY=your-google-ai-key

# OpenAI Platform
OPENAI_API_KEY=your-openai-key

# Anthropic Console
ANTHROPIC_API_KEY=your-anthropic-key

# Additional providers (optional)
GROK_API_KEY=your-grok-key
DEEPSEEK_API_KEY=your-deepseek-key
LLAMA_API_KEY=your-llama-provider-key
```

### 3. Configure Backend

Add your keys to `backend/.env`:

```bash
# Default AI Provider Configuration
DEFAULT_LLM_PROVIDER=google  # Options: google|openai|anthropic|grok|deepseek|llama

# Provider API Keys
GOOGLE_API_KEY=your-google-ai-key
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key
GROK_API_KEY=your-grok-key
DEEPSEEK_API_KEY=your-deepseek-key
LLAMA_API_KEY=your-llama-key
```

**Default Provider Selection:**
- **Google AI** (`google`) - Free tier, fast, good for development
- **OpenAI** (`openai`) - Industry standard, reliable, moderate cost
- **Anthropic** (`anthropic`) - Advanced reasoning, higher cost
- **Grok** (`grok`) - Real-time data access, subscription-based
- **DeepSeek** (`deepseek`) - Most cost-effective, good performance
- **Meta Llama** (`llama`) - Open-source flexibility, various providers

### 4. Test Your Setup

```bash
# Start backend
cd backend && python main.py

# Test provider connections
curl http://localhost:8000/ai/providers/test
```

## Using Multiple Providers in Agents

### Unified LLM Service

The platform provides a unified interface for all AI providers:

```python
from services.llm_service import get_unified_llm_service

class MyAgent(SelfContainedAgent):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.llm = get_unified_llm_service()
    
    async def _execute_job_logic(self, job_data):
        # Use default provider
        result = await self.llm.query("Your prompt here")
        
        # Use specific provider
        result = await self.llm.query("Your prompt", provider="openai")
        
        # Try multiple providers (fallback)
        result = await self.llm.query_with_fallback(
            prompt="Your prompt",
            providers=["google", "openai", "anthropic"]
        )
```

### Provider Selection in Job Data

Allow users to choose providers in your agent:

```python
@job_model
class MyJobData(BaseModel):
    prompt: str = Field(..., description="Text to process")
    ai_provider: str = Field(
        default="google", 
        description="AI provider (google|openai|anthropic|grok|deepseek|llama)"
    )
    
    @field_validator('ai_provider')
    @classmethod
    def validate_provider(cls, v):
        allowed = ["google", "openai", "anthropic", "grok", "deepseek", "llama"]
        if v not in allowed:
            raise ValueError(f"Provider must be one of: {allowed}")
        return v

class MyAgent(SelfContainedAgent):
    async def _execute_job_logic(self, job_data: MyJobData):
        result = await self.llm.query(
            prompt=job_data.prompt,
            provider=job_data.ai_provider
        )
        
        return AgentExecutionResult(
            success=True,
            result=result,
            metadata={"ai_provider": job_data.ai_provider}
        )
```

## Provider-Specific Features

### Google AI (Gemini)
- **Multimodal**: Supports text, images, video
- **Fast**: Optimized for speed
- **Free tier**: Generous limits

```python
# Multimodal example (when supported)
result = await self.llm.query(
    prompt="Describe this image",
    provider="google",
    images=[image_data]
)
```

### OpenAI (GPT)
- **Function calling**: Advanced tool integration
- **JSON mode**: Structured output
- **Code interpreter**: Built-in code execution

```python
# Structured output example
result = await self.llm.query(
    prompt="Extract data as JSON",
    provider="openai",
    response_format="json"
)
```

### Anthropic (Claude)
- **Large context**: Up to 100K tokens
- **Safety-first**: Built-in safety measures
- **Constitutional AI**: Advanced reasoning

```python
# Large context example
result = await self.llm.query(
    prompt=f"Analyze this document: {large_document}",
    provider="anthropic",
    max_tokens=4000
)
```

## Cost Optimization

### Provider Cost Comparison

| Provider | Input (1K tokens) | Output (1K tokens) | Free Tier |
|----------|-------------------|-------------------|------------|
| Google AI | $0.000125 | $0.000375 | 15 RPM free |
| OpenAI GPT-4 | $0.03 | $0.06 | $5 credit |
| Anthropic Claude | $0.015 | $0.075 | $5 credit |
| Grok | $5/month | $5/month | Limited |
| DeepSeek | $0.002 | $0.002 | Free tier |
| Llama (via Together) | $0.0006 | $0.0006 | $5 credit |

### Cost-Effective Strategies

```python
# Use cheaper models for simple tasks
if task_complexity == "simple":
    provider = "google"  # Fast and cheap
elif task_complexity == "complex":
    provider = "anthropic"  # Better reasoning
else:
    provider = "openai"  # Balanced

# Implement fallback for cost optimization
result = await self.llm.query_with_fallback(
    prompt=prompt,
    providers=["deepseek", "google", "openai"]  # Cheapest first
)
```

## Monitoring and Analytics

### Provider Usage Tracking

```python
# Track provider usage in agent metadata
return AgentExecutionResult(
    success=True,
    result=result,
    metadata={
        "ai_provider": provider,
        "model": model_used,
        "input_tokens": input_token_count,
        "output_tokens": output_token_count,
        "cost_estimate": estimated_cost
    }
)
```

### Health Monitoring

```bash
# Check provider status
curl http://localhost:8000/ai/providers/status

# Example response
{
  "google": {"status": "healthy", "latency_ms": 245},
  "openai": {"status": "healthy", "latency_ms": 892},
  "anthropic": {"status": "rate_limited", "retry_after": 60}
}
```

## Best Practices

### 1. Provider Selection Strategy
- **Google AI**: Default for general use (fast, free)
- **OpenAI**: Complex reasoning and code generation
- **Anthropic**: Document analysis and safety-critical tasks
- **DeepSeek**: Cost-sensitive applications
- **Grok**: Real-time data and current events
- **Llama**: Open-source and customization needs

### 2. Fallback Configuration
```python
# Configure provider fallbacks
PROVIDER_FALLBACKS = {
    "primary": ["google", "openai"],
    "cost_optimized": ["deepseek", "google", "openai"],
    "quality_focused": ["anthropic", "openai", "google"]
}
```

### 3. Error Handling
```python
try:
    result = await self.llm.query(prompt, provider=preferred_provider)
except ProviderError as e:
    # Log error and try fallback
    logger.warning(f"Provider {preferred_provider} failed: {e}")
    result = await self.llm.query(prompt, provider=fallback_provider)
```

### 4. Configuration Management
```bash
# Environment-specific defaults
# Development: Use free tiers
AI_PROVIDER=google
AI_FALLBACK_PROVIDERS=google,deepseek

# Production: Use reliable providers
AI_PROVIDER=openai
AI_FALLBACK_PROVIDERS=openai,anthropic,google
```

## Troubleshooting

### Common Issues

**Authentication Errors**
```bash
# Check API keys are set
env | grep API_KEY

# Test individual providers
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
  https://api.openai.com/v1/models
```

**Rate Limiting**
```python
# Configure retry logic
result = await self.llm.query(
    prompt=prompt,
    provider=provider,
    retry_on_rate_limit=True,
    max_retries=3
)
```

**Provider Downtime**
```python
# Use health checks before requests
if await self.llm.is_provider_healthy(provider):
    result = await self.llm.query(prompt, provider=provider)
else:
    result = await self.llm.query(prompt, provider=fallback_provider)
```

---

**Next Steps**: Configure individual providers using the specific integration guides linked above! 