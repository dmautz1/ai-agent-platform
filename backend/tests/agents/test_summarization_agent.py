"""
Unit tests for SummarizationAgent.

Tests cover text, audio, and video summarization operations,
error handling, integration with BaseAgent, and response formatting.
"""

import pytest
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import json
from unittest.mock import AsyncMock, MagicMock, patch
from summarization_agent import SummarizationAgent
from models import JobType, TextSummarizationJobData, AudioSummarizationJobData, VideoSummarizationJobData
from agent import AgentExecutionResult


class TestSummarizationAgent:
    """Test cases for SummarizationAgent class."""
    
    def setup_method(self):
        """Set up test environment before each test."""
        self.agent = SummarizationAgent()
    
    def test_agent_initialization(self):
        """Test SummarizationAgent initialization."""
        assert self.agent.name == "summarization_agent"
        assert "multi-media summarization agent" in self.agent.description.lower()
        assert len(self.agent.text_summary_types) == 7
        assert len(self.agent.audio_summary_types) == 6
        assert len(self.agent.video_summary_types) == 6
        assert "extractive" in self.agent.text_summary_types
        assert "comprehensive" in self.agent.audio_summary_types
        assert "visual_summary" in self.agent.video_summary_types
    
    def test_custom_name_initialization(self):
        """Test agent initialization with custom name."""
        custom_agent = SummarizationAgent(name="custom_summary_agent")
        assert custom_agent.name == "custom_summary_agent"
    
    def test_get_system_instruction(self):
        """Test system instruction generation."""
        instruction = self.agent._get_system_instruction()
        assert "summarization ai assistant" in instruction.lower()
        assert "text summarization" in instruction.lower()
        assert "audio summarization" in instruction.lower()
        assert "video summarization" in instruction.lower()
        assert "json" in instruction.lower()
        assert len(instruction) > 500  # Should be very detailed
    
    def test_get_supported_job_types(self):
        """Test supported job types."""
        job_types = self.agent.get_supported_job_types()
        expected_types = [
            JobType.text_summarization,
            JobType.audio_summarization,
            JobType.video_summarization
        ]
        assert job_types == expected_types
    
    def test_get_supported_summary_types(self):
        """Test getting supported summary types by media."""
        summary_types = self.agent.get_supported_summary_types()
        
        assert "text" in summary_types
        assert "audio" in summary_types
        assert "video" in summary_types
        assert len(summary_types["text"]) == 7
        assert len(summary_types["audio"]) == 6
        assert len(summary_types["video"]) == 6
    
    @pytest.mark.asyncio
    async def test_get_summarization_info(self):
        """Test getting detailed summarization information."""
        info = await self.agent.get_summarization_info()
        
        assert "supported_media_types" in info
        assert "text_summarization" in info
        assert "audio_summarization" in info
        assert "video_summarization" in info
        assert "total_media_types" in info
        assert info["total_media_types"] == 3
        
        # Check text summarization details
        text_info = info["text_summarization"]
        assert "supported_types" in text_info
        assert "max_input_length" in text_info
        assert "features" in text_info
    
    @pytest.mark.asyncio
    @patch('summarization_agent.SummarizationAgent._query_adk_agent')
    async def test_execute_job_logic_text_summarization(self, mock_query_adk):
        """Test text summarization execution."""
        # Mock ADK response
        mock_response = json.dumps({
            "summary": "This is a comprehensive summary of the text content.",
            "key_points": ["Point 1", "Point 2", "Point 3"],
            "summary_type": "comprehensive",
            "word_count": {"original": 500, "summary": 50},
            "reading_time": "30 seconds",
            "confidence": 0.9,
            "topics": ["topic1", "topic2"]
        })
        mock_query_adk.return_value = mock_response
        
        # Create job data
        job_data = TextSummarizationJobData(
            text="This is a long article that needs to be summarized into a shorter version with key insights.",
            max_length=150,
            min_length=50,
            style="comprehensive"
        )
        
        # Execute job
        result = await self.agent._execute_job_logic(job_data)
        
        # Verify result
        assert result.success
        assert "summary" in result.result
        assert result.metadata["job_type"] == "text_summarization"
        assert result.metadata["media_type"] == "text"
        assert result.metadata["processing_type"] == "summarization"
        
        # Verify ADK was called
        mock_query_adk.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('summarization_agent.SummarizationAgent._query_adk_agent')
    async def test_execute_job_logic_audio_summarization(self, mock_query_adk):
        """Test audio summarization execution."""
        mock_response = json.dumps({
            "summary": "This audio discusses key topics with multiple speakers.",
            "key_points": ["Discussion point 1", "Discussion point 2"],
            "speakers": ["Speaker A", "Speaker B"],
            "topics": ["AI", "Technology"],
            "duration": "15 minutes",
            "highlights": ["Key quote at 5:30"],
            "confidence": 0.85
        })
        mock_query_adk.return_value = mock_response
        
        job_data = AudioSummarizationJobData(
            transcript="This is a transcript of an audio recording about AI technology...",
            max_length=200,
            include_timestamps=True,
            extract_speakers=True,
            summary_type="comprehensive"
        )
        
        result = await self.agent._execute_job_logic(job_data)
        
        assert result.success
        assert "summary" in result.result
        assert result.metadata["job_type"] == "audio_summarization"
        assert result.metadata["media_type"] == "audio"
        mock_query_adk.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('summarization_agent.SummarizationAgent._query_adk_agent')
    async def test_execute_job_logic_video_summarization(self, mock_query_adk):
        """Test video summarization execution."""
        mock_response = json.dumps({
            "summary": "This video presents a comprehensive overview of the topic.",
            "visual_summary": "The video shows charts and diagrams illustrating key concepts.",
            "audio_summary": "Speaker explains concepts with clear examples.",
            "key_moments": ["Important demonstration at 2:15"],
            "timeline": ["0:00-1:00: Introduction", "1:00-3:00: Main content"],
            "topics": ["presentation", "education"],
            "confidence": 0.92
        })
        mock_query_adk.return_value = mock_response
        
        job_data = VideoSummarizationJobData(
            video_url="https://example.com/video.mp4",
            max_length=250,
            include_visual_analysis=True,
            include_timestamps=True,
            extract_key_moments=True,
            summary_type="comprehensive"
        )
        
        result = await self.agent._execute_job_logic(job_data)
        
        assert result.success
        assert "summary" in result.result
        assert result.metadata["job_type"] == "video_summarization"
        assert result.metadata["media_type"] == "video"
        mock_query_adk.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_execute_job_logic_unsupported_job_type(self):
        """Test execution with unsupported job type."""
        # Create a mock job data with unsupported type
        job_data = MagicMock()
        job_data.job_type = JobType.web_scraping  # Not supported by summarization agent
        
        result = await self.agent._execute_job_logic(job_data)
        
        assert not result.success
        assert "Unsupported job type" in result.error_message
    
    @pytest.mark.asyncio
    @patch('summarization_agent.SummarizationAgent._query_adk_agent')
    async def test_execute_job_logic_adk_failure(self, mock_query_adk):
        """Test handling of ADK query failure."""
        mock_query_adk.side_effect = RuntimeError("ADK connection failed")
        
        job_data = TextSummarizationJobData(
            text="Sample text for summarization",
            max_length=100
        )
        
        result = await self.agent._execute_job_logic(job_data)
        
        assert not result.success
        assert "Summarization failed" in result.error_message
        assert "ADK connection failed" in result.error_message
    
    @pytest.mark.asyncio
    @patch('summarization_agent.SummarizationAgent._query_adk_agent')
    async def test_summarize_text_with_custom_parameters(self, mock_query_adk):
        """Test text summarization with custom parameters."""
        mock_response = json.dumps({
            "summary": "Executive summary of the content.",
            "key_points": ["Key insight 1", "Key insight 2"],
            "summary_type": "executive"
        })
        mock_query_adk.return_value = mock_response
        
        job_data = TextSummarizationJobData(
            text="Long business document requiring executive summary...",
            max_length=100,
            min_length=25,
            style="executive"
        )
        
        result = await self.agent._summarize_text(job_data)
        
        # Verify the prompt included custom parameters
        call_args = mock_query_adk.call_args[0][0]
        assert "executive" in call_args
        assert "Maximum length: 100" in call_args
        assert "Minimum length: 25" in call_args
        assert "summary" in result
    
    @pytest.mark.asyncio
    async def test_prepare_audio_content_with_transcript(self):
        """Test audio content preparation with transcript."""
        job_data = AudioSummarizationJobData(
            transcript="This is a sample transcript of the audio content.",
            max_length=150
        )
        
        content = await self.agent._prepare_audio_content(job_data)
        
        assert "Transcript:" in content
        assert "sample transcript" in content
    
    @pytest.mark.asyncio
    async def test_prepare_audio_content_with_url(self):
        """Test audio content preparation with URL."""
        job_data = AudioSummarizationJobData(
            audio_url="https://example.com/audio.mp3",
            max_length=150
        )
        
        content = await self.agent._prepare_audio_content(job_data)
        
        assert "Audio from URL:" in content
        assert "example.com/audio.mp3" in content
        assert "speech-to-text integration required" in content
    
    @pytest.mark.asyncio
    async def test_prepare_audio_content_with_base64(self):
        """Test audio content preparation with base64 data."""
        job_data = AudioSummarizationJobData(
            audio_data="base64encodedaudiodata",
            max_length=150
        )
        
        content = await self.agent._prepare_audio_content(job_data)
        
        assert "Audio from base64 data" in content
        assert "speech-to-text integration required" in content
    
    @pytest.mark.asyncio
    async def test_prepare_audio_content_no_source(self):
        """Test audio content preparation with no source."""
        job_data = AudioSummarizationJobData(
            max_length=150
        )
        
        with pytest.raises(ValueError) as exc_info:
            await self.agent._prepare_audio_content(job_data)
        
        assert "No audio content source provided" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_prepare_video_content_with_transcript(self):
        """Test video content preparation with transcript."""
        job_data = VideoSummarizationJobData(
            transcript="This is the audio transcript from the video.",
            max_length=200
        )
        
        content = await self.agent._prepare_video_content(job_data)
        
        assert "Audio Transcript:" in content
        assert "audio transcript from the video" in content
    
    @pytest.mark.asyncio
    async def test_prepare_video_content_with_url(self):
        """Test video content preparation with URL."""
        job_data = VideoSummarizationJobData(
            video_url="https://example.com/video.mp4",
            max_length=200
        )
        
        content = await self.agent._prepare_video_content(job_data)
        
        assert "Video URL:" in content
        assert "example.com/video.mp4" in content
        assert "video processing integration required" in content
    
    @pytest.mark.asyncio
    async def test_prepare_video_content_with_base64(self):
        """Test video content preparation with base64 data."""
        job_data = VideoSummarizationJobData(
            video_data="base64encodedvideodata",
            max_length=200
        )
        
        content = await self.agent._prepare_video_content(job_data)
        
        assert "Video from base64 data" in content
        assert "video processing integration required" in content
    
    @pytest.mark.asyncio
    async def test_prepare_video_content_no_source(self):
        """Test video content preparation with no source."""
        job_data = VideoSummarizationJobData(
            max_length=200
        )
        
        with pytest.raises(ValueError) as exc_info:
            await self.agent._prepare_video_content(job_data)
        
        assert "No video content source provided" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_query_adk_agent_not_initialized(self):
        """Test ADK agent query when agent not initialized."""
        self.agent._adk_agent = None
        
        with pytest.raises(RuntimeError) as exc_info:
            await self.agent._query_adk_agent("test prompt")
        
        assert "ADK agent not initialized" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_query_adk_agent_success(self):
        """Test successful ADK agent query."""
        mock_adk_agent = AsyncMock()
        mock_adk_agent.process.return_value = "test response"
        self.agent._adk_agent = mock_adk_agent
        
        response = await self.agent._query_adk_agent("test prompt")
        
        assert response == "test response"
        mock_adk_agent.process.assert_called_once_with("test prompt")
    
    @pytest.mark.asyncio
    async def test_query_adk_agent_exception(self):
        """Test ADK agent query exception handling."""
        mock_adk_agent = AsyncMock()
        mock_adk_agent.process.side_effect = Exception("Processing failed")
        self.agent._adk_agent = mock_adk_agent
        
        with pytest.raises(RuntimeError) as exc_info:
            await self.agent._query_adk_agent("test prompt")
        
        assert "Failed to query ADK agent" in str(exc_info.value)
        assert "Processing failed" in str(exc_info.value)
    
    def test_format_response_valid_json(self):
        """Test response formatting with valid JSON."""
        json_response = '{"summary": "test summary", "confidence": 0.9}'
        formatted = self.agent._format_response(json_response, "text_summarization")
        
        # Should return unchanged if valid JSON
        assert formatted == json_response
        
        # Verify it's valid JSON
        parsed = json.loads(formatted)
        assert parsed["summary"] == "test summary"
        assert parsed["confidence"] == 0.9
    
    def test_format_response_invalid_json(self):
        """Test response formatting with invalid JSON."""
        text_response = "This is a plain text summary"
        formatted = self.agent._format_response(text_response, "text_summarization")
        
        # Should wrap in JSON structure
        parsed = json.loads(formatted)
        assert parsed["operation"] == "text_summarization"
        assert parsed["result"] == text_response
        assert parsed["format"] == "text"
        assert parsed["note"] == "Response was not in JSON format"
    
    def test_format_response_malformed_json(self):
        """Test response formatting with malformed JSON."""
        malformed_json = '{"summary": "incomplete"'  # Missing closing brace
        formatted = self.agent._format_response(malformed_json, "audio_summarization")
        
        parsed = json.loads(formatted)
        assert parsed["operation"] == "audio_summarization"
        assert parsed["result"] == malformed_json
        assert parsed["format"] == "text"
        assert parsed["note"] == "Response was not in JSON format"


