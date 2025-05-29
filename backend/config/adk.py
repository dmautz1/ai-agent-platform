"""
Google ADK Configuration Module

This module handles Google ADK configuration, authentication, and model setup.
It supports both Google AI Studio and Google Cloud Vertex AI configurations.
"""

import os
import logging
from typing import Optional, Dict, Any
from google.adk.agents import Agent
from google.auth import default
from google.auth.exceptions import DefaultCredentialsError

logger = logging.getLogger(__name__)


class ADKConfig:
    """Configuration class for Google ADK setup and authentication."""
    
    def __init__(self):
        """Initialize ADK configuration from environment variables."""
        self.use_vertex_ai = os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "FALSE").upper() == "TRUE"
        self.google_api_key = os.getenv("GOOGLE_API_KEY")
        self.google_cloud_project = os.getenv("GOOGLE_CLOUD_PROJECT")
        self.google_cloud_location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
        self.default_model = os.getenv("GOOGLE_DEFAULT_MODEL", "gemini-2.0-flash")
        
        # Validate configuration
        self._validate_config()
    
    def _validate_config(self) -> None:
        """Validate the ADK configuration based on the chosen authentication method."""
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
        """Get model configuration for ADK agents."""
        config = {
            "model": self.default_model,
        }
        
        if self.use_vertex_ai:
            config.update({
                "project": self.google_cloud_project,
                "location": self.google_cloud_location,
            })
        
        return config
    
    def create_agent(
        self,
        name: str,
        description: str,
        instruction: str,
        tools: Optional[list] = None,
        model: Optional[str] = None
    ) -> Agent:
        """
        Create a Google ADK agent with proper configuration.
        
        Args:
            name: Name of the agent
            description: Description of the agent's purpose
            instruction: System instruction for the agent
            tools: List of tools/functions available to the agent
            model: Optional model override
            
        Returns:
            Configured Agent instance
        """
        agent_model = model or self.default_model
        
        try:
            agent = Agent(
                name=name,
                model=agent_model,
                description=description,
                instruction=instruction,
                tools=tools or []
            )
            
            logger.info(f"Created ADK agent '{name}' with model '{agent_model}'")
            return agent
            
        except Exception as e:
            logger.error(f"Failed to create ADK agent '{name}': {e}")
            raise
    
    def get_available_models(self) -> list:
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
        Test the connection to Google AI services.
        
        Returns:
            Dictionary with connection test results
        """
        try:
            # Create a simple test agent
            test_agent = self.create_agent(
                name="test_agent",
                description="Test agent for connection validation",
                instruction="You are a test agent. Respond with 'Connection successful' when asked."
            )
            
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


# Global ADK configuration instance
adk_config = ADKConfig()


def get_adk_config() -> ADKConfig:
    """Get the global ADK configuration instance."""
    return adk_config


def create_agent(
    name: str,
    description: str,
    instruction: str,
    tools: Optional[list] = None,
    model: Optional[str] = None
) -> Agent:
    """
    Convenience function to create an ADK agent using global configuration.
    
    Args:
        name: Name of the agent
        description: Description of the agent's purpose
        instruction: System instruction for the agent
        tools: List of tools/functions available to the agent
        model: Optional model override
        
    Returns:
        Configured Agent instance
    """
    return adk_config.create_agent(name, description, instruction, tools, model)


# ADK-specific environment validation
def validate_adk_environment() -> Dict[str, Any]:
    """
    Validate that the ADK environment is properly configured.
    
    Returns:
        Dictionary with validation results
    """
    validation_result = {
        "valid": True,
        "errors": [],
        "warnings": [],
        "config": {}
    }
    
    try:
        config = get_adk_config()
        
        # Test connection
        connection_test = config.test_connection()
        
        if connection_test["status"] == "error":
            validation_result["valid"] = False
            validation_result["errors"].append(f"Connection test failed: {connection_test['error']}")
        
        validation_result["config"] = {
            "use_vertex_ai": config.use_vertex_ai,
            "default_model": config.default_model,
            "available_models": config.get_available_models(),
            "connection_test": connection_test
        }
        
        if config.use_vertex_ai and not config.google_cloud_project:
            validation_result["valid"] = False
            validation_result["errors"].append("Google Cloud project not configured")
        
        if not config.use_vertex_ai and not config.google_api_key:
            validation_result["valid"] = False
            validation_result["errors"].append("Google API key not configured")
            
    except Exception as e:
        validation_result["valid"] = False
        validation_result["errors"].append(f"Configuration error: {str(e)}")
    
    return validation_result 