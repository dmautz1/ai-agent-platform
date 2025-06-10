"""
Google AI Configuration Module

This module handles Google AI configuration and authentication for direct google.generativeai usage.
Provides clean integration with Google AI services without additional framework constraints.
"""

import os
import logging
from typing import Optional, Dict, Any, List
import google.generativeai as genai
from google.auth import default
from google.auth.exceptions import DefaultCredentialsError
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)


class GoogleAIConfig:
    """Configuration class for Google AI setup using direct google.generativeai integration."""
    
    def __init__(self):
        """Initialize Google AI configuration from environment variables."""
        self.use_vertex_ai = os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "FALSE").upper() == "TRUE"
        self.google_api_key = os.getenv("GOOGLE_API_KEY")
        self.google_cloud_project = os.getenv("GOOGLE_CLOUD_PROJECT")
        self.google_cloud_location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
        self.default_model = os.getenv("GOOGLE_DEFAULT_MODEL", "gemini-2.0-flash")
        
        # Initialize Google AI authentication
        self._setup_google_ai_auth()
        
        # Validate configuration
        self._validate_config()
    
    def _setup_google_ai_auth(self) -> None:
        """Setup Google AI authentication for direct google.generativeai usage."""
        try:
            if self.use_vertex_ai:
                # For Vertex AI, configure with project and location
                credentials, project = default()
                if not project:
                    project = self.google_cloud_project
                genai.configure(project=project, location=self.google_cloud_location)
                logger.info(f"Google AI configured for Vertex AI. Project: {project}")
            else:
                # For Google AI Studio, configure with API key
                if self.google_api_key:
                    genai.configure(api_key=self.google_api_key)
                    logger.info("Google AI configured for Google AI Studio")
                else:
                    logger.warning("No Google API key configured")
                    
        except Exception as e:
            logger.error(f"Failed to setup Google AI authentication: {e}")
            raise RuntimeError(f"Google AI authentication setup failed: {str(e)}")
    
    def _validate_config(self) -> None:
        """Validate the Google AI configuration based on the chosen authentication method."""
        if self.use_vertex_ai:
            if not self.google_cloud_project:
                raise ValueError(
                    "GOOGLE_CLOUD_PROJECT environment variable is required when using Vertex AI"
                )
            # Check if we can authenticate with Google Cloud
            try:
                credentials, project = default()
                if not project:
                    project = self.google_cloud_project
                logger.info(f"Successfully authenticated with Google Cloud. Project: {project}")
            except DefaultCredentialsError as e:
                logger.warning(
                    f"Google Cloud credentials not found: {e}. "
                    "Make sure to run 'gcloud auth login' or set up service account credentials."
                )
        else:
            if not self.google_api_key:
                raise ValueError(
                    "GOOGLE_API_KEY environment variable is required when using Google AI Studio"
                )
    
    def get_model_config(self) -> Dict[str, Any]:
        """Get model configuration for direct google.generativeai usage."""
        config = {
            "model": self.default_model,
        }
        
        if self.use_vertex_ai:
            config.update({
                "project": self.google_cloud_project,
                "location": self.google_cloud_location,
            })
        
        return config
    
    def get_generative_model(self, model: Optional[str] = None) -> genai.GenerativeModel:
        """
        Get a configured GenerativeModel instance for direct usage.
        
        Args:
            model: Optional model override
            
        Returns:
            Configured GenerativeModel instance
        """
        model_name = model or self.default_model
        
        try:
            # Create GenerativeModel using direct google.generativeai
            model_instance = genai.GenerativeModel(model_name)
            
            logger.info(f"Created GenerativeModel '{model_name}'")
            return model_instance
            
        except Exception as e:
            logger.error(f"Failed to create GenerativeModel '{model_name}': {e}")
            raise RuntimeError(f"Failed to create GenerativeModel: {str(e)}")
    
    def get_available_models(self) -> List[str]:
        """Get list of available models based on configuration."""
        if self.use_vertex_ai:
            # Vertex AI supported models
            return [
                "gemini-2.0-flash",
                "gemini-1.5-pro",
                "gemini-1.5-flash",
                "gemini-1.0-pro"
            ]
        else:
            # Google AI Studio supported models
            return [
                "gemini-2.0-flash",
                "gemini-1.5-pro",
                "gemini-1.5-flash",
                "gemini-1.0-pro"
            ]
    
    def test_connection(self) -> Dict[str, Any]:
        """
        Test the connection to Google AI services using direct google.generativeai.
        
        Returns:
            Dictionary with connection test results
        """
        try:
            # Create a simple test model to validate setup
            test_model = self.get_generative_model()
            
            return {
                "status": "success",
                "service": "Vertex AI" if self.use_vertex_ai else "Google AI Studio",
                "model": self.default_model,
                "project": self.google_cloud_project if self.use_vertex_ai else None
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "service": "Vertex AI" if self.use_vertex_ai else "Google AI Studio"
            }


# Global Google AI configuration instance
google_ai_config = None


def get_google_ai_config() -> GoogleAIConfig:
    """Get the global Google AI configuration instance with lazy initialization."""
    global google_ai_config
    if google_ai_config is None:
        google_ai_config = GoogleAIConfig()
    return google_ai_config


def get_generative_model(model: Optional[str] = None) -> genai.GenerativeModel:
    """
    Convenience function to get a GenerativeModel using global configuration.
    
    Args:
        model: Optional model override
        
    Returns:
        Configured GenerativeModel instance
    """
    return google_ai_config.get_generative_model(model)


def validate_google_ai_environment() -> Dict[str, Any]:
    """
    Validate that the Google AI environment is properly configured.
    
    Returns:
        Dictionary with validation results
    """
    try:
        config = get_google_ai_config()
        
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "config": {
                "use_vertex_ai": config.use_vertex_ai,
                "default_model": config.default_model,
                "google_cloud_project": config.google_cloud_project,
                "google_cloud_location": config.google_cloud_location
            }
        }
        
        # Test basic configuration
        config._validate_config()
        
        # Test connection using direct google.generativeai
        connection_result = config.test_connection()
        if connection_result["status"] == "error":
            validation_result["errors"].append(f"Google AI connection test failed: {connection_result['error']}")
            validation_result["valid"] = False
            
    except Exception as e:
        validation_result = {
            "valid": False,
            "errors": [f"Google AI configuration validation failed: {str(e)}"],
            "warnings": [],
            "config": {}
        }
    
    return validation_result


def get_environment_info() -> Dict[str, Any]:
    """
    Get information about the current Google AI environment setup.
    
    Returns:
        Dictionary with environment information
    """
    return {
        "google_ai_configured": True,
        "authentication_method": "Vertex AI" if google_ai_config.use_vertex_ai else "Google AI Studio",
        "default_model": google_ai_config.default_model,
        "available_models": google_ai_config.get_available_models(),
        "project": google_ai_config.google_cloud_project if google_ai_config.use_vertex_ai else None,
        "location": google_ai_config.google_cloud_location if google_ai_config.use_vertex_ai else None,
        "documentation": "https://ai.google.dev/gemini-api/docs"
    } 