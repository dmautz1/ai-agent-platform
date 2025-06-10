"""
Meta Llama Service

Provides Meta Llama integration for AI agent functionality.
Follows the same interface pattern as other LLM services for consistency.
"""

import json
import asyncio
from typing import Dict, Any, Optional, List
import openai
from config.llama import get_llama_config
from logging_system import get_logger
from .llm_utils import (
    parse_json_response, 
    create_json_prompt,
    get_sentiment_analysis_schema,
    get_keyword_extraction_schema,
    get_summarization_schema,
    handle_llm_query_error,
    create_batch_error_response,
    handle_structured_query_retry_error,
    safe_model_selection,
    monitor_connection_health,
    get_health_tracker
)

logger = get_logger(__name__)

class LlamaService:
    """Service providing Meta Llama functionality for agents via composition"""
    
    def __init__(self):
        self._llama_config = get_llama_config()
        # Meta Llama uses OpenAI-compatible API with custom base URL
        self._client = openai.AsyncOpenAI(
            api_key=self._llama_config.api_key,
            base_url=self._llama_config.base_url
        )
        logger.info("Meta Llama service initialized")
    
    # Core LLM Operations
    
    @monitor_connection_health("Meta Llama")
    async def query(
        self, 
        prompt: str, 
        model: Optional[str] = None,
        system_instruction: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs
    ) -> str:
        """
        Simple LLM query using Meta Llama API
        
        Args:
            prompt: The prompt to send to the LLM
            model: Optional model override
            system_instruction: Optional system instruction
            max_tokens: Optional max tokens override
            temperature: Optional temperature override
            **kwargs: Additional generation parameters
            
        Returns:
            LLM response as string
        """
        try:
            model_name = safe_model_selection(
                service_name="Meta Llama",
                requested_model=model,
                available_models=self._llama_config.get_available_models(),
                default_model=self._llama_config.default_model,
                strict_validation=False
            )
            
            # Prepare messages
            messages = []
            if system_instruction:
                messages.append({"role": "system", "content": system_instruction})
            messages.append({"role": "user", "content": prompt})
            
            # Prepare generation config
            generation_config = {
                "model": model_name,
                "messages": messages
            }
            
            if max_tokens:
                generation_config['max_tokens'] = max_tokens
            if temperature is not None:
                generation_config['temperature'] = temperature
            
            # Add any additional kwargs to generation config
            generation_config.update(kwargs)
            
            # Execute the query
            response = await self._client.chat.completions.create(**generation_config)
            
            # Extract text from response
            return response.choices[0].message.content
            
        except Exception as e:
            raise handle_llm_query_error("Meta Llama", e)
    
    async def query_structured(
        self,
        prompt: str,
        output_schema: Dict[str, Any],
        model: Optional[str] = None,
        max_retries: int = 2,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Query LLM with structured JSON output requirements
        
        Args:
            prompt: The prompt to send
            output_schema: Expected output schema description
            model: Optional model override
            max_retries: Number of retries for malformed JSON
            **kwargs: Additional parameters
            
        Returns:
            Parsed JSON response
        """
        for attempt in range(max_retries + 1):
            try:
                # Create appropriate prompt for this attempt
                is_retry = attempt > 0
                schema_prompt = create_json_prompt(prompt, output_schema, strict=is_retry)
                
                response_text = await self.query(schema_prompt, model=model, **kwargs)
                
                # Use the common JSON parsing utility
                result = parse_json_response(response_text, output_schema)
                
                # Check if parsing was successful (no error key means success)
                if "error" not in result:
                    return result
                
                # If this was the last attempt, return the error
                if attempt >= max_retries:
                    return result
                
                # Log warning and continue to retry
                logger.warning(f"JSON parsing failed on attempt {attempt + 1}, retrying...")
                await asyncio.sleep(1)  # Brief delay before retry
                        
            except Exception as e:
                # Use common error handling utility
                error_result = handle_structured_query_retry_error("Meta Llama", e, attempt, max_retries, output_schema)
                if error_result is not None:
                    return error_result
                await asyncio.sleep(1)  # Brief delay before retry
    
    async def batch_query(
        self,
        prompts: List[str],
        model: Optional[str] = None,
        max_concurrent: int = 3,
        **kwargs
    ) -> List[str]:
        """
        Execute multiple prompts in parallel
        
        Args:
            prompts: List of prompts to process
            model: Optional model override
            max_concurrent: Maximum concurrent executions
            **kwargs: Additional parameters for each query
            
        Returns:
            List of responses in the same order as prompts
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def execute_single(prompt: str) -> str:
            async with semaphore:
                return await self.query(prompt, model=model, **kwargs)
        
        try:
            tasks = [execute_single(prompt) for prompt in prompts]
            return await asyncio.gather(*tasks)
            
        except Exception as e:
            logger.error(f"Meta Llama batch execution failed: {e}")
            return create_batch_error_response(e, len(prompts))
    
    # Convenience Methods for Common Tasks
    
    async def analyze_sentiment(self, text: str, **kwargs) -> Dict[str, Any]:
        """Convenience method for sentiment analysis"""
        prompt = f'Analyze the sentiment of this text: "{text}"'
        return await self.query_structured(prompt, get_sentiment_analysis_schema(), **kwargs)
    
    async def extract_keywords(self, text: str, max_keywords: int = 10, **kwargs) -> Dict[str, Any]:
        """Convenience method for keyword extraction"""
        prompt = f'Extract the top {max_keywords} keywords from: "{text}"'
        return await self.query_structured(prompt, get_keyword_extraction_schema(), **kwargs)
    
    async def summarize(self, text: str, max_sentences: int = 3, **kwargs) -> Dict[str, Any]:
        """Convenience method for text summarization"""
        prompt = f'Summarize this text in {max_sentences} sentences or less: "{text}"'
        return await self.query_structured(prompt, get_summarization_schema(), **kwargs)
    
    # Service Information and Management
    
    def get_info(self) -> Dict[str, Any]:
        """Get information about the Meta Llama service configuration"""
        return {
            "service": "Llama",
            "service_name": "Meta Llama Service",
            "provider": "Meta",
            "default_model": self._llama_config.default_model,
            "available_models": self._llama_config.get_available_models(),
            "authentication_method": "API Key",
            "base_url": self._llama_config.base_url,
            "api_provider": self._llama_config.api_provider
        }
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get connection health status for the Meta Llama service"""
        tracker = get_health_tracker("Meta Llama")
        return tracker.get_health_status()
    
    def test_connection(self) -> Dict[str, Any]:
        """Test the connection to Meta Llama services"""
        try:
            # Simple test to verify API key and connection
            return {
                "status": "success",
                "service": "Meta Llama",
                "provider": "Meta",
                "model": self._llama_config.default_model,
                "base_url": self._llama_config.base_url,
                "api_provider": self._llama_config.api_provider
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "service": "Meta Llama",
                "provider": "Meta"
            }

# Global service instance for easy access
_llama_service = None

def get_llama_service() -> LlamaService:
    """Get the global Meta Llama service instance"""
    global _llama_service
    if _llama_service is None:
        _llama_service = LlamaService()
    return _llama_service 