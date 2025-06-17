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

from logging_system import get_logger, get_performance_logger

logger = get_logger(__name__)
perf_logger = get_performance_logger()

router = APIRouter(tags=["llm-providers"])

# Google AI endpoints
@router.get("/google-ai/validate")
async def validate_google_ai_setup():
    """Validate Google AI configuration - public endpoint for setup validation"""
    with perf_logger.time_operation("google_ai_validate"):
        logger.info("Google AI configuration validation requested")
        
        try:
            from config.google_ai import validate_google_ai_environment
            validation_result = validate_google_ai_environment()
            
            is_valid = validation_result.get("valid", False)
            
            if is_valid:
                logger.info("Google AI configuration validation successful")
                return {
                    "status": "valid",
                    "message": "Google AI is properly configured",
                    "config": validation_result.get("config", {})
                }
            else:
                logger.warning("Google AI configuration validation failed", errors=validation_result.get("errors", []))
                return {
                    "status": "invalid", 
                    "message": "Google AI configuration has issues",
                    "errors": validation_result.get("errors", []),
                    "warnings": validation_result.get("warnings", [])
                }
                
        except Exception as e:
            logger.error("Google AI validation failed with exception", exception=e)
            return {
                "status": "error",
                "message": "Failed to validate Google AI configuration",
                "error": str(e)
            }

@router.get("/google-ai/models")
async def get_available_models():
    """Get available Google AI models - public endpoint"""
    with perf_logger.time_operation("google_ai_models"):
        logger.info("Google AI models requested")
        
        try:
            from services.llm_service import get_unified_llm_service
            
            llm_service = get_unified_llm_service()
            models = await llm_service.get_available_models("google")
            
            return {
                "status": "success",
                "message": "Google AI models retrieved",
                "models": models,
                "provider": "google"
            }
            
        except Exception as e:
            logger.error("Google AI models retrieval failed", exception=e)
            return {
                "status": "error",
                "message": "Failed to retrieve Google AI models",
                "error": str(e)
            }

@router.get("/google-ai/connection-test")
async def test_google_ai_connection():
    """Test Google AI connection - public endpoint"""
    with perf_logger.time_operation("google_ai_connection_test"):
        logger.info("Google AI connection test requested")
        
        try:
            from services.llm_service import get_unified_llm_service
            
            llm_service = get_unified_llm_service()
            test_result = await llm_service.test_connection("google")
            
            if test_result.get("success", False):
                logger.info("Google AI connection test successful")
                return {
                    "status": "success",
                    "message": "Google AI connection successful",
                    "response_time": test_result.get("response_time"),
                    "provider": "google"
                }
            else:
                logger.warning("Google AI connection test failed", error=test_result.get("error"))
                return {
                    "status": "failed",
                    "message": "Google AI connection failed",
                    "error": test_result.get("error"),
                    "provider": "google"
                }
                
        except Exception as e:
            logger.error("Google AI connection test failed with exception", exception=e)
            return {
                "status": "error",
                "message": "Google AI connection test error",
                "error": str(e)
            }

# OpenAI endpoints
@router.get("/openai/validate")
async def validate_openai_setup():
    """Validate OpenAI configuration - public endpoint for setup validation"""
    with perf_logger.time_operation("openai_validate"):
        logger.info("OpenAI configuration validation requested")
        
        try:
            from config.openai import validate_openai_environment
            validation_result = validate_openai_environment()
            
            is_valid = validation_result.get("valid", False)
            
            if is_valid:
                logger.info("OpenAI configuration validation successful")
                return {
                    "status": "valid",
                    "message": "OpenAI is properly configured",
                    "config": validation_result.get("config", {})
                }
            else:
                logger.warning("OpenAI configuration validation failed", errors=validation_result.get("errors", []))
                return {
                    "status": "invalid", 
                    "message": "OpenAI configuration has issues",
                    "errors": validation_result.get("errors", []),
                    "warnings": validation_result.get("warnings", [])
                }
                
        except Exception as e:
            logger.error("OpenAI validation failed with exception", exception=e)
            return {
                "status": "error",
                "message": "Failed to validate OpenAI configuration",
                "error": str(e)
            }

