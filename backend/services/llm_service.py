"""
Unified LLM Service

Provides a unified interface for multiple LLM providers (Google AI, OpenAI, Grok, Anthropic).
Allows agents to use different providers seamlessly through a single interface.
"""

import asyncio
from typing import Dict, Any, Optional, List, Literal
from logging_system import get_logger
from dataclasses import dataclass
from datetime import datetime, timedelta
from .llm_utils import get_all_health_status, get_health_tracker

logger = get_logger(__name__)

# Type definition for supported providers
LLMProvider = Literal["google", "openai", "grok", "anthropic", "deepseek", "llama"]

@dataclass
class ServiceFailureInfo:
    """Tracks service failure information for retry logic"""
    last_failure_time: datetime
    failure_count: int
    last_error: str
    
    def should_retry(self, retry_delay_minutes: int = 5) -> bool:
        """Check if enough time has passed to retry a failed service"""
        return datetime.now() - self.last_failure_time > timedelta(minutes=retry_delay_minutes)

class UnifiedLLMService:
    """Unified service providing access to multiple LLM providers"""
    
    def __init__(self):
        # Service instances (None = not loaded, object = loaded successfully)
        self._google_service = None
        self._openai_service = None
        self._grok_service = None
        self._anthropic_service = None
        self._deepseek_service = None
        self._llama_service = None
        
        # Track service failures for retry logic
        self._service_failures: Dict[str, ServiceFailureInfo] = {}
        
        # Get default provider from configuration
        from config.environment import get_settings
        settings = get_settings()
        self._default_provider = settings.default_llm_provider
        logger.info(f"Unified LLM service initialized with default provider: {self._default_provider}")
    
    def _record_service_failure(self, service_name: str, error: str):
        """Record a service failure for retry tracking"""
        if service_name in self._service_failures:
            self._service_failures[service_name].failure_count += 1
            self._service_failures[service_name].last_failure_time = datetime.now()
            self._service_failures[service_name].last_error = error
        else:
            self._service_failures[service_name] = ServiceFailureInfo(
                last_failure_time=datetime.now(),
                failure_count=1,
                last_error=error
            )
        
        logger.warning(f"Service {service_name} failed (attempt #{self._service_failures[service_name].failure_count}): {error}")
    
    def _should_retry_service(self, service_name: str) -> bool:
        """Check if a failed service should be retried"""
        if service_name not in self._service_failures:
            return True  # No previous failures
        
        failure_info = self._service_failures[service_name]
        return failure_info.should_retry()
    
    def _get_google_service(self):
        """Lazy load Google AI service with failure tracking"""
        if self._google_service is not None:
            return self._google_service
        
        if not self._should_retry_service("google"):
            return None
        
        try:
            from services.google_ai_service import get_google_ai_service
            self._google_service = get_google_ai_service()
            # Clear any previous failure record on success
            if "google" in self._service_failures:
                del self._service_failures["google"]
            return self._google_service
        except Exception as e:
            self._record_service_failure("google", str(e))
            return None
    
    def _get_openai_service(self):
        """Lazy load OpenAI service with failure tracking"""
        if self._openai_service is not None:
            return self._openai_service
        
        if not self._should_retry_service("openai"):
            return None
        
        try:
            from services.openai_service import get_openai_service
            self._openai_service = get_openai_service()
            # Clear any previous failure record on success
            if "openai" in self._service_failures:
                del self._service_failures["openai"]
            return self._openai_service
        except Exception as e:
            self._record_service_failure("openai", str(e))
            return None
    
    def _get_grok_service(self):
        """Lazy load Grok service with failure tracking"""
        if self._grok_service is not None:
            return self._grok_service
        
        if not self._should_retry_service("grok"):
            return None
        
        try:
            from services.grok_service import get_grok_service
            self._grok_service = get_grok_service()
            # Clear any previous failure record on success
            if "grok" in self._service_failures:
                del self._service_failures["grok"]
            return self._grok_service
        except Exception as e:
            self._record_service_failure("grok", str(e))
            return None
    
    def _get_anthropic_service(self):
        """Lazy load Anthropic service with failure tracking"""
        if self._anthropic_service is not None:
            return self._anthropic_service
        
        if not self._should_retry_service("anthropic"):
            return None
        
        try:
            from services.anthropic_service import get_anthropic_service
            self._anthropic_service = get_anthropic_service()
            # Clear any previous failure record on success
            if "anthropic" in self._service_failures:
                del self._service_failures["anthropic"]
            return self._anthropic_service
        except Exception as e:
            self._record_service_failure("anthropic", str(e))
            return None
    
    def _get_deepseek_service(self):
        """Lazy load DeepSeek service with failure tracking"""
        if self._deepseek_service is not None:
            return self._deepseek_service
        
        if not self._should_retry_service("deepseek"):
            return None
        
        try:
            from services.deepseek_service import get_deepseek_service
            self._deepseek_service = get_deepseek_service()
            # Clear any previous failure record on success
            if "deepseek" in self._service_failures:
                del self._service_failures["deepseek"]
            return self._deepseek_service
        except Exception as e:
            self._record_service_failure("deepseek", str(e))
            return None
    
    def _get_llama_service(self):
        """Lazy load Meta Llama service with failure tracking"""
        if self._llama_service is not None:
            return self._llama_service
        
        if not self._should_retry_service("llama"):
            return None
        
        try:
            from services.llama_service import get_llama_service
            self._llama_service = get_llama_service()
            # Clear any previous failure record on success
            if "llama" in self._service_failures:
                del self._service_failures["llama"]
            return self._llama_service
        except Exception as e:
            self._record_service_failure("llama", str(e))
            return None
    
    def _get_service_for_provider(self, provider: LLMProvider):
        """Get the service instance for a specific provider"""
        if provider == "google":
            return self._get_google_service()
        elif provider == "openai":
            return self._get_openai_service()
        elif provider == "grok":
            return self._get_grok_service()
        elif provider == "anthropic":
            return self._get_anthropic_service()
        elif provider == "deepseek":
            return self._get_deepseek_service()
        elif provider == "llama":
            return self._get_llama_service()
        else:
            raise ValueError(f"Unknown provider: {provider}")
    
    async def query(
        self, 
        prompt: str,
        provider: Optional[LLMProvider] = None,
        model: Optional[str] = None,
        system_instruction: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs
    ) -> str:
        """
        Query an LLM with automatic provider selection
        
        Args:
            prompt: The prompt to send to the LLM
            provider: LLM provider to use ("google", "openai", "grok", or "anthropic"). If None, uses default.
            model: Model name to use (provider-specific)
            system_instruction: Optional system instruction
            max_tokens: Optional max tokens override
            temperature: Optional temperature override
            **kwargs: Additional provider-specific parameters
            
        Returns:
            LLM response as string
        """
        # Determine provider
        if provider is None:
            provider = self._default_provider
        
        # Get service
        service = self._get_service_for_provider(provider)
        if service is None:
            # Fallback to other providers if primary is unavailable
            available_providers = self.get_available_providers()
            if provider in available_providers:
                available_providers.remove(provider)
            
            if available_providers:
                fallback_provider = available_providers[0]
                logger.warning(f"{provider} service unavailable, trying {fallback_provider}")
                service = self._get_service_for_provider(fallback_provider)
                
                if service is None:
                    raise RuntimeError("No LLM services available")
                
                provider = fallback_provider
            else:
                raise RuntimeError("No LLM services available")
        
        # Make the query
        try:
            logger.debug(f"Making LLM query with {provider} provider")
            return await service.query(
                prompt=prompt,
                model=model,
                system_instruction=system_instruction,
                max_tokens=max_tokens,
                temperature=temperature,
                **kwargs
            )
        except Exception as e:
            logger.error(f"LLM query failed with {provider}: {e}")
            raise
    
    async def query_structured(
        self,
        prompt: str,
        output_schema: Dict[str, Any],
        provider: Optional[LLMProvider] = None,
        model: Optional[str] = None,
        max_retries: int = 2,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Query LLM with structured JSON output requirements
        
        Args:
            prompt: The prompt to send
            output_schema: Expected output schema description
            provider: LLM provider to use
            model: Optional model override
            max_retries: Number of retries for malformed JSON
            **kwargs: Additional parameters
            
        Returns:
            Parsed JSON response
        """
        # Determine provider
        if provider is None:
            provider = self._default_provider
        
        # Get service
        service = self._get_service_for_provider(provider)
        if service is None:
            # Fallback to other providers if primary is unavailable
            available_providers = self.get_available_providers()
            if provider in available_providers:
                available_providers.remove(provider)
            
            if available_providers:
                fallback_provider = available_providers[0]
                logger.warning(f"{provider} service unavailable, trying {fallback_provider}")
                service = self._get_service_for_provider(fallback_provider)
                
                if service is None:
                    raise RuntimeError("No LLM services available")
                
                provider = fallback_provider
            else:
                raise RuntimeError("No LLM services available")
        
        # Make the structured query
        try:
            logger.debug(f"Making structured LLM query with {provider} provider")
            return await service.query_structured(
                prompt=prompt,
                output_schema=output_schema,
                model=model,
                max_retries=max_retries,
                **kwargs
            )
        except Exception as e:
            logger.error(f"Structured LLM query failed with {provider}: {e}")
            raise
    
    async def batch_query(
        self,
        prompts: List[str],
        provider: Optional[LLMProvider] = None,
        model: Optional[str] = None,
        max_concurrent: int = 3,
        **kwargs
    ) -> List[str]:
        """
        Execute multiple prompts in parallel
        
        Args:
            prompts: List of prompts to process
            provider: LLM provider to use
            model: Optional model override
            max_concurrent: Maximum concurrent executions
            **kwargs: Additional parameters for each query
            
        Returns:
            List of responses in the same order as prompts
        """
        # Determine provider
        if provider is None:
            provider = self._default_provider
        
        # Get service
        service = self._get_service_for_provider(provider)
        if service is None:
            # Fallback to other providers if primary is unavailable
            available_providers = self.get_available_providers()
            if provider in available_providers:
                available_providers.remove(provider)
            
            if available_providers:
                fallback_provider = available_providers[0]
                logger.warning(f"{provider} service unavailable, trying {fallback_provider}")
                service = self._get_service_for_provider(fallback_provider)
                
                if service is None:
                    raise RuntimeError("No LLM services available")
                
                provider = fallback_provider
            else:
                raise RuntimeError("No LLM services available")
        
        # Make the batch query
        try:
            logger.debug(f"Making batch LLM query with {provider} provider")
            return await service.batch_query(
                prompts=prompts,
                model=model,
                max_concurrent=max_concurrent,
                **kwargs
            )
        except Exception as e:
            logger.error(f"Batch LLM query failed with {provider}: {e}")
            raise
    
    # Convenience methods that use the unified interface
    
    async def analyze_sentiment(
        self, 
        text: str, 
        provider: Optional[LLMProvider] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Convenience method for sentiment analysis"""
        schema = {
            "sentiment": "string (positive/negative/neutral)",
            "confidence": "number between 0 and 1",
            "emotions": ["list of detected emotions"],
            "explanation": "string explaining the analysis"
        }
        
        prompt = f'Analyze the sentiment of this text: "{text}"'
        return await self.query_structured(prompt, schema, provider=provider, **kwargs)
    
    async def extract_keywords(
        self, 
        text: str, 
        max_keywords: int = 10,
        provider: Optional[LLMProvider] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Convenience method for keyword extraction"""
        schema = {
            "keywords": ["list of important keywords"],
            "phrases": ["list of key phrases"],
            "categories": {"keyword": "category mappings"},
            "relevance_scores": {"keyword": "relevance score 0-1"}
        }
        
        prompt = f'Extract the top {max_keywords} keywords from: "{text}"'
        return await self.query_structured(prompt, schema, provider=provider, **kwargs)
    
    async def summarize(
        self, 
        text: str, 
        max_sentences: int = 3,
        provider: Optional[LLMProvider] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Convenience method for text summarization"""
        schema = {
            "summary": "concise summary text",
            "key_points": ["list of main points"],
            "word_count": {"original": "number", "summary": "number"},
            "compression_ratio": "number representing compression"
        }
        
        prompt = f'Summarize this text in {max_sentences} sentences or less: "{text}"'
        return await self.query_structured(prompt, schema, provider=provider, **kwargs)
    
    # Service information and management
    
    def get_service_health(self) -> Dict[str, Any]:
        """Get health information for all services including failure tracking"""
        health_info = {
            "healthy_services": [],
            "failed_services": [],
            "service_details": {}
        }
        
        all_providers = ["google", "openai", "grok", "anthropic", "deepseek", "llama"]
        
        for provider in all_providers:
            service = self._get_service_for_provider(provider)
            
            if service is not None:
                health_info["healthy_services"].append(provider)
                health_info["service_details"][provider] = {
                    "status": "healthy",
                    "loaded": True
                }
            elif provider in self._service_failures:
                failure_info = self._service_failures[provider]
                health_info["failed_services"].append(provider)
                health_info["service_details"][provider] = {
                    "status": "failed",
                    "loaded": False,
                    "failure_count": failure_info.failure_count,
                    "last_failure": failure_info.last_failure_time.isoformat(),
                    "last_error": failure_info.last_error,
                    "can_retry": failure_info.should_retry()
                }
            else:
                health_info["service_details"][provider] = {
                    "status": "not_loaded",
                    "loaded": False
                }
        
        return health_info
    
    def get_available_providers(self) -> List[LLMProvider]:
        """Get list of available LLM providers"""
        providers = []
        if self._get_google_service() is not None:
            providers.append("google")
        if self._get_openai_service() is not None:
            providers.append("openai")
        if self._get_grok_service() is not None:
            providers.append("grok")
        if self._get_anthropic_service() is not None:
            providers.append("anthropic")
        if self._get_deepseek_service() is not None:
            providers.append("deepseek")
        if self._get_llama_service() is not None:
            providers.append("llama")
        return providers
    
    def get_provider_info(self, provider: LLMProvider) -> Dict[str, Any]:
        """Get information about a specific provider"""
        service = self._get_service_for_provider(provider)
        
        if service is None:
            # Check if there's failure information
            if provider in self._service_failures:
                failure_info = self._service_failures[provider]
                return {
                    "provider": provider,
                    "status": "failed",
                    "failure_count": failure_info.failure_count,
                    "last_failure": failure_info.last_failure_time.isoformat(),
                    "last_error": failure_info.last_error,
                    "can_retry": failure_info.should_retry()
                }
            else:
                return {
                    "provider": provider,
                    "status": "not_loaded",
                    "error": f"{provider} service not loaded"
                }
        
        try:
            info = service.get_info()
            info["provider"] = provider
            info["status"] = "available"
            return info
        except Exception as e:
            return {
                "provider": provider,
                "status": "error",
                "error": str(e)
            }
    
    def get_all_providers_info(self) -> Dict[str, Any]:
        """Get information about all providers"""
        available_providers = self.get_available_providers()
        all_providers = ["google", "openai", "grok", "anthropic", "deepseek", "llama"]
        
        providers_info = {}
        for provider in all_providers:
            providers_info[provider] = self.get_provider_info(provider)
        
        return {
            "default_provider": self._default_provider,
            "available_providers": available_providers,
            "total_providers": len(all_providers),
            "healthy_count": len(available_providers),
            "failed_count": len([p for p in all_providers if p in self._service_failures]),
            "providers": providers_info,
            "health_summary": self.get_service_health()
        }
    
    def get_connection_health_status(self) -> Dict[str, Any]:
        """Get connection health status for all services including performance metrics"""
        # Get health tracking data from llm_utils
        all_health_status = get_all_health_status()
        
        # Get service loading status
        service_health = self.get_service_health()
        
        # Combine both types of health information
        combined_health = {
            "overall_status": "healthy",
            "total_services": 6,
            "loaded_services": len(service_health["healthy_services"]),
            "failed_services": len(service_health["failed_services"]),
            "services": {}
        }
        
        # Determine overall health
        if len(service_health["failed_services"]) > 3:
            combined_health["overall_status"] = "critical"
        elif len(service_health["failed_services"]) > 1:
            combined_health["overall_status"] = "degraded"
        
        # Process each service
        all_providers = ["google", "openai", "grok", "anthropic", "deepseek", "llama"]
        service_name_mapping = {
            "google": "Google AI",
            "openai": "OpenAI", 
            "grok": "Grok",
            "anthropic": "Anthropic",
            "deepseek": "DeepSeek",
            "llama": "Meta Llama"
        }
        
        for provider in all_providers:
            service_name = service_name_mapping[provider]
            service_info = service_health["service_details"].get(provider, {})
            health_metrics = all_health_status.get(service_name, {})
            
            combined_health["services"][provider] = {
                "provider": provider,
                "service_name": service_name,
                "loading_status": service_info.get("status", "unknown"),
                "is_loaded": service_info.get("loaded", False),
                "connection_health": health_metrics.get("health_status", "unknown"),
                "performance_metrics": {
                    "total_requests": health_metrics.get("total_requests", 0),
                    "error_rate_percent": health_metrics.get("error_rate_percent", 0),
                    "average_response_time_seconds": health_metrics.get("average_response_time_seconds", 0),
                    "recent_error_rate_percent": health_metrics.get("recent_error_rate_percent", 0),
                    "consecutive_errors": health_metrics.get("consecutive_errors", 0)
                },
                "timestamps": {
                    "last_success": health_metrics.get("last_success_time"),
                    "last_error": health_metrics.get("last_error_time")
                }
            }
        
        return combined_health

    def get_individual_service_health(self, provider: LLMProvider) -> Dict[str, Any]:
        """Get detailed health information for a specific service"""
        service = self._get_service_for_provider(provider)
        
        if service is None:
            return {
                "provider": provider,
                "status": "not_loaded",
                "error": f"{provider} service not available"
            }
        
        try:
            # Get health status from the service if it has the method
            if hasattr(service, 'get_health_status'):
                return service.get_health_status()
            else:
                return {
                    "provider": provider,
                    "status": "loaded",
                    "health_monitoring": "not_available"
                }
        except Exception as e:
            return {
                "provider": provider,
                "status": "error",
                "error": str(e)
            }
    
    def set_default_provider(self, provider: LLMProvider) -> None:
        """Set the default LLM provider"""
        if provider not in ["google", "openai", "grok", "anthropic", "deepseek", "llama"]:
            raise ValueError(f"Invalid provider: {provider}")
        
        self._default_provider = provider
        logger.info(f"Default LLM provider set to: {provider}")
    
    def test_all_connections(self) -> Dict[str, Any]:
        """Test connections to all available providers"""
        results = {}
        
        # Test Google AI
        google_service = self._get_google_service()
        if google_service:
            try:
                results["google"] = google_service.test_connection()
            except Exception as e:
                results["google"] = {"status": "error", "error": str(e)}
        else:
            results["google"] = {"status": "unavailable"}
        
        # Test OpenAI
        openai_service = self._get_openai_service()
        if openai_service:
            try:
                results["openai"] = openai_service.test_connection()
            except Exception as e:
                results["openai"] = {"status": "error", "error": str(e)}
        else:
            results["openai"] = {"status": "unavailable"}
        
        # Test Grok
        grok_service = self._get_grok_service()
        if grok_service:
            try:
                results["grok"] = grok_service.test_connection()
            except Exception as e:
                results["grok"] = {"status": "error", "error": str(e)}
        else:
            results["grok"] = {"status": "unavailable"}
        
        # Test Anthropic
        anthropic_service = self._get_anthropic_service()
        if anthropic_service:
            try:
                results["anthropic"] = anthropic_service.test_connection()
            except Exception as e:
                results["anthropic"] = {"status": "error", "error": str(e)}
        else:
            results["anthropic"] = {"status": "unavailable"}
        
        # Test DeepSeek
        deepseek_service = self._get_deepseek_service()
        if deepseek_service:
            try:
                results["deepseek"] = deepseek_service.test_connection()
            except Exception as e:
                results["deepseek"] = {"status": "error", "error": str(e)}
        else:
            results["deepseek"] = {"status": "unavailable"}
        
        # Test Meta Llama
        llama_service = self._get_llama_service()
        if llama_service:
            try:
                results["llama"] = llama_service.test_connection()
            except Exception as e:
                results["llama"] = {"status": "error", "error": str(e)}
        else:
            results["llama"] = {"status": "unavailable"}
        
        return {
            "default_provider": self._default_provider,
            "connection_tests": results,
            "summary": {
                "total_providers": len(results),
                "available_providers": len([r for r in results.values() if r.get("status") == "success"]),
                "failed_providers": len([r for r in results.values() if r.get("status") == "error"])
            }
        }

# Global service instance for easy access
_unified_llm_service = None

def get_unified_llm_service() -> UnifiedLLMService:
    """Get the global unified LLM service instance"""
    global _unified_llm_service
    if _unified_llm_service is None:
        _unified_llm_service = UnifiedLLMService()
    return _unified_llm_service

# Convenience functions for backward compatibility
async def llm_query(prompt: str, provider: Optional[LLMProvider] = None, **kwargs) -> str:
    """Convenience function for simple LLM queries"""
    service = get_unified_llm_service()
    return await service.query(prompt, provider=provider, **kwargs)

async def llm_query_structured(prompt: str, schema: Dict[str, Any], provider: Optional[LLMProvider] = None, **kwargs) -> Dict[str, Any]:
    """Convenience function for structured LLM queries"""
    service = get_unified_llm_service()
    return await service.query_structured(prompt, schema, provider=provider, **kwargs) 