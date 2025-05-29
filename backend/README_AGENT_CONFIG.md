# Agent Configuration System

The Agent Configuration System provides comprehensive customization capabilities for AI agents, allowing fine-tuned control over execution behavior, model parameters, security settings, and performance optimization.

## Table of Contents

- [Overview](#overview)
- [Configuration Structure](#configuration-structure)
- [Profiles and Performance Modes](#profiles-and-performance-modes)
- [Configuration Sources](#configuration-sources)
- [API Endpoints](#api-endpoints)
- [Usage Examples](#usage-examples)
- [Best Practices](#best-practices)

## Overview

The Agent Configuration System enables:

- **Per-agent customization** with individual settings
- **Profile-based defaults** for common use cases
- **Environment variable overrides** for deployment flexibility
- **Runtime configuration updates** without restarts
- **Comprehensive validation** to prevent invalid settings
- **File-based persistence** for configuration management

### Key Features

✅ **Hierarchical Configuration** - Profile defaults → File configs → Environment overrides → Runtime updates  
✅ **Type Safety** - Full validation and type checking  
✅ **Hot Reloading** - Runtime configuration updates  
✅ **Security Controls** - Input validation, rate limiting, and content filtering  
✅ **Performance Tuning** - Timeout, retry, and caching controls  
✅ **Model Customization** - Temperature, tokens, and model selection  

## Configuration Structure

### AgentConfig

The main configuration object contains:

```python
@dataclass
class AgentConfig:
    # Basic Settings
    name: str
    description: Optional[str] = None
    profile: AgentProfile = AgentProfile.BALANCED
    performance_mode: AgentPerformanceMode = AgentPerformanceMode.BALANCED
    enabled: bool = True
    
    # Sub-configurations
    execution: AgentExecutionConfig
    model: AgentModelConfig
    logging: AgentLoggingConfig
    security: AgentSecurityConfig
    
    # Custom settings
    custom_settings: Dict[str, Any] = field(default_factory=dict)
```

### Execution Configuration

Controls agent execution behavior:

```python
@dataclass
class AgentExecutionConfig:
    timeout_seconds: int = 300           # Maximum execution time
    max_retries: int = 3                 # Retry attempts on failure
    retry_delay_base: float = 2.0        # Exponential backoff base
    enable_caching: bool = True          # Enable response caching
    cache_ttl_seconds: int = 3600        # Cache time-to-live
    priority: int = 5                    # Job priority (0-10)
    memory_limit_mb: Optional[int] = None     # Memory limit
    cpu_limit_percent: Optional[float] = None # CPU usage limit
```

### Model Configuration

Controls AI model parameters:

```python
@dataclass
class AgentModelConfig:
    model_name: Optional[str] = None          # Override model selection
    temperature: float = 0.7                  # Creativity/randomness (0-2)
    max_tokens: Optional[int] = None          # Maximum response tokens
    top_p: float = 1.0                        # Nucleus sampling
    frequency_penalty: float = 0.0            # Reduce repetition
    presence_penalty: float = 0.0             # Encourage new topics
    stop_sequences: List[str] = []            # Stop generation sequences
    custom_parameters: Dict[str, Any] = {}    # Model-specific parameters
```

### Logging Configuration

Controls logging and monitoring:

```python
@dataclass
class AgentLoggingConfig:
    log_level: str = "INFO"                      # Log level threshold
    enable_performance_logging: bool = True      # Performance metrics
    enable_debug_logging: bool = False           # Debug information
    log_requests: bool = True                    # Log incoming requests
    log_responses: bool = False                  # Log agent responses
    log_errors: bool = True                      # Log errors and exceptions
    metrics_enabled: bool = True                 # Enable metrics collection
    trace_enabled: bool = False                  # Enable request tracing
```

### Security Configuration

Controls security and safety features:

```python
@dataclass
class AgentSecurityConfig:
    enable_input_validation: bool = True        # Validate input data
    enable_output_sanitization: bool = True     # Clean output content
    max_input_size_bytes: int = 1024 * 1024     # Maximum input size (1MB)
    max_output_size_bytes: int = 1024 * 1024    # Maximum output size (1MB)
    allowed_domains: List[str] = []             # Whitelisted domains
    blocked_keywords: List[str] = []            # Blocked content keywords
    rate_limit_per_minute: int = 60             # Requests per minute limit
```

## Profiles and Performance Modes

### Configuration Profiles

Pre-defined configuration profiles for common use cases:

#### FAST Profile
- **Use Case**: Quick responses, lower quality acceptable
- **Timeout**: 60 seconds
- **Retries**: 1 attempt
- **Temperature**: 0.3 (more deterministic)
- **Max Tokens**: 1000
- **Caching**: Enabled with 30-minute TTL

#### BALANCED Profile (Default)
- **Use Case**: Good balance of speed and quality
- **Timeout**: 300 seconds (5 minutes)
- **Retries**: 3 attempts
- **Temperature**: 0.7 (moderate creativity)
- **Max Tokens**: 2000
- **Caching**: Enabled with 1-hour TTL

#### QUALITY Profile
- **Use Case**: High-quality responses, slower execution acceptable
- **Timeout**: 600 seconds (10 minutes)
- **Retries**: 5 attempts
- **Temperature**: 0.9 (more creative)
- **Max Tokens**: 4000
- **Caching**: Disabled for fresh responses

### Performance Modes

Optimization strategies for different scenarios:

- **SPEED**: Prioritize fast execution over quality
- **QUALITY**: Prioritize output quality over speed
- **BALANCED**: Balance between speed and quality
- **POWER_SAVE**: Conservative resource usage

## Configuration Sources

Configuration is loaded from multiple sources in order of precedence:

### 1. Profile Defaults (Lowest Priority)
Built-in defaults based on the selected profile.

### 2. Configuration Files
JSON files in `config/agents/` directory:

```json
{
  "name": "text_processing_agent",
  "description": "Advanced text processing with custom settings",
  "profile": "quality",
  "performance_mode": "balanced",
  "execution": {
    "timeout_seconds": 180,
    "max_retries": 2,
    "enable_caching": true
  },
  "model": {
    "temperature": 0.8,
    "max_tokens": 3000
  },
  "security": {
    "rate_limit_per_minute": 30,
    "blocked_keywords": ["inappropriate", "harmful"]
  },
  "custom_settings": {
    "special_feature": true,
    "custom_threshold": 0.85
  }
}
```

### 3. Environment Variables
Override specific configuration values:

```bash
# Pattern: AGENT_{AGENT_NAME}_{CONFIG_PATH}
AGENT_TEXT_PROCESSING_EXECUTION_TIMEOUT_SECONDS=120
AGENT_TEXT_PROCESSING_MODEL_TEMPERATURE=0.9
AGENT_TEXT_PROCESSING_LOGGING_LOG_LEVEL=DEBUG
AGENT_WEB_SCRAPING_SECURITY_RATE_LIMIT_PER_MINUTE=20
```

### 4. Runtime Updates (Highest Priority)
API-based configuration updates that take effect immediately.

## API Endpoints

### List Agent Configurations

```http
GET /config/agents
Authorization: Bearer <token>
```

**Response:**
```json
{
  "success": true,
  "message": "Agent configurations retrieved",
  "configs": {
    "text_processing_agent": {
      "name": "text_processing_agent",
      "description": "Advanced text processing agent",
      "profile": "balanced",
      "performance_mode": "balanced",
      "enabled": true
    }
  },
  "total_count": 1
}
```

### Get Agent Configuration

```http
GET /config/agents/{agent_name}
Authorization: Bearer <token>
```

**Response:**
```json
{
  "success": true,
  "message": "Configuration retrieved for agent: text_processing_agent",
  "config": {
    "name": "text_processing_agent",
    "description": "Advanced text processing agent",
    "profile": "balanced",
    "execution": {
      "timeout_seconds": 300,
      "max_retries": 3,
      "enable_caching": true
    },
    "model": {
      "temperature": 0.7,
      "max_tokens": 2000
    }
  }
}
```

### Update Agent Configuration

```http
PUT /config/agents/{agent_name}
Authorization: Bearer <token>
Content-Type: application/json

{
  "execution": {
    "timeout_seconds": 180,
    "max_retries": 2
  },
  "model": {
    "temperature": 0.8
  },
  "custom_settings": {
    "special_mode": true
  }
}
```

**Response:**
```json
{
  "success": true,
  "message": "Configuration updated for agent: text_processing_agent",
  "config": { /* updated configuration */ }
}
```

### Set Agent Profile

```http
POST /config/agents/{agent_name}/profile
Authorization: Bearer <token>
Content-Type: application/json

{
  "profile": "fast",
  "performance_mode": "speed"
}
```

### Save Configuration to File

```http
POST /config/agents/{agent_name}/save
Authorization: Bearer <token>
```

### Get Available Profiles

```http
GET /config/profiles
Authorization: Bearer <token>
```

**Response:**
```json
{
  "success": true,
  "profiles": {
    "fast": {
      "name": "fast",
      "defaults": { /* profile defaults */ }
    },
    "balanced": {
      "name": "balanced", 
      "defaults": { /* profile defaults */ }
    },
    "quality": {
      "name": "quality",
      "defaults": { /* profile defaults */ }
    }
  },
  "performance_modes": ["speed", "quality", "balanced", "power_save"]
}
```

## Usage Examples

### Basic Configuration Usage

```python
from config.agent_config import get_agent_config, update_agent_config

# Get configuration for an agent
config = get_agent_config("text_processing_agent")
print(f"Timeout: {config.execution.timeout_seconds}")
print(f"Temperature: {config.model.temperature}")

# Update configuration
updates = {
    "execution": {"timeout_seconds": 180},
    "model": {"temperature": 0.8}
}
success = update_agent_config("text_processing_agent", updates)
```

### Using Configuration in Agents

```python
class TextProcessingAgent(BaseAgent):
    async def _execute_job_logic(self, job_data):
        # Access configuration
        timeout = self.agent_config.execution.timeout_seconds
        temperature = self.agent_config.model.temperature
        
        # Use configuration-based timeout
        async with asyncio.timeout(timeout):
            # Agent logic here
            pass
        
        # Custom settings
        if self.agent_config.custom_settings.get("special_mode"):
            # Special processing
            pass
```

### Environment-based Configuration

```bash
# Development environment
export AGENT_TEXT_PROCESSING_PROFILE=fast
export AGENT_TEXT_PROCESSING_LOGGING_LOG_LEVEL=DEBUG

# Production environment  
export AGENT_TEXT_PROCESSING_PROFILE=quality
export AGENT_TEXT_PROCESSING_EXECUTION_TIMEOUT_SECONDS=600
export AGENT_TEXT_PROCESSING_LOGGING_LOG_LEVEL=WARNING
```

### Configuration File Example

Create `config/agents/custom_agent.json`:

```json
{
  "name": "custom_agent",
  "description": "Custom agent with specialized settings",
  "profile": "custom",
  "performance_mode": "quality",
  "enabled": true,
  "execution": {
    "timeout_seconds": 240,
    "max_retries": 4,
    "enable_caching": false,
    "priority": 8
  },
  "model": {
    "model_name": "gemini-2.0-flash",
    "temperature": 0.85,
    "max_tokens": 3500,
    "top_p": 0.95,
    "stop_sequences": ["STOP", "END"]
  },
  "logging": {
    "log_level": "DEBUG",
    "enable_debug_logging": true,
    "log_responses": true,
    "trace_enabled": true
  },
  "security": {
    "rate_limit_per_minute": 40,
    "max_input_size_bytes": 2097152,
    "blocked_keywords": ["spam", "abuse"],
    "allowed_domains": ["trusted-domain.com"]
  },
  "custom_settings": {
    "use_advanced_processing": true,
    "confidence_threshold": 0.9,
    "experimental_features": {
      "feature_a": true,
      "feature_b": false
    }
  }
}
```

## Best Practices

### 1. Profile Selection

- **Development**: Use `FAST` profile for quick iterations
- **Testing**: Use `BALANCED` profile for realistic testing
- **Production**: Use `QUALITY` profile for best results
- **Resource-constrained**: Use `POWER_SAVE` mode

### 2. Configuration Management

- **Version Control**: Store configuration files in version control
- **Environment Separation**: Use environment variables for deployment-specific settings
- **Validation**: Always validate configurations before deployment
- **Documentation**: Document custom settings and their purposes

### 3. Security Considerations

- **Input Validation**: Always enable input validation in production
- **Rate Limiting**: Set appropriate rate limits for your use case
- **Content Filtering**: Use blocked keywords for sensitive applications
- **Domain Restrictions**: Whitelist trusted domains for web scraping agents

### 4. Performance Optimization

- **Caching**: Enable caching for repetitive workloads
- **Timeouts**: Set realistic timeouts based on your requirements
- **Retries**: Configure retries based on failure rates
- **Resource Limits**: Set memory/CPU limits in containerized environments

### 5. Monitoring and Debugging

- **Logging Levels**: Use appropriate log levels for each environment
- **Performance Logging**: Enable for production monitoring
- **Debug Logging**: Enable only during troubleshooting
- **Metrics**: Monitor configuration effectiveness with metrics

### 6. Configuration Updates

- **Gradual Rollout**: Test configuration changes in staging first
- **Backup**: Save current configurations before major changes
- **Monitoring**: Monitor agent performance after configuration updates
- **Rollback Plan**: Have a plan to quickly revert problematic changes

## Configuration Validation

The system validates configurations to prevent runtime errors:

### Validation Rules

- **Execution**: Positive timeouts, non-negative retries
- **Model**: Temperature between 0-2, positive max_tokens
- **Security**: Positive size limits and rate limits
- **Logging**: Valid log levels
- **Names**: Non-empty agent names

### Error Handling

Invalid configurations return detailed error messages:

```json
{
  "success": false,
  "message": "Configuration validation failed",
  "errors": [
    "Execution timeout must be positive",
    "Model temperature must be between 0 and 2",
    "Rate limit must be positive"
  ]
}
```

This comprehensive configuration system provides the flexibility and control needed to optimize agent behavior for any use case while maintaining safety and reliability. 