"""
LLM Service Utilities

Common utilities and helpers for LLM services to eliminate code duplication.
"""

import json
import asyncio
import functools
from datetime import datetime, timedelta
from typing import Dict, Any, Callable, Union, List, Optional
from logging_system import get_logger

logger = get_logger(__name__)

# Standardized schemas for convenience methods
# These ensure all services use identical schemas for consistent behavior

SENTIMENT_ANALYSIS_SCHEMA = {
    "sentiment": "string (positive/negative/neutral)",
    "confidence": "number between 0 and 1",
    "emotions": ["list of detected emotions"],
    "explanation": "string explaining the analysis"
}

KEYWORD_EXTRACTION_SCHEMA = {
    "keywords": ["list of important keywords"],
    "phrases": ["list of key phrases"],
    "categories": {"keyword": "category mappings"},
    "relevance_scores": {"keyword": "relevance score 0-1"}
}

SUMMARIZATION_SCHEMA = {
    "summary": "concise summary text",
    "key_points": ["list of main points"],
    "word_count": {"original": "number", "summary": "number"},
    "compression_ratio": "number representing compression"
}

def get_sentiment_analysis_schema() -> Dict[str, Any]:
    """Get the standardized schema for sentiment analysis"""
    return SENTIMENT_ANALYSIS_SCHEMA.copy()

def get_keyword_extraction_schema() -> Dict[str, Any]:
    """Get the standardized schema for keyword extraction"""
    return KEYWORD_EXTRACTION_SCHEMA.copy()

def get_summarization_schema() -> Dict[str, Any]:
    """Get the standardized schema for text summarization"""
    return SUMMARIZATION_SCHEMA.copy()

