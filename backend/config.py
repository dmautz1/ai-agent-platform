"""
Environment configuration management for the AI Agent Template API.
Provides centralized configuration with validation, defaults, and type safety.
"""

import os
import logging
from typing import Optional, List, Union
from enum import Enum
from dotenv import load_dotenv
from pydantic import BaseSettings, Field, validator, AnyHttpUrl

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)

class Environment(str, Enum):
    """Environment enumeration"""
    development = "development"
    staging = "staging" 
    production = "production"
    testing = "testing"

class LogLevel(str, Enum):
    """Log level enumeration"""
    debug = "DEBUG"
    info = "INFO"
    warning = "WARNING"
    error = "ERROR"
    critical = "CRITICAL"

class Settings(BaseSettings):
    """Application settings with environment variable management"""
    
    # Application Settings
    app_name: str = Field(default="AI Agent Template API", description="Application name")
    app_version: str = Field(default="1.0.0", description="Application version")
    environment: Environment = Field(default=Environment.development, description="Environment")
    debug: bool = Field(default=False, description="Debug mode")
    
    # Server Settings
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, ge=1, le=65535, description="Server port")
    reload: bool = Field(default=True, description="Auto-reload on code changes")
    
    # Database Settings (Supabase)
    supabase_url: str = Field(..., description="Supabase project URL")
    supabase_key: str = Field(..., description="Supabase anon/service key")
    supabase_service_key: Optional[str] = Field(default=None, description="Supabase service role key")
    
    # Authentication Settings
    jwt_secret: Optional[str] = Field(default=None, description="JWT secret key for additional security")
    jwt_algorithm: str = Field(default="HS256", description="JWT algorithm")
    access_token_expire_minutes: int = Field(default=30, ge=1, description="Access token expiration minutes")
    
    # AI/Agent Settings
    google_adk_api_key: Optional[str] = Field(default=None, description="Google ADK API key")
    openai_api_key: Optional[str] = Field(default=None, description="OpenAI API key")
    default_agent_timeout: int = Field(default=300, ge=1, description="Default agent timeout in seconds")
    max_concurrent_jobs: int = Field(default=10, ge=1, le=100, description="Maximum concurrent jobs")
    
    # CORS Settings
    allowed_origins: Optional[str] = Field(default=None, description="Comma-separated CORS origins")
    cors_allow_credentials: bool = Field(default=True, description="Allow credentials in CORS")
    cors_max_age: int = Field(default=86400, ge=0, description="CORS max age in seconds")
    
    # Logging Settings
    log_level: LogLevel = Field(default=LogLevel.info, description="Logging level")
    log_format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log format string"
    )
    log_file: Optional[str] = Field(default=None, description="Log file path")
    log_rotation: bool = Field(default=True, description="Enable log rotation")
    log_max_size: str = Field(default="10MB", description="Maximum log file size")
    log_backup_count: int = Field(default=5, ge=0, description="Number of backup log files")
    
    # Security Settings
    api_rate_limit: str = Field(default="100/minute", description="API rate limit")
    trusted_hosts: Optional[str] = Field(default=None, description="Comma-separated trusted hosts")
    secure_cookies: bool = Field(default=False, description="Use secure cookies")
    
    # Job Processing Settings
    job_queue_max_size: int = Field(default=1000, ge=1, description="Maximum job queue size")
    job_retry_attempts: int = Field(default=3, ge=0, description="Number of job retry attempts")
    job_timeout: int = Field(default=3600, ge=1, description="Job timeout in seconds")
    cleanup_completed_jobs_after: int = Field(
        default=86400, ge=0, description="Clean up completed jobs after seconds (0 = never)"
    )
    
    # Performance Settings
    worker_processes: int = Field(default=1, ge=1, description="Number of worker processes")
    max_request_size: int = Field(default=16777216, ge=1024, description="Maximum request size in bytes")
    
    @validator('environment', pre=True)
    def validate_environment(cls, v):
        """Validate environment value"""
        if isinstance(v, str):
            v = v.lower()
        return v
    
    @validator('supabase_url')
    def validate_supabase_url(cls, v):
        """Validate Supabase URL format"""
        if not v.startswith('https://'):
            raise ValueError('Supabase URL must start with https://')
        if not v.endswith('.supabase.co'):
            raise ValueError('Supabase URL must end with .supabase.co')
        return v
    
    @validator('port')
    def validate_port(cls, v, values):
        """Validate port is available in production"""
        environment = values.get('environment')
        if environment == Environment.production and v in [22, 80, 443]:
            logger.warning(f"Using reserved port {v} in production")
        return v
    
    @validator('debug')
    def validate_debug_mode(cls, v, values):
        """Ensure debug is disabled in production"""
        environment = values.get('environment')
        if environment == Environment.production and v:
            logger.warning("Debug mode is enabled in production - this should be disabled")
        return v
    
    @validator('allowed_origins')
    def validate_cors_origins(cls, v):
        """Validate CORS origins format"""
        if v and v.strip():
            origins = [origin.strip() for origin in v.split(',')]
            for origin in origins:
                if origin and not (origin.startswith(('http://', 'https://')) or origin == '*'):
                    raise ValueError(f'Invalid CORS origin: {origin}')
        return v
    
    def get_cors_origins(self) -> List[str]:
        """Get parsed CORS origins list"""
        if not self.allowed_origins:
            # Default origins based on environment
            if self.environment == Environment.development:
                return [
                    "http://localhost:3000",
                    "http://localhost:3001",
                    "http://127.0.0.1:3000",
                    "http://localhost:5173",  # Vite
                    "http://localhost:8080"
                ]
            elif self.environment == Environment.staging:
                return [
                    "https://staging.yourdomain.com",
                    "https://preview.yourdomain.vercel.app"
                ]
            elif self.environment == Environment.production:
                return [
                    "https://yourdomain.com",
                    "https://www.yourdomain.com",
                    "https://yourdomain.vercel.app"
                ]
            else:  # testing
                return ["http://localhost:3000"]
        
        return [origin.strip() for origin in self.allowed_origins.split(',') if origin.strip()]
    
    def get_trusted_hosts(self) -> List[str]:
        """Get parsed trusted hosts list"""
        if not self.trusted_hosts:
            return ["*"]  # Allow all hosts by default
        return [host.strip() for host in self.trusted_hosts.split(',') if host.strip()]
    
    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.environment == Environment.production
    
    def is_development(self) -> bool:
        """Check if running in development environment"""
        return self.environment == Environment.development
    
    def is_testing(self) -> bool:
        """Check if running in testing environment"""
        return self.environment == Environment.testing
    
    def get_database_url(self) -> str:
        """Get formatted database URL for Supabase"""
        return f"{self.supabase_url}/rest/v1/"
    
    def get_auth_url(self) -> str:
        """Get formatted auth URL for Supabase"""
        return f"{self.supabase_url}/auth/v1/"
    
    class Config:
        """Pydantic configuration"""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        
        # Environment variable prefixes
        env_prefix = ""
        
        # Field aliases for environment variables
        fields = {
            'app_name': {'env': 'APP_NAME'},
            'app_version': {'env': 'APP_VERSION'},
            'environment': {'env': 'ENVIRONMENT'},
            'debug': {'env': 'DEBUG'},
            'host': {'env': 'HOST'},
            'port': {'env': 'PORT'},
            'reload': {'env': 'RELOAD'},
            'supabase_url': {'env': 'SUPABASE_URL'},
            'supabase_key': {'env': 'SUPABASE_KEY'},
            'supabase_service_key': {'env': 'SUPABASE_SERVICE_KEY'},
            'jwt_secret': {'env': 'JWT_SECRET'},
            'jwt_algorithm': {'env': 'JWT_ALGORITHM'},
            'access_token_expire_minutes': {'env': 'ACCESS_TOKEN_EXPIRE_MINUTES'},
            'google_adk_api_key': {'env': 'GOOGLE_ADK_API_KEY'},
            'openai_api_key': {'env': 'OPENAI_API_KEY'},
            'default_agent_timeout': {'env': 'DEFAULT_AGENT_TIMEOUT'},
            'max_concurrent_jobs': {'env': 'MAX_CONCURRENT_JOBS'},
            'allowed_origins': {'env': 'ALLOWED_ORIGINS'},
            'cors_allow_credentials': {'env': 'CORS_ALLOW_CREDENTIALS'},
            'cors_max_age': {'env': 'CORS_MAX_AGE'},
            'log_level': {'env': 'LOG_LEVEL'},
            'log_format': {'env': 'LOG_FORMAT'},
            'log_file': {'env': 'LOG_FILE'},
            'log_rotation': {'env': 'LOG_ROTATION'},
            'log_max_size': {'env': 'LOG_MAX_SIZE'},
            'log_backup_count': {'env': 'LOG_BACKUP_COUNT'},
            'api_rate_limit': {'env': 'API_RATE_LIMIT'},
            'trusted_hosts': {'env': 'TRUSTED_HOSTS'},
            'secure_cookies': {'env': 'SECURE_COOKIES'},
            'job_queue_max_size': {'env': 'JOB_QUEUE_MAX_SIZE'},
            'job_retry_attempts': {'env': 'JOB_RETRY_ATTEMPTS'},
            'job_timeout': {'env': 'JOB_TIMEOUT'},
            'cleanup_completed_jobs_after': {'env': 'CLEANUP_COMPLETED_JOBS_AFTER'},
            'worker_processes': {'env': 'WORKER_PROCESSES'},
            'max_request_size': {'env': 'MAX_REQUEST_SIZE'}
        }

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
    
    required_fields = ['supabase_url', 'supabase_key']
    missing_fields = []
    
    for field in required_fields:
        value = getattr(settings, field, None)
        if not value:
            missing_fields.append(field.upper())
    
    if missing_fields:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_fields)}")
    
    # Warn about missing optional but recommended fields
    if settings.environment == Environment.production:
        recommended_fields = {
            'jwt_secret': 'JWT_SECRET',
            'google_adk_api_key': 'GOOGLE_ADK_API_KEY',
            'log_file': 'LOG_FILE'
        }
        
        missing_recommended = []
        for field, env_var in recommended_fields.items():
            value = getattr(settings, field, None)
            if not value:
                missing_recommended.append(env_var)
        
        if missing_recommended:
            logger.warning(f"Missing recommended environment variables for production: {', '.join(missing_recommended)}")

