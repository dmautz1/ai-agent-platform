"""
Comprehensive tests for LLM Provider routes.

Tests all 6 providers (Google AI, OpenAI, Grok, Anthropic, DeepSeek, Llama) 
with their validate, models, and connection-test endpoints.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from fastapi import FastAPI

from routes.llm_providers import router
from models import ApiResponse


@pytest.fixture
def app():
    """Create FastAPI app with LLM providers router."""
    app = FastAPI()
    app.include_router(router, prefix="/llm")
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


class TestGoogleAIRoutes:
    """Test Google AI provider endpoints."""

    def test_validate_google_ai_setup_success(self, client):
        """Test successful Google AI validation."""
        with patch('config.google_ai.validate_google_ai_environment') as mock_validate:
            mock_validate.return_value = {
                "valid": True,
                "config": {
                    "api_key_configured": True,
                    "project_id": "test-project"
                }
            }
            
            response = client.get("/llm/google-ai/validate")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["result"]["status"] == "valid"
            assert data["result"]["provider"] == "google"
            assert "Google AI is properly configured" in data["message"]

    def test_validate_google_ai_setup_invalid(self, client):
        """Test Google AI validation with invalid config."""
        with patch('config.google_ai.validate_google_ai_environment') as mock_validate:
            mock_validate.return_value = {
                "valid": False,
                "errors": ["API key not configured"],
                "warnings": ["Project ID not set"]
            }
            
            response = client.get("/llm/google-ai/validate")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["result"]["status"] == "invalid"
            assert data["result"]["errors"] == ["API key not configured"]
            assert data["result"]["warnings"] == ["Project ID not set"]

    def test_validate_google_ai_setup_exception(self, client):
        """Test Google AI validation with exception."""
        with patch('config.google_ai.validate_google_ai_environment') as mock_validate:
            mock_validate.side_effect = Exception("Validation failed")
            
            response = client.get("/llm/google-ai/validate")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is False
            assert "Validation failed" in data["error"]

    @pytest.mark.asyncio
    async def test_get_google_ai_models_success(self, client):
        """Test successful Google AI models retrieval."""
        mock_models = [
            {"id": "gemini-pro", "name": "Gemini Pro"},
            {"id": "gemini-pro-vision", "name": "Gemini Pro Vision"}
        ]
        
        with patch('services.llm_service.get_unified_llm_service') as mock_service:
            mock_llm_service = AsyncMock()
            mock_llm_service.get_available_models.return_value = mock_models
            mock_service.return_value = mock_llm_service
            
            response = client.get("/llm/google-ai/models")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["result"]["models"] == mock_models
            assert data["result"]["provider"] == "google"

    @pytest.mark.asyncio
    async def test_get_google_ai_models_exception(self, client):
        """Test Google AI models retrieval with exception."""
        with patch('services.llm_service.get_unified_llm_service') as mock_service:
            mock_llm_service = AsyncMock()
            mock_llm_service.get_available_models.side_effect = Exception("Models fetch failed")
            mock_service.return_value = mock_llm_service
            
            response = client.get("/llm/google-ai/models")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is False
            assert "Models fetch failed" in data["error"]

    @pytest.mark.asyncio
    async def test_google_ai_connection_test_success(self, client):
        """Test successful Google AI connection test."""
        with patch('services.llm_service.get_unified_llm_service') as mock_service:
            mock_llm_service = AsyncMock()
            mock_llm_service.test_connection.return_value = {
                "success": True,
                "response_time": 0.5
            }
            mock_service.return_value = mock_llm_service
            
            response = client.get("/llm/google-ai/connection-test")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["result"]["status"] == "success"
            assert data["result"]["response_time"] == 0.5

    @pytest.mark.asyncio
    async def test_google_ai_connection_test_failed(self, client):
        """Test Google AI connection test failure."""
        with patch('services.llm_service.get_unified_llm_service') as mock_service:
            mock_llm_service = AsyncMock()
            mock_llm_service.test_connection.return_value = {
                "success": False,
                "error": "Connection timeout"
            }
            mock_service.return_value = mock_llm_service
            
            response = client.get("/llm/google-ai/connection-test")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["result"]["status"] == "failed"
            assert data["result"]["error"] == "Connection timeout"

    @pytest.mark.asyncio
    async def test_google_ai_connection_test_exception(self, client):
        """Test Google AI connection test with exception."""
        with patch('services.llm_service.get_unified_llm_service') as mock_service:
            mock_llm_service = AsyncMock()
            mock_llm_service.test_connection.side_effect = Exception("Connection error")
            mock_service.return_value = mock_llm_service
            
            response = client.get("/llm/google-ai/connection-test")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is False
            assert "Connection error" in data["error"]


class TestOpenAIRoutes:
    """Test OpenAI provider endpoints."""

    def test_validate_openai_setup_success(self, client):
        """Test successful OpenAI validation."""
        with patch('config.openai.validate_openai_environment') as mock_validate:
            mock_validate.return_value = {
                "valid": True,
                "config": {"api_key_configured": True}
            }
            
            response = client.get("/llm/openai/validate")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["result"]["status"] == "valid"
            assert data["result"]["provider"] == "openai"

    def test_validate_openai_setup_invalid(self, client):
        """Test OpenAI validation with invalid config."""
        with patch('config.openai.validate_openai_environment') as mock_validate:
            mock_validate.return_value = {
                "valid": False,
                "errors": ["API key missing"]
            }
            
            response = client.get("/llm/openai/validate")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["result"]["status"] == "invalid"
            assert data["result"]["errors"] == ["API key missing"]

    @pytest.mark.asyncio
    async def test_get_openai_models_success(self, client):
        """Test successful OpenAI models retrieval."""
        mock_models = [
            {"id": "gpt-4", "name": "GPT-4"},
            {"id": "gpt-3.5-turbo", "name": "GPT-3.5 Turbo"}
        ]
        
        with patch('services.llm_service.get_unified_llm_service') as mock_service:
            mock_llm_service = AsyncMock()
            mock_llm_service.get_available_models.return_value = mock_models
            mock_service.return_value = mock_llm_service
            
            response = client.get("/llm/openai/models")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["result"]["models"] == mock_models
            assert data["result"]["provider"] == "openai"

    @pytest.mark.asyncio
    async def test_openai_connection_test_success(self, client):
        """Test successful OpenAI connection test."""
        with patch('services.llm_service.get_unified_llm_service') as mock_service:
            mock_llm_service = AsyncMock()
            mock_llm_service.test_connection.return_value = {
                "success": True,
                "response_time": 0.3
            }
            mock_service.return_value = mock_llm_service
            
            response = client.get("/llm/openai/connection-test")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["result"]["status"] == "success"
            assert data["result"]["response_time"] == 0.3


class TestGrokRoutes:
    """Test Grok provider endpoints."""

    def test_validate_grok_setup_success(self, client):
        """Test successful Grok validation."""
        with patch('config.grok.validate_grok_environment') as mock_validate:
            mock_validate.return_value = {
                "valid": True,
                "config": {"api_key_configured": True}
            }
            
            response = client.get("/llm/grok/validate")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["result"]["status"] == "valid"
            assert data["result"]["provider"] == "grok"

    @pytest.mark.asyncio
    async def test_get_grok_models_success(self, client):
        """Test successful Grok models retrieval."""
        mock_models = [{"id": "grok-1", "name": "Grok-1"}]
        
        with patch('services.llm_service.get_unified_llm_service') as mock_service:
            mock_llm_service = AsyncMock()
            mock_llm_service.get_available_models.return_value = mock_models
            mock_service.return_value = mock_llm_service
            
            response = client.get("/llm/grok/models")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["result"]["models"] == mock_models
            assert data["result"]["provider"] == "grok"

    @pytest.mark.asyncio
    async def test_grok_connection_test_success(self, client):
        """Test successful Grok connection test."""
        with patch('services.llm_service.get_unified_llm_service') as mock_service:
            mock_llm_service = AsyncMock()
            mock_llm_service.test_connection.return_value = {
                "success": True,
                "response_time": 0.4
            }
            mock_service.return_value = mock_llm_service
            
            response = client.get("/llm/grok/connection-test")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["result"]["status"] == "success"


class TestAnthropicRoutes:
    """Test Anthropic provider endpoints."""

    def test_validate_anthropic_setup_success(self, client):
        """Test successful Anthropic validation."""
        with patch('config.anthropic.validate_anthropic_environment') as mock_validate:
            mock_validate.return_value = {
                "valid": True,
                "config": {"api_key_configured": True}
            }
            
            response = client.get("/llm/anthropic/validate")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["result"]["status"] == "valid"
            assert data["result"]["provider"] == "anthropic"

    @pytest.mark.asyncio
    async def test_get_anthropic_models_success(self, client):
        """Test successful Anthropic models retrieval."""
        mock_models = [
            {"id": "claude-3-opus", "name": "Claude 3 Opus"},
            {"id": "claude-3-sonnet", "name": "Claude 3 Sonnet"}
        ]
        
        with patch('services.llm_service.get_unified_llm_service') as mock_service:
            mock_llm_service = AsyncMock()
            mock_llm_service.get_available_models.return_value = mock_models
            mock_service.return_value = mock_llm_service
            
            response = client.get("/llm/anthropic/models")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["result"]["models"] == mock_models
            assert data["result"]["provider"] == "anthropic"

    @pytest.mark.asyncio
    async def test_anthropic_connection_test_success(self, client):
        """Test successful Anthropic connection test."""
        with patch('services.llm_service.get_unified_llm_service') as mock_service:
            mock_llm_service = AsyncMock()
            mock_llm_service.test_connection.return_value = {
                "success": True,
                "response_time": 0.6
            }
            mock_service.return_value = mock_llm_service
            
            response = client.get("/llm/anthropic/connection-test")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["result"]["status"] == "success"


class TestDeepSeekRoutes:
    """Test DeepSeek provider endpoints."""

    def test_validate_deepseek_setup_success(self, client):
        """Test successful DeepSeek validation."""
        with patch('config.deepseek.validate_deepseek_environment') as mock_validate:
            mock_validate.return_value = {
                "valid": True,
                "config": {"api_key_configured": True}
            }
            
            response = client.get("/llm/deepseek/validate")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["result"]["status"] == "valid"
            assert data["result"]["provider"] == "deepseek"

    def test_validate_deepseek_setup_exception(self, client):
        """Test DeepSeek validation with exception."""
        with patch('config.deepseek.validate_deepseek_environment') as mock_validate:
            mock_validate.side_effect = Exception("DeepSeek validation error")
            
            response = client.get("/llm/deepseek/validate")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is False
            assert "DeepSeek validation error" in data["error"]

    @pytest.mark.asyncio
    async def test_get_deepseek_models_success(self, client):
        """Test successful DeepSeek models retrieval."""
        mock_models = [{"id": "deepseek-chat", "name": "DeepSeek Chat"}]
        
        with patch('services.llm_service.get_unified_llm_service') as mock_service:
            mock_llm_service = AsyncMock()
            mock_llm_service.get_available_models.return_value = mock_models
            mock_service.return_value = mock_llm_service
            
            response = client.get("/llm/deepseek/models")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["result"]["models"] == mock_models
            assert data["result"]["provider"] == "deepseek"

    @pytest.mark.asyncio
    async def test_deepseek_connection_test_failed(self, client):
        """Test DeepSeek connection test failure."""
        with patch('services.llm_service.get_unified_llm_service') as mock_service:
            mock_llm_service = AsyncMock()
            mock_llm_service.test_connection.return_value = {
                "success": False,
                "error": "API key invalid"
            }
            mock_service.return_value = mock_llm_service
            
            response = client.get("/llm/deepseek/connection-test")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["result"]["status"] == "failed"
            assert data["result"]["error"] == "API key invalid"


class TestLlamaRoutes:
    """Test Llama provider endpoints."""

    def test_validate_llama_setup_success(self, client):
        """Test successful Llama validation."""
        with patch('config.llama.validate_llama_environment') as mock_validate:
            mock_validate.return_value = {
                "valid": True,
                "config": {"api_key_configured": True}
            }
            
            response = client.get("/llm/llama/validate")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["result"]["status"] == "valid"
            assert data["result"]["provider"] == "llama"

    def test_validate_llama_setup_invalid(self, client):
        """Test Llama validation with invalid config."""
        with patch('config.llama.validate_llama_environment') as mock_validate:
            mock_validate.return_value = {
                "valid": False,
                "errors": ["Hugging Face token missing"],
                "warnings": ["Model not cached"]
            }
            
            response = client.get("/llm/llama/validate")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["result"]["status"] == "invalid"
            assert data["result"]["errors"] == ["Hugging Face token missing"]
            assert data["result"]["warnings"] == ["Model not cached"]

    @pytest.mark.asyncio
    async def test_get_llama_models_success(self, client):
        """Test successful Llama models retrieval."""
        mock_models = [
            {"id": "llama-2-7b", "name": "Llama 2 7B"},
            {"id": "llama-2-13b", "name": "Llama 2 13B"}
        ]
        
        with patch('services.llm_service.get_unified_llm_service') as mock_service:
            mock_llm_service = AsyncMock()
            mock_llm_service.get_available_models.return_value = mock_models
            mock_service.return_value = mock_llm_service
            
            response = client.get("/llm/llama/models")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["result"]["models"] == mock_models
            assert data["result"]["provider"] == "llama"

    @pytest.mark.asyncio
    async def test_get_llama_models_exception(self, client):
        """Test Llama models retrieval with exception."""
        with patch('services.llm_service.get_unified_llm_service') as mock_service:
            mock_llm_service = AsyncMock()
            mock_llm_service.get_available_models.side_effect = Exception("Model load failed")
            mock_service.return_value = mock_llm_service
            
            response = client.get("/llm/llama/models")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is False
            assert "Model load failed" in data["error"]

    @pytest.mark.asyncio
    async def test_llama_connection_test_success(self, client):
        """Test successful Llama connection test."""
        with patch('services.llm_service.get_unified_llm_service') as mock_service:
            mock_llm_service = AsyncMock()
            mock_llm_service.test_connection.return_value = {
                "success": True,
                "response_time": 1.2
            }
            mock_service.return_value = mock_llm_service
            
            response = client.get("/llm/llama/connection-test")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["result"]["status"] == "success"
            assert data["result"]["response_time"] == 1.2


class TestCrossProviderFunctionality:
    """Test cross-provider functionality and edge cases."""

    def test_all_providers_validation_endpoints_exist(self, client):
        """Test that all provider validation endpoints exist."""
        provider_configs = [
            ("google-ai", "config.google_ai.validate_google_ai_environment"),
            ("openai", "config.openai.validate_openai_environment"),
            ("grok", "config.grok.validate_grok_environment"),
            ("anthropic", "config.anthropic.validate_anthropic_environment"),
            ("deepseek", "config.deepseek.validate_deepseek_environment"),
            ("llama", "config.llama.validate_llama_environment")
        ]
        
        for provider, config_path in provider_configs:
            with patch(config_path) as mock_validate:
                mock_validate.return_value = {"valid": True, "config": {}}
                
                response = client.get(f"/llm/{provider}/validate")
                assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_all_providers_models_endpoints_exist(self, client):
        """Test that all provider models endpoints exist."""
        providers = ["google-ai", "openai", "grok", "anthropic", "deepseek", "llama"]
        
        for provider in providers:
            with patch('services.llm_service.get_unified_llm_service') as mock_service:
                mock_llm_service = AsyncMock()
                mock_llm_service.get_available_models.return_value = []
                mock_service.return_value = mock_llm_service
                
                response = client.get(f"/llm/{provider}/models")
                assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_all_providers_connection_test_endpoints_exist(self, client):
        """Test that all provider connection test endpoints exist."""
        providers = ["google-ai", "openai", "grok", "anthropic", "deepseek", "llama"]
        
        for provider in providers:
            with patch('services.llm_service.get_unified_llm_service') as mock_service:
                mock_llm_service = AsyncMock()
                mock_llm_service.test_connection.return_value = {"success": True}
                mock_service.return_value = mock_llm_service
                
                response = client.get(f"/llm/{provider}/connection-test")
                assert response.status_code == 200

    def test_response_metadata_consistency(self, client):
        """Test that all responses have consistent metadata structure."""
        with patch('config.google_ai.validate_google_ai_environment') as mock_validate:
            mock_validate.return_value = {"valid": True, "config": {}}
            
            response = client.get("/llm/google-ai/validate")
            data = response.json()
            
            assert "metadata" in data
            assert "provider" in data["metadata"]
            assert "endpoint" in data["metadata"]
            assert "timestamp" in data["metadata"]
            assert data["metadata"]["provider"] == "google"
            assert data["metadata"]["endpoint"] == "validate"

    def test_error_response_format_consistency(self, client):
        """Test that error responses have consistent format across providers."""
        with patch('config.openai.validate_openai_environment') as mock_validate:
            mock_validate.side_effect = Exception("Test error")
            
            response = client.get("/llm/openai/validate")
            data = response.json()
            
            assert data["success"] is False
            assert "error" in data
            assert "metadata" in data
            assert data["metadata"]["error_code"] == "OPENAI_VALIDATION_ERROR"

    @pytest.mark.asyncio
    async def test_models_response_empty_list_handling(self, client):
        """Test handling of empty models list."""
        with patch('services.llm_service.get_unified_llm_service') as mock_service:
            mock_llm_service = AsyncMock()
            mock_llm_service.get_available_models.return_value = []
            mock_service.return_value = mock_llm_service
            
            response = client.get("/llm/anthropic/models")
            data = response.json()
            
            assert response.status_code == 200
            assert data["success"] is True
            assert data["result"]["models"] == []
            assert data["metadata"]["model_count"] == 0 