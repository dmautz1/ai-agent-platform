# Meta Llama Integration

> **Meta Llama Setup** - Configure Meta's open-source LLM models for custom AI solutions

## Overview

Meta's Llama models provide open-source excellence with specialized variants for different use cases, offering transparency and customization opportunities.

**Key Features:**
- **Open Source**: Transparent and customizable
- **Specialized Models**: Chat, Code, Safety variants
- **Strong Performance**: Competitive with commercial models
- **Fine-tuning**: Customizable for specific needs
- **Community Support**: Large open-source community

## Quick Setup

Meta Llama models are available through various providers. We'll use Together AI as the primary example:

### 1. Create Together AI Account

1. Go to [Together AI](https://api.together.xyz/)
2. Sign up with your account
3. Complete verification
4. Add billing information (free tier available)

### 2. Generate API Key

1. Navigate to **API Keys**
2. Create new key
3. Copy the generated key

```bash
# Your Llama provider API key (Together AI example)
LLAMA_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### 3. Configure Environment

Add to `backend/.env`:

```bash
# Meta Llama Configuration (via Together AI)
LLAMA_API_KEY=your-key-here
LLAMA_MODEL=meta-llama/Llama-2-70b-chat-hf  # Default model
LLAMA_MAX_TOKENS=4000
LLAMA_TEMPERATURE=0.7
LLAMA_PROVIDER=together  # Provider service
```

### 4. Test Connection

```bash
# Start backend
cd backend && python main.py

# Test Llama connection
curl -X POST http://localhost:8000/ai/test \
  -H "Content-Type: application/json" \
  -d '{"provider": "llama", "prompt": "Hello, world!"}'
```

## Available Models

### Llama 2 Chat Models

#### Llama-2-70b-chat-hf (Large)
- **Model**: `meta-llama/Llama-2-70b-chat-hf`
- **Parameters**: 70 billion
- **Best for**: Complex reasoning, detailed responses
- **Strengths**: Highest quality, best reasoning
- **Context**: 4K tokens

#### Llama-2-13b-chat-hf (Medium)
- **Model**: `meta-llama/Llama-2-13b-chat-hf`
- **Parameters**: 13 billion
- **Best for**: Balanced performance and speed
- **Strengths**: Good quality, faster responses
- **Context**: 4K tokens

#### Llama-2-7b-chat-hf (Small)
- **Model**: `meta-llama/Llama-2-7b-chat-hf`
- **Parameters**: 7 billion
- **Best for**: Quick responses, simple tasks
- **Strengths**: Fast, lightweight
- **Context**: 4K tokens

### Code Llama Models

#### CodeLlama-34b-Instruct-hf
- **Model**: `codellama/CodeLlama-34b-Instruct-hf`
- **Parameters**: 34 billion
- **Best for**: Complex code generation, debugging
- **Strengths**: Superior code understanding
- **Context**: 16K tokens

#### CodeLlama-13b-Instruct-hf
- **Model**: `codellama/CodeLlama-13b-Instruct-hf`
- **Parameters**: 13 billion
- **Best for**: Standard code tasks
- **Strengths**: Good balance of speed and quality
- **Context**: 16K tokens

### Safety and Moderation

#### Llama Guard
- **Model**: `meta-llama/LlamaGuard-7b`
- **Parameters**: 7 billion
- **Best for**: Content moderation, safety checks
- **Strengths**: Built for safety classification
- **Context**: 4K tokens

### Model Configuration

```bash
# Large chat model (best quality)
LLAMA_MODEL=meta-llama/Llama-2-70b-chat-hf

# Balanced chat model
LLAMA_MODEL=meta-llama/Llama-2-13b-chat-hf

# Code generation
LLAMA_MODEL=codellama/CodeLlama-34b-Instruct-hf

# Content moderation
LLAMA_MODEL=meta-llama/LlamaGuard-7b
```

## Using Meta Llama in Agents

### Basic Usage

```python
from services.llm_service import get_unified_llm_service

@job_model
class LlamaJobData(BaseModel):
    prompt: str = Field(..., description="Text to process")
    model_size: str = Field(default="70b", description="Model size (7b|13b|70b)")
    use_case: str = Field(default="chat", description="Use case (chat|code|safety)")

class LlamaAgent(SelfContainedAgent):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.llm = get_unified_llm_service()
    
    async def _execute_job_logic(self, job_data: LlamaJobData):
        model = self._select_llama_model(job_data.use_case, job_data.model_size)
        
        result = await self.llm.query(
            prompt=job_data.prompt,
            provider="llama",
            model=model
        )
        
        return AgentExecutionResult(
            success=True,
            result=result,
            metadata={
                "provider": "llama",
                "model": model,
                "use_case": job_data.use_case
            }
        )
    
    def _select_llama_model(self, use_case: str, size: str) -> str:
        models = {
            "chat": {
                "7b": "meta-llama/Llama-2-7b-chat-hf",
                "13b": "meta-llama/Llama-2-13b-chat-hf",
                "70b": "meta-llama/Llama-2-70b-chat-hf"
            },
            "code": {
                "13b": "codellama/CodeLlama-13b-Instruct-hf",
                "34b": "codellama/CodeLlama-34b-Instruct-hf"
            },
            "safety": {
                "7b": "meta-llama/LlamaGuard-7b"
            }
        }
        
        return models.get(use_case, {}).get(size, "meta-llama/Llama-2-70b-chat-hf")
```

## Specialized Use Cases

### Code Generation with CodeLlama

```python
async def generate_code_with_llama(self, requirements: str, language: str):
    prompt = f"""
    Generate {language} code for the following requirements:
    
    {requirements}
    
    Include:
    1. Clean, well-commented code
    2. Error handling
    3. Example usage
    4. Documentation
    """
    
    return await self.llm.query(
        prompt=prompt,
        provider="llama",
        model="codellama/CodeLlama-34b-Instruct-hf"
    )
```

### Content Moderation with Llama Guard

```python
async def moderate_content(self, content: str):
    prompt = f"""
    Analyze this content for safety issues:
    
    {content}
    
    Check for:
    - Harmful content
    - Inappropriate material
    - Policy violations
    - Safety concerns
    
    Respond with: SAFE or UNSAFE and explanation.
    """
    
    return await self.llm.query(
        prompt=prompt,
        provider="llama",
        model="meta-llama/LlamaGuard-7b"
    )
```

### Custom Fine-tuned Models

```python
async def use_custom_llama(self, prompt: str, custom_model_id: str):
    """
    Use a custom fine-tuned Llama model
    """
    return await self.llm.query(
        prompt=prompt,
        provider="llama",
        model=custom_model_id,  # Your fine-tuned model
        extra_params={"custom_model": True}
    )
```

### Multi-size Model Selection

```python
async def intelligent_model_selection(self, task: str, complexity: str):
    """
    Select appropriate Llama model based on task complexity
    """
    if complexity == "simple":
        model = "meta-llama/Llama-2-7b-chat-hf"  # Fast, lightweight
    elif complexity == "medium":
        model = "meta-llama/Llama-2-13b-chat-hf"  # Balanced
    else:
        model = "meta-llama/Llama-2-70b-chat-hf"  # Highest quality
    
    return await self.llm.query(
        prompt=task,
        provider="llama",
        model=model
    )
```

## Provider Options

### Together AI (Recommended)
- **Strengths**: Easy setup, good performance, competitive pricing
- **Models**: Full Llama 2 and Code Llama collection
- **Pricing**: Pay-per-token with free tier

### Replicate
- **Strengths**: Various model versions, good for experimentation
- **Models**: Multiple Llama variants and fine-tuned versions
- **Pricing**: Pay-per-second compute time

### Hugging Face Inference Endpoints
- **Strengths**: Direct access to Hugging Face ecosystem
- **Models**: Official Meta releases and community fine-tunes
- **Pricing**: Custom pricing based on usage

### Local Deployment
- **Strengths**: Full control, no API costs, privacy
- **Requirements**: High-end GPU (24GB+ VRAM for 70B models)
- **Tools**: Ollama, llama.cpp, text-generation-webui

## Pricing Comparison

### Together AI Pricing (per 1M tokens)

| Model | Input | Output |
|-------|-------|--------|
| Llama-2-7b-chat | $0.20 | $0.20 |
| Llama-2-13b-chat | $0.22 | $0.22 |
| Llama-2-70b-chat | $0.90 | $0.90 |
| CodeLlama-34b | $0.78 | $0.78 |

## Error Handling

```python
import together

async def robust_llama_query(prompt: str):
    try:
        result = await self.llm.query(prompt, provider="llama")
        return result
    except together.AuthenticationError:
        logger.error("Llama provider authentication failed - check API key")
        raise
    except together.RateLimitError as e:
        logger.warning(f"Llama rate limit hit: {e}")
        # Implement backoff or fallback
        await asyncio.sleep(45)
        return await self.llm.query(prompt, provider="google")  # Fallback
    except together.APIError as e:
        logger.error(f"Llama API error: {e}")
        return await self.llm.query(prompt, provider="openai")  # Fallback
```

## Best Practices

### 1. Model Selection Strategy

```python
def select_optimal_llama_model(task_type: str, quality_requirement: str) -> str:
    """
    Choose the best Llama model for the task
    """
    
    # Code tasks
    if task_type == "code":
        return "codellama/CodeLlama-34b-Instruct-hf"
    
    # Safety/moderation tasks
    if task_type == "moderation":
        return "meta-llama/LlamaGuard-7b"
    
    # Chat tasks - select by quality requirement
    if quality_requirement == "high":
        return "meta-llama/Llama-2-70b-chat-hf"
    elif quality_requirement == "medium":
        return "meta-llama/Llama-2-13b-chat-hf"
    else:
        return "meta-llama/Llama-2-7b-chat-hf"
```

### 2. Prompt Engineering for Llama

```python
def format_llama_prompt(instruction: str, context: str = None) -> str:
    """
    Format prompts optimally for Llama models
    """
    if context:
        return f"""[INST] <<SYS>>
{context}
<</SYS>>

{instruction} [/INST]"""
    else:
        return f"[INST] {instruction} [/INST]"

# Usage example
async def llama_with_system_prompt(self, user_input: str):
    system_context = "You are a helpful assistant that provides concise, accurate answers."
    formatted_prompt = format_llama_prompt(user_input, system_context)
    
    return await self.llm.query(
        prompt=formatted_prompt,
        provider="llama",
        model="meta-llama/Llama-2-70b-chat-hf"
    )
```

### 3. Fine-tuning Integration

```python
class CustomLlamaAgent(SelfContainedAgent):
    def __init__(self, fine_tuned_model_id: str = None, **kwargs):
        super().__init__(**kwargs)
        self.fine_tuned_model = fine_tuned_model_id
        self.base_model = "meta-llama/Llama-2-13b-chat-hf"
    
    async def _execute_job_logic(self, job_data):
        # Use fine-tuned model if available, otherwise base model
        model = self.fine_tuned_model or self.base_model
        
        result = await self.llm.query(
            prompt=job_data.prompt,
            provider="llama",
            model=model
        )
        
        return AgentExecutionResult(
            success=True,
            result=result,
            metadata={
                "model": model,
                "is_fine_tuned": bool(self.fine_tuned_model)
            }
        )
```

### 4. Cost Optimization

```python
async def cost_aware_llama_processing(self, prompts: List[str]):
    """
    Process multiple prompts with cost optimization
    """
    results = []
    
    for prompt in prompts:
        # Use smaller model for simple prompts
        if len(prompt.split()) < 50:
            model = "meta-llama/Llama-2-7b-chat-hf"
        else:
            model = "meta-llama/Llama-2-70b-chat-hf"
        
        result = await self.llm.query(
            prompt=prompt,
            provider="llama",
            model=model,
            max_tokens=1000  # Limit response length
        )
        
        results.append({
            "result": result,
            "model_used": model,
            "estimated_cost": self._estimate_cost(prompt, result, model)
        })
    
    return results
```

## Troubleshooting

### Common Issues

**Model Not Available**
```python
# Check available models for your provider
available_models = [
    "meta-llama/Llama-2-70b-chat-hf",
    "meta-llama/Llama-2-13b-chat-hf", 
    "meta-llama/Llama-2-7b-chat-hf",
    "codellama/CodeLlama-34b-Instruct-hf"
]

if model not in available_models:
    logger.warning(f"Model {model} not available, using default")
    model = "meta-llama/Llama-2-13b-chat-hf"
```

**Long Response Times**
```python
# Use timeout and smaller models for time-sensitive tasks
try:
    result = await asyncio.wait_for(
        self.llm.query(prompt, provider="llama", model="meta-llama/Llama-2-7b-chat-hf"),
        timeout=30.0
    )
except asyncio.TimeoutError:
    logger.warning("Llama query timed out, using fallback")
    result = await self.llm.query(prompt, provider="google")
```

**Context Length Exceeded**
```python
def truncate_for_llama(text: str, max_tokens: int = 3000) -> str:
    """
    Truncate text to fit Llama context window
    """
    words = text.split()
    # Rough estimate: 1.3 words per token
    max_words = int(max_tokens / 1.3)
    
    if len(words) > max_words:
        return " ".join(words[:max_words]) + "..."
    return text
```

---

**Next Steps**: Return to [Multi-Provider Setup](ai-providers.md) or explore [Grok Integration](grok.md) 