def get_logging_config() -> dict:
    """Get logging configuration dictionary"""
    settings = get_settings()
    
    config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'default': {
                'format': settings.log_format,
                'datefmt': '%Y-%m-%d %H:%M:%S'
            },
            'detailed': {
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(lineno)d - %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S'
            }
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'level': settings.log_level.value,
                'formatter': 'default',
                'stream': 'ext://sys.stdout'
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
    
    # Add file handler if log file is specified
    if settings.log_file:
        if settings.log_rotation:
            config['handlers']['file'] = {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': settings.log_level.value,
                'formatter': 'detailed',
                'filename': settings.log_file,
                'maxBytes': _parse_size(settings.log_max_size),
                'backupCount': settings.log_backup_count
            }
        else:
            config['handlers']['file'] = {
                'class': 'logging.FileHandler',
                'level': settings.log_level.value,
                'formatter': 'detailed',
                'filename': settings.log_file
            }
        
        config['root']['handlers'].append('file')
        config['loggers']['uvicorn']['handlers'].append('file')
        config['loggers']['fastapi']['handlers'].append('file')
    
    return config

def _parse_size(size_str: str) -> int:
    """Parse size string like '10MB' to bytes"""
    size_str = size_str.upper().strip()
    
    if size_str.endswith('KB'):
        return int(size_str[:-2]) * 1024
    elif size_str.endswith('MB'):
        return int(size_str[:-2]) * 1024 * 1024
    elif size_str.endswith('GB'):
        return int(size_str[:-2]) * 1024 * 1024 * 1024
    else:
        return int(size_str)  # Assume bytes 