"""
Unit tests for DeepSeek Service and Configuration

Tests the DeepSeek service functionality including authentication setup,
model management, query execution, and environment validation.
"""

import unittest
from unittest.mock import Mock, patch, AsyncMock
import os
import pytest
from typing import Dict, Any, Optional

# Test imports
from config.deepseek import (
    DeepSeekConfig,
    get_deepseek_config,
    validate_deepseek_environment
)
from services.deepseek_service import DeepSeekService, get_deepseek_service


class TestDeepSeekConfig(unittest.TestCase):
    """Test cases for DeepSeekConfig class functionality"""
    
    def setUp(self):
        """Set up test environment"""
        # Store original env vars
        self.original_env = {
            'DEEPSEEK_API_KEY': os.getenv('DEEPSEEK_API_KEY'),
            'DEEPSEEK_DEFAULT_MODEL': os.getenv('DEEPSEEK_DEFAULT_MODEL')
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

    def test_deepseek_config_initialization(self):
        """Test DeepSeek configuration initialization"""
        os.environ['DEEPSEEK_API_KEY'] = 'sk-test-key-123'
        
        config = DeepSeekConfig()
        
        self.assertEqual(config.api_key, 'sk-test-key-123')
        self.assertEqual(config.default_model, 'deepseek-chat')

    def test_deepseek_config_with_custom_model(self):
        """Test DeepSeek configuration with custom model"""
        os.environ['DEEPSEEK_API_KEY'] = 'sk-test-key'
        os.environ['DEEPSEEK_DEFAULT_MODEL'] = 'deepseek-coder'
        
        config = DeepSeekConfig()
        
        self.assertEqual(config.default_model, 'deepseek-coder')

    def test_missing_api_key_validation_error(self):
        """Test validation error when API key is missing"""
        with self.assertRaises(ValueError) as context:
            DeepSeekConfig()
        
        self.assertIn('DEEPSEEK_API_KEY', str(context.exception))

    def test_get_available_models(self):
        """Test getting available models"""
        os.environ['DEEPSEEK_API_KEY'] = 'sk-test-key'
        
        config = DeepSeekConfig()
        models = config.get_available_models()
        
        expected_models = ["deepseek-chat", "deepseek-coder"]
        
        for model in expected_models:
            self.assertIn(model, models)

    def test_get_model_info(self):
        """Test getting model information"""
        os.environ['DEEPSEEK_API_KEY'] = 'sk-test-key'
        
        config = DeepSeekConfig()
        info = config.get_model_info('deepseek-chat')
        
        self.assertIn('description', info)
        self.assertIn('context_window', info)
        self.assertIn('max_output', info)

    def test_get_model_info_default(self):
        """Test getting default model information"""
        os.environ['DEEPSEEK_API_KEY'] = 'sk-test-key'
        
        config = DeepSeekConfig()
        info = config.get_model_info()
        
        self.assertIn('description', info)
        # Should return info for default model (deepseek-chat)
        self.assertIn('DeepSeek', info['description'])

    def test_get_model_info_unknown(self):
        """Test getting information for unknown model"""
        os.environ['DEEPSEEK_API_KEY'] = 'sk-test-key'
        
        config = DeepSeekConfig()
        info = config.get_model_info('unknown-model')
        
        self.assertIn('Unknown model', info['description'])

    def test_test_connection_success(self):
        """Test successful connection test"""
        os.environ['DEEPSEEK_API_KEY'] = 'sk-test-key-123'
        
        config = DeepSeekConfig()
        result = config.test_connection()
        
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['service'], 'DeepSeek')
        self.assertEqual(result['model'], 'deepseek-chat')
        self.assertIn('sk-', result['api_key_prefix'])

    def test_test_connection_missing_key(self):
        """Test connection test with missing API key"""
        config = DeepSeekConfig.__new__(DeepSeekConfig)
        config.api_key = None
        config.default_model = 'deepseek-chat'
        
        result = config.test_connection()
        
        self.assertEqual(result['status'], 'error')
        self.assertIn('No DeepSeek API key', result['error'])

    def test_test_connection_invalid_format(self):
        """Test connection test with invalid API key format"""
        config = DeepSeekConfig.__new__(DeepSeekConfig)
        config.api_key = 'invalid-key-format'
        config.default_model = 'deepseek-chat'
        
        result = config.test_connection()
        
        self.assertEqual(result['status'], 'error')
        self.assertIn('Invalid DeepSeek API key format', result['error'])


class TestDeepSeekModule(unittest.TestCase):
    """Test cases for DeepSeek module functions"""
    
    @patch('config.deepseek.DeepSeekConfig')
    def test_get_deepseek_config(self, mock_deepseek_config_class):
        """Test get_deepseek_config function"""
        mock_config = Mock()
        mock_deepseek_config_class.return_value = mock_config
        
        # Clear any existing global config
        import config.deepseek
        config.deepseek.deepseek_config = None
        
        result = get_deepseek_config()
        
        self.assertEqual(result, mock_config)
        mock_deepseek_config_class.assert_called_once()

    @patch('config.deepseek.get_deepseek_config')
    def test_validate_deepseek_environment_success(self, mock_get_config):
        """Test successful environment validation"""
        mock_config = Mock()
        mock_config.test_connection.return_value = {'status': 'success'}
        mock_get_config.return_value = mock_config
        
        result = validate_deepseek_environment()
        
        self.assertTrue(result['valid'])
        self.assertEqual(len(result['errors']), 0)

    @patch('config.deepseek.get_deepseek_config')
    def test_validate_deepseek_environment_connection_failure(self, mock_get_config):
        """Test environment validation with connection failure"""
        mock_config = Mock()
        mock_config.test_connection.return_value = {
            'status': 'error',
            'error': 'Connection failed'
        }
        mock_get_config.return_value = mock_config
        
        result = validate_deepseek_environment()
        
        self.assertFalse(result['valid'])
        self.assertIn('Connection failed', result['errors'][0])

    @patch('config.deepseek.get_deepseek_config')
    def test_validate_deepseek_environment_missing_config(self, mock_get_config):
        """Test environment validation with missing config"""
        mock_get_config.side_effect = ValueError("Missing configuration")
        
        result = validate_deepseek_environment()
        
        self.assertFalse(result['valid'])
        self.assertIn('Missing configuration', result['errors'][0])


