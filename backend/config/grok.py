"""
Grok Configuration Module

This module handles Grok (xAI) configuration and authentication for the AI Agent Template.
Provides clean integration with xAI's Grok services.
"""

import os
import logging
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)


class GrokConfig:
    """Configuration class for Grok (xAI) setup."""
    
    def __init__(self):
        """Initialize Grok configuration from environment variables."""
        self.api_key = os.getenv("GROK_API_KEY")
        self.base_url = os.getenv("GROK_BASE_URL", "https://api.x.ai/v1")
        self.default_model = os.getenv("GROK_DEFAULT_MODEL", "grok-beta")
        self.organization = os.getenv("GROK_ORGANIZATION")  # Optional
        
        # Validate configuration
        self._validate_config()
        
        logger.info(f"Grok configuration initialized with model: {self.default_model}")
    
    def _validate_config(self) -> None:
        """Validate the Grok configuration."""
        if not self.api_key:
            raise ValueError(
                "GROK_API_KEY environment variable is required for Grok integration"
            )
        
        # Validate model name
        available_models = self.get_available_models()
        if self.default_model not in available_models:
            logger.warning(f"Default model '{self.default_model}' not in known available models. "
                         f"Available: {available_models}")
    
    def get_available_models(self) -> List[str]:
        """Get list of available Grok models."""
        return [
            # Grok models (xAI)
            "grok-beta",
            "grok-vision-beta",
        ]
    
    def get_model_info(self, model: Optional[str] = None) -> Dict[str, Any]:
        """Get information about a specific model."""
        model_name = model or self.default_model
        
        # Model specifications
        model_specs = {
            "grok-beta": {
                "description": "Grok's main language model with real-time information access",
                "context_window": 131072,
                "max_output": 4096,
                "capabilities": ["text_generation", "real_time_data", "web_search"],
                "training_data": "Real-time web data"
            },
            "grok-vision-beta": {
                "description": "Grok model with vision capabilities for image understanding",
                "context_window": 131072,
                "max_output": 4096,
                "capabilities": ["text_generation", "image_understanding", "real_time_data"],
                "training_data": "Real-time web data + vision training"
            }
        }
        
        return model_specs.get(model_name, {
            "description": f"Unknown model: {model_name}",
            "context_window": "Unknown",
            "max_output": "Unknown",
            "capabilities": ["Unknown"],
            "training_data": "Unknown"
        })
    
    def test_connection(self) -> Dict[str, Any]:
        """
        Test the connection to Grok services.
        
        Returns:
            Dictionary with connection test results
        """
        try:
            if not self.api_key:
                return {
                    "status": "error",
                    "error": "No Grok API key configured",
                    "service": "Grok",
                    "provider": "xAI"
                }
            
            # Basic validation - check if API key is properly formatted
            if not self.api_key.startswith("xai-"):
                return {
                    "status": "error",
                    "error": "Invalid Grok API key format (should start with 'xai-')",
                    "service": "Grok",
                    "provider": "xAI"
                }
            
            return {
                "status": "success",
                "service": "Grok",
                "provider": "xAI",
                "model": self.default_model,
                "base_url": self.base_url,
                "api_key_prefix": self.api_key[:7] + "..." if len(self.api_key) > 7 else "***"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "service": "Grok",
                "provider": "xAI"
            }
    
    def get_client_config(self) -> Dict[str, Any]:
        """Get configuration for Grok client initialization."""
        config = {
            "api_key": self.api_key,
            "base_url": self.base_url
        }
        
        if self.organization:
            config["organization"] = self.organization
            
        return config


# Global Grok configuration instance
grok_config = None


def get_grok_config() -> GrokConfig:
    """Get the global Grok configuration instance with lazy initialization."""
    global grok_config
    if grok_config is None:
        grok_config = GrokConfig()
    return grok_config


def validate_grok_environment() -> Dict[str, Any]:
    """
    Validate that the Grok environment is properly configured.
    
    Returns:
        Dictionary with validation results
    """
    try:
        config = get_grok_config()
        
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "config": {
                "default_model": config.default_model,
                "base_url": config.base_url,
                "organization": config.organization,
                "api_key_configured": bool(config.api_key)
            }
        }
        
        # Test basic configuration
        config._validate_config()
        
        # Test connection
        connection_result = config.test_connection()
        if connection_result["status"] == "error":
            validation_result["errors"].append(f"Grok connection test failed: {connection_result['error']}")
            validation_result["valid"] = False
            
    except Exception as e:
        validation_result = {
            "valid": False,
            "errors": [f"Grok configuration validation failed: {str(e)}"],
            "warnings": [],
            "config": {}
        }
    
    return validation_result 