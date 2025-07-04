# 🤖 AI Agent Platform

> **Revolutionary Self-Contained Agent Framework** - Build AI agents with zero configuration

[![Tests](https://img.shields.io/badge/tests-passing-green)](https://github.com/dmautz1/ai-agent-platform)
[![Coverage](https://img.shields.io/badge/coverage-85%25-green)](https://github.com/dmautz1/ai-agent-platform)
[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

The AI Agent Platform revolutionizes how you build, deploy, and manage AI agents. Unlike traditional frameworks that require complex configuration and setup, our platform provides **self-contained agents** that work out of the box with automatic endpoint registration, built-in authentication, and seamless LLM integration.

## ✨ What Makes This Special

🚀 **Zero Configuration** - Agents work immediately without setup  
🔧 **Self-Contained** - Everything needed is built into each agent  
🔗 **Auto-Discovery** - Agents automatically register their endpoints  
🛡️ **Built-in Security** - Authentication and authorization included  
🎨 **Dynamic UI** - Forms generated automatically from agent schemas  
⚡ **Real-time Updates** - Live job status and progress tracking  
🔌 **LLM Agnostic** - Works with OpenAI, Anthropic, Google, and more  

## 🏗️ Architecture

```
ai-agent-platform/
├── backend/                 # FastAPI backend
│   ├── agents/             # Self-contained agent implementations
│   ├── routes/             # API route handlers
│   ├── models/             # Pydantic data models
│   ├── auth.py             # Authentication system
│   ├── agent_framework.py  # Agent framework core
│   └── main.py             # FastAPI application
├── frontend/               # React frontend
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── pages/          # Page components
│   │   ├── lib/            # Utilities and API client
│   │   └── types/          # TypeScript type definitions
│   └── public/             # Static assets
├── backend/tests/          # Backend test suite
│   ├── unit/              # Unit tests
│   ├── integration/       # Integration tests
│   └── agents/            # Agent-specific tests
└── docs/                  # Documentation
```

## 🚀 Quick Start

### Prerequisites
- **Python 3.8+** with pip
- **Node.js 18+** with npm
- **Git** for version control

### Installation

```bash
# Clone the repository
git clone https://github.com/dmautz1/ai-agent-platform.git
cd ai-agent-platform

# Install all dependencies
npm run install:all

# Set up environment variables
cp backend/.env.example backend/.env
# Edit backend/.env with your configuration
```

### Running the Platform

```bash
# Terminal 1: Start the backend
cd backend
python main.py

# Terminal 2: Start the frontend
npm run dev:frontend
```

The platform will be available at:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## 📅 Scheduling System

The AI Agent Platform includes a powerful scheduling system that allows you to automate agent execution based on cron expressions with full timezone support.

### Key Features

- **Cron Expression Support**: Standard cron syntax with validation
- **Timezone Aware**: Schedule jobs across different time zones
- **Background Processing**: Automatic execution monitoring and job creation
- **Schedule Management**: Full CRUD operations for schedules
- **Execution Tracking**: Detailed statistics and execution history
- **Immediate Execution**: Run scheduled jobs on-demand
- **Error Handling**: Robust error handling with retry mechanisms

### API Endpoints

#### Schedule Management
```bash
# Create a new schedule
POST /api/schedules/
{
  "title": "Daily Report Generation",
  "description": "Generate daily reports every morning",
  "agent_name": "report_generator",
  "cron_expression": "0 9 * * *",
  "timezone": "America/New_York",
  "enabled": true,
  "agent_config_data": {
    "name": "report_generator",
    "job_data": {
      "report_type": "daily",
      "include_charts": true
    }
  }
}

# List all schedules
GET /api/schedules/

# Get specific schedule
GET /api/schedules/{schedule_id}

# Update schedule
PUT /api/schedules/{schedule_id}

# Delete schedule
DELETE /api/schedules/{schedule_id}
```

#### Schedule Control
```bash
# Enable a schedule
POST /api/schedules/{schedule_id}/enable

# Disable a schedule
POST /api/schedules/{schedule_id}/disable

# Run schedule immediately
POST /api/schedules/{schedule_id}/run-now

# Get execution history
GET /api/schedules/{schedule_id}/history

# Get schedule statistics
GET /api/schedules/{schedule_id}/stats
```

### Usage Examples

#### Create a Daily Schedule
```python
import requests

schedule_data = {
    "title": "Daily Data Processing",
    "description": "Process daily data every morning at 8 AM EST",
    "agent_name": "data_processor",
    "cron_expression": "0 8 * * *",
    "timezone": "America/New_York",
    "enabled": True,
    "agent_config_data": {
        "name": "data_processor",
        "job_data": {
            "source": "database",
            "output_format": "csv"
        }
    }
}

response = requests.post(
    "http://localhost:8000/api/schedules/",
    json=schedule_data,
    headers={"Authorization": "Bearer your-token"}
)
```

#### Common Cron Expressions
```bash
# Every minute
* * * * *

# Every hour at minute 0
0 * * * *

# Every day at 9:00 AM
0 9 * * *

# Every Monday at 10:00 AM
0 10 * * 1

# Every first day of month at midnight
0 0 1 * *

# Every weekday at 2:30 PM
30 14 * * 1-5
```

### Background Scheduler Service

The platform runs a background scheduler service that:
- Monitors enabled schedules every 30 seconds
- Creates jobs for schedules that are due
- Updates next run times automatically
- Handles timezone conversions
- Provides error handling and logging
- Tracks execution statistics
- **Prevents duplicate execution** with atomic claim-and-update pattern

#### Race Condition Prevention

The scheduler implements several mechanisms to prevent duplicate job execution:

- **Atomic Claiming**: Updates schedule `next_run` time before creating jobs
- **Optimistic Locking**: Uses database conditional updates to prevent race conditions  
- **Reduced Tolerance Window**: 30-second tolerance window minimizes overlap
- **Duplicate Detection**: Only one scheduler instance can claim each schedule execution

For high-concurrency deployments, consider adding a database unique constraint:
```sql
ALTER TABLE schedules ADD CONSTRAINT unique_schedule_execution 
  UNIQUE (id, next_run);
```

## 🔧 Core Features

### Self-Contained Agents
Agents inherit from `SelfContainedAgent` and automatically:
- Register API endpoints
- Generate JSON schemas for forms
- Handle authentication and validation
- Provide health checks and monitoring

### Dynamic Job Management
- **Real-time Status**: Live updates on job progress
- **Job Operations**: Retry, cancel, and rerun jobs
- **Result Display**: Rich JSON result visualization
- **Error Handling**: Comprehensive error tracking

### Advanced Scheduling System
- **Cron-based Scheduling**: Full cron expression support with validation
- **Timezone Support**: Schedule jobs across different time zones
- **Automatic Execution**: Background service monitors and executes due schedules
- **Schedule Management**: Create, update, enable/disable, and delete schedules
- **Execution History**: Track job executions with success/failure statistics
- **Run Now**: Trigger immediate execution of scheduled jobs
- **Real-time Monitoring**: Live status updates and execution tracking

### Multi-LLM Support
Integrated support for:
- **OpenAI** (GPT-3.5, GPT-4)
- **Anthropic** (Claude 3)
- **Google AI** (Gemini)
- **X.AI** (Grok)
- **DeepSeek** (DeepSeek-V2)
- **Meta** (Llama models)

### Advanced Features
- **Authentication**: JWT-based user authentication
- **Real-time Updates** - Core workflows and user journeys
- **API-First Design**: RESTful API with OpenAPI documentation
- **Type Safety**: Full TypeScript support
- **Performance Monitoring**: Built-in metrics and logging
- **Comprehensive Testing** - Unit, integration, and backend test suites

## 🧪 Testing

```bash
# All tests (frontend + backend)
npm run test

# Individual test suites
npm run test:frontend        # Frontend tests
npm run test:backend         # Backend tests
npm run test:backend:unit    # Backend unit tests
npm run test:backend:integration  # Backend integration tests
```

## 📊 Tech Stack

- **Backend**: Python, FastAPI, Pydantic, SQLAlchemy
- **Frontend**: React, TypeScript, Tailwind CSS, Vite
- **Database**: SQLite (development), PostgreSQL (production)
- **Authentication**: JWT tokens, Supabase integration
- **Testing**: Pytest, Jest, React Testing Library
- **Deployment**: Docker, Vercel, Railway

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup

```bash
# Install development dependencies
npm run install:all

# Run tests
npm run test

# Run with coverage
npm run test:ci
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/) and [React](https://reactjs.org/)
- Inspired by the need for simpler AI agent development
- Thanks to all contributors and the open-source community 