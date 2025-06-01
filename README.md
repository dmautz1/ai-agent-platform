# AI Agent Template

> **Revolutionary Self-Contained Agent Framework** - Build AI agents with zero configuration

A modern, production-ready template for building AI agents with React frontend, FastAPI backend, and Supabase database. Perfect for developers who want to focus on AI agent logic, not infrastructure setup.

## ⚡ Quick Start

```bash
# 1. Clone and install
git clone <your-repo-url>
cd ai-agent-template
npm install && cd frontend && npm install && cd ../backend && pip install -r requirements.txt

# 2. Set up environment (5 minutes)
cp backend/env.example backend/.env
cp frontend/env.local.example frontend/.env.local
# Add your Supabase and Google AI credentials

# 3. Start development
# Terminal 1: Backend
cd backend && python main.py

# Terminal 2: Frontend
cd frontend && npm run dev

# 4. Create first user
cd frontend && npm run create-admin admin@example.com password123 "Admin User"
```

**✅ Ready!** Open http://localhost:5173 and start building agents.

## 🚀 What's Included

### Pre-Built AI Agents
- **Text Processing** - Sentiment analysis, keyword extraction, classification
- **Summarization** - Multi-media content summarization (text, audio, video)
- **Web Scraping** - AI-powered content extraction with rate limiting

### Core Features
- **Zero-Config Agent Development** - Drop a file, it works
- **Real-Time Updates** - Live status updates without page refresh
- **Secure Authentication** - Supabase Auth with JWT tokens
- **Production Ready** - Built-in logging, error handling, testing

### Developer Experience
- **5-Minute Setup** - Get running immediately
- **Type Safety** - Full TypeScript and Pydantic validation
- **Auto-Generated API Docs** - Interactive docs at `/docs`
- **Comprehensive Testing** - Unit, integration, and E2E tests

## 📖 Documentation

**→ [Complete Documentation Hub](docs/README.md)** ← Start here!

### Quick Links
- **[15-Minute Quick Start](docs/getting-started/quick-start.md)** - Get running fast
- **[Environment Setup](docs/getting-started/environment-setup.md)** - Detailed configuration
- **[Build Your First Agent](docs/development/agent-development.md)** - Create custom agents
- **[API Reference](docs/development/api-reference.md)** - Complete API documentation
- **[Deploy to Production](docs/deployment/deployment-guide.md)** - Go live on DigitalOcean

### Need Help?
- **[Troubleshooting Guide](docs/getting-started/troubleshooting.md)** - Common issues and fixes
- **[GitHub Issues](https://github.com/your-repo/issues)** - Bug reports and questions

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React Frontend│────│  FastAPI Backend │────│  Supabase DB    │
│   (TypeScript)  │    │   (Python)      │    │  (PostgreSQL)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │              ┌─────────────────┐              │
         └──────────────│   Google AI     │──────────────┘
                        │   (Gemini)      │
                        └─────────────────┘
```

**Self-Contained Agent Framework**: Each agent is a single file with embedded models, endpoints, and business logic. Zero configuration required.

## 🚀 Creating Your First Agent

Create `backend/agents/my_agent.py`:

```python
from agent_framework import SelfContainedAgent, endpoint, job_model
from pydantic import BaseModel, Field

@job_model
class MyJobData(BaseModel):
    text: str = Field(..., description="Text to process")

class MyAgent(SelfContainedAgent):
    def __init__(self, **kwargs):
        super().__init__(description="My custom agent", **kwargs)
    
    @endpoint("/my-agent/process", methods=["POST"], auth_required=True)
    async def process(self, request_data: dict, user: dict):
        job_data = validate_job_data(request_data, MyJobData)
        return await execute_agent_job(self, job_data, user["id"])
    
    async def _execute_job_logic(self, job_data: MyJobData):
        # Your AI logic here
        result = f"Processed: {job_data.text}"
        return AgentExecutionResult(success=True, result=result)
```

**That's it!** Your agent is automatically discovered and available at `/my-agent/process`.

## 📊 Project Stats

- **Lines of Code**: ~15K (excluding tests)
- **Setup Time**: 15 minutes
- **Deployment Cost**: ~$12/month (DigitalOcean)
- **Agent Creation**: Single file per agent
- **Production Ready**: Built-in monitoring, logging, security

## 🎯 Use Cases

- **Content Analysis** - Automated content moderation and insights
- **Data Processing** - Large-scale text and media processing
- **Research Tools** - Information extraction and summarization
- **Customer Support** - AI-powered response generation
- **Business Intelligence** - Automated report generation

## 🤝 Contributing

We welcome contributions! See our [contributing guidelines](CONTRIBUTING.md) for details.

## 📝 License

MIT License - see [LICENSE](LICENSE) for details.

---

**Built for junior developers who want to focus on AI agent logic, not infrastructure setup.**

**→ [Get Started Now](docs/getting-started/quick-start.md)** | **[View Documentation](docs/README.md)** | **[See Examples](docs/development/agent-development.md)** 