"""
Summarization Agent - Self-Contained Implementation

This agent uses the new v2.0 Self-Contained Agent Framework with embedded 
job models and API endpoints using decorators. Provides comprehensive 
summarization capabilities across multiple media types (text, audio, video).
"""

import json
import base64
from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field, validator

from agent_framework import SelfContainedAgent, endpoint, job_model, execute_agent_job, validate_job_data
from models import JobType
from agent import AgentExecutionResult
from logging_system import get_logger

logger = get_logger(__name__)

@job_model
class TextSummarizationJobData(BaseModel):
    """Text summarization job data model"""
    text: str = Field(..., min_length=1, max_length=100000, description="Text to summarize")
    max_length: Optional[int] = Field(default=150, ge=10, le=1000, description="Maximum summary length in words")
    min_length: Optional[int] = Field(default=30, ge=5, le=500, description="Minimum summary length in words")
    style: Optional[str] = Field(default="neutral", description="Summary style")
    
    @validator('min_length')
    def validate_length_relationship(cls, v, values):
        if 'max_length' in values and v >= values['max_length']:
            raise ValueError('min_length must be less than max_length')
        return v

@job_model
class AudioSummarizationJobData(BaseModel):
    """Audio summarization job data model"""
    transcript: Optional[str] = Field(default=None, description="Audio transcript text")
    audio_url: Optional[str] = Field(default=None, description="URL to audio file")
    audio_data: Optional[str] = Field(default=None, description="Base64-encoded audio data")
    max_length: Optional[int] = Field(default=200, ge=10, le=1000, description="Maximum summary length in words")
    style: Optional[str] = Field(default="comprehensive", description="Summary style")
    speaker_identification: Optional[bool] = Field(default=False, description="Include speaker identification")
    
    @validator('audio_url')
    def validate_audio_url(cls, v):
        if v and not v.startswith(('http://', 'https://')):
            raise ValueError('Audio URL must start with http:// or https://')
        return v
    
    @validator('audio_data')
    def validate_has_content(cls, v, values):
        transcript = values.get('transcript')
        audio_url = values.get('audio_url')
        if not transcript and not audio_url and not v:
            raise ValueError('Must provide either transcript, audio_url, or audio_data')
        return v

@job_model
class VideoSummarizationJobData(BaseModel):
    """Video summarization job data model"""
    transcript: Optional[str] = Field(default=None, description="Video transcript text")
    video_url: Optional[str] = Field(default=None, description="URL to video file")
    video_data: Optional[str] = Field(default=None, description="Base64-encoded video data")
    max_length: Optional[int] = Field(default=250, ge=10, le=1000, description="Maximum summary length in words")
    style: Optional[str] = Field(default="comprehensive", description="Summary style")
    include_visual_elements: Optional[bool] = Field(default=True, description="Include visual element descriptions")
    include_timestamps: Optional[bool] = Field(default=False, description="Include timestamp references")
    
    @validator('video_url')
    def validate_video_url(cls, v):
        if v and not v.startswith(('http://', 'https://')):
            raise ValueError('Video URL must start with http:// or https://')
        return v
    
    @validator('video_data')
    def validate_has_content(cls, v, values):
        transcript = values.get('transcript')
        video_url = values.get('video_url')
        if not transcript and not video_url and not v:
            raise ValueError('Must provide either transcript, video_url, or video_data')
        return v

