"""
OpenAI Configuration Module

This module handles OpenAI configuration and authentication for the AI Agent Template.
Provides clean integration with OpenAI services.
"""

import os
import logging
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)


class OpenAIConfig:
    """Configuration class for OpenAI setup."""
    
    def __init__(self):
        """Initialize OpenAI configuration from environment variables."""
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.default_model = os.getenv("OPENAI_DEFAULT_MODEL", "gpt-4o-mini")
        self.organization = os.getenv("OPENAI_ORGANIZATION")  # Optional
        self.project = os.getenv("OPENAI_PROJECT")  # Optional
        
        # Validate configuration
        self._validate_config()
        
        logger.info(f"OpenAI configuration initialized with model: {self.default_model}")
    
    def _validate_config(self) -> None:
        """Validate the OpenAI configuration."""
        if not self.api_key:
            raise ValueError(
                "OPENAI_API_KEY environment variable is required for OpenAI integration"
            )
        
        # Validate model name
        available_models = self.get_available_models()
        if self.default_model not in available_models:
            logger.warning(f"Default model '{self.default_model}' not in known available models. "
                         f"Available: {available_models}")
    
    def get_available_models(self) -> List[str]:
        """Get list of available OpenAI models."""
        return [
            # GPT-4o models (latest and most capable)
            "gpt-4o",
            "gpt-4o-mini",
            
            # GPT-4 Turbo models
            "gpt-4-turbo",
            "gpt-4-turbo-preview",
            
            # GPT-4 models
            "gpt-4",
            "gpt-4-32k",
            
            # GPT-3.5 Turbo models
            "gpt-3.5-turbo",
            "gpt-3.5-turbo-16k",
        ]
    
    def get_model_info(self, model: Optional[str] = None) -> Dict[str, Any]:
        """Get information about a specific model."""
        model_name = model or self.default_model
        
        # Model specifications
        model_specs = {
            "gpt-4o": {
                "description": "Latest GPT-4o model with improved performance",
                "context_window": 128000,
                "max_output": 4096,
                "cost_per_1k_input": 0.005,
                "cost_per_1k_output": 0.015,
                "training_data": "Up to Apr 2024"
            },
            "gpt-4o-mini": {
                "description": "Faster, cheaper GPT-4o model",
                "context_window": 128000,
                "max_output": 16384,
                "cost_per_1k_input": 0.00015,
                "cost_per_1k_output": 0.0006,
                "training_data": "Up to Oct 2023"
            },
            "gpt-4-turbo": {
                "description": "High-performance GPT-4 Turbo model",
                "context_window": 128000,
                "max_output": 4096,
                "cost_per_1k_input": 0.01,
                "cost_per_1k_output": 0.03,
                "training_data": "Up to Apr 2024"
            },
            "gpt-4": {
                "description": "Standard GPT-4 model",
                "context_window": 8192,
                "max_output": 4096,
                "cost_per_1k_input": 0.03,
                "cost_per_1k_output": 0.06,
                "training_data": "Up to Sep 2021"
            },
            "gpt-3.5-turbo": {
                "description": "Fast and efficient GPT-3.5 model",
                "context_window": 16384,
                "max_output": 4096,
                "cost_per_1k_input": 0.0005,
                "cost_per_1k_output": 0.0015,
                "training_data": "Up to Sep 2021"
            }
        }
        
        return model_specs.get(model_name, {
            "description": f"Unknown model: {model_name}",
            "context_window": "Unknown",
            "max_output": "Unknown",
            "cost_per_1k_input": "Unknown",
            "cost_per_1k_output": "Unknown",
            "training_data": "Unknown"
        })
    
    def test_connection(self) -> Dict[str, Any]:
        """
        Test the connection to OpenAI services.
        
        Returns:
            Dictionary with connection test results
        """
        try:
            if not self.api_key:
                return {
                    "status": "error",
                    "error": "No OpenAI API key configured",
                    "service": "OpenAI"
                }
            
            # Basic validation - just check if API key is properly formatted
            if not self.api_key.startswith("sk-"):
                return {
                    "status": "error",
                    "error": "Invalid OpenAI API key format",
                    "service": "OpenAI"
                }
            
            return {
                "status": "success",
                "service": "OpenAI",
                "model": self.default_model,
                "api_key_prefix": self.api_key[:7] + "..." if len(self.api_key) > 7 else "***"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "service": "OpenAI"
            }
    
    def get_client_config(self) -> Dict[str, Any]:
        """Get configuration for OpenAI client initialization."""
        config = {
            "api_key": self.api_key
        }
        
        if self.organization:
            config["organization"] = self.organization
        if self.project:
            config["project"] = self.project
            
        return config


# Global OpenAI configuration instance
openai_config = None


def get_openai_config() -> OpenAIConfig:
    """Get the global OpenAI configuration instance with lazy initialization."""
    global openai_config
    if openai_config is None:
        openai_config = OpenAIConfig()
    return openai_config


def validate_openai_environment() -> Dict[str, Any]:
    """
    Validate that the OpenAI environment is properly configured.
    
    Returns:
        Dictionary with validation results
    """
    try:
        config = get_openai_config()
        
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "config": {
                "default_model": config.default_model,
                "organization": config.organization,
                "project": config.project,
                "api_key_configured": bool(config.api_key)
            }
        }
        
        # Test basic configuration
        config._validate_config()
        
        # Test connection
        connection_result = config.test_connection()
        if connection_result["status"] == "error":
            validation_result["errors"].append(f"OpenAI connection test failed: {connection_result['error']}")
            validation_result["valid"] = False
            
    except Exception as e:
        validation_result = {
            "valid": False,
            "errors": [f"OpenAI configuration validation failed: {str(e)}"],
            "warnings": [],
            "config": {}
        }
    
    return validation_result 