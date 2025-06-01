# Google AI Services Integration

> **AI/ML service configuration** - Complete setup for Google AI Studio and Gemini models

## Overview

The AI Agent Template integrates with Google AI services to provide powerful AI capabilities:

- **Google AI Studio** - Easy-to-use AI development platform
- **Gemini Models** - Advanced language and multimodal AI models  
- **Simple API Integration** - Streamlined setup with API keys
- **Cost-Effective** - Pay-per-use pricing with generous free tier

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
GOOGLE_AI_MODEL=gemini-1.5-flash  # Default model
```

### 4. Test Connection

Test your setup with the built-in health check:

```bash
# Start your backend
cd backend && python main.py

# Test the connection
curl http://localhost:8000/adk/connection-test
```

Expected response:
```json
{
  "status": "success",
  "message": "Google AI connection successful",
  "model": "gemini-1.5-flash",
  "api_available": true
}
```

## Available Models

### Gemini 1.5 Flash (Recommended)
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
GOOGLE_AI_MODEL=gemini-1.5-flash

# Higher quality for complex tasks
GOOGLE_AI_MODEL=gemini-1.5-pro
```

## Backend Integration

### Google AI Client Setup

The template includes a pre-configured Google AI client:

```python
# backend/google_ai_client.py (simplified example)
import google.generativeai as genai
import os

def get_google_ai_client():
    """Initialize Google AI client"""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not configured")
    
    genai.configure(api_key=api_key)
    return genai
```

### Using Google AI in Agents

Example agent integration:

```python
# agents/my_ai_agent.py
from typing import Dict, Any
import google.generativeai as genai
from agent_framework import SelfContainedAgent, endpoint, job_model

@job_model
class AIJobData(BaseModel):
    prompt: str = Field(..., description="Text prompt for AI")
    max_tokens: int = Field(default=1000, description="Maximum response length")

class MyAIAgent(SelfContainedAgent):
    def __init__(self, **kwargs):
        super().__init__(description="AI-powered text processing", **kwargs)
        self.model = genai.GenerativeModel(
            model_name=os.getenv("GOOGLE_AI_MODEL", "gemini-1.5-flash")
        )
    
    @endpoint("/ai-agent/generate", methods=["POST"], auth_required=True)
    async def generate_text(self, request_data: dict, user: dict):
        job_data = validate_job_data(request_data, AIJobData)
        return await execute_agent_job(self, job_data, user["id"])
    
    async def _execute_job_logic(self, job_data: AIJobData):
        try:
            # Generate content using Google AI
            response = self.model.generate_content(
                job_data.prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=job_data.max_tokens,
                    temperature=0.7
                )
            )
            
            return AgentExecutionResult(
                success=True,
                result=response.text,
                metadata={
                    "model": self.model.model_name,
                    "prompt_length": len(job_data.prompt),
                    "response_length": len(response.text)
                }
            )
        except Exception as e:
            return AgentExecutionResult(
                success=False,
                error_message=f"AI generation failed: {str(e)}"
            )
```

## Built-in AI Agents

The template includes several pre-built agents that use Google AI:

### Text Processing Agent
- **Endpoint**: `/text-processing/analyze`
- **Features**: Sentiment analysis, keyword extraction, text classification
- **Use cases**: Content moderation, data analysis, text insights

### Summarization Agent  
- **Endpoint**: `/summarization/summarize`
- **Features**: Text, audio, and video summarization
- **Use cases**: Content summarization, meeting notes, research

### Web Scraping Agent
- **Endpoint**: `/web-scraping/extract`
- **Features**: AI-powered content extraction and analysis
- **Use cases**: Data extraction, content analysis, research

## Advanced Configuration

### Custom Generation Parameters

Fine-tune AI responses for your specific use case:

```python
generation_config = genai.types.GenerationConfig(
    max_output_tokens=2000,    # Response length
    temperature=0.7,           # Creativity (0.0-1.0)
    top_p=0.8,                # Nucleus sampling
    top_k=40,                 # Top-k sampling
    stop_sequences=["END"]     # Stop generation at specific text
)

response = model.generate_content(
    prompt,
    generation_config=generation_config
)
```

