"""
Routes package for the AI Agent Platform.

This package contains modular FastAPI route definitions organized by functionality:
- system: System health, stats, and configuration endpoints
- auth: Authentication and user management endpoints  
- agents: Agent discovery, health, and schema endpoints
- jobs: Job creation, management, and processing endpoints
- pipeline: Job pipeline status and metrics endpoints
- llm_providers: AI provider validation and configuration endpoints
"""

from .system import router as system_router
from .auth import router as auth_router
from .agents import router as agents_router
from .jobs import router as jobs_router
from .pipeline import router as pipeline_router
from .llm_providers import router as llm_providers_router

__all__ = [
    "system_router",
    "auth_router", 
    "agents_router",
    "jobs_router",
    "pipeline_router",
    "llm_providers_router"
] 