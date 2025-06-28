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