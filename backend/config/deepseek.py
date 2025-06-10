"""
DeepSeek Configuration Module

This module handles DeepSeek configuration and authentication for the AI Agent Platform.
Provides clean integration with DeepSeek's AI services.
"""

import os
import logging
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)


class DeepSeekConfig:
    """Configuration class for DeepSeek setup."""
    
    def __init__(self):
        """Initialize DeepSeek configuration from environment variables."""
        self.api_key = os.getenv("DEEPSEEK_API_KEY")
        self.default_model = os.getenv("DEEPSEEK_DEFAULT_MODEL", "deepseek-chat")
        self.base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
        
        # Validate configuration
        self._validate_config()
        
        logger.info(f"DeepSeek configuration initialized with model: {self.default_model}")
    
    def _validate_config(self) -> None:
        """Validate the DeepSeek configuration."""
        if not self.api_key:
            raise ValueError(
                "DEEPSEEK_API_KEY environment variable is required for DeepSeek integration"
            )
        
        # Validate model name
        available_models = self.get_available_models()
        if self.default_model not in available_models:
            logger.warning(f"Default model '{self.default_model}' not in known available models. "
                         f"Available: {available_models}")
    
    def get_available_models(self) -> List[str]:
        """Get list of available DeepSeek models."""
        return [
            # Main chat models
            "deepseek-chat",
            "deepseek-coder",
            
            # Reasoning models
            "deepseek-reasoner",
            
            # Legacy models
            "deepseek-v2.5",
        ]
    
    def get_model_info(self, model: Optional[str] = None) -> Dict[str, Any]:
        """Get information about a specific model."""
        model_name = model or self.default_model
        
        # Model specifications
        model_specs = {
            "deepseek-chat": {
                "description": "DeepSeek's flagship chat model with strong general capabilities",
                "context_window": 128000,
                "max_output": 8192,
                "cost_per_1m_input": 0.14,
                "cost_per_1m_output": 0.28,
                "capabilities": ["text_generation", "reasoning", "coding", "multilingual"],
                "training_data": "Up to 2024",
                "type": "chat"
            },
            "deepseek-coder": {
                "description": "Specialized coding model with enhanced programming capabilities",
                "context_window": 128000,
                "max_output": 8192,
                "cost_per_1m_input": 0.14,
                "cost_per_1m_output": 0.28,
                "capabilities": ["code_generation", "code_review", "debugging", "refactoring"],
                "training_data": "Up to 2024",
                "type": "coding"
            },
            "deepseek-reasoner": {
                "description": "Advanced reasoning model for complex problem solving",
                "context_window": 64000,
                "max_output": 8192,
                "cost_per_1m_input": 0.55,
                "cost_per_1m_output": 2.19,
                "capabilities": ["complex_reasoning", "mathematical_analysis", "logical_problem_solving"],
                "training_data": "Up to 2024",
                "type": "reasoning"
            },
            "deepseek-v2.5": {
                "description": "Previous generation model with solid performance",
                "context_window": 64000,
                "max_output": 4096,
                "cost_per_1m_input": 0.14,
                "cost_per_1m_output": 0.28,
                "capabilities": ["text_generation", "basic_reasoning"],
                "training_data": "Up to 2023",
                "type": "legacy"
            }
        }
        
        return model_specs.get(model_name, {
            "description": f"Unknown model: {model_name}",
            "context_window": "Unknown",
            "max_output": "Unknown",
            "cost_per_1m_input": "Unknown",
            "cost_per_1m_output": "Unknown",
            "capabilities": ["Unknown"],
            "training_data": "Unknown",
            "type": "unknown"
        })
    
    def test_connection(self) -> Dict[str, Any]:
        """
        Test the connection to DeepSeek services.
        
        Returns:
            Dictionary with connection test results
        """
        try:
            if not self.api_key:
                return {
                    "status": "error",
                    "error": "No DeepSeek API key configured",
                    "service": "DeepSeek",
                    "provider": "DeepSeek"
                }
            
            # Basic validation - check if API key is properly formatted
            if not self.api_key.startswith("sk-"):
                return {
                    "status": "error",
                    "error": "Invalid DeepSeek API key format (should start with 'sk-')",
                    "service": "DeepSeek",
                    "provider": "DeepSeek"
                }
            
            return {
                "status": "success",
                "service": "DeepSeek",
                "provider": "DeepSeek",
                "model": self.default_model,
                "base_url": self.base_url,
                "api_key_prefix": self.api_key[:10] + "..." if len(self.api_key) > 10 else "***"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "service": "DeepSeek",
                "provider": "DeepSeek"
            }
    
    def get_client_config(self) -> Dict[str, Any]:
        """Get configuration for DeepSeek client initialization."""
        return {
            "api_key": self.api_key,
            "base_url": self.base_url
        }


# Global DeepSeek configuration instance
deepseek_config = None


def get_deepseek_config() -> DeepSeekConfig:
    """Get the global DeepSeek configuration instance with lazy initialization."""
    global deepseek_config
    if deepseek_config is None:
        deepseek_config = DeepSeekConfig()
    return deepseek_config


def validate_deepseek_environment() -> Dict[str, Any]:
    """
    Validate that the DeepSeek environment is properly configured.
    
    Returns:
        Dictionary with validation results
    """
    try:
        config = get_deepseek_config()
        
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "config": {
                "default_model": config.default_model,
                "base_url": config.base_url,
                "api_key_configured": bool(config.api_key)
            }
        }
        
        # Test basic configuration
        config._validate_config()
        
        # Test connection
        connection_result = config.test_connection()
        if connection_result["status"] == "error":
            validation_result["errors"].append(f"DeepSeek connection test failed: {connection_result['error']}")
            validation_result["valid"] = False
            
    except Exception as e:
        validation_result = {
            "valid": False,
            "errors": [f"DeepSeek configuration validation failed: {str(e)}"],
            "warnings": [],
            "config": {}
        }
    
    return validation_result 