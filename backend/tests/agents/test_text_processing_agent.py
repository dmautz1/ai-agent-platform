"""
Comprehensive unit tests for TextProcessingAgent.

This module contains comprehensive test coverage for the TextProcessingAgent class,
including initialization, input validation, and execution scenarios.
"""

import pytest
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from unittest.mock import AsyncMock, MagicMock, patch
from text_processing_agent import TextProcessingAgent
from models import JobType, TextProcessingJobData
from agent import AgentExecutionResult


class TestTextProcessingAgent:
    """Test cases for TextProcessingAgent class."""
    
    def setup_method(self):
        """Set up test environment before each test."""
        self.agent = TextProcessingAgent()
    
    def test_agent_initialization(self):
        """Test TextProcessingAgent initialization."""
        assert self.agent.name == "text_processing_agent"
        assert "text processing agent" in self.agent.description.lower()
        assert len(self.agent.operations) == 10
        assert "analyze_sentiment" in self.agent.operations
        assert "extract_keywords" in self.agent.operations
    
    def test_custom_name_initialization(self):
        """Test agent initialization with custom name."""
        custom_agent = TextProcessingAgent(name="custom_text_agent")
        assert custom_agent.name == "custom_text_agent"
    
    def test_get_system_instruction(self):
        """Test system instruction generation."""
        instruction = self.agent._get_system_instruction()
        assert "text processing" in instruction.lower()
        assert "sentiment analysis" in instruction.lower()
        assert "json" in instruction.lower()
        assert len(instruction) > 100  # Should be detailed
    
    def test_get_supported_job_types(self):
        """Test supported job types."""
        job_types = self.agent.get_supported_job_types()
        assert job_types == [JobType.text_processing]
    
    def test_get_supported_operations(self):
        """Test getting supported operations list."""
        operations = self.agent.get_supported_operations()
        expected_operations = [
            "analyze_sentiment", "extract_keywords", "classify_text",
            "analyze_tone", "extract_entities", "summarize_brief",
            "translate", "grammar_check", "readability_score", "custom"
        ]
        
        assert len(operations) == len(expected_operations)
        for op in expected_operations:
            assert op in operations
    
    @pytest.mark.asyncio
    async def test_get_operation_info(self):
        """Test getting detailed operation information."""
        info = await self.agent.get_operation_info()
        
        assert "operations" in info
        assert "total_operations" in info
        assert info["total_operations"] == 10
        
        # Check specific operation info
        sentiment_info = info["operations"]["analyze_sentiment"]
        assert "description" in sentiment_info
        assert "parameters" in sentiment_info
        assert "output" in sentiment_info
    
    @pytest.mark.asyncio
    @patch('text_processing_agent.TextProcessingAgent._query_adk_agent')
    async def test_execute_job_logic_sentiment_analysis(self, mock_query_adk):
        """Test sentiment analysis execution."""
        # Mock ADK response
        mock_response = json.dumps({
            "sentiment": "positive",
            "confidence": 0.85,
            "emotions": {"joy": 0.7, "excitement": 0.3},
            "explanation": "The text expresses positive emotions"
        })
        mock_query_adk.return_value = mock_response
        
        # Create job data
        job_data = TextProcessingJobData(
            text="I love this product! It's amazing!",
            operation="analyze_sentiment"
        )
        
        # Execute job
        result = await self.agent._execute_job_logic(job_data)
        
        # Verify result
        assert result.success
        assert "sentiment" in result.result
        assert result.metadata["operation"] == "analyze_sentiment"
        assert result.metadata["text_length"] == len(job_data.text)
        
        # Verify ADK was called
        mock_query_adk.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('text_processing_agent.TextProcessingAgent._query_adk_agent')
    async def test_execute_job_logic_keyword_extraction(self, mock_query_adk):
        """Test keyword extraction execution."""
        mock_response = json.dumps({
            "keywords": ["artificial", "intelligence", "machine", "learning"],
            "phrases": ["artificial intelligence", "machine learning"],
            "categories": {"nouns": ["intelligence", "learning"], "adjectives": ["artificial"]},
            "relevance_scores": {"artificial": 0.9, "intelligence": 0.95}
        })
        mock_query_adk.return_value = mock_response
        
        job_data = TextProcessingJobData(
            text="Artificial intelligence and machine learning are transforming technology.",
            operation="extract_keywords",
            parameters={"max_keywords": 5}
        )
        
        result = await self.agent._execute_job_logic(job_data)
        
        assert result.success
        assert "keywords" in result.result
        assert result.metadata["parameters"] == {"max_keywords": 5}
        mock_query_adk.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('text_processing_agent.TextProcessingAgent._query_adk_agent')
    async def test_execute_job_logic_text_classification(self, mock_query_adk):
        """Test text classification execution."""
        mock_response = json.dumps({
            "primary_category": "technical",
            "secondary_categories": ["educational", "informative"],
            "confidence_scores": {"technical": 0.9, "educational": 0.7},
            "reasoning": "Contains technical terminology and explanatory content"
        })
        mock_query_adk.return_value = mock_response
        
        job_data = TextProcessingJobData(
            text="Machine learning algorithms use statistical methods to improve performance.",
            operation="classify_text",
            parameters={"categories": ["technical", "casual", "news", "educational"]}
        )
        
        result = await self.agent._execute_job_logic(job_data)
        
        assert result.success
        assert "primary_category" in result.result
        mock_query_adk.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('text_processing_agent.TextProcessingAgent._query_adk_agent')
    async def test_execute_job_logic_tone_analysis(self, mock_query_adk):
        """Test tone analysis execution."""
        mock_response = json.dumps({
            "tone": "professional",
            "style": "formal academic writing",
            "formality_level": 8,
            "emotion_indicators": [],
            "target_audience": "technical professionals"
        })
        mock_query_adk.return_value = mock_response
        
        job_data = TextProcessingJobData(
            text="The methodology employed in this research demonstrates significant improvements.",
            operation="analyze_tone"
        )
        
        result = await self.agent._execute_job_logic(job_data)
        
        assert result.success
        assert "tone" in result.result
        mock_query_adk.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('text_processing_agent.TextProcessingAgent._query_adk_agent')
    async def test_execute_job_logic_entity_extraction(self, mock_query_adk):
        """Test named entity extraction execution."""
        mock_response = json.dumps({
            "entities": [
                {"text": "Apple Inc.", "type": "ORGANIZATION", "position": [0, 9]},
                {"text": "Tim Cook", "type": "PERSON", "position": [25, 33]}
            ],
            "entity_counts": {"ORGANIZATION": 1, "PERSON": 1},
            "relationships": [{"entity1": "Tim Cook", "relation": "CEO_OF", "entity2": "Apple Inc."}],
            "confidence_scores": {"Apple Inc.": 0.95, "Tim Cook": 0.9}
        })
        mock_query_adk.return_value = mock_response
        
        job_data = TextProcessingJobData(
            text="Apple Inc. CEO Tim Cook announced new products.",
            operation="extract_entities",
            parameters={"entity_types": ["PERSON", "ORGANIZATION"]}
        )
        
        result = await self.agent._execute_job_logic(job_data)
        
        assert result.success
        assert "entities" in result.result
        mock_query_adk.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('text_processing_agent.TextProcessingAgent._query_adk_agent')
    async def test_execute_job_logic_brief_summary(self, mock_query_adk):
        """Test brief summarization execution."""
        mock_response = json.dumps({
            "summary": "AI technology is advancing rapidly with new applications.",
            "key_points": ["AI advancement", "new applications", "rapid progress"],
            "word_count": {"original": 50, "summary": 9},
            "compression_ratio": 0.18
        })
        mock_query_adk.return_value = mock_response
        
        job_data = TextProcessingJobData(
            text="Artificial intelligence technology continues to advance at a rapid pace with new applications emerging across various industries.",
            operation="summarize_brief",
            parameters={"max_sentences": 2}
        )
        
        result = await self.agent._execute_job_logic(job_data)
        
        assert result.success
        assert "summary" in result.result
        mock_query_adk.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('text_processing_agent.TextProcessingAgent._query_adk_agent')
    async def test_execute_job_logic_translation(self, mock_query_adk):
        """Test text translation execution."""
        mock_response = json.dumps({
            "translated_text": "Hola, ¿cómo estás?",
            "source_language": "English",
            "target_language": "Spanish",
            "confidence": 0.92,
            "notes": "Direct translation successful"
        })
        mock_query_adk.return_value = mock_response
        
        job_data = TextProcessingJobData(
            text="Hello, how are you?",
            operation="translate",
            parameters={"target_language": "Spanish"}
        )
        
        result = await self.agent._execute_job_logic(job_data)
        
        assert result.success
        assert "translated_text" in result.result
        mock_query_adk.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('text_processing_agent.TextProcessingAgent._query_adk_agent')
    async def test_execute_job_logic_grammar_check(self, mock_query_adk):
        """Test grammar checking execution."""
        mock_response = json.dumps({
            "corrected_text": "This is a well-written sentence.",
            "errors_found": [
                {"error": "missing article", "position": 0, "suggestion": "add 'This'"}
            ],
            "error_count": 1,
            "suggestions": ["Consider using active voice"],
            "readability_improvement": "Improved clarity"
        })
        mock_query_adk.return_value = mock_response
        
        job_data = TextProcessingJobData(
            text="Is a well-written sentence.",
            operation="grammar_check"
        )
        
        result = await self.agent._execute_job_logic(job_data)
        
        assert result.success
        assert "corrected_text" in result.result
        mock_query_adk.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('text_processing_agent.TextProcessingAgent._query_adk_agent')
    async def test_execute_job_logic_readability_analysis(self, mock_query_adk):
        """Test readability analysis execution."""
        mock_response = json.dumps({
            "reading_level": "high school",
            "complexity_score": 6,
            "average_sentence_length": 15,
            "difficult_words": 0.2,
            "recommendations": ["Break down complex sentences", "Use simpler vocabulary"]
        })
        mock_query_adk.return_value = mock_response
        
        job_data = TextProcessingJobData(
            text="The implementation of advanced algorithms requires comprehensive understanding of computational complexity.",
            operation="readability_score"
        )
        
        result = await self.agent._execute_job_logic(job_data)
        
        assert result.success
        assert "reading_level" in result.result
        mock_query_adk.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('text_processing_agent.TextProcessingAgent._query_adk_agent')
    async def test_execute_job_logic_custom_processing(self, mock_query_adk):
        """Test custom processing execution."""
        mock_response = json.dumps({
            "custom_result": "Analysis completed",
            "findings": ["Key insight 1", "Key insight 2"],
            "confidence": 0.8
        })
        mock_query_adk.return_value = mock_response
        
        job_data = TextProcessingJobData(
            text="Sample text for custom analysis",
            operation="custom",
            parameters={
                "instruction": "Identify key themes and insights",
                "output_format": "json"
            }
        )
        
        result = await self.agent._execute_job_logic(job_data)
        
        assert result.success
        assert "custom_result" in result.result
        mock_query_adk.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_execute_job_logic_unsupported_operation(self):
        """Test execution with unsupported operation."""
        job_data = TextProcessingJobData(
            text="Sample text",
            operation="unsupported_operation"
        )
        
        result = await self.agent._execute_job_logic(job_data)
        
        assert not result.success
        assert "Unsupported operation" in result.error_message
        assert "unsupported_operation" in result.error_message
    
    @pytest.mark.asyncio
    @patch('text_processing_agent.TextProcessingAgent._query_adk_agent')
    async def test_execute_job_logic_adk_query_failure(self, mock_query_adk):
        """Test handling of ADK query failure."""
        mock_query_adk.side_effect = RuntimeError("ADK connection failed")
        
        job_data = TextProcessingJobData(
            text="Sample text",
            operation="analyze_sentiment"
        )
        
        result = await self.agent._execute_job_logic(job_data)
        
        assert not result.success
        assert "Text processing failed" in result.error_message
        assert "ADK connection failed" in result.error_message
    
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
        json_response = '{"result": "test", "confidence": 0.8}'
        formatted = self.agent._format_response(json_response, "test_operation")
        
        # Should return unchanged if valid JSON
        assert formatted == json_response
        
        # Verify it's valid JSON
        parsed = json.loads(formatted)
        assert parsed["result"] == "test"
        assert parsed["confidence"] == 0.8
    
    def test_format_response_invalid_json(self):
        """Test response formatting with invalid JSON."""
        text_response = "This is just plain text"
        formatted = self.agent._format_response(text_response, "test_operation")
        
        # Should wrap in JSON structure
        parsed = json.loads(formatted)
        assert parsed["operation"] == "test_operation"
        assert parsed["result"] == text_response
        assert parsed["format"] == "text"
        assert parsed["note"] == "Response was not in JSON format"
    
    def test_format_response_non_json_text(self):
        """Test response formatting with non-JSON text."""
        text_response = "Simple response without JSON structure"
        formatted = self.agent._format_response(text_response, "sentiment_analysis")
        
        parsed = json.loads(formatted)
        assert parsed["operation"] == "sentiment_analysis"
        assert parsed["result"] == text_response
        assert parsed["format"] == "text"
    
    def test_format_response_malformed_json(self):
        """Test response formatting with malformed JSON."""
        malformed_json = '{"incomplete": "json"'  # Missing closing brace
        formatted = self.agent._format_response(malformed_json, "test_operation")
        
        parsed = json.loads(formatted)
        assert parsed["operation"] == "test_operation"
        assert parsed["result"] == malformed_json
        assert parsed["format"] == "text"
        assert parsed["note"] == "Response was not in JSON format"


