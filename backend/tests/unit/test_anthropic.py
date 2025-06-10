"""
Unit tests for Anthropic Service and Configuration

Tests the Anthropic service functionality including authentication setup,
model management, query execution, and environment validation.
"""

import unittest
from unittest.mock import Mock, patch, AsyncMock
import os
import pytest
from typing import Dict, Any, Optional

# Test imports
from config.anthropic import (
    AnthropicConfig,
    get_anthropic_config,
    validate_anthropic_environment
)
from services.anthropic_service import AnthropicService, get_anthropic_service


class TestAnthropicConfig(unittest.TestCase):
    """Test cases for AnthropicConfig class functionality"""
    
    def setUp(self):
        """Set up test environment"""
        # Store original env vars
        self.original_env = {
            'ANTHROPIC_API_KEY': os.getenv('ANTHROPIC_API_KEY'),
            'ANTHROPIC_DEFAULT_MODEL': os.getenv('ANTHROPIC_DEFAULT_MODEL')
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

    def test_anthropic_config_initialization(self):
        """Test Anthropic configuration initialization"""
        os.environ['ANTHROPIC_API_KEY'] = 'sk-ant-test-key-123'
        
        config = AnthropicConfig()
        
        self.assertEqual(config.api_key, 'sk-ant-test-key-123')
        self.assertEqual(config.default_model, 'claude-3-5-sonnet-20241022')

    def test_anthropic_config_with_custom_model(self):
        """Test Anthropic configuration with custom model"""
        os.environ['ANTHROPIC_API_KEY'] = 'sk-ant-test-key'
        os.environ['ANTHROPIC_DEFAULT_MODEL'] = 'claude-3-opus-20240229'
        
        config = AnthropicConfig()
        
        self.assertEqual(config.default_model, 'claude-3-opus-20240229')

    def test_missing_api_key_validation_error(self):
        """Test validation error when API key is missing"""
        with self.assertRaises(ValueError) as context:
            AnthropicConfig()
        
        self.assertIn('ANTHROPIC_API_KEY', str(context.exception))

    def test_get_available_models(self):
        """Test getting available models"""
        os.environ['ANTHROPIC_API_KEY'] = 'sk-ant-test-key'
        
        config = AnthropicConfig()
        models = config.get_available_models()
        
        expected_models = [
            "claude-3-5-sonnet-20241022",
            "claude-3-5-haiku-20241022",
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229", 
            "claude-3-haiku-20240307"
        ]
        
        for model in expected_models:
            self.assertIn(model, models)

    def test_get_model_info(self):
        """Test getting model information"""
        os.environ['ANTHROPIC_API_KEY'] = 'sk-ant-test-key'
        
        config = AnthropicConfig()
        info = config.get_model_info('claude-3-opus-20240229')
        
        self.assertIn('description', info)
        self.assertIn('context_window', info)
        self.assertIn('max_output', info)
        self.assertEqual(info['context_window'], 200000)

    def test_get_model_info_default(self):
        """Test getting default model information"""
        os.environ['ANTHROPIC_API_KEY'] = 'sk-ant-test-key'
        
        config = AnthropicConfig()
        info = config.get_model_info()
        
        self.assertIn('description', info)
        # Should return info for default model (claude-3-sonnet)
        self.assertEqual(info['context_window'], 200000)

    def test_get_model_info_unknown(self):
        """Test getting information for unknown model"""
        os.environ['ANTHROPIC_API_KEY'] = 'sk-ant-test-key'
        
        config = AnthropicConfig()
        info = config.get_model_info('unknown-model')
        
        self.assertIn('Unknown model', info['description'])

    def test_test_connection_success(self):
        """Test successful connection test"""
        os.environ['ANTHROPIC_API_KEY'] = 'sk-ant-test-key-123'
        
        config = AnthropicConfig()
        result = config.test_connection()
        
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['service'], 'Anthropic')
        self.assertEqual(result['model'], 'claude-3-5-sonnet-20241022')
        self.assertIn('sk-ant-', result['api_key_prefix'])

    def test_test_connection_missing_key(self):
        """Test connection test with missing API key"""
        config = AnthropicConfig.__new__(AnthropicConfig)
        config.api_key = None
        config.default_model = 'claude-3-5-sonnet-20241022'
        
        result = config.test_connection()
        
        self.assertEqual(result['status'], 'error')
        self.assertIn('No Anthropic API key', result['error'])

    def test_test_connection_invalid_format(self):
        """Test connection test with invalid API key format"""
        config = AnthropicConfig.__new__(AnthropicConfig)
        config.api_key = 'invalid-key-format'
        config.default_model = 'claude-3-5-sonnet-20241022'
        
        result = config.test_connection()
        
        self.assertEqual(result['status'], 'error')
        self.assertIn('Invalid Anthropic API key format', result['error'])


