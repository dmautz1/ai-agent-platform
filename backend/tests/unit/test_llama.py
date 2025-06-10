"""
Unit tests for Llama Service and Configuration

Tests the Llama service functionality including authentication setup,
model management, query execution, and environment validation.
"""

import unittest
from unittest.mock import Mock, patch, AsyncMock
import os
import pytest
from typing import Dict, Any, Optional

# Test imports
from config.llama import (
    LlamaConfig,
    get_llama_config,
    validate_llama_environment
)
from services.llama_service import LlamaService, get_llama_service


class TestLlamaConfig(unittest.TestCase):
    """Test cases for LlamaConfig class functionality"""
    
    def setUp(self):
        """Set up test environment"""
        # Store original env vars
        self.original_env = {
            'LLAMA_API_KEY': os.getenv('LLAMA_API_KEY'),
            'LLAMA_DEFAULT_MODEL': os.getenv('LLAMA_DEFAULT_MODEL')
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

    def test_llama_config_initialization(self):
        """Test Llama configuration initialization"""
        os.environ['LLAMA_API_KEY'] = 'llama-test-key-123456789'
        
        config = LlamaConfig()
        
        self.assertEqual(config.api_key, 'llama-test-key-123456789')
        self.assertEqual(config.default_model, 'meta-llama/Llama-3-8b-chat-hf')

    def test_llama_config_with_custom_model(self):
        """Test Llama configuration with custom model"""
        os.environ['LLAMA_API_KEY'] = 'llama-test-key'
        os.environ['LLAMA_DEFAULT_MODEL'] = 'meta-llama/Llama-3-70b-chat-hf'
        
        config = LlamaConfig()
        
        self.assertEqual(config.default_model, 'meta-llama/Llama-3-70b-chat-hf')

    def test_missing_api_key_validation_error(self):
        """Test validation error when API key is missing"""
        with self.assertRaises(ValueError) as context:
            LlamaConfig()
        
        self.assertIn('LLAMA_API_KEY', str(context.exception))

    def test_get_available_models(self):
        """Test getting available models"""
        os.environ['LLAMA_API_KEY'] = 'llama-test-key'
        
        config = LlamaConfig()
        models = config.get_available_models()
        
        expected_models = [
            "meta-llama/Llama-3-8b-chat-hf",
            "meta-llama/Llama-3-70b-chat-hf",
            "meta-llama/Meta-Llama-3-8B-Instruct",
            "meta-llama/Meta-Llama-3-70B-Instruct",
            "meta-llama/Llama-2-7b-chat-hf"
        ]
        
        for model in expected_models:
            self.assertIn(model, models)

    def test_get_model_info(self):
        """Test getting model information"""
        os.environ['LLAMA_API_KEY'] = 'llama-test-key'
        
        config = LlamaConfig()
        info = config.get_model_info('meta-llama/Llama-3-70b-chat-hf')
        
        self.assertIn('description', info)
        self.assertIn('context_window', info)
        self.assertIn('max_output', info)

    def test_get_model_info_default(self):
        """Test getting default model information"""
        os.environ['LLAMA_API_KEY'] = 'llama-test-key'
        
        config = LlamaConfig()
        info = config.get_model_info()
        
        self.assertIn('description', info)
        # Should return info for default model (meta-llama/Llama-3-8b-chat-hf)
        self.assertIn('Llama', info['description'])

    def test_get_model_info_unknown(self):
        """Test getting information for unknown model"""
        os.environ['LLAMA_API_KEY'] = 'llama-test-key'
        
        config = LlamaConfig()
        info = config.get_model_info('unknown-model')
        
        self.assertIn('Unknown model', info['description'])

    def test_test_connection_success(self):
        """Test successful connection test"""
        os.environ['LLAMA_API_KEY'] = 'llama-test-key-123456789'
        
        config = LlamaConfig()
        result = config.test_connection()
        
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['service'], 'Meta Llama')
        self.assertEqual(result['model'], 'meta-llama/Llama-3-8b-chat-hf')
        self.assertIn('llama-', result['api_key_prefix'])

    def test_test_connection_missing_key(self):
        """Test connection test with missing API key"""
        config = LlamaConfig.__new__(LlamaConfig)
        config.api_key = None
        config.default_model = 'meta-llama/Llama-3-8b-chat-hf'
        config.base_url = 'https://api.together.xyz/v1'
        config.api_provider = 'together'
        
        result = config.test_connection()
        
        self.assertEqual(result['status'], 'error')
        self.assertIn('No Meta Llama API key', result['error'])

    def test_test_connection_invalid_format(self):
        """Test connection test with invalid API key format"""
        config = LlamaConfig.__new__(LlamaConfig)
        config.api_key = 'invalid-key-format'
        config.default_model = 'meta-llama/Llama-3-8b-chat-hf'
        config.base_url = 'https://api.together.xyz/v1'
        config.api_provider = 'together'
        
        result = config.test_connection()
        
        self.assertEqual(result['status'], 'error')
        self.assertIn('Invalid Meta Llama API key format', result['error'])