@router.get("/openai/models")
async def get_available_openai_models():
    """Get available OpenAI models - public endpoint"""
    with perf_logger.time_operation("openai_models"):
        logger.info("OpenAI models requested")
        
        try:
            from services.llm_service import get_unified_llm_service
            
            llm_service = get_unified_llm_service()
            models = await llm_service.get_available_models("openai")
            
            return {
                "status": "success",
                "message": "OpenAI models retrieved",
                "models": models,
                "provider": "openai"
            }
            
        except Exception as e:
            logger.error("OpenAI models retrieval failed", exception=e)
            return {
                "status": "error",
                "message": "Failed to retrieve OpenAI models",
                "error": str(e)
            }

@router.get("/openai/connection-test")
async def test_openai_connection():
    """Test OpenAI connection - public endpoint"""
    with perf_logger.time_operation("openai_connection_test"):
        logger.info("OpenAI connection test requested")
        
        try:
            from services.llm_service import get_unified_llm_service
            
            llm_service = get_unified_llm_service()
            test_result = await llm_service.test_connection("openai")
            
            if test_result.get("success", False):
                logger.info("OpenAI connection test successful")
                return {
                    "status": "success",
                    "message": "OpenAI connection successful",
                    "response_time": test_result.get("response_time"),
                    "provider": "openai"
                }
            else:
                logger.warning("OpenAI connection test failed", error=test_result.get("error"))
                return {
                    "status": "failed",
                    "message": "OpenAI connection failed",
                    "error": test_result.get("error"),
                    "provider": "openai"
                }
                
        except Exception as e:
            logger.error("OpenAI connection test failed with exception", exception=e)
            return {
                "status": "error",
                "message": "OpenAI connection test error",
                "error": str(e)
            }

# Grok endpoints
@router.get("/grok/validate")
async def validate_grok_setup():
    """Validate Grok configuration - public endpoint for setup validation"""
    with perf_logger.time_operation("grok_validate"):
        logger.info("Grok configuration validation requested")
        
        try:
            from config.grok import validate_grok_environment
            validation_result = validate_grok_environment()
            
            is_valid = validation_result.get("valid", False)
            
            if is_valid:
                logger.info("Grok configuration validation successful")
                return {
                    "status": "valid",
                    "message": "Grok is properly configured",
                    "config": validation_result.get("config", {})
                }
            else:
                logger.warning("Grok configuration validation failed", errors=validation_result.get("errors", []))
                return {
                    "status": "invalid", 
                    "message": "Grok configuration has issues",
                    "errors": validation_result.get("errors", []),
                    "warnings": validation_result.get("warnings", [])
                }
                
        except Exception as e:
            logger.error("Grok validation failed with exception", exception=e)
            return {
                "status": "error",
                "message": "Failed to validate Grok configuration",
                "error": str(e)
            }

@router.get("/grok/models")
async def get_available_grok_models():
    """Get available Grok models - public endpoint"""
    with perf_logger.time_operation("grok_models"):
        logger.info("Grok models requested")
        
        try:
            from services.llm_service import get_unified_llm_service
            
            llm_service = get_unified_llm_service()
            models = await llm_service.get_available_models("grok")
            
            return {
                "status": "success",
                "message": "Grok models retrieved",
                "models": models,
                "provider": "grok"
            }
            
        except Exception as e:
            logger.error("Grok models retrieval failed", exception=e)
            return {
                "status": "error",
                "message": "Failed to retrieve Grok models",
                "error": str(e)
            }

@router.get("/grok/connection-test")
async def test_grok_connection():
    """Test Grok connection - public endpoint"""
    with perf_logger.time_operation("grok_connection_test"):
        logger.info("Grok connection test requested")
        
        try:
            from services.llm_service import get_unified_llm_service
            
            llm_service = get_unified_llm_service()
            test_result = await llm_service.test_connection("grok")
            
            if test_result.get("success", False):
                logger.info("Grok connection test successful")
                return {
                    "status": "success",
                    "message": "Grok connection successful",
                    "response_time": test_result.get("response_time"),
                    "provider": "grok"
                }
            else:
                logger.warning("Grok connection test failed", error=test_result.get("error"))
                return {
                    "status": "failed",
                    "message": "Grok connection failed",
                    "error": test_result.get("error"),
                    "provider": "grok"
                }
                
        except Exception as e:
            logger.error("Grok connection test failed with exception", exception=e)
            return {
                "status": "error",
                "message": "Grok connection test error",
                "error": str(e)
            }