class TestAnthropicModule(unittest.TestCase):
    """Test cases for Anthropic module functions"""
    
    @patch('config.anthropic.AnthropicConfig')
    def test_get_anthropic_config(self, mock_anthropic_config_class):
        """Test get_anthropic_config function"""
        mock_config = Mock()
        mock_anthropic_config_class.return_value = mock_config
        
        # Clear any existing global config
        import config.anthropic
        config.anthropic.anthropic_config = None
        
        result = get_anthropic_config()
        
        self.assertEqual(result, mock_config)
        mock_anthropic_config_class.assert_called_once()

    @patch('config.anthropic.get_anthropic_config')
    def test_validate_anthropic_environment_success(self, mock_get_config):
        """Test successful environment validation"""
        mock_config = Mock()
        mock_config.test_connection.return_value = {'status': 'success'}
        mock_get_config.return_value = mock_config
        
        result = validate_anthropic_environment()
        
        self.assertTrue(result['valid'])
        self.assertEqual(len(result['errors']), 0)

    @patch('config.anthropic.get_anthropic_config')
    def test_validate_anthropic_environment_connection_failure(self, mock_get_config):
        """Test environment validation with connection failure"""
        mock_config = Mock()
        mock_config.test_connection.return_value = {
            'status': 'error',
            'error': 'Connection failed'
        }
        mock_get_config.return_value = mock_config
        
        result = validate_anthropic_environment()
        
        self.assertFalse(result['valid'])
        self.assertIn('Connection failed', result['errors'][0])

    @patch('config.anthropic.get_anthropic_config')
    def test_validate_anthropic_environment_missing_config(self, mock_get_config):
        """Test environment validation with missing config"""
        mock_get_config.side_effect = ValueError("Missing configuration")
        
        result = validate_anthropic_environment()
        
        self.assertFalse(result['valid'])
        self.assertIn('Missing configuration', result['errors'][0])


