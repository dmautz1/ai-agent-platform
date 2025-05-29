"""
Text Processing Agent - Self-Contained Implementation

This agent uses the new v2.0 Self-Contained Agent Framework with embedded 
job models and API endpoints using decorators.
"""

import json
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, validator

from agent_framework import SelfContainedAgent, endpoint, job_model, execute_agent_job, validate_job_data
from models import JobType
from agent import AgentExecutionResult
from logging_system import get_logger

logger = get_logger(__name__)

@job_model
class TextProcessingJobData(BaseModel):
    """Text processing job data model"""
    text: str = Field(..., min_length=1, max_length=50000, description="Text to process")
    operation: str = Field(..., description="Processing operation to perform")
    parameters: Optional[Dict[str, Any]] = Field(default=None, description="Additional parameters")
    
    @validator('text')
    def validate_text_not_empty(cls, v):
        if not v.strip():
            raise ValueError('Text cannot be empty or only whitespace')
        return v
    
    @validator('operation')
    def validate_operation(cls, v):
        allowed_operations = [
            "analyze_sentiment", "extract_keywords", "classify_text", "analyze_tone",
            "extract_entities", "summarize_brief", "translate", "grammar_check", 
            "readability_score", "custom"
        ]
        if v.lower() not in allowed_operations:
            raise ValueError(f'Operation must be one of: {allowed_operations}')
        return v.lower()

