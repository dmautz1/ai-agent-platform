"""
Environment Configuration Module

This module handles environment-specific configuration for the AI Agent Platform.
Supports development, staging, and production environments with proper validation.
"""

import os
import logging
from typing import Optional, List
from enum import Enum
from dotenv import load_dotenv
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)

class Environment(str, Enum):
    """Supported environment types"""
    DEVELOPMENT = "development"
    STAGING = "staging"  
    PRODUCTION = "production"

class LogLevel(str, Enum):
    """Supported log levels"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class Settings(BaseSettings):
    """Main settings class with environment-based configuration"""
    
    # Environment selection
    environment: Environment = Field(default=Environment.DEVELOPMENT, description="Current environment")
    
    # Application settings
    app_name: str = Field(default="AI Agent Platform", description="Application name")
    app_version: str = Field(default="1.0.0", description="Application version")
    debug: bool = Field(default=False, description="Debug mode")
    
    # Server settings
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, description="Server port")
    reload: bool = Field(default=False, description="Auto-reload on code changes")
    
    # Security settings
    secret_key: str = Field(..., alias="JWT_SECRET", description="Secret key for JWT tokens")
    access_token_expire_minutes: int = Field(default=30, description="JWT token expiration")
    
    # Database settings
    supabase_url: str = Field(..., description="Supabase project URL")
    supabase_key: str = Field(..., description="Supabase API key")
    supabase_service_key: Optional[str] = Field(default=None, description="Supabase service role key")
    
    # Google AI settings
    google_api_key: Optional[str] = Field(default=None, description="Google AI API key")
    google_cloud_project: Optional[str] = Field(default=None, description="Google Cloud project ID")
    google_cloud_location: Optional[str] = Field(default="us-central1", description="Google Cloud location")
    google_genai_use_vertexai: bool = Field(default=False, description="Use Vertex AI instead of Google AI Studio")
    google_default_model: str = Field(default="gemini-2.0-flash", description="Default Google AI model")
    
    # LLM Service settings
    default_llm_provider: str = Field(default="google", description="Default LLM provider to use (google|openai|anthropic|grok|deepseek|llama)")
    
    # Performance settings
    max_concurrent_jobs: int = Field(default=10, description="Maximum concurrent job executions")
    job_timeout_seconds: int = Field(default=300, description="Job execution timeout")
    
    # Logging settings
    log_level: LogLevel = Field(default=LogLevel.INFO, description="Logging level")
    log_format: str = Field(default="json", description="Log format (json or text)")
    
    # CORS settings
    cors_origins: List[str] = Field(default=[], description="Allowed CORS origins")
    cors_allow_credentials: bool = Field(default=True, description="Allow credentials in CORS")
    cors_max_age: int = Field(default=600, description="CORS preflight cache time")
    
    @field_validator('environment', mode='before')
    @classmethod
    def validate_environment(cls, v):
        """Validate environment value"""
        if isinstance(v, str):
            v = v.lower()
        return v
    
    @field_validator('default_llm_provider', mode='before')
    @classmethod
    def validate_default_llm_provider(cls, v):
        """Validate default LLM provider value"""
        if isinstance(v, str):
            v = v.lower()
        
        valid_providers = ["google", "openai", "anthropic", "grok", "deepseek", "llama"]
        if v not in valid_providers:
            raise ValueError(f"Invalid default_llm_provider. Must be one of: {', '.join(valid_providers)}")
        return v
    
    def get_cors_origins(self) -> List[str]:
        """Get parsed CORS origins list with environment-appropriate defaults"""
        # Check for ALLOWED_ORIGINS environment variable first
        allowed_origins = os.getenv('ALLOWED_ORIGINS', '').strip()
        if allowed_origins:
            # Parse comma-separated origins and trim whitespace
            origins = [origin.strip() for origin in allowed_origins.split(',') if origin.strip()]
            if origins:
                return origins
        
        # Check pydantic field
        if self.cors_origins:
            return self.cors_origins
            
        # Default origins based on environment
        if self.environment == Environment.DEVELOPMENT:
            return [
                "http://localhost:3000",
                "http://localhost:3001",
                "http://127.0.0.1:3000",
                "http://127.0.0.1:3001",
                "http://localhost:5173",  # Vite default
                "http://localhost:4173",  # Vite preview
                "http://localhost:8080",  # Vue CLI default
                "http://localhost:8000",  # Local API testing
                "http://127.0.0.1:5173",
                "http://127.0.0.1:4173",
                "http://127.0.0.1:8080",
                "http://127.0.0.1:8000"
            ]
        elif self.environment == Environment.STAGING:
            return [
                "http://localhost:3000",
                "http://localhost:3001",
                "http://localhost:5173",
                "http://localhost:4173"
            ]
        elif self.environment == Environment.PRODUCTION:
            return [
                "http://localhost:3000",  # Still needed for local testing
                "https://yourdomain.vercel.app",
                "https://www.yourdomain.com"
            ]
        else:
            return ["http://localhost:3000"]
    
    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.environment == Environment.PRODUCTION
    
    def is_development(self) -> bool:
        """Check if running in development environment"""
        return self.environment == Environment.DEVELOPMENT
    
    def is_staging(self) -> bool:
        """Check if running in staging environment"""
        return self.environment == Environment.STAGING

    class Config:
        """Pydantic configuration"""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields in .env file

# Global settings instance
_settings: Optional[Settings] = None

def get_settings() -> Settings:
    """Get or create application settings instance"""
    global _settings
    if _settings is None:
        try:
            _settings = Settings()
            logger.info(f"Settings loaded for {_settings.environment} environment")
        except Exception as e:
            logger.error(f"Failed to load settings: {e}")
            raise
    return _settings

def reload_settings() -> Settings:
    """Reload settings (useful for testing)"""
    global _settings
    _settings = None
    return get_settings()

def validate_required_settings() -> None:
    """Validate that all required settings are present"""
    settings = get_settings()
    
    required_fields = ['supabase_url', 'supabase_key', 'secret_key']
    missing_fields = []
    
    for field in required_fields:
        value = getattr(settings, field, None)
        if not value:
            missing_fields.append(field.upper())
    
    if missing_fields:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_fields)}")
    
    # Warn about missing optional but recommended fields
    if settings.environment == Environment.PRODUCTION:
        if not settings.google_api_key and not settings.google_cloud_project:
            logger.warning("No Google AI configuration found - Google AI features will not be available")

def get_logging_config() -> dict:
    """Get logging configuration dictionary"""
    settings = get_settings()
    
    return {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'default': {
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S'
            }
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'level': settings.log_level.value,
                'formatter': 'default'
            }
        },
        'root': {
            'level': settings.log_level.value,
            'handlers': ['console']
        },
        'loggers': {
            'uvicorn': {
                'level': 'INFO',
                'handlers': ['console'],
                'propagate': False
            },
            'fastapi': {
                'level': 'INFO', 
                'handlers': ['console'],
                'propagate': False
            }
        }
    }