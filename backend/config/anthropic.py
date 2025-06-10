"""
Anthropic Configuration Module

This module handles Anthropic (Claude) configuration and authentication for the AI Agent Platform.
Provides clean integration with Anthropic's Claude services.
"""

import os
import logging
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)


class AnthropicConfig:
    """Configuration class for Anthropic (Claude) setup."""
    
    def __init__(self):
        """Initialize Anthropic configuration from environment variables."""
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        self.default_model = os.getenv("ANTHROPIC_DEFAULT_MODEL", "claude-3-5-sonnet-20241022")
        
        # Validate configuration
        self._validate_config()
        
        logger.info(f"Anthropic configuration initialized with model: {self.default_model}")
    
    def _validate_config(self) -> None:
        """Validate the Anthropic configuration."""
        if not self.api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY environment variable is required for Anthropic integration"
            )
        
        # Validate model name
        available_models = self.get_available_models()
        if self.default_model not in available_models:
            logger.warning(f"Default model '{self.default_model}' not in known available models. "
                         f"Available: {available_models}")
    
    def get_available_models(self) -> List[str]:
        """Get list of available Anthropic models."""
        return [
            # Claude 3.5 models (most capable)
            "claude-3-5-sonnet-20241022",
            "claude-3-5-haiku-20241022",
            
            # Claude 3 models
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229", 
            "claude-3-haiku-20240307",
        ]
    
    def get_model_info(self, model: Optional[str] = None) -> Dict[str, Any]:
        """Get information about a specific model."""
        model_name = model or self.default_model
        
        # Model specifications
        model_specs = {
            "claude-3-5-sonnet-20241022": {
                "description": "Claude 3.5 Sonnet - Most capable model with improved performance",
                "context_window": 200000,
                "max_output": 8192,
                "cost_per_1m_input": 3.00,
                "cost_per_1m_output": 15.00,
                "capabilities": ["text_generation", "reasoning", "coding", "analysis"],
                "training_data": "Up to Apr 2024"
            },
            "claude-3-5-haiku-20241022": {
                "description": "Claude 3.5 Haiku - Fastest model with good performance",
                "context_window": 200000,
                "max_output": 8192,
                "cost_per_1m_input": 0.25,
                "cost_per_1m_output": 1.25,
                "capabilities": ["text_generation", "reasoning", "fast_responses"],
                "training_data": "Up to Jul 2024"
            },
            "claude-3-opus-20240229": {
                "description": "Claude 3 Opus - Most powerful model for complex tasks",
                "context_window": 200000,
                "max_output": 4096,
                "cost_per_1m_input": 15.00,
                "cost_per_1m_output": 75.00,
                "capabilities": ["text_generation", "complex_reasoning", "analysis"],
                "training_data": "Up to Aug 2023"
            },
            "claude-3-sonnet-20240229": {
                "description": "Claude 3 Sonnet - Balanced model for most tasks",
                "context_window": 200000,
                "max_output": 4096,
                "cost_per_1m_input": 3.00,
                "cost_per_1m_output": 15.00,
                "capabilities": ["text_generation", "reasoning", "balanced_performance"],
                "training_data": "Up to Aug 2023"
            },
            "claude-3-haiku-20240307": {
                "description": "Claude 3 Haiku - Fast and efficient model",
                "context_window": 200000,
                "max_output": 4096,
                "cost_per_1m_input": 0.25,
                "cost_per_1m_output": 1.25,
                "capabilities": ["text_generation", "fast_responses"],
                "training_data": "Up to Aug 2023"
            }
        }
        
        return model_specs.get(model_name, {
            "description": f"Unknown model: {model_name}",
            "context_window": "Unknown",
            "max_output": "Unknown",
            "cost_per_1m_input": "Unknown",
            "cost_per_1m_output": "Unknown",
            "capabilities": ["Unknown"],
            "training_data": "Unknown"
        })
    
    def test_connection(self) -> Dict[str, Any]:
        """
        Test the connection to Anthropic services.
        
        Returns:
            Dictionary with connection test results
        """
        try:
            if not self.api_key:
                return {
                    "status": "error",
                    "error": "No Anthropic API key configured",
                    "service": "Anthropic",
                    "provider": "Anthropic"
                }
            
            # Basic validation - check if API key is properly formatted
            if not self.api_key.startswith("sk-ant-"):
                return {
                    "status": "error",
                    "error": "Invalid Anthropic API key format (should start with 'sk-ant-')",
                    "service": "Anthropic",
                    "provider": "Anthropic"
                }
            
            return {
                "status": "success",
                "service": "Anthropic",
                "provider": "Anthropic",
                "model": self.default_model,
                "api_key_prefix": self.api_key[:10] + "..." if len(self.api_key) > 10 else "***"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "service": "Anthropic",
                "provider": "Anthropic"
            }
    
    def get_client_config(self) -> Dict[str, Any]:
        """Get configuration for Anthropic client initialization."""
        return {
            "api_key": self.api_key
        }


# Global Anthropic configuration instance
anthropic_config = None


def get_anthropic_config() -> AnthropicConfig:
    """Get the global Anthropic configuration instance with lazy initialization."""
    global anthropic_config
    if anthropic_config is None:
        anthropic_config = AnthropicConfig()
    return anthropic_config


def validate_anthropic_environment() -> Dict[str, Any]:
    """
    Validate that the Anthropic environment is properly configured.
    
    Returns:
        Dictionary with validation results
    """
    try:
        config = get_anthropic_config()
        
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "config": {
                "default_model": config.default_model,
                "api_key_configured": bool(config.api_key)
            }
        }
        
        # Test basic configuration
        config._validate_config()
        
        # Test connection
        connection_result = config.test_connection()
        if connection_result["status"] == "error":
            validation_result["errors"].append(f"Anthropic connection test failed: {connection_result['error']}")
            validation_result["valid"] = False
            
    except Exception as e:
        validation_result = {
            "valid": False,
            "errors": [f"Anthropic configuration validation failed: {str(e)}"],
            "warnings": [],
            "config": {}
        }
    
    return validation_result 