def parse_json_response(response_text: str, schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse JSON response from LLM with fallback strategies for common formatting issues.
    
    This handles the common case where LLMs wrap JSON in markdown code blocks
    or include extra text around the JSON.
    
    Args:
        response_text: Raw response text from LLM
        schema: Expected schema for error reporting
        
    Returns:
        Parsed JSON dict or error dict with structured error information
    """
    # First, try direct JSON parsing
    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        pass
    
    # Try to extract JSON from markdown code blocks
    if "```json" in response_text:
        try:
            json_start = response_text.find("```json") + 7
            json_end = response_text.find("```", json_start)
            if json_end > json_start:
                json_str = response_text[json_start:json_end].strip()
                return json.loads(json_str)
        except json.JSONDecodeError:
            pass
    
    # Try to extract JSON from any code block (```...```)
    if "```" in response_text:
        try:
            # Find the first code block
            first_triple = response_text.find("```")
            if first_triple != -1:
                # Skip the opening ```
                start_pos = first_triple + 3
                # Skip language identifier if present (e.g., "json\n")
                if '\n' in response_text[start_pos:start_pos + 10]:
                    start_pos = response_text.find('\n', start_pos) + 1
                
                # Find closing ```
                end_pos = response_text.find("```", start_pos)
                if end_pos > start_pos:
                    json_str = response_text[start_pos:end_pos].strip()
                    return json.loads(json_str)
        except json.JSONDecodeError:
            pass
    
    # Try to find JSON-like content between braces
    try:
        first_brace = response_text.find('{')
        last_brace = response_text.rfind('}')
        if first_brace != -1 and last_brace > first_brace:
            json_str = response_text[first_brace:last_brace + 1]
            return json.loads(json_str)
    except json.JSONDecodeError:
        pass
    
    # All parsing attempts failed
    logger.warning(f"Failed to parse JSON from response: {response_text[:200]}...")
    return {
        "error": "Failed to parse JSON response",
        "raw_response": response_text,
        "schema": schema
    }

def create_json_prompt(original_prompt: str, schema: Dict[str, Any], strict: bool = False) -> str:
    """
    Create a prompt that requests JSON output with the specified schema.
    
    Args:
        original_prompt: The original user prompt
        schema: Expected output schema
        strict: Whether to use strict formatting instructions
        
    Returns:
        Enhanced prompt with JSON formatting instructions
    """
    if strict:
        return f"""{original_prompt}

CRITICAL: You must respond with ONLY valid JSON. Do not include any text before or after the JSON.

Schema to follow:
{json.dumps(schema, indent=2)}

Respond with valid JSON only:"""
    else:
        return f"""{original_prompt}

Please provide your response as valid JSON matching this schema:
{json.dumps(schema, indent=2)}

Ensure your response is properly formatted JSON that can be parsed."""

# Common error handling utilities

def handle_llm_query_error(service_name: str, error: Exception, operation: str = "query") -> RuntimeError:
    """
    Standard error handling for LLM query operations
    
    Args:
        service_name: Name of the service (e.g., "OpenAI", "DeepSeek")
        error: The caught exception
        operation: Type of operation that failed
        
    Returns:
        Standardized RuntimeError
    """
    logger.error(f"{service_name} {operation} failed: {error}")
    return RuntimeError(f"LLM {operation} failed: {str(error)}")

def create_structured_error_response(service_name: str, error: Exception, schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a standardized error response for structured queries
    
    Args:
        service_name: Name of the service
        error: The caught exception
        schema: The expected schema
        
    Returns:
        Standardized error response dict
    """
    return {
        "error": f"{service_name} query failed: {str(error)}",
        "schema": schema
    }

def create_batch_error_response(error: Exception, prompt_count: int) -> List[str]:
    """
    Create error response for batch query failures
    
    Args:
        error: The caught exception
        prompt_count: Number of prompts that failed
        
    Returns:
        List of error messages
    """
    error_msg = f"Batch execution failed: {str(error)}"
    return [error_msg] * prompt_count

def handle_structured_query_retry_error(
    service_name: str, 
    error: Exception, 
    attempt: int, 
    max_retries: int, 
    schema: Dict[str, Any]
) -> Union[None, Dict[str, Any]]:
    """
    Handle errors in structured query retry loops
    
    Args:
        service_name: Name of the service
        error: The caught exception
        attempt: Current attempt number (0-based)
        max_retries: Maximum number of retries
        schema: Expected schema
        
    Returns:
        None if should continue retrying, error dict if should stop
    """
    if attempt < max_retries:
        logger.warning(f"{service_name} structured query failed, retrying... (attempt {attempt + 1}): {error}")
        return None
    else:
        logger.error(f"{service_name} structured query failed after {max_retries + 1} attempts: {error}")
        return create_structured_error_response(service_name, error, schema)

# Model validation utilities

def validate_model_name(
    service_name: str,
    model_name: str,
    available_models: List[str],
    default_model: str,
    allow_fallback: bool = True
) -> str:
    """
    Validate model name against available models and provide helpful error messages
    
    Args:
        service_name: Name of the service for error messages
        model_name: The model name to validate  
        available_models: List of available model names
        default_model: Default model to fall back to
        allow_fallback: Whether to fall back to default if model not found
        
    Returns:
        Validated model name (original or fallback)
        
    Raises:
        ValueError: If model is invalid and fallback is not allowed
    """
    if not model_name:
        return default_model
        
    # Check if model is available (case-insensitive)
    model_lower = model_name.lower()
    available_lower = [m.lower() for m in available_models]
    
    if model_lower in available_lower:
        # Return the properly cased model name
        return available_models[available_lower.index(model_lower)]
    
    # Model not found - handle based on fallback setting
    if allow_fallback:
        logger.warning(
            f"{service_name}: Model '{model_name}' not found in available models. "
            f"Falling back to default model '{default_model}'. "
            f"Available models: {', '.join(available_models)}"
        )
        return default_model
    else:
        raise ValueError(
            f"{service_name}: Invalid model '{model_name}'. "
            f"Available models: {', '.join(available_models)}"
        )

def safe_model_selection(
    service_name: str,
    requested_model: Optional[str],
    available_models: List[str],
    default_model: str,
    strict_validation: bool = False
) -> str:
    """
    Safely select and validate a model with helpful error messages
    
    Args:
        service_name: Name of the service for error messages
        requested_model: User-requested model (can be None)
        available_models: List of available models
        default_model: Default model to use
        strict_validation: If True, raise error for invalid models instead of fallback
        
    Returns:
        Validated model name
        
    Raises:
        ValueError: If strict_validation is True and model is invalid
    """
    # Use default if no model requested
    if not requested_model:
        return default_model
    
    # Validate the requested model
    return validate_model_name(
        service_name=service_name,
        model_name=requested_model,
        available_models=available_models,
        default_model=default_model,
        allow_fallback=not strict_validation
    )

def get_model_info(model_name: str, available_models: List[str]) -> Dict[str, Any]:
    """
    Get information about a model's availability
    
    Args:
        model_name: The model name to check
        available_models: List of available models
        
    Returns:
        Dictionary with model information
    """
    model_lower = model_name.lower() if model_name else ""
    available_lower = [m.lower() for m in available_models]
    
    is_available = model_lower in available_lower
    suggested_models = []
    
    if not is_available and model_name:
        # Find similar model names for suggestions
        for model in available_models:
            if model_name.lower() in model.lower() or model.lower() in model_name.lower():
                suggested_models.append(model)
    
    return {
        "model_name": model_name,
        "is_available": is_available,
        "exact_match": available_models[available_lower.index(model_lower)] if is_available else None,
        "suggested_models": suggested_models[:5],  # Limit to 5 suggestions
        "available_models": available_models
    }

# Connection health monitoring utilities

class ConnectionHealthTracker:
    """Track basic connection health for LLM services"""
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.total_errors = 0
        self.consecutive_errors = 0
        self.last_error_time: Optional[datetime] = None
        
    def record_request(self, success: bool, error_type: Optional[str] = None):
        """Record a request outcome"""
        if success:
            self.consecutive_errors = 0
        else:
            self.total_errors += 1
            self.consecutive_errors += 1
            self.last_error_time = datetime.now()
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get basic health status"""
        return {
            "service_name": self.service_name,
            "total_errors": self.total_errors,
            "consecutive_errors": self.consecutive_errors,
            "last_error_time": self.last_error_time.isoformat() if self.last_error_time else None
        }

# Global health trackers for each service
_health_trackers: Dict[str, ConnectionHealthTracker] = {}

def get_health_tracker(service_name: str) -> ConnectionHealthTracker:
    """Get or create a health tracker for a service"""
    if service_name not in _health_trackers:
        _health_trackers[service_name] = ConnectionHealthTracker(service_name)
    return _health_trackers[service_name]

def monitor_connection_health(service_name: str):
    """Decorator to monitor connection health for LLM service methods"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            tracker = get_health_tracker(service_name)
            
            try:
                result = await func(*args, **kwargs)
                tracker.record_request(success=True)
                return result
                
            except Exception as e:
                error_type = type(e).__name__
                tracker.record_request(success=False, error_type=error_type)
                raise
                
        return wrapper
    return decorator

def get_all_health_status() -> Dict[str, Dict[str, Any]]:
    """Get health status for all tracked services"""
    return {
        service_name: tracker.get_health_status() 
        for service_name, tracker in _health_trackers.items()
    }

def reset_health_tracker(service_name: str):
    """Reset health tracking for a specific service"""
    if service_name in _health_trackers:
        del _health_trackers[service_name]

def should_circuit_break(service_name: str, threshold: int = 5) -> bool:
    """Check if service should be circuit broken based on consecutive errors"""
    tracker = get_health_tracker(service_name)
    return tracker.consecutive_errors >= threshold 