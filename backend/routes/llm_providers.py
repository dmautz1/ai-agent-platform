"""
LLM Provider routes for the AI Agent Platform.

Contains endpoints for:
- Google AI validation, models, and connection testing
- OpenAI validation, models, and connection testing  
- Grok validation, models, and connection testing
- Anthropic validation, models, and connection testing
- DeepSeek validation, models, and connection testing
- Llama validation, models, and connection testing
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List
from datetime import datetime, timezone

from logging_system import get_logger
from models import ApiResponse
from utils.responses import (
    create_success_response,
    create_error_response,
    api_response_validator
)

logger = get_logger(__name__)

router = APIRouter(tags=["llm-providers"])

# LLM Provider Response Types
ProviderValidationResponse = Dict[str, Any]
ProviderModelsResponse = Dict[str, Any]
ConnectionTestResponse = Dict[str, Any]

# Google AI endpoints
@router.get("/google-ai/validate", response_model=ApiResponse[ProviderValidationResponse])
@api_response_validator(result_type=ProviderValidationResponse)
async def validate_google_ai_setup():
    """Validate Google AI configuration - public endpoint for setup validation"""
    logger.info("Google AI configuration validation requested")
    
    try:
        from config.google_ai import validate_google_ai_environment
        validation_result = validate_google_ai_environment()
        
        is_valid = validation_result.get("valid", False)
        
        if is_valid:
            logger.info("Google AI configuration validation successful")
            result_data = {
                "status": "valid",
                "config": validation_result.get("config", {}),
                "provider": "google"
            }
            return create_success_response(
                result=result_data,
                message="Google AI is properly configured",
                metadata={
                    "provider": "google",
                    "endpoint": "validate",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
        else:
            logger.warning("Google AI configuration validation failed", errors=validation_result.get("errors", []))
            result_data = {
                "status": "invalid",
                "errors": validation_result.get("errors", []),
                "warnings": validation_result.get("warnings", []),
                "provider": "google"
            }
            return create_success_response(
                result=result_data,
                message="Google AI configuration has issues",
                metadata={
                    "provider": "google",
                    "endpoint": "validate",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
            
    except Exception as e:
        logger.error("Google AI validation failed with exception", exception=e)
        return create_error_response(
            error_message=str(e),
            message="Failed to validate Google AI configuration",
            metadata={
                "error_code": "GOOGLE_AI_VALIDATION_ERROR",
                "provider": "google",
                "endpoint": "validate",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )

@router.get("/google-ai/models", response_model=ApiResponse[ProviderModelsResponse])
@api_response_validator(result_type=ProviderModelsResponse)
async def get_available_models():
    """Get available Google AI models - public endpoint"""
    logger.info("Google AI models requested")
    
    try:
        from services.llm_service import get_unified_llm_service
        
        llm_service = get_unified_llm_service()
        models = await llm_service.get_available_models("google")
        
        result_data = {
            "models": models,
            "provider": "google"
        }
        
        return create_success_response(
            result=result_data,
            message="Google AI models retrieved",
            metadata={
                "provider": "google",
                "endpoint": "models",
                "model_count": len(models) if isinstance(models, list) else 0,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
        
    except Exception as e:
        logger.error("Google AI models retrieval failed", exception=e)
        return create_error_response(
            error_message=str(e),
            message="Failed to retrieve Google AI models",
            metadata={
                "error_code": "GOOGLE_AI_MODELS_ERROR",
                "provider": "google",
                "endpoint": "models",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )

@router.get("/google-ai/connection-test", response_model=ApiResponse[ConnectionTestResponse])
@api_response_validator(result_type=ConnectionTestResponse)
async def test_google_ai_connection():
    """Test Google AI connection - public endpoint"""
    logger.info("Google AI connection test requested")
    
    try:
        from services.llm_service import get_unified_llm_service
        
        llm_service = get_unified_llm_service()
        test_result = await llm_service.test_connection("google")
        
        if test_result.get("success", False):
            logger.info("Google AI connection test successful")
            result_data = {
                "status": "success",
                "response_time": test_result.get("response_time"),
                "provider": "google"
            }
            return create_success_response(
                result=result_data,
                message="Google AI connection successful",
                metadata={
                    "provider": "google",
                    "endpoint": "connection-test",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
        else:
            logger.warning("Google AI connection test failed", error=test_result.get("error"))
            result_data = {
                "status": "failed",
                "error": test_result.get("error"),
                "provider": "google"
            }
            return create_success_response(
                result=result_data,
                message="Google AI connection failed",
                metadata={
                    "provider": "google",
                    "endpoint": "connection-test",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
            
    except Exception as e:
        logger.error("Google AI connection test failed with exception", exception=e)
        return create_error_response(
            error_message=str(e),
            message="Google AI connection test error",
            metadata={
                "error_code": "GOOGLE_AI_CONNECTION_ERROR",
                "provider": "google",
                "endpoint": "connection-test",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )

# OpenAI endpoints
@router.get("/openai/validate", response_model=ApiResponse[ProviderValidationResponse])
@api_response_validator(result_type=ProviderValidationResponse)
async def validate_openai_setup():
    """Validate OpenAI configuration - public endpoint for setup validation"""
    logger.info("OpenAI configuration validation requested")
    
    try:
        from config.openai import validate_openai_environment
        validation_result = validate_openai_environment()
        
        is_valid = validation_result.get("valid", False)
        
        if is_valid:
            logger.info("OpenAI configuration validation successful")
            result_data = {
                "status": "valid",
                "config": validation_result.get("config", {}),
                "provider": "openai"
            }
            return create_success_response(
                result=result_data,
                message="OpenAI is properly configured",
                metadata={
                    "provider": "openai",
                    "endpoint": "validate",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
        else:
            logger.warning("OpenAI configuration validation failed", errors=validation_result.get("errors", []))
            result_data = {
                "status": "invalid",
                "errors": validation_result.get("errors", []),
                "warnings": validation_result.get("warnings", []),
                "provider": "openai"
            }
            return create_success_response(
                result=result_data,
                message="OpenAI configuration has issues",
                metadata={
                    "provider": "openai",
                    "endpoint": "validate",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
            
    except Exception as e:
        logger.error("OpenAI validation failed with exception", exception=e)
        return create_error_response(
            error_message=str(e),
            message="Failed to validate OpenAI configuration",
            metadata={
                "error_code": "OPENAI_VALIDATION_ERROR",
                "provider": "openai",
                "endpoint": "validate",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )

@router.get("/openai/models", response_model=ApiResponse[ProviderModelsResponse])
@api_response_validator(result_type=ProviderModelsResponse)
async def get_available_openai_models():
    """Get available OpenAI models - public endpoint"""
    logger.info("OpenAI models requested")
    
    try:
        from services.llm_service import get_unified_llm_service
        
        llm_service = get_unified_llm_service()
        models = await llm_service.get_available_models("openai")
        
        result_data = {
            "models": models,
            "provider": "openai"
        }
        
        return create_success_response(
            result=result_data,
            message="OpenAI models retrieved",
            metadata={
                "provider": "openai",
                "endpoint": "models",
                "model_count": len(models) if isinstance(models, list) else 0,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
        
    except Exception as e:
        logger.error("OpenAI models retrieval failed", exception=e)
        return create_error_response(
            error_message=str(e),
            message="Failed to retrieve OpenAI models",
            metadata={
                "error_code": "OPENAI_MODELS_ERROR",
                "provider": "openai",
                "endpoint": "models",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )

@router.get("/openai/connection-test", response_model=ApiResponse[ConnectionTestResponse])
@api_response_validator(result_type=ConnectionTestResponse)
async def test_openai_connection():
    """Test OpenAI connection - public endpoint"""
    logger.info("OpenAI connection test requested")
    
    try:
        from services.llm_service import get_unified_llm_service
        
        llm_service = get_unified_llm_service()
        test_result = await llm_service.test_connection("openai")
        
        if test_result.get("success", False):
            logger.info("OpenAI connection test successful")
            result_data = {
                "status": "success",
                "response_time": test_result.get("response_time"),
                "provider": "openai"
            }
            return create_success_response(
                result=result_data,
                message="OpenAI connection successful",
                metadata={
                    "provider": "openai",
                    "endpoint": "connection-test",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
        else:
            logger.warning("OpenAI connection test failed", error=test_result.get("error"))
            result_data = {
                "status": "failed",
                "error": test_result.get("error"),
                "provider": "openai"
            }
            return create_success_response(
                result=result_data,
                message="OpenAI connection failed",
                metadata={
                    "provider": "openai",
                    "endpoint": "connection-test",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
            
    except Exception as e:
        logger.error("OpenAI connection test failed with exception", exception=e)
        return create_error_response(
            error_message=str(e),
            message="OpenAI connection test error",
            metadata={
                "error_code": "OPENAI_CONNECTION_ERROR",
                "provider": "openai",
                "endpoint": "connection-test",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )

# Grok endpoints
@router.get("/grok/validate", response_model=ApiResponse[ProviderValidationResponse])
@api_response_validator(result_type=ProviderValidationResponse)
async def validate_grok_setup():
    """Validate Grok configuration - public endpoint for setup validation"""
    logger.info("Grok configuration validation requested")
    
    try:
        from config.grok import validate_grok_environment
        validation_result = validate_grok_environment()
        
        is_valid = validation_result.get("valid", False)
        
        if is_valid:
            logger.info("Grok configuration validation successful")
            result_data = {
                "status": "valid",
                "config": validation_result.get("config", {}),
                "provider": "grok"
            }
            return create_success_response(
                result=result_data,
                message="Grok is properly configured",
                metadata={
                    "provider": "grok",
                    "endpoint": "validate",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
        else:
            logger.warning("Grok configuration validation failed", errors=validation_result.get("errors", []))
            result_data = {
                "status": "invalid",
                "errors": validation_result.get("errors", []),
                "warnings": validation_result.get("warnings", []),
                "provider": "grok"
            }
            return create_success_response(
                result=result_data,
                message="Grok configuration has issues",
                metadata={
                    "provider": "grok",
                    "endpoint": "validate",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
            
    except Exception as e:
        logger.error("Grok validation failed with exception", exception=e)
        return create_error_response(
            error_message=str(e),
            message="Failed to validate Grok configuration",
            metadata={
                "error_code": "GROK_VALIDATION_ERROR",
                "provider": "grok",
                "endpoint": "validate",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )

@router.get("/grok/models", response_model=ApiResponse[ProviderModelsResponse])
@api_response_validator(result_type=ProviderModelsResponse)
async def get_available_grok_models():
    """Get available Grok models - public endpoint"""
    logger.info("Grok models requested")
    
    try:
        from services.llm_service import get_unified_llm_service
        
        llm_service = get_unified_llm_service()
        models = await llm_service.get_available_models("grok")
        
        result_data = {
            "models": models,
            "provider": "grok"
        }
        
        return create_success_response(
            result=result_data,
            message="Grok models retrieved",
            metadata={
                "provider": "grok",
                "endpoint": "models",
                "model_count": len(models) if isinstance(models, list) else 0,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
        
    except Exception as e:
        logger.error("Grok models retrieval failed", exception=e)
        return create_error_response(
            error_message=str(e),
            message="Failed to retrieve Grok models",
            metadata={
                "error_code": "GROK_MODELS_ERROR",
                "provider": "grok",
                "endpoint": "models",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )

@router.get("/grok/connection-test", response_model=ApiResponse[ConnectionTestResponse])
@api_response_validator(result_type=ConnectionTestResponse)
async def test_grok_connection():
    """Test Grok connection - public endpoint"""
    logger.info("Grok connection test requested")
    
    try:
        from services.llm_service import get_unified_llm_service
        
        llm_service = get_unified_llm_service()
        test_result = await llm_service.test_connection("grok")
        
        if test_result.get("success", False):
            logger.info("Grok connection test successful")
            result_data = {
                "status": "success",
                "response_time": test_result.get("response_time"),
                "provider": "grok"
            }
            return create_success_response(
                result=result_data,
                message="Grok connection successful",
                metadata={
                    "provider": "grok",
                    "endpoint": "connection-test",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
        else:
            logger.warning("Grok connection test failed", error=test_result.get("error"))
            result_data = {
                "status": "failed",
                "error": test_result.get("error"),
                "provider": "grok"
            }
            return create_success_response(
                result=result_data,
                message="Grok connection failed",
                metadata={
                    "provider": "grok",
                    "endpoint": "connection-test",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
            
    except Exception as e:
        logger.error("Grok connection test failed with exception", exception=e)
        return create_error_response(
            error_message=str(e),
            message="Grok connection test error",
            metadata={
                "error_code": "GROK_CONNECTION_ERROR",
                "provider": "grok",
                "endpoint": "connection-test",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )

# Anthropic endpoints
@router.get("/anthropic/validate", response_model=ApiResponse[ProviderValidationResponse])
@api_response_validator(result_type=ProviderValidationResponse)
async def validate_anthropic_setup():
    """Validate Anthropic configuration - public endpoint for setup validation"""
    logger.info("Anthropic configuration validation requested")
    
    try:
        from config.anthropic import validate_anthropic_environment
        validation_result = validate_anthropic_environment()
        
        is_valid = validation_result.get("valid", False)
        
        if is_valid:
            logger.info("Anthropic configuration validation successful")
            result_data = {
                "status": "valid",
                "config": validation_result.get("config", {}),
                "provider": "anthropic"
            }
            return create_success_response(
                result=result_data,
                message="Anthropic is properly configured",
                metadata={
                    "provider": "anthropic",
                    "endpoint": "validate",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
        else:
            logger.warning("Anthropic configuration validation failed", errors=validation_result.get("errors", []))
            result_data = {
                "status": "invalid",
                "errors": validation_result.get("errors", []),
                "warnings": validation_result.get("warnings", []),
                "provider": "anthropic"
            }
            return create_success_response(
                result=result_data,
                message="Anthropic configuration has issues",
                metadata={
                    "provider": "anthropic",
                    "endpoint": "validate",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
            
    except Exception as e:
        logger.error("Anthropic validation failed with exception", exception=e)
        return create_error_response(
            error_message=str(e),
            message="Failed to validate Anthropic configuration",
            metadata={
                "error_code": "ANTHROPIC_VALIDATION_ERROR",
                "provider": "anthropic",
                "endpoint": "validate",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )

@router.get("/anthropic/models", response_model=ApiResponse[ProviderModelsResponse])
@api_response_validator(result_type=ProviderModelsResponse)
async def get_available_anthropic_models():
    """Get available Anthropic models - public endpoint"""
    logger.info("Anthropic models requested")
    
    try:
        from services.llm_service import get_unified_llm_service
        
        llm_service = get_unified_llm_service()
        models = await llm_service.get_available_models("anthropic")
        
        result_data = {
            "models": models,
            "provider": "anthropic"
        }
        
        return create_success_response(
            result=result_data,
            message="Anthropic models retrieved",
            metadata={
                "provider": "anthropic",
                "endpoint": "models",
                "model_count": len(models) if isinstance(models, list) else 0,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
        
    except Exception as e:
        logger.error("Anthropic models retrieval failed", exception=e)
        return create_error_response(
            error_message=str(e),
            message="Failed to retrieve Anthropic models",
            metadata={
                "error_code": "ANTHROPIC_MODELS_ERROR",
                "provider": "anthropic",
                "endpoint": "models",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )

@router.get("/anthropic/connection-test", response_model=ApiResponse[ConnectionTestResponse])
@api_response_validator(result_type=ConnectionTestResponse)
async def test_anthropic_connection():
    """Test Anthropic connection - public endpoint"""
    logger.info("Anthropic connection test requested")
    
    try:
        from services.llm_service import get_unified_llm_service
        
        llm_service = get_unified_llm_service()
        test_result = await llm_service.test_connection("anthropic")
        
        if test_result.get("success", False):
            logger.info("Anthropic connection test successful")
            result_data = {
                "status": "success",
                "response_time": test_result.get("response_time"),
                "provider": "anthropic"
            }
            return create_success_response(
                result=result_data,
                message="Anthropic connection successful",
                metadata={
                    "provider": "anthropic",
                    "endpoint": "connection-test",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
        else:
            logger.warning("Anthropic connection test failed", error=test_result.get("error"))
            result_data = {
                "status": "failed",
                "error": test_result.get("error"),
                "provider": "anthropic"
            }
            return create_success_response(
                result=result_data,
                message="Anthropic connection failed",
                metadata={
                    "provider": "anthropic",
                    "endpoint": "connection-test",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
            
    except Exception as e:
        logger.error("Anthropic connection test failed with exception", exception=e)
        return create_error_response(
            error_message=str(e),
            message="Anthropic connection test error",
            metadata={
                "error_code": "ANTHROPIC_CONNECTION_ERROR",
                "provider": "anthropic",
                "endpoint": "connection-test",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )

# DeepSeek endpoints
@router.get("/deepseek/validate", response_model=ApiResponse[ProviderValidationResponse])
@api_response_validator(result_type=ProviderValidationResponse)
async def validate_deepseek_setup():
    """Validate DeepSeek configuration - public endpoint for setup validation"""
    logger.info("DeepSeek configuration validation requested")
    
    try:
        from config.deepseek import validate_deepseek_environment
        validation_result = validate_deepseek_environment()
        
        is_valid = validation_result.get("valid", False)
        
        if is_valid:
            logger.info("DeepSeek configuration validation successful")
            result_data = {
                "status": "valid",
                "config": validation_result.get("config", {}),
                "provider": "deepseek"
            }
            return create_success_response(
                result=result_data,
                message="DeepSeek is properly configured",
                metadata={
                    "provider": "deepseek",
                    "endpoint": "validate",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
        else:
            logger.warning("DeepSeek configuration validation failed", errors=validation_result.get("errors", []))
            result_data = {
                "status": "invalid",
                "errors": validation_result.get("errors", []),
                "warnings": validation_result.get("warnings", []),
                "provider": "deepseek"
            }
            return create_success_response(
                result=result_data,
                message="DeepSeek configuration has issues",
                metadata={
                    "provider": "deepseek",
                    "endpoint": "validate",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
            
    except Exception as e:
        logger.error("DeepSeek validation failed with exception", exception=e)
        return create_error_response(
            error_message=str(e),
            message="Failed to validate DeepSeek configuration",
            metadata={
                "error_code": "DEEPSEEK_VALIDATION_ERROR",
                "provider": "deepseek",
                "endpoint": "validate",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )

@router.get("/deepseek/models", response_model=ApiResponse[ProviderModelsResponse])
@api_response_validator(result_type=ProviderModelsResponse)
async def get_available_deepseek_models():
    """Get available DeepSeek models - public endpoint"""
    logger.info("DeepSeek models requested")
    
    try:
        from services.llm_service import get_unified_llm_service
        
        llm_service = get_unified_llm_service()
        models = await llm_service.get_available_models("deepseek")
        
        result_data = {
            "models": models,
            "provider": "deepseek"
        }
        
        return create_success_response(
            result=result_data,
            message="DeepSeek models retrieved",
            metadata={
                "provider": "deepseek",
                "endpoint": "models",
                "model_count": len(models) if isinstance(models, list) else 0,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
        
    except Exception as e:
        logger.error("DeepSeek models retrieval failed", exception=e)
        return create_error_response(
            error_message=str(e),
            message="Failed to retrieve DeepSeek models",
            metadata={
                "error_code": "DEEPSEEK_MODELS_ERROR",
                "provider": "deepseek",
                "endpoint": "models",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )

@router.get("/deepseek/connection-test", response_model=ApiResponse[ConnectionTestResponse])
@api_response_validator(result_type=ConnectionTestResponse)
async def test_deepseek_connection():
    """Test DeepSeek connection - public endpoint"""
    logger.info("DeepSeek connection test requested")
    
    try:
        from services.llm_service import get_unified_llm_service
        
        llm_service = get_unified_llm_service()
        test_result = await llm_service.test_connection("deepseek")
        
        if test_result.get("success", False):
            logger.info("DeepSeek connection test successful")
            result_data = {
                "status": "success",
                "response_time": test_result.get("response_time"),
                "provider": "deepseek"
            }
            return create_success_response(
                result=result_data,
                message="DeepSeek connection successful",
                metadata={
                    "provider": "deepseek",
                    "endpoint": "connection-test",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
        else:
            logger.warning("DeepSeek connection test failed", error=test_result.get("error"))
            result_data = {
                "status": "failed",
                "error": test_result.get("error"),
                "provider": "deepseek"
            }
            return create_success_response(
                result=result_data,
                message="DeepSeek connection failed",
                metadata={
                    "provider": "deepseek",
                    "endpoint": "connection-test",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
            
    except Exception as e:
        logger.error("DeepSeek connection test failed with exception", exception=e)
        return create_error_response(
            error_message=str(e),
            message="DeepSeek connection test error",
            metadata={
                "error_code": "DEEPSEEK_CONNECTION_ERROR",
                "provider": "deepseek",
                "endpoint": "connection-test",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )

# Llama endpoints
@router.get("/llama/validate", response_model=ApiResponse[ProviderValidationResponse])
@api_response_validator(result_type=ProviderValidationResponse)
async def validate_llama_setup():
    """Validate Llama configuration - public endpoint for setup validation"""
    logger.info("Llama configuration validation requested")
    
    try:
        from config.llama import validate_llama_environment
        validation_result = validate_llama_environment()
        
        is_valid = validation_result.get("valid", False)
        
        if is_valid:
            logger.info("Llama configuration validation successful")
            result_data = {
                "status": "valid",
                "config": validation_result.get("config", {}),
                "provider": "llama"
            }
            return create_success_response(
                result=result_data,
                message="Llama is properly configured",
                metadata={
                    "provider": "llama",
                    "endpoint": "validate",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
        else:
            logger.warning("Llama configuration validation failed", errors=validation_result.get("errors", []))
            result_data = {
                "status": "invalid",
                "errors": validation_result.get("errors", []),
                "warnings": validation_result.get("warnings", []),
                "provider": "llama"
            }
            return create_success_response(
                result=result_data,
                message="Llama configuration has issues",
                metadata={
                    "provider": "llama",
                    "endpoint": "validate",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
            
    except Exception as e:
        logger.error("Llama validation failed with exception", exception=e)
        return create_error_response(
            error_message=str(e),
            message="Failed to validate Llama configuration",
            metadata={
                "error_code": "LLAMA_VALIDATION_ERROR",
                "provider": "llama",
                "endpoint": "validate",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )

@router.get("/llama/models", response_model=ApiResponse[ProviderModelsResponse])
@api_response_validator(result_type=ProviderModelsResponse)
async def get_available_llama_models():
    """Get available Llama models - public endpoint"""
    logger.info("Llama models requested")
    
    try:
        from services.llm_service import get_unified_llm_service
        
        llm_service = get_unified_llm_service()
        models = await llm_service.get_available_models("llama")
        
        result_data = {
            "models": models,
            "provider": "llama"
        }
        
        return create_success_response(
            result=result_data,
            message="Llama models retrieved",
            metadata={
                "provider": "llama",
                "endpoint": "models",
                "model_count": len(models) if isinstance(models, list) else 0,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
        
    except Exception as e:
        logger.error("Llama models retrieval failed", exception=e)
        return create_error_response(
            error_message=str(e),
            message="Failed to retrieve Llama models",
            metadata={
                "error_code": "LLAMA_MODELS_ERROR",
                "provider": "llama",
                "endpoint": "models",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )

@router.get("/llama/connection-test", response_model=ApiResponse[ConnectionTestResponse])
@api_response_validator(result_type=ConnectionTestResponse)
async def test_llama_connection():
    """Test Llama connection - public endpoint"""
    logger.info("Llama connection test requested")
    
    try:
        from services.llm_service import get_unified_llm_service
        
        llm_service = get_unified_llm_service()
        test_result = await llm_service.test_connection("llama")
        
        if test_result.get("success", False):
            logger.info("Llama connection test successful")
            result_data = {
                "status": "success",
                "response_time": test_result.get("response_time"),
                "provider": "llama"
            }
            return create_success_response(
                result=result_data,
                message="Llama connection successful",
                metadata={
                    "provider": "llama",
                    "endpoint": "connection-test",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
        else:
            logger.warning("Llama connection test failed", error=test_result.get("error"))
            result_data = {
                "status": "failed",
                "error": test_result.get("error"),
                "provider": "llama"
            }
            return create_success_response(
                result=result_data,
                message="Llama connection failed",
                metadata={
                    "provider": "llama",
                    "endpoint": "connection-test",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
            
    except Exception as e:
        logger.error("Llama connection test failed with exception", exception=e)
        return create_error_response(
            error_message=str(e),
            message="Llama connection test error",
            metadata={
                "error_code": "LLAMA_CONNECTION_ERROR",
                "provider": "llama",
                "endpoint": "connection-test",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        ) 