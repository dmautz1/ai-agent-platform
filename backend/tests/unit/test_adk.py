"""
Unit tests for Google ADK configuration management.

Tests cover authentication setup, configuration validation, and agent creation.
"""

import pytest
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import asyncio
from unittest.mock import patch, MagicMock
from google.auth.exceptions import DefaultCredentialsError

from config.adk import (
    ADKConfig,
    get_adk_config,
    validate_adk_config,
    validate_adk_environment,
    create_agent
)


class TestADKConfig:
    """Test cases for ADKConfig class."""
    
    def setup_method(self):
        """Set up test environment before each test."""
        # Clear any existing environment variables
        env_vars = [
            "GOOGLE_GENAI_USE_VERTEXAI",
            "GOOGLE_API_KEY", 
            "GOOGLE_CLOUD_PROJECT",
            "GOOGLE_CLOUD_LOCATION",
            "GOOGLE_DEFAULT_MODEL"
        ]
        for var in env_vars:
            if var in os.environ:
                delattr(os.environ, var)
    
    def test_google_ai_studio_config(self):
        """Test ADK configuration for Google AI Studio."""
        with patch.dict(os.environ, {
            "GOOGLE_GENAI_USE_VERTEXAI": "FALSE",
            "GOOGLE_API_KEY": "test-api-key"
        }):
            config = ADKConfig()
            
            assert not config.use_vertex_ai
            assert config.google_api_key == "test-api-key"
            assert config.default_model == "gemini-2.0-flash"
    
    def test_vertex_ai_config(self):
        """Test ADK configuration for Vertex AI."""
        with patch.dict(os.environ, {
            "GOOGLE_GENAI_USE_VERTEXAI": "TRUE",
            "GOOGLE_CLOUD_PROJECT": "test-project",
            "GOOGLE_CLOUD_LOCATION": "us-west1"
        }):
            with patch('config.adk.default') as mock_default:
                mock_default.return_value = (MagicMock(), "test-project")
                
                config = ADKConfig()
                
                assert config.use_vertex_ai
                assert config.google_cloud_project == "test-project"
                assert config.google_cloud_location == "us-west1"
    
    def test_missing_api_key_validation(self):
        """Test validation failure when API key is missing for Google AI Studio."""
        with patch.dict(os.environ, {
            "GOOGLE_GENAI_USE_VERTEXAI": "FALSE"
        }):
            with pytest.raises(ValueError) as exc_info:
                ADKConfig()
            
            assert "GOOGLE_API_KEY environment variable is required" in str(exc_info.value)
    
    def test_missing_project_validation(self):
        """Test validation failure when project is missing for Vertex AI."""
        with patch.dict(os.environ, {
            "GOOGLE_GENAI_USE_VERTEXAI": "TRUE"
        }):
            with pytest.raises(ValueError) as exc_info:
                ADKConfig()
            
            assert "GOOGLE_CLOUD_PROJECT environment variable is required" in str(exc_info.value)
    
    def test_vertex_ai_credentials_warning(self):
        """Test warning when Vertex AI credentials are not available."""
        with patch.dict(os.environ, {
            "GOOGLE_GENAI_USE_VERTEXAI": "TRUE",
            "GOOGLE_CLOUD_PROJECT": "test-project"
        }):
            with patch('config.adk.default') as mock_default:
                mock_default.side_effect = DefaultCredentialsError("No credentials")
                
                with patch('config.adk.logger') as mock_logger:
                    config = ADKConfig()
                    mock_logger.warning.assert_called_once()
    
    def test_get_model_config_ai_studio(self):
        """Test model configuration for Google AI Studio."""
        with patch.dict(os.environ, {
            "GOOGLE_GENAI_USE_VERTEXAI": "FALSE",
            "GOOGLE_API_KEY": "test-key"
        }):
            config = ADKConfig()
            model_config = config.get_model_config()
            
            assert model_config["model"] == "gemini-2.0-flash"
            assert "project" not in model_config
            assert "location" not in model_config
    
    def test_get_model_config_vertex_ai(self):
        """Test model configuration for Vertex AI."""
        with patch.dict(os.environ, {
            "GOOGLE_GENAI_USE_VERTEXAI": "TRUE",
            "GOOGLE_CLOUD_PROJECT": "test-project",
            "GOOGLE_CLOUD_LOCATION": "us-west1"
        }):
            with patch('config.adk.default') as mock_default:
                mock_default.return_value = (MagicMock(), "test-project")
                
                config = ADKConfig()
                model_config = config.get_model_config()
                
                assert model_config["model"] == "gemini-2.0-flash"
                assert model_config["project"] == "test-project"
                assert model_config["location"] == "us-west1"
    
    @patch('config.adk.Agent')
    def test_create_agent_success(self, mock_agent_class):
        """Test successful agent creation."""
        with patch.dict(os.environ, {
            "GOOGLE_GENAI_USE_VERTEXAI": "FALSE",
            "GOOGLE_API_KEY": "test-key"
        }):
            config = ADKConfig()
            mock_agent_instance = MagicMock()
            mock_agent_class.return_value = mock_agent_instance
            
            tools = [lambda x: x]
            agent = config.create_agent(
                name="test_agent",
                description="Test agent",
                instruction="Test instruction",
                tools=tools
            )
            
            mock_agent_class.assert_called_once()
            assert agent == mock_agent_instance
    
    @patch('config.adk.Agent')
    def test_create_agent_with_custom_model(self, mock_agent_class):
        """Test agent creation with custom model."""
        with patch.dict(os.environ, {
            "GOOGLE_GENAI_USE_VERTEXAI": "FALSE",
            "GOOGLE_API_KEY": "test-key"
        }):
            config = ADKConfig()
            mock_agent_instance = MagicMock()
            mock_agent_class.return_value = mock_agent_instance
            
            agent = config.create_agent(
                name="test_agent",
                description="Test agent",
                instruction="Test instruction",
                model="gemini-1.5-pro"
            )
            
            mock_agent_class.assert_called_once()
            call_args = mock_agent_class.call_args
            assert call_args[1]["model_config"]["model"] == "gemini-1.5-pro"
            assert agent == mock_agent_instance
    
    @patch('config.adk.Agent')
    def test_create_agent_failure(self, mock_agent_class):
        """Test agent creation failure."""
        with patch.dict(os.environ, {
            "GOOGLE_GENAI_USE_VERTEXAI": "FALSE",
            "GOOGLE_API_KEY": "test-key"
        }):
            config = ADKConfig()
            mock_agent_class.side_effect = Exception("Agent creation failed")
            
            with pytest.raises(Exception) as exc_info:
                config.create_agent(
                    name="test_agent",
                    description="Test agent", 
                    instruction="Test instruction"
                )
            
            assert "Agent creation failed" in str(exc_info.value)
    
    def test_get_available_models_ai_studio(self):
        """Test available models for Google AI Studio."""
        with patch.dict(os.environ, {
            "GOOGLE_GENAI_USE_VERTEXAI": "FALSE",
            "GOOGLE_API_KEY": "test-key"
        }):
            config = ADKConfig()
            models = config.get_available_models()
            
            expected_models = [
                "gemini-2.0-flash",
                "gemini-1.5-pro", 
                "gemini-1.5-flash",
                "gemini-1.0-pro"
            ]
            assert models == expected_models
    
    def test_get_available_models_vertex_ai(self):
        """Test available models for Vertex AI."""
        with patch.dict(os.environ, {
            "GOOGLE_GENAI_USE_VERTEXAI": "TRUE",
            "GOOGLE_CLOUD_PROJECT": "test-project"
        }):
            with patch('adk_config.default') as mock_default:
                mock_default.return_value = (MagicMock(), "test-project")
                
                config = ADKConfig()
                models = config.get_available_models()
                
                expected_models = [
                    "gemini-2.0-flash",
                    "gemini-1.5-pro",
                    "gemini-1.5-flash", 
                    "gemini-1.0-pro"
                ]
                assert models == expected_models
    
    @patch('config.adk.ADKConfig.create_agent')
    def test_test_connection_success(self, mock_create_agent):
        """Test successful connection test."""
        with patch.dict(os.environ, {
            "GOOGLE_GENAI_USE_VERTEXAI": "FALSE",
            "GOOGLE_API_KEY": "test-key"
        }):
            config = ADKConfig()
            mock_create_agent.return_value = MagicMock()
            
            result = config.test_connection()
            
            assert result["status"] == "success"
            assert result["service"] == "Google AI Studio"
            assert result["model"] == "gemini-2.0-flash"
            assert result["project"] is None
    
    @patch('config.adk.ADKConfig.create_agent')
    def test_test_connection_failure(self, mock_create_agent):
        """Test connection test failure."""
        with patch.dict(os.environ, {
            "GOOGLE_GENAI_USE_VERTEXAI": "FALSE",
            "GOOGLE_API_KEY": "test-key"
        }):
            config = ADKConfig()
            mock_create_agent.side_effect = Exception("Connection failed")
            
            result = config.test_connection()
            
            assert result["status"] == "error"
            assert "Connection failed" in result["error"]
            assert result["service"] == "Google AI Studio"