class TestSummarizationAgentIntegration:
    """Integration tests for SummarizationAgent with BaseAgent."""
    
    def setup_method(self):
        """Set up test environment before each test."""
        self.agent = SummarizationAgent(name="integration_test_summarizer")
    
    @pytest.mark.asyncio
    @patch('summarization_agent.create_agent')
    @patch('summarization_agent.DatabaseClient')
    @patch('summarization_agent.SummarizationAgent._query_adk_agent')
    async def test_full_job_execution_integration(self, mock_query_adk, mock_db_client, mock_create_agent):
        """Test full job execution through BaseAgent interface."""
        # Mock dependencies
        mock_adk_agent = MagicMock()
        mock_create_agent.return_value = mock_adk_agent
        mock_db_instance = AsyncMock()
        mock_db_client.return_value = mock_db_instance
        
        # Mock ADK response
        mock_query_adk.return_value = json.dumps({
            "summary": "This is a comprehensive summary.",
            "key_points": ["Point 1", "Point 2"],
            "confidence": 0.9
        })
        
        # Create job data
        job_data = TextSummarizationJobData(
            text="This is a long article that needs summarization for better readability.",
            max_length=100,
            style="comprehensive"
        )
        
        # Execute job through BaseAgent interface
        result = await self.agent.execute_job("test-job-id", job_data, "test-user-id")
        
        # Verify result
        assert result.success
        assert "summary" in result.result
        assert result.execution_time is not None
        assert result.metadata["job_type"] == "text_summarization"
        
        # Verify agent state
        assert self.agent.execution_count == 1
        assert self.agent.last_execution_time is not None
        
        # Verify database updates
        assert mock_db_instance.update_job.call_count == 2  # running, then completed
    
    @pytest.mark.asyncio
    async def test_agent_info_includes_summarization_types(self):
        """Test that agent info includes summarization capabilities."""
        info = await self.agent.get_agent_info()
        
        assert info["name"] == "integration_test_summarizer"
        expected_job_types = ["text_summarization", "audio_summarization", "video_summarization"]
        assert info["supported_job_types"] == expected_job_types
        assert "multi-media summarization" in info["description"]
    
    @pytest.mark.asyncio
    @patch('summarization_agent.create_agent')
    @patch('summarization_agent.DatabaseClient')
    async def test_health_check_integration(self, mock_db_client, mock_create_agent):
        """Test health check integration."""
        # Mock dependencies
        mock_create_agent.return_value = MagicMock()
        mock_db_instance = AsyncMock()
        mock_db_instance.test_connection = AsyncMock()
        mock_db_client.return_value = mock_db_instance
        
        await self.agent.initialize()
        health = await self.agent.health_check()
        
        assert health["healthy"] is True
        assert health["agent_name"] == "integration_test_summarizer"
        assert health["checks"]["adk_agent"] == "healthy"
        assert health["checks"]["database"] == "healthy"
    
    @pytest.mark.asyncio
    @patch('summarization_agent.SummarizationAgent._query_adk_agent')
    async def test_multiple_media_type_support(self, mock_query_adk):
        """Test that agent supports multiple media types correctly."""
        mock_query_adk.return_value = json.dumps({"summary": "Test summary"})
        
        # Test text summarization
        text_job = TextSummarizationJobData(text="Test text", max_length=50)
        text_result = await self.agent._execute_job_logic(text_job)
        assert text_result.success
        assert text_result.metadata["media_type"] == "text"
        
        # Test audio summarization
        audio_job = AudioSummarizationJobData(transcript="Test transcript", max_length=50)
        audio_result = await self.agent._execute_job_logic(audio_job)
        assert audio_result.success
        assert audio_result.metadata["media_type"] == "audio"
        
        # Test video summarization
        video_job = VideoSummarizationJobData(transcript="Test video transcript", max_length=50)
        video_result = await self.agent._execute_job_logic(video_job)
        assert video_result.success
        assert video_result.metadata["media_type"] == "video"


