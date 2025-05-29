"""
CORS configuration management for the AI Agent Template API.
Centralizes CORS settings and provides utilities for managing cross-origin requests.
"""

import os
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class CORSConfig:
    """CORS configuration management class"""
    
    def __init__(self):
        """Initialize CORS configuration"""
        self.environment = os.getenv("ENVIRONMENT", "development")
        self.allowed_origins = self._get_allowed_origins()
        self.allowed_methods = self._get_allowed_methods()
        self.allowed_headers = self._get_allowed_headers()
        self.exposed_headers = self._get_exposed_headers()
        self.allow_credentials = True
        self.max_age = 86400  # 24 hours
        
        logger.info(f"CORS configured for {self.environment} environment with {len(self.allowed_origins)} origins")
    
    def _get_allowed_origins(self) -> List[str]:
        """Get allowed origins from environment or defaults"""
        origins_env = os.getenv("ALLOWED_ORIGINS", "")
        if origins_env:
            origins = [origin.strip() for origin in origins_env.split(",")]
            logger.info(f"CORS origins from environment: {origins}")
            return origins
        
        # Default origins based on environment
        default_origins = [
            "http://localhost:3000",
            "http://localhost:3001", 
            "http://127.0.0.1:3000",
            "http://127.0.0.1:3001"
        ]
        
        if self.environment == "production":
            production_origins = [
                "https://yourdomain.vercel.app",
                "https://www.yourdomain.com",
                "https://api.yourdomain.com"
            ]
            default_origins.extend(production_origins)
        elif self.environment == "development":
            dev_origins = [
                "http://localhost:8080",
                "http://localhost:5173",  # Vite default
                "http://localhost:4173",  # Vite preview
                "http://localhost:8000"   # Local API testing
            ]
            default_origins.extend(dev_origins)
        elif self.environment == "staging":
            staging_origins = [
                "https://staging.yourdomain.com",
                "https://preview.yourdomain.vercel.app"
            ]
            default_origins.extend(staging_origins)
        
        logger.info(f"Using default CORS origins for {self.environment}: {default_origins}")
        return default_origins
    
    def _get_allowed_methods(self) -> List[str]:
        """Get allowed HTTP methods"""
        return [
            "GET",
            "POST", 
            "PUT",
            "DELETE",
            "OPTIONS",
            "PATCH",
            "HEAD"
        ]
    
    def _get_allowed_headers(self) -> List[str]:
        """Get allowed request headers"""
        return [
            "Authorization",
            "Content-Type",
            "Accept",
            "Origin",
            "User-Agent",
            "DNT",
            "Cache-Control",
            "X-Mx-ReqToken",
            "Keep-Alive",
            "X-Requested-With",
            "If-Modified-Since",
            "X-CSRF-Token",
            "X-API-Key",
            "X-Client-Version"
        ]
    
    def _get_exposed_headers(self) -> List[str]:
        """Get headers to expose to the client"""
        return [
            "Content-Length",
            "Content-Range",
            "X-Content-Range",
            "X-Total-Count",
            "X-Rate-Limit-Remaining",
            "X-Rate-Limit-Reset"
        ]
    
    def get_middleware_config(self) -> Dict[str, Any]:
        """Get CORS middleware configuration dictionary"""
        return {
            "allow_origins": self.allowed_origins,
            "allow_credentials": self.allow_credentials,
            "allow_methods": self.allowed_methods,
            "allow_headers": self.allowed_headers,
            "expose_headers": self.exposed_headers,
            "max_age": self.max_age
        }
    
    def is_origin_allowed(self, origin: str) -> bool:
        """Check if an origin is allowed"""
        return origin in self.allowed_origins
    
    def get_debug_info(self) -> Dict[str, Any]:
        """Get CORS configuration info for debugging"""
        if self.environment == "development":
            return {
                "environment": self.environment,
                "allowed_origins": self.allowed_origins,
                "allowed_methods": self.allowed_methods,
                "allowed_headers": self.allowed_headers,
                "exposed_headers": self.exposed_headers,
                "allow_credentials": self.allow_credentials,
                "max_age": self.max_age,
                "message": "CORS configuration (development mode)"
            }
        else:
            return {
                "environment": self.environment,
                "cors_enabled": True,
                "origins_count": len(self.allowed_origins),
                "methods_count": len(self.allowed_methods),
                "headers_count": len(self.allowed_headers),
                "allow_credentials": self.allow_credentials,
                "message": "CORS configuration (production mode - details hidden)"
            }

# Global CORS configuration instance
_cors_config: CORSConfig = None

def get_cors_config() -> CORSConfig:
    """Get or create CORS configuration instance"""
    global _cors_config
    if _cors_config is None:
        _cors_config = CORSConfig()
    return _cors_config

def validate_cors_origin(origin: str) -> bool:
    """Validate if an origin is allowed by CORS policy"""
    config = get_cors_config()
    return config.is_origin_allowed(origin) 