class TestGlobalFunctions:
    """Test cases for global functions."""
    
    def setup_method(self):
        """Set up test environment before each test."""
        # Reset global config
        import config.adk
        config.adk.adk_config = None
    
    @patch('config.adk.ADKConfig')
    def test_get_adk_config(self, mock_adk_config_class):
        """Test getting global ADK configuration."""
        mock_config = MagicMock()
        mock_adk_config_class.return_value = mock_config
        
        # This will trigger recreation of global config
        import config.adk
        config.adk.adk_config = config.adk.ADKConfig()
        
        config = get_adk_config()
        assert config is not None
    
    @patch('config.adk.adk_config')
    def test_create_agent_convenience_function(self, mock_global_config):
        """Test convenience function for creating agents."""
        mock_agent = MagicMock()
        mock_global_config.create_agent.return_value = mock_agent
        
        tools = [lambda x: x]
        agent = create_agent(
            name="test_agent",
            description="Test agent",
            instruction="Test instruction", 
            tools=tools,
            model="gemini-1.5-pro"
        )
        
        mock_global_config.create_agent.assert_called_once_with(
            "test_agent",
            "Test agent", 
            "Test instruction",
            tools,
            "gemini-1.5-pro"
        )
        assert agent == mock_agent


class TestEnvironmentValidation:
    """Test cases for environment validation."""
    
    @patch('config.adk.get_adk_config')
    def test_validate_adk_environment_success(self, mock_get_config):
        """Test successful environment validation."""
        mock_config = MagicMock()
        mock_config.use_vertex_ai = False
        mock_config.default_model = "gemini-2.0-flash"
        mock_config.google_cloud_project = None
        mock_config.google_api_key = "test-key"
        mock_config.get_available_models.return_value = ["gemini-2.0-flash"]
        mock_config.test_connection.return_value = {"status": "success", "service": "Google AI Studio"}
        
        mock_get_config.return_value = mock_config
        
        result = validate_adk_environment()
        
        assert result["valid"] is True
        assert len(result["errors"]) == 0
        assert result["config"]["use_vertex_ai"] is False
        assert result["config"]["default_model"] == "gemini-2.0-flash"
    
    @patch('config.adk.get_adk_config')
    def test_validate_adk_environment_connection_failure(self, mock_get_config):
        """Test environment validation with connection failure."""
        mock_config = MagicMock()
        mock_config.use_vertex_ai = False
        mock_config.google_api_key = "test-key"
        mock_config.test_connection.return_value = {"status": "error", "error": "Connection failed"}
        
        mock_get_config.return_value = mock_config
        
        result = validate_adk_environment()
        
        assert result["valid"] is False
        assert "Connection test failed" in result["errors"][0]
    
    @patch('config.adk.get_adk_config')
    def test_validate_adk_environment_missing_config(self, mock_get_config):
        """Test environment validation with missing configuration."""
        mock_config = MagicMock()
        mock_config.use_vertex_ai = True
        mock_config.google_cloud_project = None  # Missing project
        mock_config.test_connection.return_value = {"status": "success"}
        
        mock_get_config.return_value = mock_config
        
        result = validate_adk_environment()
        
        assert result["valid"] is False
        assert "Google Cloud project not configured" in result["errors"]
    
    @patch('config.adk.get_adk_config')
    def test_validate_adk_environment_exception(self, mock_get_config):
        """Test environment validation with exception."""
        mock_get_config.side_effect = Exception("Configuration error")
        
        result = validate_adk_environment()
        
        assert result["valid"] is False
        assert "Configuration error" in result["errors"][0]


if __name__ == "__main__":
    pytest.main([__file__]) 