class TestLlamaModule(unittest.TestCase):
    """Test cases for Llama module functions"""
    
    @patch('config.llama.LlamaConfig')
    def test_get_llama_config(self, mock_llama_config_class):
        """Test get_llama_config function"""
        mock_config = Mock()
        mock_llama_config_class.return_value = mock_config
        
        # Clear any existing global config
        import config.llama
        config.llama.llama_config = None
        
        result = get_llama_config()
        
        self.assertEqual(result, mock_config)
        mock_llama_config_class.assert_called_once()

    @patch('config.llama.get_llama_config')
    def test_validate_llama_environment_success(self, mock_get_config):
        """Test successful environment validation"""
        mock_config = Mock()
        mock_config.test_connection.return_value = {'status': 'success'}
        mock_get_config.return_value = mock_config
        
        result = validate_llama_environment()
        
        self.assertTrue(result['valid'])
        self.assertEqual(len(result['errors']), 0)

    @patch('config.llama.get_llama_config')
    def test_validate_llama_environment_connection_failure(self, mock_get_config):
        """Test environment validation with connection failure"""
        mock_config = Mock()
        mock_config.test_connection.return_value = {
            'status': 'error',
            'error': 'Connection failed'
        }
        mock_get_config.return_value = mock_config
        
        result = validate_llama_environment()
        
        self.assertFalse(result['valid'])
        self.assertIn('Connection failed', result['errors'][0])

    @patch('config.llama.get_llama_config')
    def test_validate_llama_environment_missing_config(self, mock_get_config):
        """Test environment validation with missing config"""
        mock_get_config.side_effect = ValueError("Missing configuration")
        
        result = validate_llama_environment()
        
        self.assertFalse(result['valid'])
        self.assertIn('Missing configuration', result['errors'][0])


class TestLlamaService:
    """Test cases for LlamaService functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        with patch('services.llama_service.get_llama_config') as mock_config, \
             patch('services.llama_service.openai.AsyncOpenAI') as mock_client:
            
            mock_config.return_value = Mock()
            mock_config.return_value.api_key = 'llama-test-key'
            mock_config.return_value.base_url = 'https://api.groq.com/openai/v1'
            mock_client.return_value = Mock()
            
            self.service = LlamaService()
    
    def test_service_initialization(self):
        """Test service initialization"""
        assert self.service is not None
        assert hasattr(self.service, '_llama_config')
        assert hasattr(self.service, '_client')
    
    @pytest.mark.asyncio
    async def test_query_success(self):
        """Test successful query execution"""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Test response"
        
        self.service._client.chat.completions.create = AsyncMock(return_value=mock_response)
        self.service._llama_config.get_available_models.return_value = ['meta-llama/Llama-3-70b-chat-hf']
        self.service._llama_config.default_model = 'meta-llama/Llama-3-70b-chat-hf'
        
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
        self.service._llama_config.get_available_models.return_value = ['meta-llama/Llama-3-70b-chat-hf']
        self.service._llama_config.default_model = 'meta-llama/Llama-3-70b-chat-hf'
        
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
        self.service._llama_config.get_available_models.return_value = ['meta-llama/Meta-Llama-3-8B-Instruct']
        self.service._llama_config.default_model = 'meta-llama/Llama-3-70b-chat-hf'
        
        result = await self.service.query(
            "Test prompt",
            model="meta-llama/Meta-Llama-3-8B-Instruct",
            system_instruction="System prompt",
            max_tokens=100,
            temperature=0.8
        )
        
        assert result == "Full response"
        
        call_args = self.service._client.chat.completions.create.call_args[1]
        assert call_args['model'] == 'meta-llama/Meta-Llama-3-8B-Instruct'
        assert call_args['max_tokens'] == 100
        assert call_args['temperature'] == 0.8

    @pytest.mark.asyncio
    async def test_query_failure(self):
        """Test query failure handling"""
        self.service._client.chat.completions.create = AsyncMock(
            side_effect=Exception("API Error")
        )
        self.service._llama_config.get_available_models.return_value = ['meta-llama/Llama-3-70b-chat-hf']
        self.service._llama_config.default_model = 'meta-llama/Llama-3-70b-chat-hf'
        
        with pytest.raises(RuntimeError):
            await self.service.query("Test prompt")

    @pytest.mark.asyncio
    async def test_query_structured_success(self):
        """Test successful structured query"""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = '{"result": "success", "data": "test"}'
        
        self.service._client.chat.completions.create = AsyncMock(return_value=mock_response)
        self.service._llama_config.get_available_models.return_value = ['meta-llama/Llama-3-70b-chat-hf']
        self.service._llama_config.default_model = 'meta-llama/Llama-3-70b-chat-hf'
        
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
        self.service._llama_config.get_available_models.return_value = ['meta-llama/Llama-3-70b-chat-hf']
        self.service._llama_config.default_model = 'meta-llama/Llama-3-70b-chat-hf'
        
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
        self.service._llama_config.default_model = 'meta-llama/Llama-3-70b-chat-hf'
        self.service._llama_config.get_available_models.return_value = ['meta-llama/Llama-3-70b-chat-hf', 'meta-llama/Meta-Llama-3-8B-Instruct']
        
        info = self.service.get_info()
        
        assert info['service'] == 'Llama'
        assert info['default_model'] == 'meta-llama/Llama-3-70b-chat-hf'
        assert 'available_models' in info

    def test_test_connection(self):
        """Test connection testing"""
        self.service._llama_config.test_connection.return_value = {
            'status': 'success',
            'service': 'Meta Llama'
        }
        
        result = self.service.test_connection()
        
        assert result['status'] == 'success'
        assert result['service'] == 'Meta Llama'


class TestLlamaServiceSingleton:
    """Test Llama service singleton functionality"""
    
    def test_get_llama_service_singleton(self):
        """Test that get_llama_service returns singleton"""
        with patch('services.llama_service.get_llama_config'), \
             patch('services.llama_service.openai.AsyncOpenAI'):
            
            service1 = get_llama_service()
            service2 = get_llama_service()
            
            assert service1 is service2  # Same instance 