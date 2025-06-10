"""
Unit tests for OpenAI Service and Configuration

Tests the OpenAI service functionality including authentication setup,
model management, query execution, and environment validation.
"""

import unittest
from unittest.mock import Mock, patch, AsyncMock
import os
import pytest
from typing import Dict, Any, Optional

# Test imports
from config.openai import (
    OpenAIConfig,
    get_openai_config,
    validate_openai_environment
)
from services.openai_service import OpenAIService, get_openai_service


class TestOpenAIConfig(unittest.TestCase):
    """Test cases for OpenAIConfig class functionality"""
    
    def setUp(self):
        """Set up test environment"""
        # Store original env vars
        self.original_env = {
            'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY'),
            'OPENAI_DEFAULT_MODEL': os.getenv('OPENAI_DEFAULT_MODEL'),
            'OPENAI_ORGANIZATION': os.getenv('OPENAI_ORGANIZATION'),
            'OPENAI_PROJECT': os.getenv('OPENAI_PROJECT')
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

    def test_openai_config_initialization(self):
        """Test OpenAI configuration initialization"""
        os.environ['OPENAI_API_KEY'] = 'sk-test-api-key-123'
        
        config = OpenAIConfig()
        
        self.assertEqual(config.api_key, 'sk-test-api-key-123')
        self.assertEqual(config.default_model, 'gpt-4o-mini')
        self.assertIsNone(config.organization)
        self.assertIsNone(config.project)

    def test_openai_config_with_custom_model(self):
        """Test OpenAI configuration with custom model"""
        os.environ['OPENAI_API_KEY'] = 'sk-test-key'
        os.environ['OPENAI_DEFAULT_MODEL'] = 'gpt-4'
        
        config = OpenAIConfig()
        
        self.assertEqual(config.default_model, 'gpt-4')

    def test_openai_config_with_organization(self):
        """Test OpenAI configuration with organization"""
        os.environ['OPENAI_API_KEY'] = 'sk-test-key'
        os.environ['OPENAI_ORGANIZATION'] = 'org-test123'
        os.environ['OPENAI_PROJECT'] = 'proj-test456'
        
        config = OpenAIConfig()
        
        self.assertEqual(config.organization, 'org-test123')
        self.assertEqual(config.project, 'proj-test456')

    def test_missing_api_key_validation_error(self):
        """Test validation error when API key is missing"""
        with self.assertRaises(ValueError) as context:
            OpenAIConfig()
        
        self.assertIn('OPENAI_API_KEY', str(context.exception))

    def test_get_available_models(self):
        """Test getting available models"""
        os.environ['OPENAI_API_KEY'] = 'sk-test-key'
        
        config = OpenAIConfig()
        models = config.get_available_models()
        
        expected_models = [
            "gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-4-turbo-preview",
            "gpt-4", "gpt-4-32k", "gpt-3.5-turbo", "gpt-3.5-turbo-16k"
        ]
        
        for model in expected_models:
            self.assertIn(model, models)

    def test_get_model_info(self):
        """Test getting model information"""
        os.environ['OPENAI_API_KEY'] = 'sk-test-key'
        
        config = OpenAIConfig()
        info = config.get_model_info('gpt-4o')
        
        self.assertIn('description', info)
        self.assertIn('context_window', info)
        self.assertIn('max_output', info)
        self.assertEqual(info['context_window'], 128000)

    def test_get_model_info_default(self):
        """Test getting default model information"""
        os.environ['OPENAI_API_KEY'] = 'sk-test-key'
        
        config = OpenAIConfig()
        info = config.get_model_info()
        
        self.assertIn('description', info)
        # Should return info for default model (gpt-4o-mini)
        self.assertEqual(info['context_window'], 128000)

    def test_get_model_info_unknown(self):
        """Test getting information for unknown model"""
        os.environ['OPENAI_API_KEY'] = 'sk-test-key'
        
        config = OpenAIConfig()
        info = config.get_model_info('unknown-model')
        
        self.assertIn('Unknown model', info['description'])

    def test_test_connection_success(self):
        """Test successful connection test"""
        os.environ['OPENAI_API_KEY'] = 'sk-test-api-key-123'
        
        config = OpenAIConfig()
        result = config.test_connection()
        
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['service'], 'OpenAI')
        self.assertEqual(result['model'], 'gpt-4o-mini')
        self.assertIn('sk-test', result['api_key_prefix'])

    def test_test_connection_missing_key(self):
        """Test connection test with missing API key"""
        config = OpenAIConfig.__new__(OpenAIConfig)  # Create without __init__
        config.api_key = None
        config.default_model = 'gpt-4o-mini'
        
        result = config.test_connection()
        
        self.assertEqual(result['status'], 'error')
        self.assertIn('No OpenAI API key', result['error'])

    def test_test_connection_invalid_format(self):
        """Test connection test with invalid API key format"""
        config = OpenAIConfig.__new__(OpenAIConfig)  # Create without __init__
        config.api_key = 'invalid-key-format'
        config.default_model = 'gpt-4o-mini'
        
        result = config.test_connection()
        
        self.assertEqual(result['status'], 'error')
        self.assertIn('Invalid OpenAI API key format', result['error'])

    def test_get_client_config(self):
        """Test getting client configuration"""
        os.environ['OPENAI_API_KEY'] = 'sk-test-key'
        os.environ['OPENAI_ORGANIZATION'] = 'org-123'
        os.environ['OPENAI_PROJECT'] = 'proj-456'
        
        config = OpenAIConfig()
        client_config = config.get_client_config()
        
        self.assertEqual(client_config['api_key'], 'sk-test-key')
        self.assertEqual(client_config['organization'], 'org-123')
        self.assertEqual(client_config['project'], 'proj-456')

    def test_get_client_config_minimal(self):
        """Test getting client configuration with minimal settings"""
        os.environ['OPENAI_API_KEY'] = 'sk-test-key'
        
        config = OpenAIConfig()
        client_config = config.get_client_config()
        
        self.assertEqual(client_config['api_key'], 'sk-test-key')
        self.assertNotIn('organization', client_config)
        self.assertNotIn('project', client_config)


