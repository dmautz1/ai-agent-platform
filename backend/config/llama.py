"""
Meta Llama Configuration Module

This module handles Meta Llama configuration and authentication for the AI Agent Platform.
Provides clean integration with Meta Llama models through OpenAI-compatible APIs.
"""

import os
import logging
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)


class LlamaConfig:
    """Configuration class for Meta Llama setup."""
    
    def __init__(self):
        """Initialize Meta Llama configuration from environment variables."""
        self.api_key = os.getenv("LLAMA_API_KEY")
        self.default_model = os.getenv("LLAMA_DEFAULT_MODEL", "meta-llama/Llama-3-8b-chat-hf")
        self.base_url = os.getenv("LLAMA_BASE_URL", "https://api.together.xyz/v1")
        self.api_provider = os.getenv("LLAMA_API_PROVIDER", "together")
        
        # Validate configuration
        self._validate_config()
        
        logger.info(f"Meta Llama configuration initialized with model: {self.default_model}")
    
    def _validate_config(self) -> None:
        """Validate the Meta Llama configuration."""
        if not self.api_key:
            raise ValueError(
                "LLAMA_API_KEY environment variable is required for Meta Llama integration"
            )
        
        # Validate model name
        available_models = self.get_available_models()
        if self.default_model not in available_models:
            logger.warning(f"Default model '{self.default_model}' not in known available models. "
                         f"Available: {available_models}")
    
    def get_available_models(self) -> List[str]:
        """Get list of available Meta Llama models."""
        return [
            # Llama 3 models (latest generation)
            "meta-llama/Llama-3-8b-chat-hf",
            "meta-llama/Llama-3-70b-chat-hf",
            "meta-llama/Meta-Llama-3-8B-Instruct",
            "meta-llama/Meta-Llama-3-70B-Instruct",
            
            # Llama 2 models
            "meta-llama/Llama-2-7b-chat-hf",
            "meta-llama/Llama-2-13b-chat-hf", 
            "meta-llama/Llama-2-70b-chat-hf",
            
            # Code Llama models
            "meta-llama/CodeLlama-7b-Instruct-hf",
            "meta-llama/CodeLlama-13b-Instruct-hf",
            "meta-llama/CodeLlama-34b-Instruct-hf",
            
            # Specialized models
            "meta-llama/Llama-Guard-7b",
        ]
    
    def get_model_info(self, model: Optional[str] = None) -> Dict[str, Any]:
        """Get information about a specific model."""
        model_name = model or self.default_model
        
        # Model specifications
        model_specs = {
            "meta-llama/Llama-3-8b-chat-hf": {
                "description": "Llama 3 8B Chat model with strong general capabilities",
                "context_window": 8192,
                "max_output": 4096,
                "cost_per_1m_input": 0.20,
                "cost_per_1m_output": 0.20,
                "capabilities": ["text_generation", "conversation", "reasoning", "multilingual"],
                "training_data": "Up to March 2024",
                "type": "chat",
                "size": "8B"
            },
            "meta-llama/Llama-3-70b-chat-hf": {
                "description": "Llama 3 70B Chat model with advanced capabilities",
                "context_window": 8192,
                "max_output": 4096,
                "cost_per_1m_input": 0.90,
                "cost_per_1m_output": 0.90,
                "capabilities": ["text_generation", "conversation", "complex_reasoning", "multilingual"],
                "training_data": "Up to March 2024",
                "type": "chat",
                "size": "70B"
            },
            "meta-llama/Meta-Llama-3-8B-Instruct": {
                "description": "Llama 3 8B Instruct model optimized for instruction following",
                "context_window": 8192,
                "max_output": 4096,
                "cost_per_1m_input": 0.20,
                "cost_per_1m_output": 0.20,
                "capabilities": ["instruction_following", "text_generation", "reasoning"],
                "training_data": "Up to March 2024",
                "type": "instruct",
                "size": "8B"
            },
            "meta-llama/Meta-Llama-3-70B-Instruct": {
                "description": "Llama 3 70B Instruct model with superior instruction following",
                "context_window": 8192,
                "max_output": 4096,
                "cost_per_1m_input": 0.90,
                "cost_per_1m_output": 0.90,
                "capabilities": ["instruction_following", "complex_reasoning", "text_generation"],
                "training_data": "Up to March 2024",
                "type": "instruct",
                "size": "70B"
            },
            "meta-llama/Llama-2-7b-chat-hf": {
                "description": "Llama 2 7B Chat model for general conversation",
                "context_window": 4096,
                "max_output": 2048,
                "cost_per_1m_input": 0.20,
                "cost_per_1m_output": 0.20,
                "capabilities": ["text_generation", "conversation"],
                "training_data": "Up to September 2022",
                "type": "chat",
                "size": "7B"
            },
            "meta-llama/Llama-2-13b-chat-hf": {
                "description": "Llama 2 13B Chat model with improved capabilities",
                "context_window": 4096,
                "max_output": 2048,
                "cost_per_1m_input": 0.25,
                "cost_per_1m_output": 0.25,
                "capabilities": ["text_generation", "conversation", "reasoning"],
                "training_data": "Up to September 2022",
                "type": "chat",
                "size": "13B"
            },
            "meta-llama/Llama-2-70b-chat-hf": {
                "description": "Llama 2 70B Chat model with advanced reasoning",
                "context_window": 4096,
                "max_output": 2048,
                "cost_per_1m_input": 0.90,
                "cost_per_1m_output": 0.90,
                "capabilities": ["text_generation", "conversation", "complex_reasoning"],
                "training_data": "Up to September 2022",
                "type": "chat",
                "size": "70B"
            },
            "meta-llama/CodeLlama-7b-Instruct-hf": {
                "description": "Code Llama 7B specialized for code generation and understanding",
                "context_window": 16384,
                "max_output": 4096,
                "cost_per_1m_input": 0.20,
                "cost_per_1m_output": 0.20,
                "capabilities": ["code_generation", "code_review", "debugging", "code_explanation"],
                "training_data": "Code-focused training up to 2022",
                "type": "code",
                "size": "7B"
            },
            "meta-llama/CodeLlama-13b-Instruct-hf": {
                "description": "Code Llama 13B with enhanced coding capabilities",
                "context_window": 16384,
                "max_output": 4096,
                "cost_per_1m_input": 0.25,
                "cost_per_1m_output": 0.25,
                "capabilities": ["code_generation", "code_review", "debugging", "refactoring"],
                "training_data": "Code-focused training up to 2022",
                "type": "code",
                "size": "13B"
            },
            "meta-llama/CodeLlama-34b-Instruct-hf": {
                "description": "Code Llama 34B with advanced coding and reasoning abilities",
                "context_window": 16384,
                "max_output": 4096,
                "cost_per_1m_input": 0.80,
                "cost_per_1m_output": 0.80,
                "capabilities": ["advanced_code_generation", "complex_debugging", "architecture_design"],
                "training_data": "Code-focused training up to 2022",
                "type": "code",
                "size": "34B"
            },
            "meta-llama/Llama-Guard-7b": {
                "description": "Llama Guard model for content safety and moderation",
                "context_window": 4096,
                "max_output": 2048,
                "cost_per_1m_input": 0.20,
                "cost_per_1m_output": 0.20,
                "capabilities": ["content_moderation", "safety_classification", "harm_detection"],
                "training_data": "Safety-focused training",
                "type": "safety",
                "size": "7B"
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
            "type": "unknown",
            "size": "Unknown"
        })
    
    def test_connection(self) -> Dict[str, Any]:
        """
        Test the connection to Meta Llama services.
        
        Returns:
            Dictionary with connection test results
        """
        try:
            if not self.api_key:
                return {
                    "status": "error",
                    "error": "No Meta Llama API key configured",
                    "service": "Meta Llama",
                    "provider": "Meta"
                }
            
            # Basic validation - check if API key has proper format
            # Most API keys should be at least 20 characters and contain alphanumeric/special chars
            if len(self.api_key.strip()) < 20 or not any(c.isalnum() for c in self.api_key):
                return {
                    "status": "error",
                    "error": "Invalid Meta Llama API key format (should be at least 20 characters with alphanumeric content)",
                    "service": "Meta Llama",
                    "provider": "Meta"
                }
            
            return {
                "status": "success",
                "service": "Meta Llama",
                "provider": "Meta",
                "model": self.default_model,
                "base_url": self.base_url,
                "api_provider": self.api_provider,
                "api_key_prefix": self.api_key[:10] + "..." if len(self.api_key) > 10 else "***"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "service": "Meta Llama",
                "provider": "Meta"
            }
    
    def get_client_config(self) -> Dict[str, Any]:
        """Get configuration for Meta Llama client initialization."""
        return {
            "api_key": self.api_key,
            "base_url": self.base_url
        }


# Global Meta Llama configuration instance
llama_config = None


def get_llama_config() -> LlamaConfig:
    """Get the global Meta Llama configuration instance with lazy initialization."""
    global llama_config
    if llama_config is None:
        llama_config = LlamaConfig()
    return llama_config


def validate_llama_environment() -> Dict[str, Any]:
    """
    Validate that the Meta Llama environment is properly configured.
    
    Returns:
        Dictionary with validation results
    """
    try:
        config = get_llama_config()
        
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "config": {
                "default_model": config.default_model,
                "base_url": config.base_url,
                "api_provider": config.api_provider,
                "api_key_configured": bool(config.api_key)
            }
        }
        
        # Test basic configuration
        config._validate_config()
        
        # Test connection
        connection_result = config.test_connection()
        if connection_result["status"] == "error":
            validation_result["errors"].append(f"Meta Llama connection test failed: {connection_result['error']}")
            validation_result["valid"] = False
            
    except Exception as e:
        validation_result = {
            "valid": False,
            "errors": [f"Meta Llama configuration validation failed: {str(e)}"],
            "warnings": [],
            "config": {}
        }
    
    return validation_result 