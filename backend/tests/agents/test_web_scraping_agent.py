"""
Unit tests for Web Scraping Agent

Tests the WebScrapingAgent class functionality including web scraping,
AI content analysis, and error handling.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from pydantic import ValidationError
import requests
from datetime import datetime, timezone

from agents.web_scraping_agent import WebScrapingAgent, WebScrapingJobData
from agent import AgentExecutionResult


class TestWebScrapingJobData:
    """Test WebScrapingJobData model validation"""
    
    def test_web_scraping_job_data_valid(self):
        """Test valid WebScrapingJobData creation"""
        data = WebScrapingJobData(
            url="https://example.com",
            max_depth=2,
            include_links=True,
            analyze_content=True
        )
        assert data.url == "https://example.com"
        assert data.max_depth == 2
        assert data.include_links is True
        assert data.analyze_content is True
        assert data.summary_length == "medium"
        assert data.extract_keywords is True
    
    def test_web_scraping_job_data_defaults(self):
        """Test WebScrapingJobData with default values"""
        data = WebScrapingJobData(url="https://example.com")
        assert data.url == "https://example.com"
        assert data.max_depth == 1
        assert data.include_links is True
        assert data.include_images is True
        assert data.analyze_content is True
        assert data.summary_length == "medium"
        assert data.extract_keywords is True
        assert data.custom_selectors is None
    
    def test_web_scraping_job_data_all_fields(self):
        """Test WebScrapingJobData with all fields specified"""
        custom_selectors = {"title": "h1.main-title", "content": ".article-body"}
        data = WebScrapingJobData(
            url="https://example.com/article",
            max_depth=3,
            include_links=False,
            include_images=False,
            analyze_content=True,
            summary_length="long",
            extract_keywords=True,
            custom_selectors=custom_selectors
        )
        assert data.url == "https://example.com/article"
        assert data.max_depth == 3
        assert data.include_links is False
        assert data.include_images is False
        assert data.summary_length == "long"
        assert data.custom_selectors == custom_selectors
    
    def test_web_scraping_job_data_invalid_url(self):
        """Test validation with invalid URL"""
        with pytest.raises(ValidationError):
            WebScrapingJobData(url="not-a-valid-url")
        
        with pytest.raises(ValidationError):
            WebScrapingJobData(url="ftp://example.com")
    
    def test_web_scraping_job_data_invalid_depth(self):
        """Test validation with invalid max_depth"""
        with pytest.raises(ValidationError):
            WebScrapingJobData(url="https://example.com", max_depth=0)
        
        with pytest.raises(ValidationError):
            WebScrapingJobData(url="https://example.com", max_depth=-1)
    
    def test_web_scraping_job_data_invalid_summary_length(self):
        """Test validation with invalid summary_length"""
        with pytest.raises(ValidationError):
            WebScrapingJobData(url="https://example.com", summary_length="invalid")


class TestWebScrapingAgent:
    """Test WebScrapingAgent functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.agent = WebScrapingAgent()
    
    def test_agent_initialization(self):
        """Test agent initialization"""
        assert self.agent.name == "web_scraping"
        assert "scrapes websites" in self.agent.description.lower()
        assert self.agent.result_format == "json"
        assert self.agent.google_ai is not None
        assert self.agent.session is not None
    
    def test_get_system_instruction(self):
        """Test system instruction method"""
        instruction = self.agent._get_system_instruction()
        assert isinstance(instruction, str)
        assert len(instruction) > 0
        assert "web content analysis" in instruction.lower()
        assert "summaries" in instruction.lower()
    
    @pytest.mark.asyncio
    async def test_execute_job_logic_success(self):
        """Test successful job execution"""
        job_data = WebScrapingJobData(
            url="https://example.com",
            analyze_content=True
        )
        
        mock_scraped_data = {
            'url': 'https://example.com',
            'title': 'Example Page',
            'description': 'Example description',
            'content': 'This is example content',
            'links': [],
            'images': [],
            'status_code': 200,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        mock_ai_analysis = {
            'summary': 'This is a summary',
            'insights': ['Insight 1', 'Insight 2'],
            'keywords': ['example', 'content']
        }
        
        with patch.object(self.agent, '_scrape_website') as mock_scrape, \
             patch.object(self.agent, '_analyze_content') as mock_analyze:
            
            mock_scrape.return_value = mock_scraped_data
            mock_analyze.return_value = mock_ai_analysis
            
            result = await self.agent._execute_job_logic(job_data)
            
            assert result.success is True
            assert result.result_format == 'json'
            assert result.metadata['agent'] == 'web_scraping'
            assert result.metadata['url'] == 'https://example.com'
            assert result.metadata['ai_analysis_requested'] is True
            
            mock_scrape.assert_called_once_with(job_data)
            mock_analyze.assert_called_once_with(
                'This is example content', 'medium', True
            )
    
    @pytest.mark.asyncio
    async def test_execute_job_logic_no_analysis(self):
        """Test job execution without AI analysis"""
        job_data = WebScrapingJobData(
            url="https://example.com",
            analyze_content=False
        )
        
        mock_scraped_data = {
            'url': 'https://example.com',
            'title': 'Example Page',
            'description': 'Example description',
            'content': 'This is example content',
            'links': [],
            'images': [],
            'status_code': 200,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        with patch.object(self.agent, '_scrape_website') as mock_scrape:
            mock_scrape.return_value = mock_scraped_data
            
            result = await self.agent._execute_job_logic(job_data)
            
            assert result.success is True
            assert result.metadata['ai_analysis_requested'] is False
            assert result.metadata['ai_analysis_included'] is False
    
    @pytest.mark.asyncio
    async def test_execute_job_logic_scraping_failure(self):
        """Test job execution with scraping failure"""
        job_data = WebScrapingJobData(url="https://example.com")
        
        with patch.object(self.agent, '_scrape_website') as mock_scrape:
            mock_scrape.side_effect = requests.RequestException("Connection failed")
            
            result = await self.agent._execute_job_logic(job_data)
            
            assert result.success is False
            assert "Connection failed" in result.error_message
            assert result.metadata['agent'] == 'web_scraping'
    
    @pytest.mark.asyncio
    async def test_scrape_website_success(self):
        """Test successful website scraping"""
        job_data = WebScrapingJobData(url="https://example.com")
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b"""
        <html>
            <head>
                <title>Example Page</title>
                <meta name="description" content="Example description">
            </head>
            <body>
                <h1>Main Title</h1>
                <p>This is the main content of the page.</p>
                <a href="https://example.com/link1">Link 1</a>
                <img src="https://example.com/image1.jpg" alt="Image 1">
            </body>
        </html>
        """
        mock_response.url = "https://example.com"
        
        with patch.object(self.agent.session, 'get') as mock_get:
            mock_get.return_value = mock_response
            
            scraped_data = await self.agent._scrape_website(job_data)
            
            assert scraped_data['url'] == 'https://example.com'
            assert scraped_data['title'] == 'Example Page'
            assert scraped_data['description'] == 'Example description'
            assert 'Main Title' in scraped_data['content']
            assert 'main content' in scraped_data['content']
            assert scraped_data['status_code'] == 200
            assert len(scraped_data['links']) > 0
            assert len(scraped_data['images']) > 0
    
    @pytest.mark.asyncio
    async def test_scrape_website_http_error(self):
        """Test website scraping with HTTP error"""
        job_data = WebScrapingJobData(url="https://example.com")
        
        with patch.object(self.agent.session, 'get') as mock_get:
            mock_get.side_effect = requests.HTTPError("404 Not Found")
            
            with pytest.raises(Exception) as exc_info:
                await self.agent._scrape_website(job_data)
            
            assert "Failed to fetch URL" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_analyze_content_success(self):
        """Test successful content analysis"""
        content = "This is a test article about artificial intelligence and machine learning."
        
        mock_ai_response = """
        SUMMARY: This article discusses artificial intelligence and machine learning technologies.
        KEY_INSIGHTS: 
        1. AI is transforming various industries
        2. Machine learning is a subset of AI
        3. These technologies require careful implementation
        CONTENT_TYPE: article
        TONE: informational
        TARGET_AUDIENCE: general public
        KEYWORDS: artificial intelligence, machine learning, technology, AI
        """
        
        with patch.object(self.agent.google_ai, 'query') as mock_query:
            mock_query.return_value = mock_ai_response
            
            analysis = await self.agent._analyze_content(content, "medium", True)
            
            assert analysis['summary'] == "This article discusses artificial intelligence and machine learning technologies."
            assert analysis['content_type'] == 'article'
            assert analysis['tone'] == 'informational'
            assert analysis['target_audience'] == 'general public'
            assert len(analysis['keywords']) > 0
            assert 'artificial intelligence' in analysis['keywords']
    
    @pytest.mark.asyncio
    async def test_analyze_content_service_unavailable(self):
        """Test content analysis with unavailable service"""
        content = "Test content"
        
        # Test with None google_ai service
        self.agent.google_ai = None
        
        analysis = await self.agent._analyze_content(content, "medium", True)
        
        assert 'error' in analysis
        assert 'service not available' in analysis['error'].lower()
        assert analysis['summary'] == 'Analysis unavailable - service not initialized'
    
    @pytest.mark.asyncio
    async def test_analyze_content_ai_failure(self):
        """Test content analysis with AI service failure"""
        content = "Test content"
        
        with patch.object(self.agent.google_ai, 'query') as mock_query:
            mock_query.side_effect = Exception("AI service error")
            
            analysis = await self.agent._analyze_content(content, "medium", True)
            
            assert 'error' in analysis
            assert 'AI service error' in analysis['error']
            assert analysis['summary'] == 'Analysis unavailable'
    
    def test_parse_ai_response(self):
        """Test AI response parsing"""
        response = """
        SUMMARY: This is a test summary of the content.
        KEY_INSIGHTS: 
        1. First insight about the topic
        2. Second insight with more details
        3. Third important observation
        CONTENT_TYPE: blog post
        TONE: casual
        TARGET_AUDIENCE: developers
        KEYWORDS: programming, development, coding, software
        """
        
        analysis = self.agent._parse_ai_response(response)
        
        assert analysis['summary'] == "This is a test summary of the content."
        assert analysis['content_type'] == 'blog post'
        assert analysis['tone'] == 'casual'
        assert analysis['target_audience'] == 'developers'
        assert len(analysis['keywords']) == 4
        assert 'programming' in analysis['keywords']
        assert 'development' in analysis['keywords']
    
    def test_structure_output(self):
        """Test output structure formatting"""
        scraped_data = {
            'url': 'https://example.com',
            'title': 'Test Page',
            'description': 'Test description',
            'content': 'Test content',
            'links': [{'url': 'https://example.com/link1', 'text': 'Link 1'}],
            'images': [{'src': 'https://example.com/image1.jpg', 'alt': 'Image 1'}],
            'status_code': 200,
            'timestamp': '2024-01-01T00:00:00Z',
            'ai_analysis': {
                'summary': 'Test summary',
                'insights': ['Insight 1'],
                'keywords': ['test']
            }
        }
        
        job_data = WebScrapingJobData(url="https://example.com")
        
        output = self.agent._structure_output(scraped_data, job_data)
        
        assert 'scraping_metadata' in output
        assert 'page_info' in output
        assert 'content' in output
        assert 'links' in output
        assert 'images' in output
        assert 'ai_analysis' in output
        
        assert output['scraping_metadata']['url'] == 'https://example.com'
        assert output['page_info']['title'] == 'Test Page'
        assert output['content']['text'] == 'Test content'
        assert output['ai_analysis']['summary'] == 'Test summary'
    
    def test_extract_links(self):
        """Test link extraction from HTML"""
        html_content = """
        <html>
            <body>
                <a href="https://example.com/page1">Page 1</a>
                <a href="/relative-link">Relative Link</a>
                <a href="mailto:test@example.com">Email</a>
                <a href="javascript:void(0)">JavaScript Link</a>
                <a href="https://example.com/page2" target="_blank">External Page</a>
            </body>
        </html>
        """
        
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')
        base_url = "https://example.com"
        
        links = self.agent._extract_links(soup, base_url)
        
        assert len(links) >= 3  # Should extract valid HTTP links
        
        # Check that absolute URLs are preserved
        absolute_links = [link for link in links if link['url'].startswith('https://')]
        assert len(absolute_links) >= 2
        
        # Check that relative URLs are converted to absolute
        relative_converted = [link for link in links if 'relative-link' in link['url']]
        assert len(relative_converted) == 1
        assert relative_converted[0]['url'] == 'https://example.com/relative-link'
    
    def test_extract_images(self):
        """Test image extraction from HTML"""
        html_content = """
        <html>
            <body>
                <img src="https://example.com/image1.jpg" alt="Image 1">
                <img src="/relative-image.png" alt="Relative Image">
                <img src="data:image/png;base64,abc123" alt="Data URL Image">
                <img src="https://example.com/image2.gif">
            </body>
        </html>
        """
        
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')
        base_url = "https://example.com"
        
        images = self.agent._extract_images(soup, base_url)
        
        assert len(images) >= 2  # Should extract HTTP images
        
        # Check that absolute URLs are preserved
        absolute_images = [img for img in images if img.get('url', '').startswith('https://')]
        assert len(absolute_images) >= 2
        
        # Check that relative URLs are converted to absolute
        relative_converted = [img for img in images if 'relative-image' in img.get('url', '')]
        assert len(relative_converted) == 1
        assert relative_converted[0]['url'] == 'https://example.com/relative-image.png'
    
    def test_categorize_links(self):
        """Test link categorization"""
        links = [
            {'url': 'https://example.com/page1', 'type': 'webpage'},
            {'url': 'https://example.com/doc.pdf', 'type': 'document'},
            {'url': 'https://example.com/page2', 'type': 'webpage'},
            {'url': 'https://example.com/image.jpg', 'type': 'image'},
            {'url': 'https://example.com/doc.pdf', 'type': 'document'}
        ]
        
        categories = self.agent._categorize_links(links)
        
        assert categories['webpage'] == 2
        assert categories['document'] == 2
        assert categories['image'] == 1


class TestWebScrapingAgentEndpoints:
    """Test WebScrapingAgent endpoint functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.agent = WebScrapingAgent()
        self.mock_user = {'id': 'user123', 'email': 'test@example.com'}
    
    @pytest.mark.asyncio
    async def test_scrape_website_endpoint_success(self):
        """Test successful website scraping via endpoint"""
        request_data = {
            'url': 'https://example.com',
            'analyze_content': True
        }
        
        mock_result = AgentExecutionResult(
            success=True,
            result={'url': 'https://example.com', 'title': 'Test Page'},
            metadata={'agent': 'web_scraping'},
            result_format='json'
        )
        
        with patch.object(self.agent, '_execute_job_logic') as mock_execute:
            mock_execute.return_value = mock_result
            
            response = await self.agent.scrape_website(request_data, self.mock_user)
            
            assert response['status'] == 'success'
            assert response['data']['url'] == 'https://example.com'
            assert response['result_format'] == 'json'
    
    @pytest.mark.asyncio
    async def test_scrape_website_endpoint_failure(self):
        """Test failed website scraping via endpoint"""
        request_data = {
            'url': 'https://invalid-url.com'
        }
        
        mock_result = AgentExecutionResult(
            success=False,
            error_message="Failed to scrape website",
            metadata={'agent': 'web_scraping'}
        )
        
        with patch.object(self.agent, '_execute_job_logic') as mock_execute:
            mock_execute.return_value = mock_result
            
            response = await self.agent.scrape_website(request_data, self.mock_user)
            
            assert response['status'] == 'error'
            assert response['error'] == "Failed to scrape website"
    
    @pytest.mark.asyncio
    async def test_diagnose_ai_analysis_endpoint(self):
        """Test AI analysis diagnostic endpoint"""
        request_data = {
            'test_content': 'This is test content for AI analysis',
            'summary_length': 'short',
            'extract_keywords': True
        }
        
        mock_analysis = {
            'summary': 'Test summary',
            'insights': ['Test insight'],
            'keywords': ['test', 'content']
        }
        
        with patch.object(self.agent, '_analyze_content') as mock_analyze, \
             patch.object(self.agent.google_ai, 'get_info') as mock_info:
            
            mock_analyze.return_value = mock_analysis
            mock_info.return_value = {'service': 'google_ai', 'status': 'available'}
            
            response = await self.agent.diagnose_ai_analysis(request_data, self.mock_user)
            
            assert response['status'] == 'success'
            assert response['analysis_result']['summary'] == 'Test summary'
            assert response['diagnostic'] == 'ai_analysis_successful'
    
    @pytest.mark.asyncio
    async def test_get_agent_info_endpoint(self):
        """Test get agent info endpoint"""
        with patch.object(self.agent.google_ai, 'get_info') as mock_info:
            mock_info.return_value = {'service': 'google_ai', 'status': 'available'}
            
            response = await self.agent.get_agent_info()
            
            assert response['name'] == 'web_scraping'
            assert 'description' in response
            assert 'capabilities' in response
            assert 'google_ai_service' in response
            assert response['status'] == 'available'


class TestWebScrapingAgentIntegration:
    """Integration tests for WebScrapingAgent"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.agent = WebScrapingAgent()
    
    @pytest.mark.asyncio
    async def test_complete_scraping_workflow(self):
        """Test complete scraping workflow with mocked HTTP response"""
        job_data = WebScrapingJobData(
            url="https://example.com",
            analyze_content=True,
            summary_length="short"
        )
        
        # Mock HTTP response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b"""
        <html>
            <head><title>Test Article</title></head>
            <body>
                <h1>Test Article Title</h1>
                <p>This is a test article about web scraping and AI analysis.</p>
                <a href="https://example.com/related">Related Article</a>
            </body>
        </html>
        """
        mock_response.url = "https://example.com"
        
        # Mock AI analysis
        mock_ai_response = """
        SUMMARY: This is a test article about web scraping.
        KEY_INSIGHTS: 1. Web scraping extracts data from websites
        CONTENT_TYPE: article
        TONE: informational
        TARGET_AUDIENCE: developers
        KEYWORDS: web scraping, AI, analysis
        """
        
        with patch.object(self.agent.session, 'get') as mock_get, \
             patch.object(self.agent.google_ai, 'query') as mock_ai_query:
            
            mock_get.return_value = mock_response
            mock_ai_query.return_value = mock_ai_response
            
            result = await self.agent._execute_job_logic(job_data)
            
            assert result.success is True
            assert result.result_format == 'json'
            
            # Verify structure of result
            data = result.result
            assert 'scraping_metadata' in data
            assert 'page_info' in data
            assert 'content' in data
            assert 'ai_analysis' in data
            
            # Verify content extraction
            assert data['page_info']['title'] == 'Test Article'
            assert 'web scraping' in data['content']['text'].lower()
            
            # Verify AI analysis
            assert data['ai_analysis']['summary'] == 'This is a test article about web scraping.'
            assert 'web scraping' in data['ai_analysis']['keywords'] 