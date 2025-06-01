# Architecture Overview

> **System Design and Patterns** - Understanding the AI Agent Template architecture

## System Architecture

The AI Agent Template follows a **modern full-stack architecture** with clear separation between frontend, backend, and data layers:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React Frontend│────│  FastAPI Backend │────│  Supabase DB    │
│   (TypeScript)  │    │   (Python)      │    │  (PostgreSQL)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │              ┌─────────────────┐              │
         └──────────────│   External APIs │──────────────┘
                        │  (Google AI)    │
                        └─────────────────┘
```

## Core Components

### Frontend Architecture (React + TypeScript)

```
frontend/
├── src/
│   ├── components/     # Reusable UI components
│   ├── pages/          # Route-based page components
│   ├── contexts/       # React context providers
│   ├── lib/           # Utilities and API client
│   └── test/          # Unit and component tests
├── tests/             # Integration tests
└── public/            # Static assets
```

**Key Patterns:**
- **Component-based architecture** with shadcn/ui components
- **Context-driven state management** for auth and global state
- **API-first design** with centralized HTTP client
- **Type-safe** with TypeScript throughout

### Backend Architecture (FastAPI + Python)

```
backend/
├── main.py                 # Application entry point
├── agent_framework.py      # Self-contained agent framework
├── agents/                 # Agent implementations
│   ├── __init__.py        # Auto-discovery system
│   └── *_agent.py         # Individual agent files
├── models.py              # Core data models
├── auth.py                # Authentication system
├── database.py            # Database connections
└── logging_system.py      # Structured logging
```

## Self-Contained Agent Framework v2.0

### Revolutionary Single-File Architecture

The framework uses a **zero-configuration approach** where each agent is completely self-contained:

```python
# agents/my_agent.py - Everything in one file!

@job_model  # Embedded data model
class MyJobData(BaseModel):
    text: str

class MyAgent(SelfContainedAgent):
    @endpoint("/my-agent/process", methods=["POST"])  # Embedded endpoint
    async def process(self, request_data: dict, user: dict):
        # Business logic here
        pass
```

### Key Framework Features

1. **Automatic Discovery**: Agents are found and registered automatically
2. **Embedded Models**: Data models defined within agent files
3. **Embedded Endpoints**: API endpoints defined within agent files
4. **Zero Configuration**: No changes to main application files needed
5. **Type Safety**: Full Pydantic validation throughout

### Agent Lifecycle

```
Agent File Created → Auto-Discovery → Model Registration → Endpoint Registration → Ready for Requests
```

## Data Flow Architecture

### Request Flow

```
1. Frontend Request
   ↓
2. FastAPI Router
   ↓
3. Authentication Middleware
   ↓
4. Agent Endpoint
   ↓
5. Job Validation
   ↓
6. Business Logic
   ↓
7. Database/External APIs
   ↓
8. Response Formation
   ↓
9. Frontend Update
```

### Authentication Flow

```
1. User Login (Frontend)
   ↓
2. Supabase Auth
   ↓
3. JWT Token Generated
   ↓
4. Token Stored (Frontend)
   ↓
5. API Requests with Bearer Token
   ↓
6. Backend JWT Verification
   ↓
7. User Context Available
```

## Database Design

### Core Tables

```sql
-- Jobs table for agent task management
jobs (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES auth.users,
  agent_type TEXT NOT NULL,
  status job_status NOT NULL,
  job_data JSONB,
  result JSONB,
  created_at TIMESTAMP,
  updated_at TIMESTAMP
)

-- Built-in Supabase auth tables
auth.users (
  id UUID PRIMARY KEY,
  email TEXT UNIQUE,
  encrypted_password TEXT,
  -- ... other auth fields
)
```

### Data Patterns

- **JSONB Storage**: Flexible job data and results
- **UUID Primary Keys**: Distributed-friendly identifiers
- **Row Level Security**: Supabase built-in security
- **Real-time Subscriptions**: Live updates via Supabase

## Security Architecture

### Multi-Layer Security

1. **Frontend**: Environment variable protection, HTTPS-only
2. **API**: JWT authentication, CORS configuration
3. **Database**: Row-level security, service role separation
4. **External APIs**: API key management, rate limiting

### Authentication Stack

```
Frontend ←→ Supabase Auth ←→ Backend JWT Verification ←→ Database RLS
```

## Deployment Architecture

### DigitalOcean App Platform

```
┌─────────────────┐    ┌─────────────────┐
│   Frontend App  │    │   Backend App   │
│   (Static Site) │    │   (Docker)      │
└─────────────────┘    └─────────────────┘
         │                       │
         └───────┬───────────────┘
                 │
    ┌─────────────────┐    ┌─────────────────┐
    │  Supabase DB    │    │  External APIs  │
    │  (Managed)      │    │  (Google AI)    │
    └─────────────────┘    └─────────────────┘
```

### Production Considerations

- **Horizontal Scaling**: Multiple backend instances
- **Load Balancing**: DigitalOcean managed load balancer
- **Database Connection Pooling**: Supabase built-in
- **CDN**: Global asset distribution
- **Monitoring**: Built-in application metrics

## Performance Patterns

### Optimization Strategies

1. **Frontend**: Code splitting, lazy loading, asset optimization
2. **Backend**: Connection pooling, async processing, caching
3. **Database**: Indexed queries, efficient JSONB operations
4. **API**: Request/response compression, rate limiting

### Monitoring and Observability

- **Structured Logging**: JSON-formatted logs with correlation IDs
- **Performance Metrics**: Request timing, error rates
- **Health Checks**: Comprehensive system health endpoints
- **Error Tracking**: Detailed error reporting and alerting

## Extension Points

### Adding New Features

1. **New Agents**: Drop files in `agents/` directory
2. **New Endpoints**: Use `@endpoint` decorator
3. **New Models**: Use `@job_model` decorator
4. **New UI Components**: Follow component patterns
5. **New Integrations**: Extend service layer

### Customization Patterns

- **Agent Configuration**: Environment-based settings
- **UI Theming**: CSS custom properties and Tailwind
- **API Extensions**: Middleware and dependency injection
- **Database Extensions**: Custom migrations and RLS policies

---

**Next Steps:**
- **[Agent Development Guide](agent-development.md)** - Build your first agent
- **[API Reference](api-reference.md)** - Complete endpoint documentation
- **[Testing Strategy](testing.md)** - Testing patterns and tools 