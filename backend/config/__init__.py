"""
Configuration Module - Central configuration management for the AI Agent Template

This module provides comprehensive configuration management for:
- Agent configuration with profiles and performance modes
- Google AI configuration and authentication  
- Database configuration for Supabase
- Environment variables and validation
- JWT authentication settings
"""

from .google_ai import *
from .agent import *
# from .database import *  # Commented out - file doesn't exist
# from .auth import *  # Commented out - file doesn't exist

# Export configuration components
__all__ = [
    # Agent configuration
    'AgentConfig', 'AgentProfile', 'PerformanceMode',
    'ModelConfig', 'ExecutionConfig', 'get_agent_config',
    
    # Google AI configuration
    'GoogleAIConfig', 'get_google_ai_config', 'validate_google_ai_environment',
    'get_generative_model', 'get_environment_info',
    
    # Database configuration
    'DatabaseConfig', 'get_database_config', 'validate_database_config',
    
    # Authentication configuration
    'AuthConfig', 'get_auth_config', 'validate_auth_config'
] 