class TestAnthropicService:
    """Test cases for AnthropicService functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        with patch('services.anthropic_service.get_anthropic_config') as mock_config, \
             patch('services.anthropic_service.anthropic.AsyncAnthropic') as mock_client:
            
            mock_config.return_value = Mock()
            mock_config.return_value.api_key = 'sk-ant-test-key'
            mock_client.return_value = Mock()
            
            self.service = AnthropicService()
    
    def test_service_initialization(self):
        """Test service initialization"""
        assert self.service is not None
        assert hasattr(self.service, '_anthropic_config')
        assert hasattr(self.service, '_client')
    
    @pytest.mark.asyncio
    async def test_query_success(self):
        """Test successful query execution"""
        mock_response = Mock()
        mock_response.content = [Mock()]
        mock_response.content[0].text = "Test response"
        
        self.service._client.messages.create = AsyncMock(return_value=mock_response)
        self.service._anthropic_config.get_available_models.return_value = ['claude-3-sonnet-20240229']
        self.service._anthropic_config.default_model = 'claude-3-sonnet-20240229'
        
        result = await self.service.query("Test prompt")
        
        assert result == "Test response"
        self.service._client.messages.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_query_with_system_instruction(self):
        """Test query with system instruction"""
        mock_response = Mock()
        mock_response.content = [Mock()]
        mock_response.content[0].text = "System response"
        
        self.service._client.messages.create = AsyncMock(return_value=mock_response)
        self.service._anthropic_config.get_available_models.return_value = ['claude-3-sonnet-20240229']
        self.service._anthropic_config.default_model = 'claude-3-sonnet-20240229'
        
        result = await self.service.query(
            "Test prompt",
            system_instruction="You are a helpful assistant"
        )
        
        assert result == "System response"
        
        # Verify system message was included
        call_args = self.service._client.messages.create.call_args[1]
        assert 'system' in call_args

    @pytest.mark.asyncio
    async def test_query_with_all_parameters(self):
        """Test query with all parameters"""
        mock_response = Mock()
        mock_response.content = [Mock()]
        mock_response.content[0].text = "Full response"
        
        self.service._client.messages.create = AsyncMock(return_value=mock_response)
        self.service._anthropic_config.get_available_models.return_value = ['claude-3-opus-20240229']
        self.service._anthropic_config.default_model = 'claude-3-sonnet-20240229'
        
        result = await self.service.query(
            "Test prompt",
            model="claude-3-opus-20240229",
            system_instruction="System prompt",
            max_tokens=100,
            temperature=0.8
        )
        
        assert result == "Full response"
        
        call_args = self.service._client.messages.create.call_args[1]
        assert call_args['model'] == 'claude-3-opus-20240229'
        assert call_args['max_tokens'] == 100
        assert call_args['temperature'] == 0.8

    @pytest.mark.asyncio
    async def test_query_failure(self):
        """Test query failure handling"""
        self.service._client.messages.create = AsyncMock(
            side_effect=Exception("API Error")
        )
        self.service._anthropic_config.get_available_models.return_value = ['claude-3-sonnet-20240229']
        self.service._anthropic_config.default_model = 'claude-3-sonnet-20240229'
        
        with pytest.raises(RuntimeError):
            await self.service.query("Test prompt")

    @pytest.mark.asyncio
    async def test_query_structured_success(self):
        """Test successful structured query"""
        mock_response = Mock()
        mock_response.content = [Mock()]
        mock_response.content[0].text = '{"result": "success", "data": "test"}'
        
        self.service._client.messages.create = AsyncMock(return_value=mock_response)
        self.service._anthropic_config.get_available_models.return_value = ['claude-3-sonnet-20240229']
        self.service._anthropic_config.default_model = 'claude-3-sonnet-20240229'
        
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
            response.content = [Mock()]
            response.content[0].text = responses.pop(0) if responses else "Default"
            return response
        
        self.service._client.messages.create = mock_create
        self.service._anthropic_config.get_available_models.return_value = ['claude-3-sonnet-20240229']
        self.service._anthropic_config.default_model = 'claude-3-sonnet-20240229'
        
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
        self.service._anthropic_config.default_model = 'claude-3-sonnet-20240229'
        self.service._anthropic_config.get_available_models.return_value = ['claude-3-sonnet-20240229', 'claude-3-opus-20240229']
        
        info = self.service.get_info()
        
        assert info['service'] == 'Anthropic'
        assert info['default_model'] == 'claude-3-sonnet-20240229'
        assert 'available_models' in info

    def test_test_connection(self):
        """Test connection testing"""
        self.service._anthropic_config.test_connection.return_value = {
            'status': 'success',
            'service': 'Anthropic'
        }
        
        result = self.service.test_connection()
        
        assert result['status'] == 'success'
        assert result['service'] == 'Anthropic'


class TestAnthropicServiceSingleton:
    """Test Anthropic service singleton functionality"""
    
    def test_get_anthropic_service_singleton(self):
        """Test that get_anthropic_service returns singleton"""
        with patch('services.anthropic_service.get_anthropic_config'), \
             patch('services.anthropic_service.anthropic.AsyncAnthropic'):
            
            service1 = get_anthropic_service()
            service2 = get_anthropic_service()
            
            assert service1 is service2  # Same instance 