class TestOpenAIModule(unittest.TestCase):
    """Test cases for OpenAI module functions"""
    
    @patch('config.openai.OpenAIConfig')
    def test_get_openai_config(self, mock_openai_config_class):
        """Test get_openai_config function"""
        mock_config = Mock()
        mock_openai_config_class.return_value = mock_config
        
        # Clear any existing global config
        import config.openai
        config.openai.openai_config = None
        
        result = get_openai_config()
        
        self.assertEqual(result, mock_config)
        mock_openai_config_class.assert_called_once()

    @patch('config.openai.get_openai_config')
    def test_validate_openai_environment_success(self, mock_get_config):
        """Test successful environment validation"""
        mock_config = Mock()
        mock_config.test_connection.return_value = {'status': 'success'}
        mock_get_config.return_value = mock_config
        
        result = validate_openai_environment()
        
        self.assertTrue(result['valid'])
        self.assertEqual(len(result['errors']), 0)

    @patch('config.openai.get_openai_config')
    def test_validate_openai_environment_connection_failure(self, mock_get_config):
        """Test environment validation with connection failure"""
        mock_config = Mock()
        mock_config.test_connection.return_value = {
            'status': 'error',
            'error': 'Connection failed'
        }
        mock_get_config.return_value = mock_config
        
        result = validate_openai_environment()
        
        self.assertFalse(result['valid'])
        self.assertIn('Connection failed', result['errors'][0])

    @patch('config.openai.get_openai_config')
    def test_validate_openai_environment_missing_config(self, mock_get_config):
        """Test environment validation with missing config"""
        mock_get_config.side_effect = ValueError("Missing configuration")
        
        result = validate_openai_environment()
        
        self.assertFalse(result['valid'])
        self.assertIn('Missing configuration', result['errors'][0])

    @patch('config.openai.get_openai_config')
    def test_validate_openai_environment_exception(self, mock_get_config):
        """Test environment validation with unexpected exception"""
        mock_get_config.side_effect = Exception("Unexpected error")
        
        result = validate_openai_environment()
        
        self.assertFalse(result['valid'])
        self.assertIn('Unexpected error', result['errors'][0])