class TestDeepSeekService:
    """Test cases for DeepSeekService functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        with patch('services.deepseek_service.get_deepseek_config') as mock_config, \
             patch('services.deepseek_service.openai.AsyncOpenAI') as mock_client:
            
            mock_config.return_value = Mock()
            mock_config.return_value.api_key = 'sk-test-key'
            mock_config.return_value.base_url = 'https://api.deepseek.com'
            mock_client.return_value = Mock()
            
            self.service = DeepSeekService()
    
    def test_service_initialization(self):
        """Test service initialization"""
        assert self.service is not None
        assert hasattr(self.service, '_deepseek_config')
        assert hasattr(self.service, '_client')
    
    @pytest.mark.asyncio
    async def test_query_success(self):
        """Test successful query execution"""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Test response"
        
        self.service._client.chat.completions.create = AsyncMock(return_value=mock_response)
        self.service._deepseek_config.get_available_models.return_value = ['deepseek-chat']
        self.service._deepseek_config.default_model = 'deepseek-chat'
        
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
        self.service._deepseek_config.get_available_models.return_value = ['deepseek-chat']
        self.service._deepseek_config.default_model = 'deepseek-chat'
        
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
        self.service._deepseek_config.get_available_models.return_value = ['deepseek-coder']
        self.service._deepseek_config.default_model = 'deepseek-chat'
        
        result = await self.service.query(
            "Test prompt",
            model="deepseek-coder",
            system_instruction="System prompt",
            max_tokens=100,
            temperature=0.8
        )
        
        assert result == "Full response"
        
        call_args = self.service._client.chat.completions.create.call_args[1]
        assert call_args['model'] == 'deepseek-coder'
        assert call_args['max_tokens'] == 100
        assert call_args['temperature'] == 0.8

    @pytest.mark.asyncio
    async def test_query_failure(self):
        """Test query failure handling"""
        self.service._client.chat.completions.create = AsyncMock(
            side_effect=Exception("API Error")
        )
        self.service._deepseek_config.get_available_models.return_value = ['deepseek-chat']
        self.service._deepseek_config.default_model = 'deepseek-chat'
        
        with pytest.raises(RuntimeError):
            await self.service.query("Test prompt")

    @pytest.mark.asyncio
    async def test_query_structured_success(self):
        """Test successful structured query"""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = '{"result": "success", "data": "test"}'
        
        self.service._client.chat.completions.create = AsyncMock(return_value=mock_response)
        self.service._deepseek_config.get_available_models.return_value = ['deepseek-chat']
        self.service._deepseek_config.default_model = 'deepseek-chat'
        
        schema = {"result": "string", "data": "string"}
        result = await self.service.query_structured("Test prompt", schema)
        
        assert result['result'] == 'success'
        assert result['data'] == 'test'

    @pytest.mark.asyncio
    async def test_batch_query_success(self):
        """Test successful batch query"""
        # Mock different responses for each call
        responses = ["Response 1", "Response 2", "Response 3"]
        
        async def mock_create(**kwargs):
            response = Mock()
            response.choices = [Mock()]
            response.choices[0].message.content = responses.pop(0) if responses else "Default"
            return response
        
        self.service._client.chat.completions.create = mock_create
        self.service._deepseek_config.get_available_models.return_value = ['deepseek-chat']
        self.service._deepseek_config.default_model = 'deepseek-chat'
        
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
        self.service._deepseek_config.default_model = 'deepseek-chat'
        self.service._deepseek_config.get_available_models.return_value = ['deepseek-chat', 'deepseek-coder']
        
        info = self.service.get_info()
        
        assert info['service'] == 'DeepSeek'
        assert info['default_model'] == 'deepseek-chat'
        assert 'available_models' in info

    def test_test_connection(self):
        """Test connection testing"""
        self.service._deepseek_config.test_connection.return_value = {
            'status': 'success',
            'service': 'DeepSeek'
        }
        
        result = self.service.test_connection()
        
        assert result['status'] == 'success'
        assert result['service'] == 'DeepSeek'


class TestDeepSeekServiceSingleton:
    """Test DeepSeek service singleton functionality"""
    
    def test_get_deepseek_service_singleton(self):
        """Test that get_deepseek_service returns singleton"""
        with patch('services.deepseek_service.get_deepseek_config'), \
             patch('services.deepseek_service.openai.AsyncOpenAI'):
            
            service1 = get_deepseek_service()
            service2 = get_deepseek_service()
            
            assert service1 is service2  # Same instance 