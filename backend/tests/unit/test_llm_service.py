"""
Unit tests for LLM Service

Tests the unified LLM service functionality including provider management,
query routing, error handling, and health monitoring.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, Any

from services.llm_service import (
    UnifiedLLMService, 
    LLMProvider, 
    get_unified_llm_service
)


class TestUnifiedLLMService:
    """Test UnifiedLLMService functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.service = UnifiedLLMService()
    
    def test_service_initialization(self):
        """Test service initialization"""
        assert self.service is not None
        assert hasattr(self.service, '_google_service')
        assert hasattr(self.service, '_openai_service')
        assert hasattr(self.service, '_default_provider')
        assert self.service._default_provider == "google"
    
    def test_get_available_providers(self):
        """Test getting available providers"""
        # Mock the service getter methods to control availability
        with patch.object(self.service, '_get_google_service') as mock_google, \
             patch.object(self.service, '_get_openai_service') as mock_openai, \
             patch.object(self.service, '_get_anthropic_service') as mock_anthropic:
            
            # Set up mocks - google and openai available, anthropic unavailable
            mock_google.return_value = Mock()
            mock_openai.return_value = Mock()
            mock_anthropic.return_value = None  # Unavailable
            
            available = self.service.get_available_providers()
            
            assert 'google' in available
            assert 'openai' in available
            assert 'anthropic' not in available
    
    @pytest.mark.asyncio
    async def test_query_success_with_provider(self):
        """Test successful query with specific provider"""
        mock_service = AsyncMock()
        mock_service.query.return_value = "Test response"
        
        with patch.object(self.service, '_get_openai_service') as mock_get:
            mock_get.return_value = mock_service
            
            result = await self.service.query(
                prompt="Test prompt",
                provider="openai",
                temperature=0.7
            )
            
            assert result == "Test response"
            mock_service.query.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_query_with_fallback(self):
        """Test query with provider fallback"""
        mock_fallback_service = AsyncMock()
        mock_fallback_service.query.return_value = "Fallback response"
        
        with patch.object(self.service, '_get_openai_service') as mock_get_openai, \
             patch.object(self.service, '_get_google_service') as mock_get_google:
            
            mock_get_openai.return_value = None  # Unavailable
            mock_get_google.return_value = mock_fallback_service  # Available fallback
            self.service._default_provider = 'google'
            
            result = await self.service.query(
                prompt="Test prompt",
                provider="openai"  # Request unavailable provider
            )
            
            assert result == "Fallback response"
            mock_fallback_service.query.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_query_all_parameters(self):
        """Test query with all parameters"""
        mock_service = AsyncMock()
        mock_service.query.return_value = "Complete response"
        
        with patch.object(self.service, '_get_anthropic_service') as mock_get:
            mock_get.return_value = mock_service
            
            result = await self.service.query(
                prompt="Complex prompt",
                provider="anthropic",
                model="claude-3-sonnet",
                temperature=0.8,
                system_instruction="You are an expert",
                max_tokens=500
            )
            
            assert result == "Complete response"
            mock_service.query.assert_called_once()
    
    def test_get_all_providers_info(self):
        """Test getting all providers information"""
        mock_google = Mock()
        mock_openai = Mock()
        
        with patch.object(self.service, '_get_google_service') as mock_get_google, \
             patch.object(self.service, '_get_openai_service') as mock_get_openai:
            
            mock_get_google.return_value = mock_google
            mock_get_openai.return_value = mock_openai
            
            info = self.service.get_all_providers_info()
            
            assert 'available_providers' in info
            assert 'default_provider' in info
            assert info['default_provider'] == 'google'
    
    def test_get_connection_health_status(self):
        """Test getting connection health status"""
        mock_google = Mock()
        mock_openai = Mock()
        
        with patch.object(self.service, '_get_google_service') as mock_get_google, \
             patch.object(self.service, '_get_openai_service') as mock_get_openai:
            
            mock_get_google.return_value = mock_google
            mock_get_openai.return_value = mock_openai
            
            health = self.service.get_connection_health_status()
            
            assert 'overall_status' in health
            assert 'services' in health
            assert 'loaded_services' in health
    
    def test_get_service_for_provider(self):
        """Test getting service for specific provider"""
        mock_google = Mock()
        
        with patch.object(self.service, '_get_google_service') as mock_get:
            mock_get.return_value = mock_google
            
            service = self.service._get_service_for_provider("google")
            
            assert service == mock_google
    
    def test_record_service_failure(self):
        """Test service failure recording"""
        self.service._record_service_failure("test_service", "Connection failed")
        
        assert "test_service" in self.service._service_failures
        failure_info = self.service._service_failures["test_service"]
        assert failure_info.failure_count == 1
        assert "Connection failed" in failure_info.last_error
    
    def test_should_retry_service(self):
        """Test retry logic"""
        # New service should be retryable
        assert self.service._should_retry_service("new_service") is True
        
        # Service with recent failure should be retryable after some time
        self.service._record_service_failure("test_service", "Error")
        assert self.service._should_retry_service("test_service") is False
    
    def test_set_default_provider(self):
        """Test setting default provider"""
        self.service.set_default_provider("openai")
        assert self.service._default_provider == "openai"


class TestLLMServiceSingleton:
    """Test LLM service singleton functionality"""
    
    def test_get_unified_llm_service_singleton(self):
        """Test that get_unified_llm_service returns singleton"""
        service1 = get_unified_llm_service()
        service2 = get_unified_llm_service()
        
        assert service1 is service2  # Same instance
    
    def test_service_instance_properties(self):
        """Test service instance has required properties"""
        service = get_unified_llm_service()
        
        assert hasattr(service, 'query')
        assert hasattr(service, 'get_all_providers_info')
        assert hasattr(service, 'get_connection_health_status')
        assert hasattr(service, 'test_all_connections')
        assert callable(service.query)
        assert callable(service.get_all_providers_info)


class TestLLMServiceIntegration:
    """Integration tests for LLM service"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_query_workflow(self):
        """Test complete query workflow"""
        service = UnifiedLLMService()
        
        # Mock a provider
        mock_provider = AsyncMock()
        mock_provider.query.return_value = "Integration test response"
        
        with patch.object(service, '_get_google_service') as mock_get:
            mock_get.return_value = mock_provider
            
            # Test query execution
            result = await service.query(
                prompt="Integration test prompt",
                provider="google",
                temperature=0.5
            )
            
            assert result == "Integration test response"
            mock_provider.query.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_provider_fallback_workflow(self):
        """Test provider fallback workflow"""
        service = UnifiedLLMService()
        
        # Mock providers - first fails, second succeeds
        mock_fallback = AsyncMock()
        mock_fallback.query.return_value = "Fallback success"
        
        with patch.object(service, '_get_openai_service') as mock_get_openai, \
             patch.object(service, '_get_google_service') as mock_get_google:
            
            mock_get_openai.return_value = None  # Unavailable
            mock_get_google.return_value = mock_fallback
            service._default_provider = 'google'
            
            # Should fallback to available provider
            result = await service.query(
                prompt="Test prompt",
                provider="openai"  # Request unavailable provider
            )
            
            assert result == "Fallback success"
            mock_fallback.query.assert_called_once()
    
    def test_provider_loading_integration(self):
        """Test provider loading integration"""
        service = UnifiedLLMService()
        
        with patch.object(service, '_get_google_service') as mock_google:
            mock_google.return_value = Mock()
            
            # Test that service can be loaded
            google_service = service._get_google_service()
            
            assert google_service is not None
            mock_google.assert_called() 