# Anthropic endpoints
@router.get("/anthropic/validate")
async def validate_anthropic_setup():
    """Validate Anthropic configuration - public endpoint for setup validation"""
    with perf_logger.time_operation("anthropic_validate"):
        logger.info("Anthropic configuration validation requested")
        
        try:
            from config.anthropic import validate_anthropic_environment
            validation_result = validate_anthropic_environment()
            
            is_valid = validation_result.get("valid", False)
            
            if is_valid:
                logger.info("Anthropic configuration validation successful")
                return {
                    "status": "valid",
                    "message": "Anthropic is properly configured",
                    "config": validation_result.get("config", {})
                }
            else:
                logger.warning("Anthropic configuration validation failed", errors=validation_result.get("errors", []))
                return {
                    "status": "invalid", 
                    "message": "Anthropic configuration has issues",
                    "errors": validation_result.get("errors", []),
                    "warnings": validation_result.get("warnings", [])
                }
                
        except Exception as e:
            logger.error("Anthropic validation failed with exception", exception=e)
            return {
                "status": "error",
                "message": "Failed to validate Anthropic configuration",
                "error": str(e)
            }

@router.get("/anthropic/models")
async def get_available_anthropic_models():
    """Get available Anthropic models - public endpoint"""
    with perf_logger.time_operation("anthropic_models"):
        logger.info("Anthropic models requested")
        
        try:
            from services.llm_service import get_unified_llm_service
            
            llm_service = get_unified_llm_service()
            models = await llm_service.get_available_models("anthropic")
            
            return {
                "status": "success",
                "message": "Anthropic models retrieved",
                "models": models,
                "provider": "anthropic"
            }
            
        except Exception as e:
            logger.error("Anthropic models retrieval failed", exception=e)
            return {
                "status": "error",
                "message": "Failed to retrieve Anthropic models",
                "error": str(e)
            }

@router.get("/anthropic/connection-test")
async def test_anthropic_connection():
    """Test Anthropic connection - public endpoint"""
    with perf_logger.time_operation("anthropic_connection_test"):
        logger.info("Anthropic connection test requested")
        
        try:
            from services.llm_service import get_unified_llm_service
            
            llm_service = get_unified_llm_service()
            test_result = await llm_service.test_connection("anthropic")
            
            if test_result.get("success", False):
                logger.info("Anthropic connection test successful")
                return {
                    "status": "success",
                    "message": "Anthropic connection successful",
                    "response_time": test_result.get("response_time"),
                    "provider": "anthropic"
                }
            else:
                logger.warning("Anthropic connection test failed", error=test_result.get("error"))
                return {
                    "status": "failed",
                    "message": "Anthropic connection failed",
                    "error": test_result.get("error"),
                    "provider": "anthropic"
                }
                
        except Exception as e:
            logger.error("Anthropic connection test failed with exception", exception=e)
            return {
                "status": "error",
                "message": "Anthropic connection test error",
                "error": str(e)
            }

# DeepSeek endpoints
@router.get("/deepseek/validate")
async def validate_deepseek_setup():
    """Validate DeepSeek configuration - public endpoint for setup validation"""
    with perf_logger.time_operation("deepseek_validate"):
        logger.info("DeepSeek configuration validation requested")
        
        try:
            from config.deepseek import validate_deepseek_environment
            validation_result = validate_deepseek_environment()
            
            is_valid = validation_result.get("valid", False)
            
            if is_valid:
                logger.info("DeepSeek configuration validation successful")
                return {
                    "status": "valid",
                    "message": "DeepSeek is properly configured",
                    "config": validation_result.get("config", {})
                }
            else:
                logger.warning("DeepSeek configuration validation failed", errors=validation_result.get("errors", []))
                return {
                    "status": "invalid", 
                    "message": "DeepSeek configuration has issues",
                    "errors": validation_result.get("errors", []),
                    "warnings": validation_result.get("warnings", [])
                }
                
        except Exception as e:
            logger.error("DeepSeek validation failed with exception", exception=e)
            return {
                "status": "error",
                "message": "Failed to validate DeepSeek configuration",
                "error": str(e)
            }

