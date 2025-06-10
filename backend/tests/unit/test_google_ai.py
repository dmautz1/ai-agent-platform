"""
Unit tests for Google AI configuration
Tests the Google AI configuration module functionality including authentication setup,
model management, and environment validation.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import os
from typing import Dict, Any, Optional

# Test imports
from config.google_ai import (
    GoogleAIConfig,
    get_google_ai_config,
    validate_google_ai_environment,
    get_generative_model,
    get_environment_info
)

class TestGoogleAIConfig(unittest.TestCase):
    """Test cases for GoogleAIConfig class functionality"""
    
    def setUp(self):
        """Set up test environment"""
        # Store original env vars
        self.original_env = {
            'GOOGLE_API_KEY': os.getenv('GOOGLE_API_KEY'),
            'GOOGLE_CLOUD_PROJECT': os.getenv('GOOGLE_CLOUD_PROJECT'),
            'GOOGLE_GENAI_USE_VERTEXAI': os.getenv('GOOGLE_GENAI_USE_VERTEXAI'),
            'GOOGLE_DEFAULT_MODEL': os.getenv('GOOGLE_DEFAULT_MODEL'),
            'GOOGLE_CLOUD_LOCATION': os.getenv('GOOGLE_CLOUD_LOCATION')
        }
        
        # Clear env vars for clean test
        for key in self.original_env.keys():
            if key in os.environ:
                del os.environ[key]
    
    def tearDown(self):
        """Clean up test environment"""
        # Restore original env vars
        for key, value in self.original_env.items():
            if value is not None:
                os.environ[key] = value
            elif key in os.environ:
                del os.environ[key]

    @patch('google.generativeai.configure')
    def test_google_ai_studio_setup(self, mock_configure):
        """Test Google AI Studio authentication setup"""
        os.environ['GOOGLE_API_KEY'] = 'test-api-key'
        
        config = GoogleAIConfig()
        
        self.assertEqual(config.google_api_key, 'test-api-key')
        self.assertFalse(config.use_vertex_ai)
        mock_configure.assert_called_once_with(api_key='test-api-key')

    @patch('google.generativeai.configure')
    @patch('google.auth.default')
    def test_vertex_ai_setup(self, mock_default, mock_configure):
        """Test Vertex AI setup with mocked authentication"""
        # Mock the authentication to avoid real credential requirements
        mock_default.return_value = (Mock(), 'test-project')
        
        os.environ['GOOGLE_GENAI_USE_VERTEXAI'] = 'TRUE'
        os.environ['GOOGLE_CLOUD_PROJECT'] = 'test-project'
        
        with patch('config.google_ai.GoogleAIConfig._setup_google_ai_auth'):
            config = GoogleAIConfig()
            
            self.assertTrue(config.use_vertex_ai)
            self.assertEqual(config.google_cloud_project, 'test-project')

    def test_default_values(self):
        """Test default configuration values"""
        os.environ['GOOGLE_API_KEY'] = 'test-key'  # Required to avoid validation error
        
        with patch('google.generativeai.configure'):
            config = GoogleAIConfig()
            
            self.assertFalse(config.use_vertex_ai)
            self.assertEqual(config.default_model, 'gemini-2.0-flash')
            self.assertEqual(config.google_cloud_location, 'us-central1')

    def test_custom_model_and_location(self):
        """Test custom model and location configuration"""
        os.environ['GOOGLE_API_KEY'] = 'test-key'
        os.environ['GOOGLE_DEFAULT_MODEL'] = 'gemini-1.5-pro'
        os.environ['GOOGLE_CLOUD_LOCATION'] = 'europe-west1'
        
        with patch('google.generativeai.configure'):
            config = GoogleAIConfig()
            
            self.assertEqual(config.default_model, 'gemini-1.5-pro')
            self.assertEqual(config.google_cloud_location, 'europe-west1')

    def test_missing_api_key_validation_error(self):
        """Test validation error when API key is missing for Google AI Studio"""
        with self.assertRaises(ValueError) as context:
            GoogleAIConfig()
        
        self.assertIn('GOOGLE_API_KEY', str(context.exception))

    def test_missing_project_validation_error(self):
        """Test validation error for missing project in Vertex AI mode"""
        os.environ['GOOGLE_GENAI_USE_VERTEXAI'] = 'TRUE'
        # Don't set GOOGLE_CLOUD_PROJECT to test validation
        if 'GOOGLE_CLOUD_PROJECT' in os.environ:
            del os.environ['GOOGLE_CLOUD_PROJECT']
        
        with patch('config.google_ai.GoogleAIConfig._setup_google_ai_auth'):
            with self.assertRaises(ValueError) as context:
                GoogleAIConfig()
            self.assertIn('GOOGLE_CLOUD_PROJECT', str(context.exception))

    @patch('google.generativeai.configure')
    @patch('google.generativeai.GenerativeModel')
    def test_get_generative_model(self, mock_model_class, mock_configure):
        """Test GenerativeModel creation"""
        os.environ['GOOGLE_API_KEY'] = 'test-key'
        mock_model = Mock()
        mock_model_class.return_value = mock_model
        
        config = GoogleAIConfig()
        result = config.get_generative_model('gemini-1.5-pro')
        
        mock_model_class.assert_called_once_with('gemini-1.5-pro')
        self.assertEqual(result, mock_model)

    @patch('google.generativeai.configure')
    @patch('google.generativeai.GenerativeModel')
    def test_get_generative_model_default(self, mock_model_class, mock_configure):
        """Test GenerativeModel creation with default model"""
        os.environ['GOOGLE_API_KEY'] = 'test-key'
        mock_model = Mock()
        mock_model_class.return_value = mock_model
        
        config = GoogleAIConfig()
        result = config.get_generative_model()
        
        mock_model_class.assert_called_once_with('gemini-2.0-flash')

    @patch('google.generativeai.configure')
    def test_get_available_models_ai_studio(self, mock_configure):
        """Test available models for Google AI Studio"""
        os.environ['GOOGLE_API_KEY'] = 'test-key'
        
        config = GoogleAIConfig()
        models = config.get_available_models()
        
        expected_models = [
            "gemini-2.0-flash",
            "gemini-1.5-pro", 
            "gemini-1.5-flash",
            "gemini-1.0-pro"
        ]
        self.assertEqual(models, expected_models)

    @patch('google.generativeai.configure')
    @patch('google.auth.default')
    def test_get_available_models_vertex_ai(self, mock_default, mock_configure):
        """Test available models for Vertex AI"""
        # Mock authentication to avoid credential issues
        mock_default.return_value = (Mock(), 'test-project')
        
        os.environ['GOOGLE_GENAI_USE_VERTEXAI'] = 'TRUE'
        os.environ['GOOGLE_CLOUD_PROJECT'] = 'test-project'
        
        with patch('config.google_ai.GoogleAIConfig._setup_google_ai_auth'):
            config = GoogleAIConfig()
            models = config.get_available_models()
            
            expected_models = [
                "gemini-2.0-flash",
                "gemini-1.5-pro",
                "gemini-1.5-flash", 
                "gemini-1.0-pro"
            ]
            self.assertEqual(models, expected_models)

    @patch('google.generativeai.configure')
    def test_test_connection_success(self, mock_configure):
        """Test successful connection test"""
        os.environ['GOOGLE_API_KEY'] = 'test-key'
        
        with patch.object(GoogleAIConfig, 'get_generative_model') as mock_get_model:
            mock_get_model.return_value = Mock()
            
            config = GoogleAIConfig()
            result = config.test_connection()
            
            self.assertEqual(result['status'], 'success')
            self.assertEqual(result['service'], 'Google AI Studio')
            self.assertEqual(result['model'], 'gemini-2.0-flash')

    @patch('google.generativeai.configure')
    def test_test_connection_failure(self, mock_configure):
        """Test connection test failure"""
        os.environ['GOOGLE_API_KEY'] = 'test-key'
        
        with patch.object(GoogleAIConfig, 'get_generative_model') as mock_get_model:
            mock_get_model.side_effect = Exception('Connection failed')
            
            config = GoogleAIConfig()
            result = config.test_connection()
            
            self.assertEqual(result['status'], 'error')
            self.assertIn('Connection failed', result['error'])

    @patch('google.generativeai.configure')
    def test_get_model_config(self, mock_configure):
        """Test model configuration generation"""
        os.environ['GOOGLE_API_KEY'] = 'test-key'
        
        config = GoogleAIConfig()
        model_config = config.get_model_config()
        
        expected_config = {
            'model': 'gemini-2.0-flash'
        }
        self.assertEqual(model_config, expected_config)

    @patch('google.generativeai.configure')
    @patch('google.auth.default')
    def test_get_model_config_vertex_ai(self, mock_default, mock_configure):
        """Test model configuration for Vertex AI"""
        # Mock authentication to avoid credential issues
        mock_default.return_value = (Mock(), 'test-project')
        
        os.environ['GOOGLE_GENAI_USE_VERTEXAI'] = 'TRUE'
        os.environ['GOOGLE_CLOUD_PROJECT'] = 'test-project'
        
        with patch('config.google_ai.GoogleAIConfig._setup_google_ai_auth'):
            config = GoogleAIConfig()
            model_config = config.get_model_config()
            
            expected_config = {
                'model': 'gemini-2.0-flash',
                'project': 'test-project',
                'location': 'us-central1'
            }
            self.assertEqual(model_config, expected_config)

class TestGoogleAIModule(unittest.TestCase):
    """Test cases for module-level functions"""
    
    @patch('config.google_ai.GoogleAIConfig')
    def test_get_google_ai_config(self, mock_google_ai_config_class):
        """Test global config instance retrieval"""
        # Mock the global instance
        import config.google_ai
        
        config = get_google_ai_config()
        
        # Should return the global instance, not create a new one
        self.assertIsNotNone(config)

    @patch('config.google_ai.google_ai_config')
    def test_get_generative_model_convenience(self, mock_global_config):
        """Test convenience function for getting GenerativeModel"""
        mock_model = Mock()
        mock_global_config.get_generative_model.return_value = mock_model
        
        result = get_generative_model('test-model')
        
        mock_global_config.get_generative_model.assert_called_once_with('test-model')
        self.assertEqual(result, mock_model)

class TestGoogleAIEnvironmentValidation(unittest.TestCase):
    """Test cases for environment validation functionality"""
    
    @patch('config.google_ai.get_google_ai_config')
    def test_validate_google_ai_environment_success(self, mock_get_config):
        """Test successful environment validation"""
        mock_config = Mock()
        mock_config.test_connection.return_value = {'status': 'success'}
        mock_config.use_vertex_ai = False
        mock_config.default_model = 'gemini-2.0-flash'
        mock_config.google_cloud_project = None
        mock_config.google_cloud_location = 'us-central1'
        mock_get_config.return_value = mock_config
        
        result = validate_google_ai_environment()
        
        self.assertTrue(result['valid'])
        self.assertEqual(len(result['errors']), 0)

    @patch('config.google_ai.get_google_ai_config')
    def test_validate_google_ai_environment_connection_failure(self, mock_get_config):
        """Test environment validation with connection failure"""
        mock_config = Mock()
        mock_config.test_connection.return_value = {'status': 'error', 'error': 'Connection failed'}
        mock_config._validate_config = Mock()  # Don't raise any config errors
        mock_get_config.return_value = mock_config
        
        result = validate_google_ai_environment()
        
        self.assertFalse(result['valid'])
        self.assertIn('Google AI connection test failed', result['errors'][0])

    @patch('config.google_ai.get_google_ai_config')
    def test_validate_google_ai_environment_missing_config(self, mock_get_config):
        """Test environment validation with missing configuration"""
        mock_config = Mock()
        mock_config._validate_config.side_effect = ValueError('Missing configuration')
        mock_get_config.return_value = mock_config
        
        result = validate_google_ai_environment()
        
        self.assertFalse(result['valid'])
        self.assertIn('Google AI configuration validation failed', result['errors'][0])

    @patch('config.google_ai.get_google_ai_config')
    def test_validate_google_ai_environment_exception(self, mock_get_config):
        """Test environment validation with unexpected exception"""
        mock_get_config.side_effect = Exception('Unexpected error')
        
        result = validate_google_ai_environment()
        
        self.assertFalse(result['valid'])
        self.assertIn('Google AI configuration validation failed', result['errors'][0])

if __name__ == '__main__':
    unittest.main() 