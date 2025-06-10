# Anthropic Integration

> **Anthropic (Claude) Setup** - Configure Claude models for advanced reasoning and analysis

## Overview

Anthropic's Claude models excel at complex reasoning, safety, and handling large documents. Known for Constitutional AI training, large context windows, and thoughtful responses.

**Key Features:**
- **Large Context**: Up to 200K tokens (Claude 3 Opus)
- **Superior Reasoning**: Excellent at complex analysis
- **Safety-First**: Built with Constitutional AI principles
- **Document Processing**: Handles long documents effectively
- **Nuanced Understanding**: Great at context and subtlety

## Quick Setup

### 1. Create Anthropic Account

1. Go to [Anthropic Console](https://console.anthropic.com/)
2. Sign up with your email or Google account
3. Complete account verification
4. Add billing information (required for API access)

### 2. Generate API Key

1. Navigate to **API Keys** in the console
2. Click **"Create Key"**
3. Give it a descriptive name (e.g., "AI Agent Platform")
4. Select appropriate permissions
5. Copy the generated key

```bash
# Your Anthropic API key
ANTHROPIC_API_KEY=sk-ant-api03-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

⚠️ **Security Note**: Keep this key secure. It provides access to your Anthropic billing account.

### 3. Configure Environment

Add your Anthropic configuration to `backend/.env`:

```bash
# Anthropic Configuration
ANTHROPIC_API_KEY=sk-ant-api03-your-key-here
ANTHROPIC_MODEL=claude-3-sonnet-20240229  # Default model
ANTHROPIC_MAX_TOKENS=4000                 # Response length limit
ANTHROPIC_TEMPERATURE=0.7                 # Creativity level (0-1)
```

### 4. Test Connection

```bash
# Start backend
cd backend && python main.py

# Test Anthropic connection
curl -X POST http://localhost:8000/ai/test \
  -H "Content-Type: application/json" \
  -d '{"provider": "anthropic", "prompt": "Hello, Claude!"}'
```

Expected response:
```json
{
  "success": true,
  "result": "Hello! I'm Claude, an AI assistant created by Anthropic. How can I help you today?",
  "provider": "anthropic",
  "model": "claude-3-sonnet-20240229"
}
```

## Available Models

### Claude 3 Opus (Most Powerful)
- **Model**: `claude-3-opus-20240229`
- **Context**: 200K tokens
- **Best for**: Complex reasoning, research, creative tasks
- **Cost**: $15/1M input, $75/1M output tokens
- **Strengths**: Highest intelligence, best reasoning

### Claude 3 Sonnet (Balanced)
- **Model**: `claude-3-sonnet-20240229`
- **Context**: 200K tokens
- **Best for**: General tasks, analysis, coding
- **Cost**: $3/1M input, $15/1M output tokens
- **Strengths**: Great balance of capability and speed

### Claude 3 Haiku (Fast)
- **Model**: `claude-3-haiku-20240307`
- **Context**: 200K tokens
- **Best for**: Quick responses, simple tasks
- **Cost**: $0.25/1M input, $1.25/1M output tokens
- **Strengths**: Fastest responses, most economical

### Model Configuration

```bash
# Maximum capability (expensive)
ANTHROPIC_MODEL=claude-3-opus-20240229

# Balanced capability and cost (recommended)
ANTHROPIC_MODEL=claude-3-sonnet-20240229

# Fast and economical
ANTHROPIC_MODEL=claude-3-haiku-20240307
```

## Using Anthropic in Agents

### Basic Usage

```python
from services.llm_service import get_unified_llm_service

class MyClaudeAgent(SelfContainedAgent):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.llm = get_unified_llm_service()
    
    async def _execute_job_logic(self, job_data):
        result = await self.llm.query(
            prompt=job_data.prompt,
            provider="anthropic",
            model="claude-3-sonnet-20240229"
        )
        
        return AgentExecutionResult(
            success=True,
            result=result,
            metadata={"provider": "anthropic"}
        )
```

### Advanced Configuration

```python
@job_model
class AnthropicJobData(BaseModel):
    prompt: str = Field(..., description="Text prompt")
    model: str = Field(default="claude-3-sonnet-20240229", description="Claude model")
    temperature: float = Field(default=0.7, ge=0, le=1, description="Creativity level")
    max_tokens: int = Field(default=4000, description="Maximum response length")
    system_prompt: Optional[str] = Field(None, description="System instructions")

class AdvancedClaudeAgent(SelfContainedAgent):
    async def _execute_job_logic(self, job_data: AnthropicJobData):
        result = await self.llm.query(
            prompt=job_data.prompt,
            provider="anthropic",
            model=job_data.model,
            temperature=job_data.temperature,
            max_tokens=job_data.max_tokens,
            system_message=job_data.system_prompt
        )
        
        return AgentExecutionResult(
            success=True,
            result=result,
            metadata={
                "provider": "anthropic",
                "model": job_data.model,
                "temperature": job_data.temperature
            }
        )
```

## Claude-Specific Features

### 1. Large Document Processing

Claude excels at processing long documents:

```python
async def analyze_document(self, document: str):
    # Claude can handle up to 200K tokens (~150K words)
    prompt = f"""
    Please analyze the following document and provide:
    1. Key themes and topics
    2. Main arguments or findings
    3. Critical insights
    4. Summary of conclusions
    
    Document:
    {document}
    """
    
    result = await self.llm.query(
        prompt=prompt,
        provider="anthropic",
        model="claude-3-opus-20240229",  # Use Opus for complex analysis
        max_tokens=8000
    )
    
    return result
```

### 2. Constitutional AI Reasoning

Use Claude's reasoning capabilities:

```python
async def ethical_analysis(self, scenario: str):
    system_prompt = """
    You are an AI assistant trained in ethical reasoning. When analyzing scenarios:
    1. Consider multiple ethical frameworks
    2. Identify potential harms and benefits
    3. Suggest balanced approaches
    4. Acknowledge uncertainty where it exists
    """
    
    result = await self.llm.query(
        prompt=f"Analyze the ethical implications of: {scenario}",
        provider="anthropic",
        system_message=system_prompt,
        temperature=0.3  # Lower temperature for more consistent reasoning
    )
    
    return result
```

### 3. Structured Analysis

Claude is excellent at structured thinking:

```python
async def structured_analysis(self, topic: str):
    prompt = f"""
    Provide a structured analysis of: {topic}
    
    Please organize your response as follows:
    
    ## Overview
    [Brief summary]
    
    ## Key Components
    [Main elements or aspects]
    
    ## Analysis
    [Detailed examination]
    
    ## Implications
    [Consequences or significance]
    
    ## Recommendations
    [Actionable suggestions]
    """
    
    result = await self.llm.query(
        prompt=prompt,
        provider="anthropic",
        model="claude-3-sonnet-20240229"
    )
    
    return result
```

### 4. Code Review and Analysis

Claude provides thoughtful code review:

```python
async def code_review(self, code: str, language: str):
    prompt = f"""
    Please review this {language} code and provide feedback on:
    
    1. Code quality and style
    2. Potential bugs or issues
    3. Performance considerations
    4. Security concerns
    5. Suggestions for improvement
    
    Code:
    ```{language}
    {code}
    ```
    """
    
    result = await self.llm.query(
        prompt=prompt,
        provider="anthropic",
        model="claude-3-sonnet-20240229",
        temperature=0.2  # Lower temperature for consistent technical feedback
    )
    
    return result
```

## Cost Management

### Pricing (as of Dec 2024)

| Model | Input (1M tokens) | Output (1M tokens) | Context Window |
|-------|-------------------|-------------------|----------------|
| Claude 3 Opus | $15 | $75 | 200K |
| Claude 3 Sonnet | $3 | $15 | 200K |
| Claude 3 Haiku | $0.25 | $1.25 | 200K |

### Cost Optimization Strategies

```python
# Model selection based on task complexity
def select_claude_model(task_type: str, document_length: int) -> str:
    if task_type == "simple" or document_length < 1000:
        return "claude-3-haiku-20240307"  # Most economical
    elif task_type == "analysis" or document_length < 10000:
        return "claude-3-sonnet-20240229"  # Balanced
    else:
        return "claude-3-opus-20240229"  # Maximum capability

# Token-aware processing
async def cost_efficient_query(prompt: str, complexity: str) -> str:
    # Estimate tokens (rough approximation)
    estimated_tokens = len(prompt.split()) * 1.3
    
    if estimated_tokens > 100000:  # Very long document
        model = "claude-3-opus-20240229"  # Best for complex long docs
        max_tokens = 8000
    elif estimated_tokens > 10000:  # Medium document
        model = "claude-3-sonnet-20240229"
        max_tokens = 4000
    else:  # Short document
        model = "claude-3-haiku-20240307"
        max_tokens = 2000
    
    return await self.llm.query(
        prompt=prompt,
        provider="anthropic",
        model=model,
        max_tokens=max_tokens
    )
```

### Usage Monitoring

```python
# Track detailed usage
return AgentExecutionResult(
    success=True,
    result=result,
    metadata={
        "provider": "anthropic",
        "model": model_used,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": total_tokens,
        "estimated_cost": calculate_anthropic_cost(input_tokens, output_tokens, model_used)
    }
)

def calculate_anthropic_cost(input_tokens: int, output_tokens: int, model: str) -> float:
    pricing = {
        "claude-3-opus-20240229": {"input": 15/1000000, "output": 75/1000000},
        "claude-3-sonnet-20240229": {"input": 3/1000000, "output": 15/1000000},
        "claude-3-haiku-20240307": {"input": 0.25/1000000, "output": 1.25/1000000}
    }
    
    if model not in pricing:
        return 0.0
    
    return (input_tokens * pricing[model]["input"] + 
            output_tokens * pricing[model]["output"])
```

## Error Handling

### Common Errors

```python
import anthropic

async def robust_anthropic_query(prompt: str):
    try:
        result = await self.llm.query(prompt, provider="anthropic")
        return result
    except anthropic.AuthenticationError:
        logger.error("Anthropic authentication failed - check API key")
        raise
    except anthropic.RateLimitError as e:
        logger.warning(f"Anthropic rate limit hit: {e}")
        # Implement backoff or fallback
        await asyncio.sleep(60)
        return await self.llm.query(prompt, provider="google")  # Fallback
    except anthropic.BadRequestError as e:
        logger.error(f"Bad request to Anthropic: {e}")
        # Handle invalid requests
        raise
    except anthropic.APIError as e:
        logger.error(f"Anthropic API error: {e}")
        return await self.llm.query(prompt, provider="openai")  # Fallback
```

### Rate Limiting

Anthropic has generous rate limits:
- **Claude 3 Opus**: 1,000 requests/minute
- **Claude 3 Sonnet**: 1,000 requests/minute
- **Claude 3 Haiku**: 1,000 requests/minute

```python
# Rate limit handling with exponential backoff
async def rate_limited_anthropic_query(prompt: str, max_retries: int = 3):
    for attempt in range(max_retries):
        try:
            return await self.llm.query(prompt, provider="anthropic")
        except anthropic.RateLimitError:
            if attempt == max_retries - 1:
                raise
            
            wait_time = (2 ** attempt) * 30  # 30s, 60s, 120s
            logger.info(f"Rate limited, waiting {wait_time}s...")
            await asyncio.sleep(wait_time)
```

## Best Practices

### 1. Leverage Large Context Windows

```python
# Take advantage of 200K token context
async def comprehensive_analysis(self, documents: List[str]):
    # Combine multiple documents for analysis
    combined_docs = "\n\n---\n\n".join(documents)
    
    prompt = f"""
    Please analyze these related documents together and identify:
    1. Common themes across all documents
    2. Contradictions or disagreements
    3. Gaps in information
    4. Synthesis of key insights
    
    Documents:
    {combined_docs}
    """
    
    # Claude can handle all documents at once
    return await self.llm.query(
        prompt=prompt,
        provider="anthropic",
        model="claude-3-opus-20240229"
    )
```

### 2. Use System Messages Effectively

```python
# Provide clear behavioral instructions
system_messages = {
    "analyst": "You are a thorough analyst. Always provide evidence for your conclusions and acknowledge limitations.",
    "teacher": "You are a patient teacher. Explain concepts clearly with examples and check for understanding.",
    "critic": "You are a constructive critic. Identify both strengths and areas for improvement.",
    "summarizer": "You are a precise summarizer. Capture key points without losing important nuance."
}

async def role_based_query(self, prompt: str, role: str):
    return await self.llm.query(
        prompt=prompt,
        provider="anthropic",
        system_message=system_messages.get(role, "")
    )
```

### 3. Temperature Settings for Different Tasks

```python
temperature_settings = {
    "analysis": 0.1,      # Very consistent for analysis
    "explanation": 0.3,   # Slightly creative for clarity
    "creative": 0.7,      # More creative for writing
    "brainstorming": 0.9  # Most creative for ideation
}

async def task_optimized_query(self, prompt: str, task_type: str):
    temperature = temperature_settings.get(task_type, 0.5)
    
    return await self.llm.query(
        prompt=prompt,
        provider="anthropic",
        temperature=temperature
    )
```

### 4. Document Chunking for Very Large Documents

```python
async def process_very_large_document(self, document: str):
    # If document exceeds even Claude's context window
    max_chunk_size = 150000  # Leave room for prompt and response
    
    if len(document) <= max_chunk_size:
        # Process entire document
        return await self.analyze_document(document)
    
    # Split into chunks with overlap
    chunks = self.split_with_overlap(document, max_chunk_size, overlap=5000)
    chunk_analyses = []
    
    for i, chunk in enumerate(chunks):
        analysis = await self.analyze_document(chunk)
        chunk_analyses.append(f"Chunk {i+1}: {analysis}")
    
    # Synthesize all chunk analyses
    synthesis_prompt = f"""
    Synthesize these analyses of document chunks into a coherent overall analysis:
    
    {chr(10).join(chunk_analyses)}
    """
    
    return await self.llm.query(
        prompt=synthesis_prompt,
        provider="anthropic",
        model="claude-3-opus-20240229"
    )
```

## Troubleshooting

### Authentication Issues

```bash
# Test API key
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "Content-Type: application/json" \
  -H "anthropic-version: 2023-06-01" \
  -d '{"model": "claude-3-haiku-20240307", "max_tokens": 10, "messages": [{"role": "user", "content": "Hi"}]}'
```

### Common Problems

**"Invalid API Key"**
- Check key format (starts with `sk-ant-api03-`)
- Verify key hasn't been revoked in console
- Ensure billing is properly set up

**"Model Not Found"**
- Use exact model names from Anthropic docs
- Check if you have access to the specific model
- Some models may have access restrictions

**"Context Length Exceeded"**
- Even with 200K context, very large documents might exceed limits
- Implement document chunking strategy
- Consider summarizing before analysis

**"Rate Limit Exceeded"**
- Implement exponential backoff
- Consider distributing load across time
- Use multiple API keys if allowed

**High Costs**
- Monitor token usage carefully
- Use Haiku for simple tasks
- Implement prompt optimization
- Set strict max_tokens limits

---

**Next Steps**: Explore [Additional Providers](additional-providers.md) or return to [Multi-Provider Setup](ai-providers.md) 