### Safety Settings

Configure content filtering and safety:

```python
safety_settings = [
    {
        "category": "HARM_CATEGORY_HARASSMENT",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
    },
    {
        "category": "HARM_CATEGORY_HATE_SPEECH", 
        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
    },
    {
        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
    },
    {
        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
    }
]

response = model.generate_content(
    prompt,
    safety_settings=safety_settings
)
```

### Error Handling

Robust error handling for AI operations:

```python
try:
    response = model.generate_content(prompt)
    
    # Check if response was blocked
    if response.prompt_feedback.block_reason:
        return AgentExecutionResult(
            success=False,
            error_message=f"Content blocked: {response.prompt_feedback.block_reason}"
        )
    
    # Check if content was filtered
    if not response.text:
        return AgentExecutionResult(
            success=False,
            error_message="No content generated (possibly filtered)"
        )
    
    return AgentExecutionResult(success=True, result=response.text)
    
except genai.types.BlockedPromptException:
    return AgentExecutionResult(
        success=False,
        error_message="Prompt blocked by safety filters"
    )
except genai.types.StopCandidateException:
    return AgentExecutionResult(
        success=False, 
        error_message="Generation stopped by safety filters"
    )
except Exception as e:
    return AgentExecutionResult(
        success=False,
        error_message=f"AI generation error: {str(e)}"
    )
```

## Cost Management

### Understanding Pricing

Google AI Studio offers:
- **Free Tier**: Generous limits for development and testing
- **Pay-per-use**: Only pay for what you use in production
- **Token-based pricing**: Charged per input/output tokens

### Monitoring Usage

Track AI usage in your applications:

```python
class AIUsageTracker:
    def __init__(self):
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.request_count = 0
    
    def track_request(self, prompt: str, response: str):
        self.request_count += 1
        self.total_input_tokens += len(prompt.split())  # Rough estimate
        self.total_output_tokens += len(response.split())
        
        logger.info(f"AI Usage - Requests: {self.request_count}, "
                   f"Input tokens: {self.total_input_tokens}, "
                   f"Output tokens: {self.total_output_tokens}")
```

### Cost Optimization Tips

1. **Choose the right model**: Use `gemini-1.5-flash` for most tasks
2. **Optimize prompts**: Shorter, clearer prompts = lower costs
3. **Cache responses**: Store common responses to avoid re-generation
4. **Set token limits**: Use `max_output_tokens` to control costs
5. **Monitor usage**: Track usage patterns and optimize

## Troubleshooting

### Common Issues

**API Key Problems:**
```bash
# Check if API key is set
echo $GOOGLE_API_KEY

# Test API key validity
curl -H "Authorization: Bearer $GOOGLE_API_KEY" \
     "https://generativelanguage.googleapis.com/v1/models"
```

**Model Access Issues:**
```python
# List available models
for model in genai.list_models():
    print(f"Model: {model.name}")
    print(f"Supported methods: {model.supported_generation_methods}")
```

**Content Safety Blocks:**
```python
# Check why content was blocked
if response.prompt_feedback.block_reason:
    print(f"Blocked reason: {response.prompt_feedback.block_reason}")
    print(f"Safety ratings: {response.prompt_feedback.safety_ratings}")
```

### Performance Optimization

1. **Async requests**: Use async/await for concurrent requests
2. **Connection pooling**: Reuse HTTP connections
3. **Retry logic**: Handle temporary failures gracefully
4. **Caching**: Cache responses for repeated prompts

### Security Best Practices

1. **API Key Protection**: Never commit API keys to version control
2. **Environment Variables**: Use secure environment variable storage
3. **Rate Limiting**: Implement rate limiting to prevent abuse
4. **Input Validation**: Validate all prompts before sending to AI
5. **Output Filtering**: Filter AI responses before displaying to users

---

**Next Steps:**
- **[Authentication Setup](authentication.md)** - User management integration
- **[Agent Development Guide](../development/agent-development.md)** - Build AI-powered agents
- **[API Reference](../development/api-reference.md)** - AI agent endpoints 