@router.get("/deepseek/models")
async def get_available_deepseek_models():
    """Get available DeepSeek models - public endpoint"""
    with perf_logger.time_operation("deepseek_models"):
        logger.info("DeepSeek models requested")
        
        try:
            from services.llm_service import get_unified_llm_service
            
            llm_service = get_unified_llm_service()
            models = await llm_service.get_available_models("deepseek")
            
            return {
                "status": "success",
                "message": "DeepSeek models retrieved",
                "models": models,
                "provider": "deepseek"
            }
            
        except Exception as e:
            logger.error("DeepSeek models retrieval failed", exception=e)
            return {
                "status": "error",
                "message": "Failed to retrieve DeepSeek models",
                "error": str(e)
            }

@router.get("/deepseek/connection-test")
async def test_deepseek_connection():
    """Test DeepSeek connection - public endpoint"""
    with perf_logger.time_operation("deepseek_connection_test"):
        logger.info("DeepSeek connection test requested")
        
        try:
            from services.llm_service import get_unified_llm_service
            
            llm_service = get_unified_llm_service()
            test_result = await llm_service.test_connection("deepseek")
            
            if test_result.get("success", False):
                logger.info("DeepSeek connection test successful")
                return {
                    "status": "success",
                    "message": "DeepSeek connection successful",
                    "response_time": test_result.get("response_time"),
                    "provider": "deepseek"
                }
            else:
                logger.warning("DeepSeek connection test failed", error=test_result.get("error"))
                return {
                    "status": "failed",
                    "message": "DeepSeek connection failed",
                    "error": test_result.get("error"),
                    "provider": "deepseek"
                }
                
        except Exception as e:
            logger.error("DeepSeek connection test failed with exception", exception=e)
            return {
                "status": "error",
                "message": "DeepSeek connection test error",
                "error": str(e)
            }

# Llama endpoints
@router.get("/llama/validate")
async def validate_llama_setup():
    """Validate Llama configuration - public endpoint for setup validation"""
    with perf_logger.time_operation("llama_validate"):
        logger.info("Llama configuration validation requested")
        
        try:
            from config.llama import validate_llama_environment
            validation_result = validate_llama_environment()
            
            is_valid = validation_result.get("valid", False)
            
            if is_valid:
                logger.info("Llama configuration validation successful")
                return {
                    "status": "valid",
                    "message": "Llama is properly configured",
                    "config": validation_result.get("config", {})
                }
            else:
                logger.warning("Llama configuration validation failed", errors=validation_result.get("errors", []))
                return {
                    "status": "invalid", 
                    "message": "Llama configuration has issues",
                    "errors": validation_result.get("errors", []),
                    "warnings": validation_result.get("warnings", [])
                }
                
        except Exception as e:
            logger.error("Llama validation failed with exception", exception=e)
            return {
                "status": "error",
                "message": "Failed to validate Llama configuration",
                "error": str(e)
            }

@router.get("/llama/models")
async def get_available_llama_models():
    """Get available Llama models - public endpoint"""
    with perf_logger.time_operation("llama_models"):
        logger.info("Llama models requested")
        
        try:
            from services.llm_service import get_unified_llm_service
            
            llm_service = get_unified_llm_service()
            models = await llm_service.get_available_models("llama")
            
            return {
                "status": "success",
                "message": "Llama models retrieved",
                "models": models,
                "provider": "llama"
            }
            
        except Exception as e:
            logger.error("Llama models retrieval failed", exception=e)
            return {
                "status": "error",
                "message": "Failed to retrieve Llama models",
                "error": str(e)
            }

@router.get("/llama/connection-test")
async def test_llama_connection():
    """Test Llama connection - public endpoint"""
    with perf_logger.time_operation("llama_connection_test"):
        logger.info("Llama connection test requested")
        
        try:
            from services.llm_service import get_unified_llm_service
            
            llm_service = get_unified_llm_service()
            test_result = await llm_service.test_connection("llama")
            
            if test_result.get("success", False):
                logger.info("Llama connection test successful")
                return {
                    "status": "success",
                    "message": "Llama connection successful",
                    "response_time": test_result.get("response_time"),
                    "provider": "llama"
                }
            else:
                logger.warning("Llama connection test failed", error=test_result.get("error"))
                return {
                    "status": "failed",
                    "message": "Llama connection failed",
                    "error": test_result.get("error"),
                    "provider": "llama"
                }
                
        except Exception as e:
            logger.error("Llama connection test failed with exception", exception=e)
            return {
                "status": "error",
                "message": "Llama connection test error",
                "error": str(e)
            } 