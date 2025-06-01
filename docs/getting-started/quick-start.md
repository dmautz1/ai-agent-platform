# Quick Start Guide

> **Get running in 15 minutes** - Streamlined setup for immediate results

## Prerequisites

- **Node.js 18+** and **Python 3.8+**
- **Git** for cloning
- **Code editor** (VS Code recommended)

## 🚀 15-Minute Setup

### Step 1: Clone and Install (2 minutes)

```bash
# Clone the repository
git clone <your-repo-url>
cd ai-agent-template

# Install dependencies
npm install
cd frontend && npm install && cd ..
cd backend && pip install -r requirements.txt && cd ..
```

### Step 2: Quick Environment Setup (5 minutes)

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
GOOGLE_API_KEY=your-google-ai-api-key
```

### Step 3: Database Setup (5 minutes)

1. **Create Supabase account** at [supabase.com](https://supabase.com)
2. **Create new project** (takes 2-3 minutes)
3. **Get credentials** from Settings → API:
   ```bash
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_KEY=your-anon-key
   SUPABASE_SERVICE_KEY=your-service-key
   ```
4. **Run SQL migration** in Supabase SQL Editor:
   - Copy content from `supabase/migrations/001_create_jobs_table.sql`
   - Run the SQL

### Step 4: Start Application (1 minute)

```bash
# Terminal 1 - Backend
cd backend
python main.py

# Terminal 2 - Frontend  
cd frontend
npm run dev
```

### Step 5: Create First User (2 minutes)

```bash
cd frontend
npm run create-admin admin@example.com password123 "Admin User"
```

## ✅ Verify Setup

1. **Frontend**: Open http://localhost:5173
2. **Backend API**: Open http://localhost:8000/docs
3. **Login**: Use your admin credentials
4. **Test**: Create a sample job in the dashboard

## 🎉 You're Ready!

Your AI Agent Template is now running! 

### What's Next?

- **[Create your first agent](../development/agent-development.md)**
- **[Explore the API](../development/api-reference.md)**
- **[Deploy to production](../deployment/deployment-guide.md)**

### Need Help?

- **Environment issues**: See [Environment Setup](environment-setup.md)
- **Errors**: Check [Troubleshooting](troubleshooting.md)
- **Development**: Browse [Development Docs](../development/)

---

**🚀 Happy building!** Start with the agent development guide to create your first custom AI agent. 