class TestOpenAIService:
    """Test cases for OpenAIService functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        with patch('services.openai_service.get_openai_config') as mock_config, \
             patch('services.openai_service.openai.AsyncOpenAI') as mock_client:
            
            mock_config.return_value = Mock()
            mock_config.return_value.api_key = 'sk-test-key'
            mock_client.return_value = Mock()
            
            self.service = OpenAIService()
    
    def test_service_initialization(self):
        """Test service initialization"""
        assert self.service is not None
        assert hasattr(self.service, '_openai_config')
        assert hasattr(self.service, '_client')
    
    @pytest.mark.asyncio
    async def test_query_success(self):
        """Test successful query execution"""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Test response"
        
        self.service._client.chat.completions.create = AsyncMock(return_value=mock_response)
        self.service._openai_config.get_available_models.return_value = ['gpt-4o-mini']
        self.service._openai_config.default_model = 'gpt-4o-mini'
        
        result = await self.service.query("Test prompt")
        
        assert result == "Test response"
        self.service._client.chat.completions.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_query_with_system_instruction(self):
        """Test query with system instruction"""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "System response"
        
        self.service._client.chat.completions.create = AsyncMock(return_value=mock_response)
        self.service._openai_config.get_available_models.return_value = ['gpt-4o-mini']
        self.service._openai_config.default_model = 'gpt-4o-mini'
        
        result = await self.service.query(
            "Test prompt",
            system_instruction="You are a helpful assistant"
        )
        
        assert result == "System response"
        
        # Verify system message was included
        call_args = self.service._client.chat.completions.create.call_args[1]
        messages = call_args['messages']
        assert len(messages) == 2
        assert messages[0]['role'] == 'system'
        assert messages[1]['role'] == 'user'

    @pytest.mark.asyncio
    async def test_query_with_all_parameters(self):
        """Test query with all parameters"""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Full response"
        
        self.service._client.chat.completions.create = AsyncMock(return_value=mock_response)
        self.service._openai_config.get_available_models.return_value = ['gpt-4']
        self.service._openai_config.default_model = 'gpt-4o-mini'
        
        result = await self.service.query(
            "Test prompt",
            model="gpt-4",
            system_instruction="System prompt",
            max_tokens=100,
            temperature=0.8
        )
        
        assert result == "Full response"
        
        call_args = self.service._client.chat.completions.create.call_args[1]
        assert call_args['model'] == 'gpt-4'
        assert call_args['max_tokens'] == 100
        assert call_args['temperature'] == 0.8

    @pytest.mark.asyncio
    async def test_query_failure(self):
        """Test query failure handling"""
        self.service._client.chat.completions.create = AsyncMock(
            side_effect=Exception("API Error")
        )
        self.service._openai_config.get_available_models.return_value = ['gpt-4o-mini']
        self.service._openai_config.default_model = 'gpt-4o-mini'
        
        with pytest.raises(RuntimeError):
            await self.service.query("Test prompt")

    @pytest.mark.asyncio
    async def test_query_structured_success(self):
        """Test successful structured query"""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = '{"result": "success", "data": "test"}'
        
        self.service._client.chat.completions.create = AsyncMock(return_value=mock_response)
        self.service._openai_config.get_available_models.return_value = ['gpt-4o-mini']
        self.service._openai_config.default_model = 'gpt-4o-mini'
        
        schema = {"result": "string", "data": "string"}
        result = await self.service.query_structured("Test prompt", schema)
        
        assert result['result'] == 'success'
        assert result['data'] == 'test'

    @pytest.mark.asyncio
    async def test_query_structured_invalid_json(self):
        """Test structured query with invalid JSON response"""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = 'Invalid JSON response'
        
        self.service._client.chat.completions.create = AsyncMock(return_value=mock_response)
        self.service._openai_config.get_available_models.return_value = ['gpt-4o-mini']
        self.service._openai_config.default_model = 'gpt-4o-mini'
        
        schema = {"result": "string"}
        result = await self.service.query_structured("Test prompt", schema, max_retries=0)
        
        assert 'error' in result
        assert 'raw_response' in result

    @pytest.mark.asyncio
    async def test_batch_query_success(self):
        """Test successful batch query"""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        
        # Mock different responses for each call
        responses = ["Response 1", "Response 2", "Response 3"]
        mock_response.choices[0].message.content = "placeholder"
        
        async def mock_create(**kwargs):
            response = Mock()
            response.choices = [Mock()]
            response.choices[0].message.content = responses.pop(0) if responses else "Default"
            return response
        
        self.service._client.chat.completions.create = mock_create
        self.service._openai_config.get_available_models.return_value = ['gpt-4o-mini']
        self.service._openai_config.default_model = 'gpt-4o-mini'
        
        prompts = ["Prompt 1", "Prompt 2", "Prompt 3"]
        results = await self.service.batch_query(prompts)
        
        assert len(results) == 3
        assert results[0] == "Response 1"
        assert results[1] == "Response 2"
        assert results[2] == "Response 3"

    @pytest.mark.asyncio
    async def test_analyze_sentiment(self):
        """Test sentiment analysis convenience method"""
        with patch.object(self.service, 'query_structured') as mock_structured:
            mock_structured.return_value = {'sentiment': 'positive', 'confidence': 0.9}
            
            result = await self.service.analyze_sentiment("I love this!")
            
            assert result['sentiment'] == 'positive'
            mock_structured.assert_called_once()

    @pytest.mark.asyncio
    async def test_extract_keywords(self):
        """Test keyword extraction convenience method"""
        with patch.object(self.service, 'query_structured') as mock_structured:
            mock_structured.return_value = {'keywords': ['test', 'keyword']}
            
            result = await self.service.extract_keywords("Test text", max_keywords=5)
            
            assert result['keywords'] == ['test', 'keyword']
            mock_structured.assert_called_once()

    @pytest.mark.asyncio
    async def test_summarize(self):
        """Test summarization convenience method"""
        with patch.object(self.service, 'query_structured') as mock_structured:
            mock_structured.return_value = {'summary': 'Test summary'}
            
            result = await self.service.summarize("Long text here", max_sentences=2)
            
            assert result['summary'] == 'Test summary'
            mock_structured.assert_called_once()

    def test_get_info(self):
        """Test getting service information"""
        self.service._openai_config.default_model = 'gpt-4o-mini'
        self.service._openai_config.get_available_models.return_value = ['gpt-4o-mini', 'gpt-4']
        
        info = self.service.get_info()
        
        assert info['service'] == 'OpenAI'
        assert info['default_model'] == 'gpt-4o-mini'
        assert 'available_models' in info

    def test_test_connection(self):
        """Test connection testing"""
        self.service._openai_config.test_connection.return_value = {
            'status': 'success',
            'service': 'OpenAI'
        }
        
        result = self.service.test_connection()
        
        assert result['status'] == 'success'
        assert result['service'] == 'OpenAI'


class TestOpenAIServiceSingleton:
    """Test OpenAI service singleton functionality"""
    
    def test_get_openai_service_singleton(self):
        """Test that get_openai_service returns singleton"""
        with patch('services.openai_service.get_openai_config'), \
             patch('services.openai_service.openai.AsyncOpenAI'):
            
            service1 = get_openai_service()
            service2 = get_openai_service()
            
            assert service1 is service2  # Same instance 