class TestTextProcessingAgentIntegration:
    """Integration tests for TextProcessingAgent with BaseAgent."""
    
    def setup_method(self):
        """Set up test environment before each test."""
        self.agent = TextProcessingAgent(name="integration_test_agent")
    
    @pytest.mark.asyncio
    @patch('text_processing_agent.create_agent')
    @patch('text_processing_agent.DatabaseClient')
    @patch('text_processing_agent.TextProcessingAgent._query_adk_agent')
    async def test_full_job_execution_integration(self, mock_query_adk, mock_db_client, mock_create_agent):
        """Test full job execution through BaseAgent interface."""
        # Mock dependencies
        mock_adk_agent = MagicMock()
        mock_create_agent.return_value = mock_adk_agent
        mock_db_instance = AsyncMock()
        mock_db_client.return_value = mock_db_instance
        
        # Mock ADK response
        mock_query_adk.return_value = json.dumps({
            "sentiment": "positive",
            "confidence": 0.9
        })
        
        # Create job data
        job_data = TextProcessingJobData(
            text="I love this new feature!",
            operation="analyze_sentiment"
        )
        
        # Execute job through BaseAgent interface
        result = await self.agent.execute_job("test-job-id", job_data, "test-user-id")
        
        # Verify result
        assert result.success
        assert "sentiment" in result.result
        assert result.execution_time is not None
        assert result.metadata["operation"] == "analyze_sentiment"
        
        # Verify agent state
        assert self.agent.execution_count == 1
        assert self.agent.last_execution_time is not None
        
        # Verify database updates
        assert mock_db_instance.update_job.call_count == 2  # running, then completed
    
    @pytest.mark.asyncio
    async def test_agent_info_includes_operations(self):
        """Test that agent info includes text processing operations."""
        info = await self.agent.get_agent_info()
        
        assert info["name"] == "integration_test_agent"
        assert info["supported_job_types"] == ["text_processing"]
        assert "text processing" in info["description"]
    
    @pytest.mark.asyncio
    @patch('text_processing_agent.create_agent')
    @patch('text_processing_agent.DatabaseClient')
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
        assert health["agent_name"] == "integration_test_agent"
        assert health["checks"]["adk_agent"] == "healthy"
        assert health["checks"]["database"] == "healthy"


if __name__ == "__main__":
    pytest.main([__file__]) 