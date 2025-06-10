"""
Google AI Service

Provides simple Google AI integration using direct google.generativeai for maximum flexibility.
Focused on essential LLM query methods without framework constraints.
"""

import json
import asyncio
from typing import Dict, Any, Optional, List
import google.generativeai as genai
from config.google_ai import get_google_ai_config, get_generative_model
from logging_system import get_logger

logger = get_logger(__name__)

class GoogleAIService:
    """Service providing Google AI functionality for agents via composition"""
    
    def __init__(self):
        
        self._google_ai_config = get_google_ai_config()
        self._model_cache = {}
        logger.info("Google AI service initialized")
    
    def _get_model(self, model: Optional[str] = None) -> genai.GenerativeModel:
        """Get or cache a GenerativeModel instance"""
        model_name = model or self._google_ai_config.default_model
        
        if model_name not in self._model_cache:
            self._model_cache[model_name] = get_generative_model(model_name)
        
        return self._model_cache[model_name]
    
    # Core LLM Operations
    
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
        Simple LLM query using direct google.generativeai
        
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
            # Get the model
            llm_model = self._get_model(model)
            
            # Prepare the full prompt
            full_prompt = prompt
            if system_instruction:
                full_prompt = f"System: {system_instruction}\n\nUser: {prompt}"
            
            # Prepare generation config
            generation_config = {}
            if max_tokens:
                generation_config['max_output_tokens'] = max_tokens
            if temperature is not None:
                generation_config['temperature'] = temperature
            
            # Add any additional kwargs to generation config
            generation_config.update(kwargs)
            
            # Execute the query
            response = await asyncio.to_thread(
                llm_model.generate_content,
                full_prompt,
                generation_config=generation_config if generation_config else None
            )
            
            # Extract text from response
            if hasattr(response, 'text'):
                return response.text
            elif hasattr(response, 'content'):
                return response.content
            else:
                return str(response)
            
        except Exception as e:
            logger.error(f"Google AI query failed: {e}")
            raise RuntimeError(f"LLM query failed: {str(e)}")
    
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
        schema_prompt = f"""{prompt}

Please provide your response as valid JSON matching this schema:
{json.dumps(output_schema, indent=2)}

Ensure your response is properly formatted JSON that can be parsed."""
        
        for attempt in range(max_retries + 1):
            try:
                response_text = await self.query(schema_prompt, model=model, **kwargs)
                
                # Try to parse as JSON
                return json.loads(response_text)
                
            except json.JSONDecodeError as e:
                logger.warning(f"JSON parse failed (attempt {attempt + 1}): {e}")
                if attempt < max_retries:
                    # Retry with more explicit instructions
                    schema_prompt = f"""{prompt}

CRITICAL: You must respond with ONLY valid JSON. Do not include any text before or after the JSON.

Schema to follow:
{json.dumps(output_schema, indent=2)}

Respond with valid JSON only:"""
                    continue
                else:
                    # Final attempt failed, return error response
                    logger.error(f"Failed to get valid JSON after {max_retries + 1} attempts")
                    return {
                        "error": "Failed to parse response as JSON",
                        "raw_response": response_text,
                        "schema_requested": output_schema,
                        "attempts": max_retries + 1
                    }
            except Exception as e:
                logger.error(f"Structured query failed: {e}")
                return {
                    "error": f"Structured query failed: {str(e)}",
                    "schema_requested": output_schema
                }
    
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
            logger.error(f"Google AI batch execution failed: {e}")
            # Return error messages for all prompts
            error_msg = f"Batch execution failed: {str(e)}"
            return [error_msg] * len(prompts)
    
    # Convenience Methods for Common Tasks
    
    async def analyze_sentiment(self, text: str, **kwargs) -> Dict[str, Any]:
        """Convenience method for sentiment analysis"""
        schema = {
            "sentiment": "string (positive/negative/neutral)",
            "confidence": "number between 0 and 1",
            "emotions": ["list of detected emotions"],
            "explanation": "string explaining the analysis"
        }
        
        prompt = f'Analyze the sentiment of this text: "{text}"'
        return await self.query_structured(prompt, schema, **kwargs)
    
    async def extract_keywords(self, text: str, max_keywords: int = 10, **kwargs) -> Dict[str, Any]:
        """Convenience method for keyword extraction"""
        schema = {
            "keywords": ["list of important keywords"],
            "phrases": ["list of key phrases"],
            "categories": {"keyword": "category mappings"},
            "relevance_scores": {"keyword": "relevance score 0-1"}
        }
        
        prompt = f'Extract the top {max_keywords} keywords from: "{text}"'
        return await self.query_structured(prompt, schema, **kwargs)
    
    async def summarize(self, text: str, max_sentences: int = 3, **kwargs) -> Dict[str, Any]:
        """Convenience method for text summarization"""
        schema = {
            "summary": "concise summary text",
            "key_points": ["list of main points"],
            "word_count": {"original": "number", "summary": "number"},
            "compression_ratio": "number representing compression"
        }
        
        prompt = f'Summarize this text in {max_sentences} sentences or less: "{text}"'
        return await self.query_structured(prompt, schema, **kwargs)
    
    # Agent Information and Management
    
    def get_info(self) -> Dict[str, Any]:
        """Get information about the LLM configuration"""
        return {
            "service_name": "Google AI Service",
            "default_model": self._google_ai_config.default_model,
            "available_models": self._google_ai_config.get_available_models(),
            "cached_models": list(self._model_cache.keys()),
            "authentication_method": "Vertex AI" if self._google_ai_config.use_vertex_ai else "Google AI Studio"
        }
    
    def test_connection(self) -> Dict[str, Any]:
        """Test the connection to Google AI services"""
        try:
            return self._google_ai_config.test_connection()
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "service": "Google AI Service"
            }

    def clear_model_cache(self) -> None:
        """Clear the model cache (useful for memory management)"""
        self._model_cache.clear()
        logger.info("Cleared Google AI service model cache") 

# Global service instance for easy access
_google_ai_service = None

def get_google_ai_service() -> GoogleAIService:
    """Get the global Google AI service instance"""
    global _google_ai_service
    if _google_ai_service is None:
        _google_ai_service = GoogleAIService()
    return _google_ai_service
