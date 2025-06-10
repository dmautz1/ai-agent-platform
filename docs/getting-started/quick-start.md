# Quick Start Guide

> **Get running in 30 minutes** - Streamlined setup for immediate results

## Prerequisites

Before starting, ensure you have:

**System Requirements:**
- **Node.js 20+** ([Download](https://nodejs.org/))
- **Python 3.8+** ([Download](https://python.org/))
- **Git** ([Download](https://git-scm.com/))

**Online Accounts:**
- **Supabase account** ([Sign up free](https://supabase.com)) - Database and authentication
- **AI Provider account** (choose one or more):
  - **Google AI Studio** ([Sign up free](https://aistudio.google.com)) - Google's AI models (Gemini)
  - **OpenAI** ([Sign up](https://platform.openai.com)) - OpenAI models (GPT-4, GPT-3.5)
  - **Anthropic** ([Sign up](https://console.anthropic.com/)) - Claude models with advanced reasoning
  - **Additional providers**: Grok, DeepSeek, Meta Llama (see [AI Providers Guide](../integrations/ai-providers.md))

**Development Tools:**
- **Code editor**
- **Terminal/Command line** access

**⏱️ Time Required:** ~30 minutes total

## 🚀 30-Minute Setup

### Step 1: Clone and Install (5 minutes)

```bash
# Clone the repository
git clone https://github.com/dmautz1/ai-agent-platform
cd ai-agent-platform

# Install root dependencies (for testing)
npm install

# Install frontend dependencies
cd frontend
npm install
cd ..

# Set up backend virtual environment and dependencies
cd backend
python -m venv venv

# Activate virtual environment
source venv/bin/activate  # Linux/Mac
# OR venv\Scripts\activate  # Windows

# Install backend dependencies
pip install -r requirements.txt
cd ..
```

**⚠️ Important**: Always activate the virtual environment when working with the backend:
```bash
cd backend
source venv/bin/activate  # Linux/Mac
# OR venv\Scripts\activate  # Windows
```

### Step 2: Quick Environment Setup (8 minutes)

```bash
# Create environment files
cp backend/env.example backend/.env
cp frontend/env.local.example frontend/.env.local
```

**Minimum required settings** in `backend/.env`:
```bash
# Quick development setup
ENVIRONMENT=development
DEBUG=true
JWT_SECRET=your-32-character-secret-key-here

# AI Provider (choose one to start)
GOOGLE_API_KEY=your-google-ai-api-key
# OPENAI_API_KEY=your-openai-api-key  # Alternative
# ANTHROPIC_API_KEY=your-anthropic-api-key  # Alternative

# Database
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-key
```

**Update** `frontend/.env.local`:
```bash
# Frontend only needs client-safe variables
VITE_API_BASE_URL=http://localhost:8000
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key
```

### Step 3: Database Setup (10 minutes)

1. **Create Supabase account** at [supabase.com](https://supabase.com)
2. **Create new project** (takes 2-3 minutes)
3. **Get credentials** from Settings → API:
   - Copy `Project URL` and both keys to `backend/.env`
   - Copy `Project URL` and `anon key` to `frontend/.env.local`
4. **Run SQL migration** in Supabase SQL Editor:
   - Copy content from `supabase/migrations/supabase_setup.sql`
   - Run the SQL

### Step 4: AI Provider Setup (5 minutes)

Choose your preferred AI provider:

**Option A: Google AI (Recommended - Free)**
1. Go to [Google AI Studio](https://aistudio.google.com)
2. Create API key
3. Add to `backend/.env`: `GOOGLE_API_KEY=your-key`

**Option B: OpenAI (Industry Standard)**
1. Go to [OpenAI Platform](https://platform.openai.com)
2. Create API key (requires billing)
3. Add to `backend/.env`: `OPENAI_API_KEY=your-key`

**Multiple Providers:**
You can configure multiple providers for fallback and provider selection. See [Multi-Provider Setup](../integrations/ai-providers.md).

### Step 5: Start Application (2 minutes)

```bash
# Terminal 1 - Backend (with virtual environment activated)
cd backend
source venv/bin/activate  # Linux/Mac
# OR venv\Scripts\activate  # Windows
python main.py

# Terminal 2 - Frontend  
cd frontend
npm run dev
```

### Step 6: Create First User (2 minutes)

```bash
# IMPORTANT: Run from backend directory with venv activated
cd backend
source venv/bin/activate  # Linux/Mac
# OR venv\Scripts\activate  # Windows
python create_admin_user.py admin@example.com password123 "Admin User"
```

**🔐 Security Note:** Admin user creation uses the service role key, which must stay in the backend environment only.

## ✅ Verify Setup

1. **Frontend**: Open http://localhost:5173
2. **Backend API**: Open http://localhost:8000/docs
3. **Login**: Use your admin credentials
4. **Test**: Create a sample job in the dashboard

**Success indicators:**
- ✅ No console errors in browser
- ✅ Backend shows "Server started" message
- ✅ Can log in with admin credentials
- ✅ Dashboard loads agent list
- ✅ Can submit and execute test jobs

## 🤖 AI Provider Options

### Primary Providers (Choose One)

| Provider | Setup Difficulty | Free Tier | Best For |
|----------|------------------|-----------|----------|
| **Google AI** | Easy | ✅ Yes | General purpose, getting started |
| **OpenAI** | Easy | ❌ No | Production, reliability |
| **Anthropic** | Easy | ❌ No | Complex reasoning, analysis |

### Specialized Providers (Optional)

| Provider | Best For | Documentation |
|----------|----------|---------------|
| **Grok** | Real-time data, current events | [Setup Guide](../integrations/grok.md) |
| **DeepSeek** | Cost-effective processing | [Setup Guide](../integrations/deepseek.md) |
| **Meta Llama** | Open-source, customizable | [Setup Guide](../integrations/meta-llama.md) |

## 🔧 Development Workflow

### Daily Development Routine

```bash
# Terminal 1 - Backend
cd backend
source venv/bin/activate  # Always activate first!
python main.py

# Terminal 2 - Frontend
cd frontend
npm run dev
```

### Creating Your First Agent

1. **Create agent file**: `backend/agents/my_first_agent.py`
2. **Copy from template**:

```python
from pydantic import BaseModel, Field
from agent import SelfContainedAgent, AgentExecutionResult

@job_model
class MyFirstAgentJobData(BaseModel):
    message: str = Field(..., description="Message to process")

class MyFirstAgent(SelfContainedAgent):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "My First Agent"

    async def _execute_job_logic(self, job_data: MyFirstAgentJobData):
        # Your agent logic here
        result = await self.llm.query(
            prompt=f"Process this message: {job_data.message}"
        )
        
        return AgentExecutionResult(
            success=True,
            result={"response": result},
            metadata={"agent": self.name}
        )
```

3. **Restart backend** - Agent is automatically discovered!
4. **Test in UI** - Form is automatically generated

## 🐛 Quick Troubleshooting

### Common Issues

| Issue | Quick Fix |
|-------|-----------|
| "ModuleNotFoundError" | Activate virtual environment: `source venv/bin/activate` |
| "Supabase connection failed" | Check URL starts with `https://` |
| "AI Provider error" | Verify API key in provider dashboard |
| "CORS error" | Add `ALLOWED_ORIGINS=http://localhost:5173` to backend/.env |
| "Frontend blank page" | Check browser console, ensure backend is running |

### Health Checks

```bash
# Check backend health
curl http://localhost:8000/health

# Check frontend
# Should open browser automatically, or visit http://localhost:5173

# Check virtual environment
which python  # Should show path with 'venv' in it
```

### Reset & Restart

If something goes wrong, try this reset sequence:

```bash
# Stop all servers (Ctrl+C in terminals)

# Reset backend
cd backend
source venv/bin/activate
pip install -r requirements.txt
python main.py

# Reset frontend
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run dev
```

## 🚀 Next Steps

### Immediate Next Steps

1. **Explore the dashboard** - Browse available agents
2. **Run sample jobs** - Test the simple prompt agent
3. **Check logs** - Monitor job execution in real-time
4. **Review API docs** - Visit http://localhost:8000/docs

### Development Path

1. **[Create Custom Agents](../development/creating-agents.md)** - Build your first agent
2. **[Multi-Provider Setup](../integrations/ai-providers.md)** - Add more AI providers
3. **[Testing](../development/testing.md)** - Write tests for your agents
4. **[Deployment](../deployment/deployment-guide.md)** - Go live in production

### Learning Resources

- **[Complete Documentation](../README.md)** - Full documentation hub
- **[Agent Examples](../development/agent-examples.md)** - Sample agent implementations
- **[API Reference](../development/api-reference.md)** - Complete API documentation
- **[Video Tutorials](../tutorials/)** - Step-by-step video guides

---

**🎉 Congratulations!** You now have a fully functional AI Agent Platform. Start building amazing agents!

**Need help?** Check our [Troubleshooting Guide](troubleshooting.md) or [create an issue](https://github.com/dmautz1/ai-agent-platform/issues/new/choose). 