class TextProcessingAgent(SelfContainedAgent):
    """
    Self-Contained Text Processing Agent for various text analysis tasks.
    
    Supported operations:
    - analyze_sentiment: Analyze the sentiment of text
    - extract_keywords: Extract important keywords from text
    - classify_text: Classify text into categories
    - analyze_tone: Analyze the tone and style of text
    - extract_entities: Extract named entities from text
    - summarize_brief: Create a brief summary (different from full summarization)
    - translate: Translate text to another language
    - grammar_check: Check and correct grammar
    - readability_score: Calculate readability metrics
    - custom: Custom text processing operation
    """
    
    def __init__(self, **kwargs):
        super().__init__(
            description="Advanced text processing agent using Google ADK for various text analysis tasks",
            **kwargs
        )
        
        # Supported operations mapping
        self.operations = {
            "analyze_sentiment": self._analyze_sentiment,
            "extract_keywords": self._extract_keywords,
            "classify_text": self._classify_text,
            "analyze_tone": self._analyze_tone,
            "extract_entities": self._extract_entities,
            "summarize_brief": self._summarize_brief,
            "translate": self._translate_text,
            "grammar_check": self._check_grammar,
            "readability_score": self._calculate_readability,
            "custom": self._custom_processing
        }
        
        logger.info(f"Initialized TextProcessingAgent with {len(self.operations)} supported operations")
    
    def get_supported_job_types(self) -> List[JobType]:
        """Return the job types supported by this agent."""
        return [JobType.text_processing]
    
    @endpoint("/text-processing/capabilities", methods=["GET"], auth_required=False)
    async def get_capabilities(self):
        """Get text processing capabilities - public endpoint"""
        return {
            "status": "success",
            "agent_name": self.name,
            "operations": list(self.operations.keys()),
            "description": "Advanced text processing with multiple analysis operations",
            "supported_job_types": [jt.value for jt in self.get_supported_job_types()],
            "framework_version": "2.0"
        }
    
    @endpoint("/text-processing/process", methods=["POST"], auth_required=True)
    async def process_text(self, request_data: dict, user: dict):
        """Main text processing endpoint - requires authentication"""
        job_data = validate_job_data(request_data, TextProcessingJobData)
        return await execute_agent_job(self, job_data, user["id"])
    
    @endpoint("/text-processing/analyze-sentiment", methods=["POST"], auth_required=True)
    async def analyze_sentiment_endpoint(self, request_data: dict, user: dict):
        """Direct sentiment analysis endpoint"""
        request_data["operation"] = "analyze_sentiment"
        job_data = validate_job_data(request_data, TextProcessingJobData)
        return await execute_agent_job(self, job_data, user["id"])
    
    @endpoint("/text-processing/extract-keywords", methods=["POST"], auth_required=True)
    async def extract_keywords_endpoint(self, request_data: dict, user: dict):
        """Direct keyword extraction endpoint"""
        request_data["operation"] = "extract_keywords"
        job_data = validate_job_data(request_data, TextProcessingJobData)
        return await execute_agent_job(self, job_data, user["id"])
    
    @endpoint("/text-processing/classify-text", methods=["POST"], auth_required=True)
    async def classify_text_endpoint(self, request_data: dict, user: dict):
        """Direct text classification endpoint"""
        request_data["operation"] = "classify_text"
        job_data = validate_job_data(request_data, TextProcessingJobData)
        return await execute_agent_job(self, job_data, user["id"])
    
    @endpoint("/text-processing/operations", methods=["GET"], auth_required=False)
    async def get_operation_info(self):
        """Get detailed information about supported operations"""
        return {
            "status": "success",
            "operations": {
                "analyze_sentiment": {
                    "description": "Analyze sentiment and emotions in text",
                    "parameters": ["confidence_threshold"],
                    "output": "sentiment, confidence, emotions, explanation"
                },
                "extract_keywords": {
                    "description": "Extract important keywords and phrases",
                    "parameters": ["max_keywords"],
                    "output": "keywords, phrases, categories, relevance_scores"
                },
                "classify_text": {
                    "description": "Classify text into predefined categories",
                    "parameters": ["categories"],
                    "output": "primary_category, secondary_categories, confidence_scores"
                },
                "analyze_tone": {
                    "description": "Analyze tone and writing style",
                    "parameters": [],
                    "output": "tone, style, formality_level, emotion_indicators"
                },
                "extract_entities": {
                    "description": "Extract named entities (people, places, etc.)",
                    "parameters": ["entity_types"],
                    "output": "entities, entity_counts, relationships"
                },
                "summarize_brief": {
                    "description": "Create brief summary of text",
                    "parameters": ["max_sentences"],
                    "output": "summary, key_points, compression_ratio"
                },
                "translate": {
                    "description": "Translate text to another language",
                    "parameters": ["target_language"],
                    "output": "translated_text, source_language, confidence"
                },
                "grammar_check": {
                    "description": "Check and correct grammar",
                    "parameters": [],
                    "output": "corrected_text, errors_found, suggestions"
                },
                "readability_score": {
                    "description": "Calculate readability metrics",
                    "parameters": [],
                    "output": "reading_level, complexity_score, recommendations"
                },
                "custom": {
                    "description": "Custom text processing with user-defined instructions",
                    "parameters": ["instruction", "output_format"],
                    "output": "Custom based on instruction"
                }
            },
            "total_operations": len(self.operations)
        }

    async def _execute_job_logic(self, job_data: TextProcessingJobData) -> AgentExecutionResult:
        """
        Execute the text processing job logic.
        
        Args:
            job_data: Text processing job data
            
        Returns:
            AgentExecutionResult with processing results
        """
        try:
            operation = job_data.operation.lower()
            text = job_data.text
            parameters = job_data.parameters or {}
            
            logger.info(f"Processing text with operation: {operation}", text_length=len(text))
            
            # Validate operation
            if operation not in self.operations:
                available_ops = list(self.operations.keys())
                error_msg = f"Unsupported operation '{operation}'. Available operations: {available_ops}"
                logger.error(error_msg)
                return AgentExecutionResult(
                    success=False,
                    error_message=error_msg
                )
            
            # Execute the specific operation
            operation_func = self.operations[operation]
            result = await operation_func(text, parameters)
            
            logger.info(f"Text processing completed successfully for operation: {operation}")
            
            return AgentExecutionResult(
                success=True,
                result=result,
                metadata={
                    "operation": operation,
                    "text_length": len(text),
                    "parameters": parameters,
                    "processing_type": "text_analysis"
                }
            )
            
        except Exception as e:
            error_msg = f"Text processing failed: {str(e)}"
            logger.error(error_msg, operation=job_data.operation, exception=e)
            return AgentExecutionResult(
                success=False,
                error_message=error_msg,
                metadata={
                    "operation": job_data.operation,
                    "text_length": len(job_data.text)
                }
            )
    
    def _get_system_instruction(self) -> str:
        """Get the system instruction for the Google ADK agent."""
        return """You are an expert text processing AI assistant specialized in analyzing and processing text content. 

Your capabilities include:
- Sentiment analysis (positive, negative, neutral with confidence scores)
- Keyword extraction (identifying important terms and phrases)
- Text classification (categorizing content by topic, intent, or type)
- Tone analysis (formal, casual, professional, emotional, etc.)
- Named entity recognition (people, places, organizations, etc.)
- Brief summarization (concise summaries different from full summarization)
- Text translation (accurate translation between languages)
- Grammar checking and correction
- Readability analysis (reading level, complexity metrics)
- Custom text processing based on specific requirements

Always provide structured, accurate responses with confidence scores where applicable. 
Format your responses as JSON when requested for programmatic use.
Be thorough but concise in your analysis."""

    async def _analyze_sentiment(self, text: str, parameters: Dict[str, Any]) -> str:
        """Analyze sentiment of the text."""
        prompt = f"""Analyze the sentiment of the following text and provide a detailed analysis:

Text: "{text}"

Please provide a JSON response with:
- sentiment: overall sentiment (positive, negative, neutral)
- confidence: confidence score (0-1)
- emotions: detected emotions and their intensities
- explanation: brief explanation of the analysis

Format as valid JSON."""
        
        response = await self._query_adk_agent(prompt)
        return self._format_response(response, "sentiment_analysis")
    
    async def _extract_keywords(self, text: str, parameters: Dict[str, Any]) -> str:
        """Extract keywords from the text."""
        max_keywords = parameters.get("max_keywords", 10)
        
        prompt = f"""Extract the most important keywords and phrases from the following text:

Text: "{text}"

Please provide a JSON response with:
- keywords: list of up to {max_keywords} most important keywords
- phrases: key phrases (2-4 words)
- categories: categorize keywords by type (nouns, verbs, adjectives, etc.)
- relevance_scores: relevance score for each keyword (0-1)

Format as valid JSON."""
        
        response = await self._query_adk_agent(prompt)
        return self._format_response(response, "keyword_extraction")
    
    async def _classify_text(self, text: str, parameters: Dict[str, Any]) -> str:
        """Classify text into categories."""
        categories = parameters.get("categories", ["news", "opinion", "technical", "casual", "formal"])
        
        prompt = f"""Classify the following text into the most appropriate categories:

Text: "{text}"

Available categories: {categories}

Please provide a JSON response with:
- primary_category: most likely category
- secondary_categories: other relevant categories
- confidence_scores: confidence for each category (0-1)
- reasoning: brief explanation for classification

Format as valid JSON."""
        
        response = await self._query_adk_agent(prompt)
        return self._format_response(response, "text_classification")
    
    async def _analyze_tone(self, text: str, parameters: Dict[str, Any]) -> str:
        """Analyze tone and style of the text."""
        prompt = f"""Analyze the tone and writing style of the following text:

Text: "{text}"

Please provide a JSON response with:
- tone: primary tone (formal, casual, professional, friendly, aggressive, etc.)
- style: writing style characteristics
- formality_level: scale from 1-10 (1=very casual, 10=very formal)
- emotion_indicators: words/phrases that indicate emotion
- target_audience: likely intended audience

Format as valid JSON."""
        
        response = await self._query_adk_agent(prompt)
        return self._format_response(response, "tone_analysis")
    
    async def _extract_entities(self, text: str, parameters: Dict[str, Any]) -> str:
        """Extract named entities from the text."""
        entity_types = parameters.get("entity_types", ["PERSON", "ORGANIZATION", "LOCATION", "DATE", "MONEY"])
        
        prompt = f"""Extract named entities from the following text:

Text: "{text}"

Focus on these entity types: {entity_types}

Please provide a JSON response with:
- entities: list of entities with their types and positions
- entity_counts: count of each entity type
- relationships: relationships between entities if apparent
- confidence_scores: confidence for each extracted entity

Format as valid JSON."""
        
        response = await self._query_adk_agent(prompt)
        return self._format_response(response, "entity_extraction")
    
    async def _summarize_brief(self, text: str, parameters: Dict[str, Any]) -> str:
        """Create a brief summary of the text."""
        max_sentences = parameters.get("max_sentences", 3)
        
        prompt = f"""Create a brief summary of the following text in {max_sentences} sentences or less:

Text: "{text}"

Please provide a JSON response with:
- summary: concise summary
- key_points: main points covered
- word_count: original vs summary word count
- compression_ratio: how much the text was compressed

Format as valid JSON."""
        
        response = await self._query_adk_agent(prompt)
        return self._format_response(response, "brief_summary")
    
    async def _translate_text(self, text: str, parameters: Dict[str, Any]) -> str:
        """Translate text to another language."""
        target_language = parameters.get("target_language", "Spanish")
        
        prompt = f"""Translate the following text to {target_language}:

Text: "{text}"

Please provide a JSON response with:
- translated_text: the translated text
- source_language: detected source language
- target_language: target language
- confidence: translation confidence (0-1)
- notes: any translation notes or challenges

Format as valid JSON."""
        
        response = await self._query_adk_agent(prompt)
        return self._format_response(response, "translation")
    
    async def _check_grammar(self, text: str, parameters: Dict[str, Any]) -> str:
        """Check and correct grammar in the text."""
        prompt = f"""Check the grammar of the following text and provide corrections:

Text: "{text}"

Please provide a JSON response with:
- corrected_text: text with grammar corrections
- errors_found: list of grammar errors with explanations
- error_count: total number of errors
- suggestions: improvement suggestions beyond grammar
- readability_improvement: how corrections improve readability

Format as valid JSON."""
        
        response = await self._query_adk_agent(prompt)
        return self._format_response(response, "grammar_check")
    
    async def _calculate_readability(self, text: str, parameters: Dict[str, Any]) -> str:
        """Calculate readability metrics for the text."""
        prompt = f"""Analyze the readability of the following text:

Text: "{text}"

Please provide a JSON response with:
- reading_level: estimated reading level (elementary, middle school, high school, college)
- complexity_score: complexity on scale 1-10
- average_sentence_length: average words per sentence
- difficult_words: percentage of difficult words
- recommendations: suggestions to improve readability

Format as valid JSON."""
        
        response = await self._query_adk_agent(prompt)
        return self._format_response(response, "readability_analysis")
    
    async def _custom_processing(self, text: str, parameters: Dict[str, Any]) -> str:
        """Perform custom text processing based on parameters."""
        custom_instruction = parameters.get("instruction", "Analyze this text")
        output_format = parameters.get("output_format", "json")
        
        prompt = f"""Perform the following custom text processing task:

Task: {custom_instruction}

Text: "{text}"

Please provide your response in {output_format} format with structured results."""
        
        response = await self._query_adk_agent(prompt)
        return self._format_response(response, "custom_processing")
    
    async def _query_adk_agent(self, prompt: str) -> str:
        """
        Query the Google ADK agent with the given prompt.
        
        Args:
            prompt: The prompt to send to the agent
            
        Returns:
            Agent response as string
        """
        if not self._adk_agent:
            raise RuntimeError("ADK agent not initialized")
        
        try:
            # Note: This is a simplified interface. The actual Google ADK API
            # may have different methods for querying agents.
            # This would need to be updated based on the actual ADK implementation.
            response = await self._adk_agent.process(prompt)
            return response
            
        except Exception as e:
            logger.error(f"ADK agent query failed: {e}")
            raise RuntimeError(f"Failed to query ADK agent: {str(e)}")
    
    def _format_response(self, response: str, operation_type: str) -> str:
        """
        Format the response from the ADK agent.
        
        Args:
            response: Raw response from ADK agent
            operation_type: Type of operation performed
            
        Returns:
            Formatted response string
        """
        try:
            # Try to parse as JSON to validate format
            if response.strip().startswith('{'):
                json.loads(response)
                return response
            else:
                # If not JSON, wrap in a JSON structure
                return json.dumps({
                    "operation": operation_type,
                    "result": response,
                    "format": "text"
                })
                
        except json.JSONDecodeError:
            # If JSON parsing fails, return as text result
            logger.warning(f"Response not in JSON format for {operation_type}")
            return json.dumps({
                "operation": operation_type,
                "result": response,
                "format": "text",
                "note": "Response was not in JSON format"
            }) 