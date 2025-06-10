# DeepSeek Integration

> **DeepSeek Setup** - Configure DeepSeek for cost-effective AI processing

## Overview

DeepSeek provides competitive AI capabilities at cost-effective pricing, making it ideal for high-volume applications and budget-conscious development.

**Key Features:**
- **Cost-Effective**: Very competitive pricing
- **Code Generation**: Strong programming capabilities
- **Multilingual**: Supports multiple languages
- **High Throughput**: Good for bulk processing
- **Open-Source Friendly**: Supports open research and development

## Quick Setup

### 1. Create DeepSeek Account

1. Go to [DeepSeek Platform](https://platform.deepseek.com/)
2. Sign up with email
3. Complete verification
4. Add billing information (free tier available)

### 2. Generate API Key

1. Go to **API Keys** section
2. Create new key
3. Copy the generated key

```bash
# Your DeepSeek API key
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### 3. Configure Environment

Add to `backend/.env`:

```bash
# DeepSeek Configuration
DEEPSEEK_API_KEY=sk-your-key-here
DEEPSEEK_MODEL=deepseek-chat  # Default model
DEEPSEEK_MAX_TOKENS=4000
DEEPSEEK_TEMPERATURE=0.7
```

### 4. Test Connection

```bash
# Start backend
cd backend && python main.py

# Test DeepSeek connection
curl -X POST http://localhost:8000/ai/test \
  -H "Content-Type: application/json" \
  -d '{"provider": "deepseek", "prompt": "Hello, world!"}'
```

## Available Models

### DeepSeek Chat (General Purpose)
- **Model**: `deepseek-chat`
- **Best for**: General conversation and analysis
- **Strengths**: Balanced performance, good reasoning
- **Context**: Standard context window

### DeepSeek Coder (Programming)
- **Model**: `deepseek-coder`
- **Best for**: Code generation, debugging, refactoring
- **Strengths**: Strong programming capabilities
- **Context**: Optimized for code understanding

### DeepSeek Math (Mathematical Reasoning)
- **Model**: `deepseek-math`
- **Best for**: Mathematical problems, calculations
- **Strengths**: Superior mathematical reasoning
- **Context**: Optimized for mathematical notation

### Model Configuration

```bash
# General purpose (default)
DEEPSEEK_MODEL=deepseek-chat

# Code-focused tasks
DEEPSEEK_MODEL=deepseek-coder

# Mathematical calculations
DEEPSEEK_MODEL=deepseek-math
```

## Using DeepSeek in Agents

### Basic Usage

```python
from services.llm_service import get_unified_llm_service

@job_model
class DeepSeekJobData(BaseModel):
    prompt: str = Field(..., description="Text to process")
    model: str = Field(default="deepseek-chat", description="DeepSeek model")
    task_type: str = Field(default="general", description="Type of task")

class DeepSeekAgent(SelfContainedAgent):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.llm = get_unified_llm_service()
    
    async def _execute_job_logic(self, job_data: DeepSeekJobData):
        # Select appropriate model based on task
        model = self._select_model(job_data.task_type)
        
        result = await self.llm.query(
            prompt=job_data.prompt,
            provider="deepseek",
            model=model
        )
        
        return AgentExecutionResult(
            success=True,
            result=result,
            metadata={
                "provider": "deepseek",
                "model": model,
                "task_type": job_data.task_type
            }
        )
    
    def _select_model(self, task_type: str) -> str:
        model_mapping = {
            "code": "deepseek-coder",
            "math": "deepseek-math",
            "general": "deepseek-chat"
        }
        return model_mapping.get(task_type, "deepseek-chat")
```

## Best Use Cases

### Code Generation

```python
async def generate_code(self, requirements: str, language: str):
    prompt = f"""
    Generate {language} code for the following requirements:
    
    {requirements}
    
    Requirements:
    1. Clean, readable code
    2. Proper error handling
    3. Comments explaining key logic
    4. Follow best practices
    """
    
    return await self.llm.query(
        prompt=prompt,
        provider="deepseek",
        model="deepseek-coder"
    )
```

### Mathematical Problem Solving

```python
async def solve_math_problem(self, problem: str):
    prompt = f"""
    Solve this mathematical problem step by step:
    
    {problem}
    
    Please show:
    1. Each step of the solution
    2. Mathematical reasoning
    3. Final answer
    4. Verification if possible
    """
    
    return await self.llm.query(
        prompt=prompt,
        provider="deepseek",
        model="deepseek-math"
    )
```

### Bulk Document Processing

```python
async def bulk_process_documents(self, documents: List[str]):
    results = []
    
    for doc in documents:
        # DeepSeek's low cost makes it ideal for bulk operations
        result = await self.llm.query(
            prompt=f"Summarize this document: {doc}",
            provider="deepseek",
            model="deepseek-chat"
        )
        results.append(result)
    
    return results
```

### Code Review and Analysis

```python
async def code_review(self, code: str, language: str):
    prompt = f"""
    Review this {language} code and provide feedback:
    
    {code}
    
    Please analyze:
    1. Code quality and style
    2. Potential bugs or issues
    3. Performance optimizations
    4. Best practice suggestions
    5. Security considerations
    """
    
    return await self.llm.query(
        prompt=prompt,
        provider="deepseek",
        model="deepseek-coder"
    )
```

## Pricing and Cost Optimization

### Pricing Structure (as of Dec 2024)

| Model | Input (1M tokens) | Output (1M tokens) | Free Tier |
|-------|-------------------|-------------------|------------|
| DeepSeek Chat | $0.14 | $0.28 | 10M tokens/month |
| DeepSeek Coder | $0.14 | $0.28 | 10M tokens/month |
| DeepSeek Math | $0.14 | $0.28 | 10M tokens/month |

### Cost Optimization Strategies

```python
# Use DeepSeek for cost-sensitive applications
def select_cost_effective_provider(task_complexity: str, budget: str) -> str:
    if budget == "low" or task_complexity == "simple":
        return "deepseek"
    elif task_complexity == "complex":
        return "openai"
    else:
        return "google"

# Batch processing for better efficiency
async def batch_process_with_deepseek(self, tasks: List[str]):
    # Process multiple tasks in one request to reduce overhead
    combined_prompt = f"""
    Process these tasks:
    
    {chr(10).join(f"{i+1}. {task}" for i, task in enumerate(tasks))}
    
    Provide numbered responses for each task.
    """
    
    result = await self.llm.query(
        prompt=combined_prompt,
        provider="deepseek",
        model="deepseek-chat"
    )
    
    # Parse the combined result
    return self._parse_batch_results(result, len(tasks))
```

## Error Handling

```python
import deepseek

async def robust_deepseek_query(prompt: str):
    try:
        result = await self.llm.query(prompt, provider="deepseek")
        return result
    except deepseek.AuthenticationError:
        logger.error("DeepSeek authentication failed - check API key")
        raise
    except deepseek.RateLimitError as e:
        logger.warning(f"DeepSeek rate limit hit: {e}")
        # Implement backoff or fallback
        await asyncio.sleep(30)
        return await self.llm.query(prompt, provider="google")  # Fallback
    except deepseek.APIError as e:
        logger.error(f"DeepSeek API error: {e}")
        return await self.llm.query(prompt, provider="openai")  # Fallback
```

## Best Practices

### 1. Model Selection Strategy

```python
def select_deepseek_model(task_description: str) -> str:
    """
    Intelligent model selection based on task content
    """
    task_lower = task_description.lower()
    
    # Code-related keywords
    code_keywords = ["code", "program", "function", "class", "debug", "refactor"]
    if any(keyword in task_lower for keyword in code_keywords):
        return "deepseek-coder"
    
    # Math-related keywords
    math_keywords = ["calculate", "solve", "equation", "formula", "mathematics"]
    if any(keyword in task_lower for keyword in math_keywords):
        return "deepseek-math"
    
    # Default to chat model
    return "deepseek-chat"
```

### 2. Prompt Optimization for Cost

```python
async def cost_optimized_query(self, prompt: str):
    # Compress prompt while maintaining meaning
    optimized_prompt = self._optimize_prompt_length(prompt)
    
    result = await self.llm.query(
        prompt=optimized_prompt,
        provider="deepseek",
        max_tokens=2000,  # Limit response length
        temperature=0.3   # Lower temperature for more focused responses
    )
    
    return result

def _optimize_prompt_length(self, prompt: str) -> str:
    """
    Remove unnecessary words while preserving meaning
    """
    # Remove redundant phrases
    optimizations = [
        ("please", ""),
        ("could you", ""),
        ("I would like you to", ""),
        ("Can you help me", "")
    ]
    
    optimized = prompt
    for old, new in optimizations:
        optimized = optimized.replace(old, new)
    
    return optimized.strip()
```

### 3. Caching for Repeated Queries

```python
from functools import lru_cache
import hashlib

class DeepSeekCachedAgent(SelfContainedAgent):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.cache = {}
    
    async def cached_query(self, prompt: str, model: str):
        # Create cache key
        cache_key = hashlib.md5(f"{prompt}:{model}".encode()).hexdigest()
        
        if cache_key in self.cache:
            logger.info("Cache hit for DeepSeek query")
            return self.cache[cache_key]
        
        # Query DeepSeek
        result = await self.llm.query(
            prompt=prompt,
            provider="deepseek",
            model=model
        )
        
        # Cache result
        self.cache[cache_key] = result
        return result
```

## Troubleshooting

### Common Issues

**Authentication Errors**
```bash
# Check API key format
echo $DEEPSEEK_API_KEY | grep "^sk-"

# Test authentication
curl -H "Authorization: Bearer $DEEPSEEK_API_KEY" \
  https://api.deepseek.com/v1/models
```

**Model Not Available**
```python
# Check available models
available_models = ["deepseek-chat", "deepseek-coder", "deepseek-math"]
if model not in available_models:
    logger.warning(f"Model {model} not available, using deepseek-chat")
    model = "deepseek-chat"
```

**Rate Limiting**
```python
# Implement exponential backoff
async def rate_limited_deepseek_query(prompt: str, max_retries: int = 3):
    for attempt in range(max_retries):
        try:
            return await self.llm.query(prompt, provider="deepseek")
        except deepseek.RateLimitError:
            if attempt == max_retries - 1:
                raise
            
            wait_time = (2 ** attempt) * 15  # 15s, 30s, 60s
            logger.info(f"Rate limited, waiting {wait_time}s...")
            await asyncio.sleep(wait_time)
```

### Performance Optimization

**Token Usage Monitoring**
```python
def track_token_usage(self, prompt: str, response: str):
    # Estimate token usage (approximate)
    input_tokens = len(prompt.split()) * 1.3
    output_tokens = len(response.split()) * 1.3
    
    estimated_cost = (input_tokens * 0.14 + output_tokens * 0.28) / 1000000
    
    logger.info(f"DeepSeek usage: {input_tokens:.0f} in, {output_tokens:.0f} out, ${estimated_cost:.6f}")
    
    return {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "estimated_cost": estimated_cost
    }
```

---

**Next Steps**: Return to [Multi-Provider Setup](ai-providers.md) or explore [Meta Llama Integration](meta-llama.md) 