class SummarizationAgent(SelfContainedAgent):
    """
    Self-Contained Comprehensive Summarization Agent for multiple media types.
    
    Supported Media Types:
    - Text: Long-form articles, documents, reports
    - Audio: Podcasts, meetings, lectures, interviews
    - Video: Presentations, tutorials, conferences, movies
    
    Supported Summarization Types:
    - extractive: Extract key sentences/segments
    - abstractive: Generate new summary text
    - structured: Organize summary in structured format
    - bullet_points: Key points in bullet format
    - executive: Executive summary style
    - comprehensive: Detailed comprehensive summary
    - highlight_reel: Key moments/highlights
    """
    
    def __init__(self, **kwargs):
        super().__init__(
            description="Advanced multi-media summarization agent using Google ADK for text, audio, and video content",
            **kwargs
        )
        
        # Supported summarization types by media
        self.text_summary_types = [
            "extractive", "abstractive", "structured", "bullet_points", 
            "executive", "comprehensive", "key_insights"
        ]
        
        self.audio_summary_types = [
            "comprehensive", "key_points", "transcript_summary", 
            "speaker_analysis", "topic_breakdown", "highlight_reel"
        ]
        
        self.video_summary_types = [
            "comprehensive", "visual_summary", "scene_breakdown", 
            "key_moments", "transcript_visual", "highlight_reel"
        ]
        
        logger.info(f"Initialized SummarizationAgent supporting {len(self.get_supported_job_types())} media types")
    
    def get_supported_job_types(self) -> List[JobType]:
        """Return the job types supported by this agent."""
        return [
            JobType.text_summarization,
            JobType.audio_summarization,
            JobType.video_summarization
        ]
    
    @endpoint("/summarization/capabilities", methods=["GET"], auth_required=False)
    async def get_capabilities(self):
        """Get summarization capabilities - public endpoint"""
        return {
            "status": "success",
            "agent_name": self.name,
            "supported_media_types": ["text", "audio", "video"],
            "supported_job_types": [jt.value for jt in self.get_supported_job_types()],
            "text_summary_types": self.text_summary_types,
            "audio_summary_types": self.audio_summary_types,
            "video_summary_types": self.video_summary_types,
            "framework_version": "2.0"
        }
    
    @endpoint("/summarization/text", methods=["POST"], auth_required=True)
    async def summarize_text(self, request_data: dict, user: dict):
        """Text summarization endpoint"""
        job_data = validate_job_data(request_data, TextSummarizationJobData)
        return await execute_agent_job(self, job_data, user["id"])
    
    @endpoint("/summarization/audio", methods=["POST"], auth_required=True)
    async def summarize_audio(self, request_data: dict, user: dict):
        """Audio summarization endpoint"""
        job_data = validate_job_data(request_data, AudioSummarizationJobData)
        return await execute_agent_job(self, job_data, user["id"])
    
    @endpoint("/summarization/video", methods=["POST"], auth_required=True)
    async def summarize_video(self, request_data: dict, user: dict):
        """Video summarization endpoint"""
        job_data = validate_job_data(request_data, VideoSummarizationJobData)
        return await execute_agent_job(self, job_data, user["id"])
    
    @endpoint("/summarization/info", methods=["GET"], auth_required=False)
    async def get_summarization_info(self):
        """Get detailed summarization information"""
        return {
            "status": "success",
            "supported_summary_types": {
                "text": self.text_summary_types,
                "audio": self.audio_summary_types,
                "video": self.video_summary_types
            },
            "features": {
                "multi_media_support": True,
                "speaker_identification": True,
                "visual_element_analysis": True,
                "timestamp_support": True,
                "custom_length_control": True,
                "style_customization": True
            },
            "media_type_info": {
                "text": {
                    "max_length": 100000,
                    "supported_formats": ["plain_text", "markdown", "html"],
                    "min_summary_length": 5,
                    "max_summary_length": 1000
                },
                "audio": {
                    "supported_formats": ["transcript", "url", "base64"],
                    "speaker_identification": True,
                    "processing_note": "Audio processing requires transcript or URL"
                },
                "video": {
                    "supported_formats": ["transcript", "url", "base64"],
                    "visual_analysis": True,
                    "timestamp_support": True,
                    "processing_note": "Video processing requires transcript or URL"
                }
            }
        }

    async def _execute_job_logic(
        self, 
        job_data: Union[TextSummarizationJobData, AudioSummarizationJobData, VideoSummarizationJobData]
    ) -> AgentExecutionResult:
        """
        Execute the summarization job logic based on media type.
        
        Args:
            job_data: Summarization job data for specific media type
            
        Returns:
            AgentExecutionResult with summarization results
        """
        try:
            # Determine job type from the job data instance
            if isinstance(job_data, TextSummarizationJobData):
                job_type = JobType.text_summarization
                result = await self._summarize_text(job_data)
            elif isinstance(job_data, AudioSummarizationJobData):
                job_type = JobType.audio_summarization
                result = await self._summarize_audio(job_data)
            elif isinstance(job_data, VideoSummarizationJobData):
                job_type = JobType.video_summarization
                result = await self._summarize_video(job_data)
            else:
                raise ValueError(f"Unsupported job data type: {type(job_data)}")
            
            logger.info(f"Processing {job_type.value} summarization request")
            
            logger.info(f"Successfully completed {job_type.value} summarization")
            
            return AgentExecutionResult(
                success=True,
                result=result,
                metadata={
                    "job_type": job_type.value,
                    "summary_length": len(result),
                    "media_type": job_type.value.split('_')[0],  # text, audio, video
                    "processing_type": "summarization"
                }
            )
            
        except Exception as e:
            error_msg = f"Summarization failed: {str(e)}"
            logger.error(error_msg, exception=e)
            return AgentExecutionResult(
                success=False,
                error_message=error_msg,
                metadata={
                    "processing_type": "summarization"
                }
            )
    
    def _get_system_instruction(self) -> str:
        """Get the system instruction for the Google ADK agent."""
        return """You are an expert summarization AI assistant specialized in creating high-quality summaries across different media types.

Your capabilities include:

TEXT SUMMARIZATION:
- Extractive summarization (selecting key sentences)
- Abstractive summarization (generating new summary text)
- Structured summaries with clear sections
- Executive summaries for business content
- Key insights and takeaways identification
- Bullet point summaries for quick reading

AUDIO SUMMARIZATION:
- Transcript-based summarization
- Speaker identification and analysis
- Key topics and discussion points
- Meeting minutes and action items
- Podcast highlights and key moments
- Interview summaries with speaker attribution

VIDEO SUMMARIZATION:
- Combined visual and audio analysis
- Scene-by-scene breakdown
- Key visual moments identification
- Presentation slide summaries
- Action sequences and highlights
- Timeline-based summaries with timestamps

QUALITY STANDARDS:
- Maintain factual accuracy and context
- Preserve important details and nuances
- Use clear, concise language
- Provide structured, organized output
- Include confidence scores when applicable
- Format responses as JSON for programmatic use

Always tailor the summary length, style, and focus to the specified requirements.
Be thorough but concise, and ensure summaries capture the essence of the content."""

    async def _summarize_text(self, job_data: TextSummarizationJobData) -> str:
        """Summarize text content."""
        text = job_data.text
        max_length = job_data.max_length or 150
        min_length = job_data.min_length or 30
        style = job_data.style or "neutral"
        
        # Determine summary type from style or use comprehensive as default
        summary_type = style if style in self.text_summary_types else "comprehensive"
        
        prompt = f"""Summarize the following text using {summary_type} summarization approach:

Text: "{text}"

Requirements:
- Maximum length: {max_length} words
- Minimum length: {min_length} words
- Style: {style}
- Summary type: {summary_type}

Please provide a JSON response with:
- summary: the main summary text
- key_points: list of key points (3-5 items)
- summary_type: type of summarization used
- word_count: original vs summary word counts
- reading_time: estimated reading time for summary
- confidence: confidence score (0-1)
- topics: main topics covered

Format as valid JSON."""
        
        response = await self._query_adk_agent(prompt)
        return self._format_response(response, "text_summarization")
    
    async def _summarize_audio(self, job_data: AudioSummarizationJobData) -> str:
        """Summarize audio content."""
        content = await self._prepare_audio_content(job_data)
        max_length = job_data.max_length or 200
        style = job_data.style or "comprehensive"
        speaker_id = job_data.speaker_identification or False
        
        summary_type = style if style in self.audio_summary_types else "comprehensive"
        
        prompt = f"""Summarize the following audio content using {summary_type} approach:

Audio Content: "{content}"

Requirements:
- Maximum length: {max_length} words
- Style: {style}
- Speaker identification: {speaker_id}
- Summary type: {summary_type}

Please provide a JSON response with:
- summary: the main summary text
- key_topics: main topics discussed
- speakers: speaker analysis if applicable
- highlights: key moments or highlights
- action_items: any action items mentioned
- confidence: confidence score (0-1)
- duration_estimate: estimated original duration

Format as valid JSON."""
        
        response = await self._query_adk_agent(prompt)
        return self._format_response(response, "audio_summarization")
    
    async def _summarize_video(self, job_data: VideoSummarizationJobData) -> str:
        """Summarize video content."""
        content = await self._prepare_video_content(job_data)
        max_length = job_data.max_length or 250
        style = job_data.style or "comprehensive"
        visual_elements = job_data.include_visual_elements or True
        timestamps = job_data.include_timestamps or False
        
        summary_type = style if style in self.video_summary_types else "comprehensive"
        
        prompt = f"""Summarize the following video content using {summary_type} approach:

Video Content: "{content}"

Requirements:
- Maximum length: {max_length} words
- Style: {style}
- Include visual elements: {visual_elements}
- Include timestamps: {timestamps}
- Summary type: {summary_type}

Please provide a JSON response with:
- summary: the main summary text
- key_scenes: important scenes or segments
- visual_highlights: key visual elements
- speakers: speaker analysis if applicable
- topics: main topics covered
- timestamps: key timestamps if requested
- confidence: confidence score (0-1)

Format as valid JSON."""
        
        response = await self._query_adk_agent(prompt)
        return self._format_response(response, "video_summarization")
    
    async def _prepare_audio_content(self, job_data: AudioSummarizationJobData) -> str:
        """Prepare audio content for summarization."""
        if job_data.transcript:
            return job_data.transcript
        elif job_data.audio_url:
            # TODO: Implement audio transcription from URL
            return f"[Audio URL provided: {job_data.audio_url}] - Transcription service integration needed"
        elif job_data.audio_data:
            # TODO: Implement audio transcription from base64 data
            return "[Audio data provided as base64] - Transcription service integration needed"
        else:
            raise ValueError("No audio content provided")
    
    async def _prepare_video_content(self, job_data: VideoSummarizationJobData) -> str:
        """Prepare video content for summarization."""
        if job_data.transcript:
            return job_data.transcript
        elif job_data.video_url:
            # TODO: Implement video transcription and analysis from URL
            return f"[Video URL provided: {job_data.video_url}] - Video processing service integration needed"
        elif job_data.video_data:
            # TODO: Implement video transcription and analysis from base64 data
            return "[Video data provided as base64] - Video processing service integration needed"
        else:
            raise ValueError("No video content provided")
    
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