# Additional AI Providers

> **Extended AI Provider Support** - Grok, DeepSeek, and Meta Llama integration guides

This section covers the setup and configuration of three additional AI providers supported by AI Agent Platform, each offering unique capabilities for specialized use cases.

## 🚀 Grok (xAI) - Real-time Data Access

**Best for**: Current events, research, real-time information

Grok by xAI offers real-time information access and web search capabilities, making it ideal for current events and research tasks.

**Key Features:**
- Real-time data access and web search
- Conversational AI with current event awareness  
- X Platform integration for social media context
- Excellent for breaking news and market updates

**→ [Complete Grok Setup Guide](grok.md)**

---

## 💎 DeepSeek - Cost-Effective Processing  

**Best for**: High-volume applications, budget-conscious development

DeepSeek provides competitive AI capabilities at cost-effective pricing, making it ideal for bulk processing and cost-sensitive applications.

**Key Features:**
- Very competitive pricing with generous free tier
- Strong code generation capabilities
- Specialized models for chat, coding, and math
- High throughput for bulk operations

**→ [Complete DeepSeek Setup Guide](deepseek.md)**

---

## 🦙 Meta Llama - Open-Source Excellence

**Best for**: Open-source projects, custom fine-tuning, transparency

Meta's Llama models provide open-source excellence with specialized variants for different use cases.

**Key Features:**
- Full open-source transparency
- Multiple model sizes (7B, 13B, 70B parameters)
- Specialized Code Llama variants
- Fine-tuning and customization support

**→ [Complete Meta Llama Setup Guide](meta-llama.md)**

---

## Quick Provider Comparison

| Feature | Grok | DeepSeek | Meta Llama |
|---------|------|----------|------------|
| **Real-time Data** | ✅ Excellent | ❌ No | ❌ No |
| **Cost** | 💰 Moderate | 💰 Very Low | 💰 Low |
| **Code Generation** | ⭐ Good | ⭐ Excellent | ⭐ Excellent |
| **Open Source** | ❌ No | ❌ No | ✅ Yes |
| **Customization** | ❌ Limited | ❌ Limited | ✅ Full |
| **Context Window** | 🔄 Large | 🔄 Standard | 🔄 4K-16K |
| **Specialized Models** | ❌ No | ✅ Chat/Code/Math | ✅ Chat/Code/Safety |

## Provider Selection Guide

### When to Use Grok
- **Current events analysis** - Real-time information needs
- **Market research** - Live data and social media sentiment
- **Breaking news** - Latest developments and trends
- **Social media analysis** - X platform integration

### When to Use DeepSeek  
- **Cost-sensitive applications** - Budget constraints
- **Bulk processing** - High-volume operations
- **Code generation** - Programming tasks
- **Mathematical problems** - Specialized math model

### When to Use Meta Llama
- **Open-source requirements** - Transparency needs
- **Custom fine-tuning** - Specialized use cases
- **Code generation** - Programming with Code Llama
- **Content moderation** - Safety with Llama Guard

## Multi-Provider Configuration

### Environment Setup

Configure multiple additional providers in `backend/.env`:

```bash
# Additional AI Providers (optional)
GROK_API_KEY=xai-your-grok-key
DEEPSEEK_API_KEY=sk-your-deepseek-key  
LLAMA_API_KEY=your-llama-provider-key

# Provider Models
GROK_MODEL=grok-2
DEEPSEEK_MODEL=deepseek-chat
LLAMA_MODEL=meta-llama/Llama-2-70b-chat-hf
```

### Intelligent Provider Selection

```python
def select_additional_provider(task_type: str, context: dict) -> str:
    """
    Intelligent selection among additional providers
    """
    
    # Real-time information needs
    if context.get("needs_current_data"):
        return "grok"
    
    # Cost-sensitive applications
    if context.get("budget") == "low":
        return "deepseek"
    
    # Open-source requirements
    if context.get("open_source_required"):
        return "llama"
    
    # Code generation tasks
    if task_type == "code":
        if context.get("budget") == "low":
            return "deepseek"  # Cost-effective
        else:
            return "llama"     # Code Llama specialization
    
    # Default fallback
    return "deepseek"  # Most cost-effective
```

## Error Handling and Fallbacks

```python
async def robust_additional_provider_query(prompt: str, provider: str):
    try:
        return await self.llm.query(prompt, provider=provider)
    except ProviderError as e:
        logger.warning(f"{provider} failed: {e}")
        
        # Fallback strategy for each provider
        fallbacks = {
            "grok": "google",      # For real-time needs, fall back to Google
            "deepseek": "google",  # For cost-effective, fall back to Google  
            "llama": "openai"      # For open-source, fall back to OpenAI
        }
        
        fallback_provider = fallbacks.get(provider, "google")
        return await self.llm.query(prompt, provider=fallback_provider)
```

## Getting Started

1. **Choose Your Providers** - Select based on your specific needs
2. **Follow Setup Guides** - Use the detailed guides for each provider
3. **Configure Environment** - Add API keys to your backend environment
4. **Test Integration** - Verify each provider works correctly
5. **Implement Selection Logic** - Use intelligent provider selection

## Configuration Examples

### Development Environment
```bash
# Focus on free/low-cost providers
AI_PROVIDER=google
AI_FALLBACK_PROVIDERS=google,deepseek
DEEPSEEK_API_KEY=your-deepseek-key
```

### Production Environment  
```bash
# Balanced approach with specialized providers
AI_PROVIDER=openai
AI_FALLBACK_PROVIDERS=openai,deepseek,grok
GROK_API_KEY=your-grok-key
DEEPSEEK_API_KEY=your-deepseek-key
```

### Research Environment
```bash
# Real-time and open-source focus
AI_PROVIDER=grok
AI_FALLBACK_PROVIDERS=grok,llama,google
GROK_API_KEY=your-grok-key
LLAMA_API_KEY=your-llama-key
```

---

**Next Steps**: 
- **[Grok Setup](grok.md)** - Real-time data and current events
- **[DeepSeek Setup](deepseek.md)** - Cost-effective AI processing  
- **[Meta Llama Setup](meta-llama.md)** - Open-source AI models
- **[Multi-Provider Guide](ai-providers.md)** - Main provider documentation 