class TestSummarizationJobDataValidation:
    """Test job data validation for different summarization types."""
    
    def test_text_summarization_job_data_validation(self):
        """Test TextSummarizationJobData validation."""
        # Valid data
        valid_data = TextSummarizationJobData(
            text="Sample text for summarization",
            max_length=100,
            min_length=30
        )
        assert valid_data.job_type == JobType.text_summarization
        assert valid_data.max_length == 100
        assert valid_data.min_length == 30
        
        # Test min_length >= max_length validation
        with pytest.raises(ValueError):
            TextSummarizationJobData(
                text="Sample text",
                max_length=50,
                min_length=60  # Invalid: min > max
            )
    
    def test_audio_summarization_job_data_validation(self):
        """Test AudioSummarizationJobData validation."""
        # Valid with transcript
        valid_transcript = AudioSummarizationJobData(
            transcript="Sample transcript",
            max_length=200
        )
        assert valid_transcript.job_type == JobType.audio_summarization
        
        # Valid with audio URL
        valid_url = AudioSummarizationJobData(
            audio_url="https://example.com/audio.mp3",
            max_length=200
        )
        assert valid_url.audio_url == "https://example.com/audio.mp3"
        
        # Valid with base64 data
        valid_data = AudioSummarizationJobData(
            audio_data="base64data",
            max_length=200
        )
        assert valid_data.audio_data == "base64data"
    
    def test_video_summarization_job_data_validation(self):
        """Test VideoSummarizationJobData validation."""
        # Valid with transcript
        valid_transcript = VideoSummarizationJobData(
            transcript="Sample video transcript",
            max_length=300
        )
        assert valid_transcript.job_type == JobType.video_summarization
        
        # Valid with video URL
        valid_url = VideoSummarizationJobData(
            video_url="https://example.com/video.mp4",
            max_length=300
        )
        assert valid_url.video_url == "https://example.com/video.mp4"
        
        # Test frame sampling rate validation
        valid_frame_rate = VideoSummarizationJobData(
            transcript="Sample",
            frame_sampling_rate=60,
            max_length=300
        )
        assert valid_frame_rate.frame_sampling_rate == 60


if __name__ == "__main__":
    pytest.main([__file__]) 