# AI Agent Platform Architecture

> **Complete guide to the platform's dual-agent architecture** - Understanding when and how to use BaseAgent vs SelfContainedAgent

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Agent Framework Design](#agent-framework-design)
- [BaseAgent vs SelfContainedAgent](#baseagent-vs-selfcontainedagent)
- [LLM Provider Integration](#llm-provider-integration)
- [API and Routing Layer](#api-and-routing-layer)
- [Database and Job Management](#database-and-job-management)
- [Frontend Integration](#frontend-integration)
- [Configuration System](#configuration-system)
- [Development Patterns](#development-patterns)
- [Deployment Architecture](#deployment-architecture)

## Architecture Overview

The AI Agent Platform uses a **dual-agent architecture** that provides both maximum flexibility and rapid development capabilities. The platform is designed around three core principles:

1. **LLM Provider Agnostic** - Support for 6+ providers (Google AI, OpenAI, Anthropic, Grok, DeepSeek, Meta Llama)
2. **Two-Tier Agent System** - BaseAgent for complex integrations, SelfContainedAgent for rapid development
3. **Auto-Discovery Framework** - Zero-configuration agent registration and API generation

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (React)                        │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐   │
│  │   Agent Cards   │ │  Job Results    │ │   Settings      │   │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                                 │ REST API
┌─────────────────────────────────────────────────────────────────┐
│                      FastAPI Backend                           │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐   │
│  │  Auto-Discovery │ │   Agent Router  │ │   Auth & Jobs   │   │
│  │    Framework    │ │                 │ │                 │   │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                                 │
┌─────────────────────────────────────────────────────────────────┐
│                      Agent Framework                           │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐   │
│  │   BaseAgent     │ │SelfContainedAgent│ │  LLM Service   │   │
│  │   (Complex)     │ │   (Rapid Dev)    │ │   (Unified)     │   │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                                 │
┌─────────────────────────────────────────────────────────────────┐
│                    LLM Provider Layer                          │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────┐ │
│  │Google  │ │OpenAI  │ │Anthropic│ │  Grok  │ │DeepSeek│ │Llama│ │
│  │   AI   │ │  GPT   │ │ Claude  │ │   xAI  │ │        │ │    │ │
│  └────────┘ └────────┘ └────────┘ └────────┘ └────────┘ └────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## Agent Framework Design

### Core Components

1. **Agent Registry** - Central registration and discovery system
2. **Job Management** - Async job execution with status tracking
3. **Provider Service** - Unified LLM provider interface
4. **Auto-Discovery** - Metaclass-based automatic registration
5. **Type Safety** - Full Pydantic validation throughout

### Framework Flow

```
Agent Creation → Registration → Auto-Discovery → API Generation → Runtime Execution
      ↓              ↓              ↓              ↓              ↓
   File Drop    Metaclass      Endpoint Scan   FastAPI Route   Job Processing
```

## BaseAgent vs SelfContainedAgent

### BaseAgent - Maximum Control

**Use BaseAgent when you need:**
- Complex multi-step workflows
- Custom database integrations
- Advanced error handling and retry logic
- Manual API endpoint management
- Integration with external services
- Custom configuration requirements

```python
class CustomWorkflowAgent(BaseAgent):
    def __init__(self, **kwargs):
        super().__init__(
            name="custom_workflow",
            description="Complex multi-step workflow agent",
            **kwargs
        )
        # Manual setup and configuration
        self.external_api = ExternalAPIClient()
        self.custom_db = CustomDatabase()
    
    def _get_system_instruction(self) -> str:
        return "Complex system instruction..."
    
    async def _execute_job_logic(self, job_data) -> AgentExecutionResult:
        # Multi-step custom logic
        step1_result = await self._execute_step_1(job_data)
        step2_result = await self._execute_step_2(step1_result)
        final_result = await self._execute_step_3(step2_result)
        
        return AgentExecutionResult(
            success=True,
            result=final_result
        )
```

**BaseAgent Architecture:**
- **Provider-Aware Initialization** - Only initializes Google AI config when it's the default provider
- **Unified LLM Service** - Always provides access to the configured default provider
- **Flexible job execution pipeline** with comprehensive error handling
- **Custom database and service integration** for complex workflows
- **Manual API endpoint creation** for specialized use cases
- **Full control over execution flow** and resource management

### SelfContainedAgent - Rapid Development

**Use SelfContainedAgent when you need:**
- Quick prototyping and development
- Standard AI processing workflows
- Auto-generated API endpoints
- Zero configuration setup
- Standard job patterns

```python
@job_model
class SimpleJobData(BaseModel):
    prompt: str = Field(..., description="Text to process")
    provider: Optional[str] = Field(default="google", description="LLM provider")

class RapidAgent(SelfContainedAgent):
    def __init__(self, **kwargs):
        super().__init__(
            description="Rapid development agent",
            **kwargs
        )
        self.llm = get_unified_llm_service()
    
    @endpoint("/rapid/process", methods=["POST"], auth_required=True)
    async def process(self, request_data: dict, user: dict):
        job_data = validate_job_data(request_data, SimpleJobData)
        return await execute_agent_job(self, job_data, user["id"])
    
    async def _execute_job_logic(self, job_data) -> AgentExecutionResult:
        result = await self.llm.query(
            prompt=job_data.prompt,
            provider=job_data.provider
        )
        return AgentExecutionResult(success=True, result=result)
```

**SelfContainedAgent Architecture:**
- Automatic registration via metaclass
- Auto-discovery of endpoints and models
- Built-in job execution framework
- Automatic API route generation
- Convention-based development

### Decision Matrix

| Requirement | BaseAgent | SelfContainedAgent |
|-------------|-----------|-------------------|
| **Development Speed** | Slower | **Faster** |
| **Flexibility** | **Maximum** | Constrained |
| **Configuration** | Manual | **Automatic** |
| **API Generation** | Manual | **Automatic** |
| **Complex Workflows** | **Excellent** | Limited |
| **Standard AI Tasks** | Overkill | **Perfect** |
| **Learning Curve** | Steeper | **Gentle** |
| **Maintenance** | Higher | **Lower** |

## LLM Provider Integration

### Unified LLM Service

The platform uses a unified service that abstracts away provider differences:

```python
# Single interface for all providers
llm_service = get_unified_llm_service()

# Use default provider (configurable)
result = await llm_service.query("Your prompt")

# Use specific provider
result = await llm_service.query("Your prompt", provider="openai")

# Fallback across providers
result = await llm_service.query_with_fallback(
    prompt="Your prompt",
    providers=["google", "openai", "anthropic"]
)
```

### Provider Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Unified LLM Service                     │
│  ┌─────────────────────────────────────────────────────┐   │
│  │        Common Interface & Fallback Logic           │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                             │
    ┌────────────────────────┼────────────────────────┐
    │                        │                        │
┌───▼───┐                ┌───▼───┐                ┌───▼───┐
│Google │                │OpenAI │                │Claude │
│AI Svc │                │ Svc   │                │ Svc   │
└───────┘                └───────┘                └───────┘
```

### Provider Configuration

Each provider can be configured independently:

```json
{
  "llm_providers": {
    "google": {
      "enabled": true,
      "priority": 1,
      "default_model": "gemini-2.0-flash",
      "rate_limit": 1000
    },
    "openai": {
      "enabled": true,
      "priority": 2,
      "default_model": "gpt-4-turbo-preview",
      "rate_limit": 500
    },
    "anthropic": {
      "enabled": false,
      "priority": 3,
      "default_model": "claude-3-sonnet-20240229"
    }
  },
  "default_provider": "google",
  "fallback_enabled": true
}
```

### Default Provider Configuration

The platform's default LLM provider is configurable via environment variables:

```bash
# Set your preferred default provider
DEFAULT_LLM_PROVIDER=google  # Options: google|openai|anthropic|grok|deepseek|llama
```

**How it works:**
1. **Environment Config** - Set `DEFAULT_LLM_PROVIDER` in your `.env` file
2. **Automatic Loading** - The UnifiedLLMService reads this setting at startup
3. **BaseAgent Integration** - All agents can access the default provider via `get_llm_service()`
4. **Runtime Override** - Individual requests can still specify a different provider

**Selection Guidelines:**
- **Development**: `google` (free tier, reliable)
- **Production**: `openai` or `anthropic` (enterprise-grade)
- **Cost-Conscious**: `deepseek` (most economical)
- **Real-time Data**: `grok` (current events access)
- **Open Source**: `llama` (flexible deployment options)

## API and Routing Layer

### Auto-Discovery System

The platform automatically discovers and registers agent endpoints:

1. **File Scanning** - Agents in `backend/agents/` are automatically imported
2. **Metaclass Registration** - `AgentMeta` registers classes and endpoints
3. **Route Generation** - FastAPI routes are automatically created
4. **OpenAPI Documentation** - Swagger docs are auto-generated

### Endpoint Registration Flow

```
Agent Class Definition → Metaclass Processing → Endpoint Collection → Route Registration
        ↓                       ↓                      ↓                    ↓
   @endpoint decorator    AgentMeta.__new__()    get_endpoints()    FastAPI.add_route()
```

### Route Structure

```
/agents/                    # Agent discovery and listing
├── /list                   # List all available agents
├── /info/{agent_name}      # Get agent information
└── /health                 # Health status of all agents

/{agent_name}/              # Agent-specific endpoints
├── /process               # Main processing endpoint
├── /info                  # Agent information
├── /health                # Health check
└── /custom-endpoints      # Custom endpoints defined by agent
```

## Database and Job Management

### Job Lifecycle

```
Job Creation → Validation → Queue → Execution → Result Storage → Client Response
     ↓            ↓         ↓         ↓             ↓              ↓
  POST Request  Pydantic   Redis    Agent       PostgreSQL    JSON Response
```

### Database Schema

```sql
-- Jobs table
CREATE TABLE jobs (
    id UUID PRIMARY KEY,
    agent_name VARCHAR(100) NOT NULL,
    user_id VARCHAR(100),
    status job_status NOT NULL,
    job_data JSONB NOT NULL,
    result TEXT,
    error_message TEXT,
    result_format VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    execution_time_seconds DECIMAL(10,3)
);

-- Agent configurations
CREATE TABLE agent_configs (
    agent_name VARCHAR(100) PRIMARY KEY,
    config JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### Job Status Flow

```
pending → running → completed
   ↓        ↓         ↓
created  processing  finished
   ↓        ↓         ↓
queued   executing   success/error
```

## Frontend Integration

### Component Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      App Component                          │
│  ┌─────────────────┐ ┌─────────────────┐ ┌───────────────┐ │
│  │   Navigation    │ │   Main Content  │ │   Sidebar     │ │
│  └─────────────────┘ └─────────────────┘ └───────────────┘ │
└─────────────────────────────────────────────────────────────┘
                             │
┌─────────────────────────────────────────────────────────────┐
│                    Agent Components                         │
│  ┌─────────────────┐ ┌─────────────────┐ ┌───────────────┐ │
│  │   Agent Card    │ │   Job Results   │ │  Settings     │ │
│  │   (Dynamic)     │ │   (Real-time)   │ │  (Config)     │ │
│  └─────────────────┘ └─────────────────┘ └───────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Dynamic UI Generation

The frontend automatically generates UI based on agent schemas:

```javascript
// Agent discovery
const agents = await fetch('/agents/list').then(r => r.json());

// Schema-based form generation
agents.forEach(agent => {
  const schema = agent.job_schema;
  const form = generateFormFromSchema(schema);
  renderAgentCard(agent, form);
});
```

## Configuration System

### Hierarchical Configuration

```
Environment Variables → Config Files → Agent Defaults → Runtime Override
        ↓                    ↓              ↓              ↓
   DATABASE_URL        config.json     agent_config    request params
```

### Configuration Layers

1. **Environment** - Database, API keys, deployment settings
2. **Application** - Server config, logging, performance
3. **Agent** - Default models, timeouts, retry logic
4. **Job** - Runtime parameters, user preferences

### Config File Structure

```json
{
  "database": {
    "url": "${DATABASE_URL}",
    "pool_size": 10,
    "timeout": 30
  },
  "agents": {
    "simple_prompt": {
      "default_provider": "google",
      "timeout_seconds": 120,
      "max_retries": 3
    }
  },
  "llm_providers": {
    "google": {
      "enabled": true,
      "api_key": "${GOOGLE_AI_API_KEY}"
    }
  }
}
```

## Development Patterns

### Recommended Development Flow

1. **Start with SelfContainedAgent** for new features
2. **Use BaseAgent** when you hit SelfContainedAgent limitations
3. **Leverage unified LLM service** for provider agnosticism
4. **Follow schema-first development** with Pydantic models
5. **Add comprehensive error handling** and logging

### Common Patterns

#### Pattern 1: Simple AI Processing
```python
class SimpleAgent(SelfContainedAgent):
    async def _execute_job_logic(self, job_data):
        result = await self.llm.query(job_data.prompt)
        return AgentExecutionResult(success=True, result=result)
```

#### Pattern 2: Multi-Provider Support
```python
class FlexibleAgent(SelfContainedAgent):
    async def _execute_job_logic(self, job_data):
        result = await self.llm.query(
            prompt=job_data.prompt,
            provider=job_data.preferred_provider
        )
        return AgentExecutionResult(success=True, result=result)
```

#### Pattern 3: Complex Workflow
```python
class WorkflowAgent(BaseAgent):
    async def _execute_job_logic(self, job_data):
        # Multi-step processing
        analysis = await self._analyze(job_data)
        processing = await self._process(analysis)
        result = await self._finalize(processing)
        return AgentExecutionResult(success=True, result=result)
```

## Deployment Architecture

### Production Deployment

```
┌─────────────────────────────────────────────────────────────┐
│                      Load Balancer                         │
└─────────────────────────────────────────────────────────────┘
                             │
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (Static)                       │
│              Nginx / CloudFlare / Vercel                   │
└─────────────────────────────────────────────────────────────┘
                             │
┌─────────────────────────────────────────────────────────────┐
│                  Backend API Servers                       │
│          FastAPI + Uvicorn (Multiple instances)            │
└─────────────────────────────────────────────────────────────┘
                             │
┌─────────────────────────────────────────────────────────────┐
│                     Data Layer                             │
│  ┌─────────────────┐ ┌─────────────────┐ ┌───────────────┐ │
│  │   PostgreSQL    │ │     Redis       │ │   File Store  │ │
│  │   (Jobs/Data)   │ │   (Cache/Jobs)  │ │   (Uploads)   │ │
│  └─────────────────┘ └─────────────────┘ └───────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Scaling Considerations

1. **Horizontal Scaling** - Multiple FastAPI instances behind load balancer
2. **Database Connection Pooling** - Efficient connection management
3. **Caching Strategy** - Redis for session and job caching
4. **Provider Rate Limiting** - Respect API limits across providers
5. **Job Queue Management** - Async job processing with proper queuing

### Environment-Specific Configuration

- **Development** - Single instance, SQLite, file-based config
- **Staging** - Docker Compose, PostgreSQL, environment variables
- **Production** - Kubernetes/Docker Swarm, managed databases, secrets management

---

This architecture provides both flexibility for complex integrations and simplicity for rapid development, while maintaining LLM provider agnosticism and production-ready scalability. 