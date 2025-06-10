# Simple Prompt Agent Guide

The Simple Prompt Agent has been enhanced to support multiple LLM providers and advanced configuration options while maintaining backward compatibility.

## Overview

The Simple Prompt Agent provides a clean interface for processing text prompts using any available LLM provider (Google AI, OpenAI, Grok, Anthropic, DeepSeek, Meta Llama). It supports provider selection, model selection, custom system instructions, and advanced generation parameters.

## Features

- **Multi-Provider Support**: Use any available LLM provider
- **Model Selection**: Choose specific models within each provider
- **Custom System Instructions**: Override default behavior
- **Temperature Control**: Fine-tune response creativity
- **Token Limits**: Control response length
- **Health Monitoring**: Real-time provider health status
- **Automatic Fallback**: Graceful handling of unavailable providers

## API Endpoints

### Process Prompt
**POST** `/simple-prompt/process`

Process a text prompt with optional provider and model selection.

**Request Body:**
```json
{
  "prompt": "Write a haiku about artificial intelligence",
  "provider": "openai",           // optional: google, openai, grok, anthropic, deepseek, llama
  "model": "gpt-4",              // optional: provider-specific model name
  "temperature": 0.8,            // optional: 0.0-1.0, default 0.7
  "system_instruction": "...",   // optional: custom system prompt
  "max_tokens": 150              // optional: maximum tokens to generate
}
```

**Response:**
```json
{
  "status": "success",
  "result": "Silicon minds awakening,\nThoughts flow through circuits of light,\nFuture consciousness.",
  "result_format": "markdown",
  "metadata": {
    "provider": "openai",
    "model": "gpt-4", 
    "temperature": 0.8
  }
}
```

### Get Agent Information
**GET** `/simple-prompt/info`

Get basic agent information and supported parameters.

**Response:**
```json
{
  "name": "simple_prompt",
  "description": "A simple agent that processes text prompts using any available LLM provider",
  "status": "available",
  "available_providers": ["google", "openai", "anthropic"],
  "default_provider": "google",
  "supported_parameters": {
    "prompt": "Text prompt to send to LLM (required)",
    "provider": "LLM provider to use. Options: google, openai, anthropic",
    "model": "Specific model to use (provider-specific, optional)",
    "temperature": "Temperature for response generation (0.0-1.0, default: 0.7)",
    "system_instruction": "Custom system instruction (optional)",
    "max_tokens": "Maximum tokens to generate (optional)"
  }
}
```

### Get Providers Information
**GET** `/simple-prompt/providers`

Get detailed information about all LLM providers.

**Response:**
```json
{
  "default_provider": "google",
  "available_providers": ["google", "openai", "anthropic"],
  "total_providers": 6,
  "healthy_count": 3,
  "failed_count": 1,
  "providers": {
    "google": {
      "provider": "google",
      "status": "available",
      "service_name": "Google AI Service",
      "default_model": "gemini-1.5-flash",
      "available_models": ["gemini-1.5-flash", "gemini-1.5-pro"]
    },
    "openai": {
      "provider": "openai", 
      "status": "available",
      "service_name": "OpenAI Service",
      "default_model": "gpt-3.5-turbo",
      "available_models": ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo"]
    }
  }
}
```

### Get Health Status
**GET** `/simple-prompt/health`

Get real-time health status and performance metrics for all providers.

**Response:**
```json
{
  "overall_status": "healthy",
  "total_services": 6,
  "loaded_services": 3,
  "failed_services": 1,
  "services": {
    "google": {
      "provider": "google",
      "service_name": "Google AI",
      "loading_status": "healthy",
      "is_loaded": true,
      "connection_health": "healthy",
      "performance_metrics": {
        "total_requests": 45,
        "error_rate_percent": 2.22,
        "average_response_time_seconds": 1.8,
        "recent_error_rate_percent": 0,
        "consecutive_errors": 0
      }
    }
  }
}
```

### Test Connections
**GET** `/simple-prompt/test-connections` *(requires auth)*

Test connections to all available LLM providers.

## Usage Examples

### Basic Usage (Default Provider)
```json
POST /simple-prompt/process
{
  "prompt": "Explain machine learning in simple terms"
}
```

### Specific Provider
```json
POST /simple-prompt/process
{
  "prompt": "Write a creative story",
  "provider": "anthropic",
  "temperature": 0.9
}
```

### Advanced Configuration
```json
POST /simple-prompt/process
{
  "prompt": "Analyze this code for bugs",
  "provider": "openai",
  "model": "gpt-4",
  "temperature": 0.2,
  "max_tokens": 500,
  "system_instruction": "You are a senior software engineer specializing in code review. Focus on security vulnerabilities and performance issues."
}
```

### Fallback Behavior
```json
POST /simple-prompt/process
{
  "prompt": "Hello world",
  "provider": "grok"  // If unavailable, will fallback to default provider
}
```

## Provider-Specific Models

### Google AI
- `gemini-1.5-flash` (default)
- `gemini-1.5-pro`
- `gemini-1.0-pro`

### OpenAI
- `gpt-3.5-turbo` (default)
- `gpt-4`
- `gpt-4-turbo`
- `gpt-4o`

### Anthropic
- `claude-3-haiku-20240307` (default)
- `claude-3-sonnet-20240229`
- `claude-3-opus-20240229`

### DeepSeek
- `deepseek-chat` (default)
- `deepseek-coder`

### Meta Llama
- `meta-llama/Llama-2-70b-chat-hf` (default)
- `meta-llama/Llama-2-13b-chat-hf`

### Grok
- `grok-beta` (default)

## Error Handling

The agent provides graceful error handling:

1. **Provider Unavailable**: Automatically falls back to available providers
2. **Model Not Found**: Falls back to provider's default model with warning
3. **Service Failures**: Returns structured error messages
4. **Rate Limits**: Propagates provider-specific rate limit errors

## Monitoring and Health

The agent includes comprehensive monitoring:

- **Connection Health**: Real-time health status for each provider
- **Performance Metrics**: Response times, error rates, request counts
- **Failure Tracking**: Automatic retry logic with exponential backoff
- **Circuit Breaking**: Prevents cascade failures

## Development and Testing

Use the test script to verify functionality:

```bash
python backend/test_simple_prompt_agent.py
```

This will test all providers, demonstrate fallback behavior, and show performance metrics.

## Backward Compatibility

The enhanced agent maintains full backward compatibility:

- Existing API calls without provider specification work unchanged
- Default behavior uses the configured default provider (Google AI)
- All previous parameters continue to work as expected 