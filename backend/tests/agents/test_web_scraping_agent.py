"""
Unit tests for WebScrapingAgent.

Tests cover various web scraping operations, error handling, 
rate limiting, content extraction, and integration with BaseAgent.
"""

import pytest
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import json
import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch
from bs4 import BeautifulSoup
from web_scraping_agent import WebScrapingAgent
from models import JobType, WebScrapingJobData
from agent import AgentExecutionResult


class TestWebScrapingAgent:
    """Test cases for WebScrapingAgent class."""
    
    def setup_method(self):
        """Set up test environment before each test."""
        self.agent = WebScrapingAgent()
    
    def test_agent_initialization(self):
        """Test WebScrapingAgent initialization."""
        assert self.agent.name == "web_scraping_agent"
        assert "web scraping agent" in self.agent.description.lower()
        assert len(self.agent.supported_operations) == 12
        assert "extract_text" in self.agent.supported_operations
        assert "extract_links" in self.agent.supported_operations
        assert "full_page_scrape" in self.agent.supported_operations
        assert self.agent.default_options["timeout"] == 30
        assert self.agent.default_options["max_page_size"] == 10 * 1024 * 1024
    
    def test_custom_name_initialization(self):
        """Test agent initialization with custom name."""
        custom_agent = WebScrapingAgent(name="custom_scraper")
        assert custom_agent.name == "custom_scraper"
    
    def test_get_system_instruction(self):
        """Test system instruction generation."""
        instruction = self.agent._get_system_instruction()
        assert "web scraping and content extraction" in instruction.lower()
        assert "content extraction" in instruction.lower()
        assert "error handling" in instruction.lower()
        assert "json responses" in instruction.lower()
        assert len(instruction) > 1000  # Should be very detailed
    
    def test_get_supported_job_types(self):
        """Test supported job types."""
        job_types = self.agent.get_supported_job_types()
        assert job_types == [JobType.web_scraping]
    
    def test_get_supported_operations(self):
        """Test getting supported operations."""
        operations = self.agent.get_supported_operations()
        expected_ops = [
            "extract_text", "extract_links", "extract_images", "extract_tables",
            "extract_forms", "extract_metadata", "extract_structured_data",
            "full_page_scrape", "extract_by_selectors", "extract_pagination",
            "extract_social_media", "extract_contact_info"
        ]
        assert operations == expected_ops
    
    @pytest.mark.asyncio
    async def test_get_scraping_info(self):
        """Test getting detailed scraping information."""
        info = await self.agent.get_scraping_info()
        
        assert "supported_operations" in info
        assert "default_options" in info
        assert "features" in info
        assert "extraction_capabilities" in info
        assert info["features"]["rate_limiting"] is True
        assert info["features"]["error_recovery"] is True
        assert len(info["supported_operations"]) == 12
    
    def test_determine_operation(self):
        """Test operation determination logic."""
        # With selectors
        selectors = {"title": "h1", "content": ".main"}
        operation = self.agent._determine_operation(selectors, {})
        assert operation == "extract_by_selectors"
        
        # With explicit operation in options
        operation = self.agent._determine_operation({}, {"operation": "extract_text"})
        assert operation == "extract_text"
        
        # Invalid operation defaults to full_page_scrape
        operation = self.agent._determine_operation({}, {"operation": "invalid_op"})
        assert operation == "full_page_scrape"
        
        # No selectors or operation defaults to full_page_scrape
        operation = self.agent._determine_operation({}, {})
        assert operation == "full_page_scrape"
    
    @pytest.mark.asyncio
    async def test_apply_rate_limiting(self):
        """Test rate limiting functionality."""
        url = "https://example.com"
        delay = 0.1  # Small delay for testing
        
        # First request should not be delayed
        start_time = time.time()
        await self.agent._apply_rate_limiting(url, delay)
        elapsed = time.time() - start_time
        assert elapsed < 0.05  # Should be almost instant
        
        # Second request should be delayed
        start_time = time.time()
        await self.agent._apply_rate_limiting(url, delay)
        elapsed = time.time() - start_time
        assert elapsed >= delay * 0.8  # Allow some tolerance
    
    @pytest.mark.asyncio
    @patch('web_scraping_agent.aiohttp.ClientSession')
    async def test_fetch_page_success(self, mock_session):
        """Test successful page fetching."""
        # Mock response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.headers = {
            'Content-Type': 'text/html; charset=utf-8',
            'Content-Length': '1000'
        }
        mock_response.read.return_value = b'<html><body>Test content</body></html>'
        mock_response.get_encoding.return_value = 'utf-8'
        mock_response.url = 'https://example.com'
        
        mock_session_instance = AsyncMock()
        mock_session_instance.get.return_value.__aenter__.return_value = mock_response
        mock_session.return_value.__aenter__.return_value = mock_session_instance
        
        url = "https://example.com"
        options = {"timeout": 30}
        
        html_content, metadata = await self.agent._fetch_page(url, options)
        
        assert html_content == '<html><body>Test content</body></html>'
        assert metadata["status_code"] == 200
        assert metadata["content_type"] == 'text/html; charset=utf-8'
        assert metadata["encoding"] == 'utf-8'
    
    @pytest.mark.asyncio
    @patch('web_scraping_agent.aiohttp.ClientSession')
    async def test_fetch_page_http_error(self, mock_session):
        """Test page fetching with HTTP error."""
        mock_response = AsyncMock()
        mock_response.status = 404
        mock_response.reason = "Not Found"
        
        mock_session_instance = AsyncMock()
        mock_session_instance.get.return_value.__aenter__.return_value = mock_response
        mock_session.return_value.__aenter__.return_value = mock_session_instance
        
        url = "https://example.com/notfound"
        options = {"timeout": 30}
        
        with pytest.raises(Exception) as exc_info:
            await self.agent._fetch_page(url, options)
        
        assert "HTTP 404" in str(exc_info.value)
    
    @pytest.mark.asyncio
    @patch('web_scraping_agent.aiohttp.ClientSession')
    async def test_fetch_page_content_too_large(self, mock_session):
        """Test page fetching with content size limit."""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.headers = {'Content-Length': '20000000'}  # 20MB
        
        mock_session_instance = AsyncMock()
        mock_session_instance.get.return_value.__aenter__.return_value = mock_response
        mock_session.return_value.__aenter__.return_value = mock_session_instance
        
        url = "https://example.com"
        options = {"timeout": 30, "max_page_size": 10 * 1024 * 1024}  # 10MB limit
        
        with pytest.raises(Exception) as exc_info:
            await self.agent._fetch_page(url, options)
        
        assert "Page too large" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_extract_text(self):
        """Test text extraction functionality."""
        html = """
        <html>
            <head><title>Test Page</title></head>
            <body>
                <nav>Navigation</nav>
                <main>
                    <h1>Main Title</h1>
                    <h2 id="subtitle">Subtitle</h2>
                    <p>First paragraph content.</p>
                    <p>Second paragraph content.</p>
                </main>
                <footer>Footer content</footer>
                <script>console.log('test');</script>
            </body>
        </html>
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        result = await self.agent._extract_text(soup, "https://example.com", {})
        
        assert result["operation"] == "extract_text"
        assert "Main Title" in result["full_text"]
        assert "First paragraph content" in result["full_text"]
        assert "Navigation" not in result["full_text"]  # Should be removed
        assert "console.log" not in result["full_text"]  # Script should be removed
        
        # Check headings extraction
        assert len(result["headings"]) == 2
        assert result["headings"][0]["level"] == 1
        assert result["headings"][0]["text"] == "Main Title"
        assert result["headings"][1]["id"] == "subtitle"
        
        # Check paragraphs
        assert len(result["paragraphs"]) == 2
        assert "First paragraph content." in result["paragraphs"]
        
        # Check statistics
        assert result["word_count"] > 0
        assert result["character_count"] > 0
    
    @pytest.mark.asyncio
    async def test_extract_links(self):
        """Test link extraction functionality."""
        html = """
        <html>
            <body>
                <a href="/internal-page">Internal Link</a>
                <a href="https://external.com">External Link</a>
                <a href="mailto:test@example.com">Email Link</a>
                <a href="tel:+1234567890">Phone Link</a>
                <a href="https://example.com/page" title="Title" target="_blank">Link with attributes</a>
            </body>
        </html>
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        result = await self.agent._extract_links(soup, "https://example.com", {})
        
        assert result["operation"] == "extract_links"
        assert result["total_count"] == 5
        
        # Check categorization
        assert len(result["internal_links"]) == 2  # /internal-page and /page
        assert len(result["external_links"]) == 1  # https://external.com
        assert len(result["email_links"]) == 1
        assert len(result["phone_links"]) == 1
        
        # Check link attributes
        email_link = result["email_links"][0]
        assert email_link["is_email"] is True
        assert "test@example.com" in email_link["url"]
        
        phone_link = result["phone_links"][0]
        assert phone_link["is_phone"] is True
        assert "+1234567890" in phone_link["url"]
    
    @pytest.mark.asyncio
    async def test_extract_images(self):
        """Test image extraction functionality."""
        html = """
        <html>
            <body>
                <img src="/image1.jpg" alt="Image 1" title="First Image" width="100" height="200">
                <img src="https://external.com/image2.png" alt="" class="responsive">
                <img src="image3.gif" loading="lazy">
            </body>
        </html>
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        result = await self.agent._extract_images(soup, "https://example.com", {})
        
        assert result["operation"] == "extract_images"
        assert result["total_count"] == 3
        assert result["with_alt_text"] == 1  # Only first image has alt text
        
        # Check first image
        img1 = result["images"][0]
        assert img1["url"] == "https://example.com/image1.jpg"  # Should be absolute
        assert img1["alt"] == "Image 1"
        assert img1["title"] == "First Image"
        assert img1["width"] == "100"
        assert img1["height"] == "200"
        
        # Check external image
        img2 = result["images"][1]
        assert img2["url"] == "https://external.com/image2.png"
        assert img2["alt"] == ""
        assert "responsive" in img2["class"]
    
    @pytest.mark.asyncio
    async def test_extract_tables(self):
        """Test table extraction functionality."""
        html = """
        <html>
            <body>
                <table>
                    <caption>Sample Table</caption>
                    <thead>
                        <tr><th>Name</th><th>Age</th><th>City</th></tr>
                    </thead>
                    <tbody>
                        <tr><td>John</td><td>25</td><td>NYC</td></tr>
                        <tr><td>Jane</td><td>30</td><td>LA</td></tr>
                    </tbody>
                </table>
                <table>
                    <tr><td>Simple</td><td>Table</td></tr>
                    <tr><td>Row 2</td><td>Data</td></tr>
                </table>
            </body>
        </html>
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        result = await self.agent._extract_tables(soup, "https://example.com", {})
        
        assert result["operation"] == "extract_tables"
        assert result["total_count"] == 2
        
        # Check first table with headers
        table1 = result["tables"][0]
        assert table1["caption"] == "Sample Table"
        assert table1["headers"] == ["Name", "Age", "City"]
        assert len(table1["rows"]) == 2
        assert table1["rows"][0] == ["John", "25", "NYC"]
        
        # Check simple table (first row becomes headers)
        table2 = result["tables"][1]
        assert table2["headers"] == ["Simple", "Table"]
        assert len(table2["rows"]) == 1
        assert table2["rows"][0] == ["Row 2", "Data"]
    
    @pytest.mark.asyncio
    async def test_extract_metadata(self):
        """Test metadata extraction functionality."""
        html = """
        <html lang="en">
            <head>
                <title>Test Page Title</title>
                <meta name="description" content="Test page description">
                <meta name="keywords" content="test, page, keywords">
                <meta name="author" content="Test Author">
                <meta name="robots" content="index, follow">
                <meta name="viewport" content="width=device-width, initial-scale=1">
                <link rel="canonical" href="https://example.com/canonical">
            </head>
            <body></body>
        </html>
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        result = await self.agent._extract_metadata(soup, "https://example.com", {})
        
        assert result["operation"] == "extract_metadata"
        metadata = result["metadata"]
        
        assert metadata["title"] == "Test Page Title"
        assert metadata["description"] == "Test page description"
        assert metadata["keywords"] == "test, page, keywords"
        assert metadata["author"] == "Test Author"
        assert metadata["robots"] == "index, follow"
        assert metadata["viewport"] == "width=device-width, initial-scale=1"
        assert metadata["language"] == "en"
        assert metadata["canonical_url"] == "https://example.com/canonical"
    
    @pytest.mark.asyncio
    async def test_extract_structured_data(self):
        """Test structured data extraction."""
        html = """
        <html>
            <head>
                <script type="application/ld+json">
                {
                    "@type": "Article",
                    "headline": "Test Article",
                    "author": "Test Author"
                }
                </script>
            </head>
            <body>
                <div itemscope itemtype="https://schema.org/Person">
                    <span itemprop="name">John Doe</span>
                    <span itemprop="email">john@example.com</span>
                </div>
            </body>
        </html>
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        result = await self.agent._extract_structured_data(soup, "https://example.com", {})
        
        assert result["operation"] == "extract_structured_data"
        structured_data = result["structured_data"]
        
        # Check JSON-LD
        assert result["json_ld_count"] == 1
        assert len(structured_data["json_ld"]) == 1
        json_ld = structured_data["json_ld"][0]
        assert json_ld["@type"] == "Article"
        assert json_ld["headline"] == "Test Article"
        
        # Check microdata
        assert result["microdata_count"] == 1
        assert len(structured_data["microdata"]) == 1
        microdata = structured_data["microdata"][0]
        assert "https://schema.org/Person" in microdata["itemtype"]
        assert microdata["properties"]["name"] == "John Doe"
        assert microdata["properties"]["email"] == "john@example.com"
    
    @pytest.mark.asyncio
    async def test_extract_social_media(self):
        """Test social media metadata extraction."""
        html = """
        <html>
            <head>
                <meta property="og:title" content="Open Graph Title">
                <meta property="og:description" content="OG Description">
                <meta property="og:image" content="https://example.com/og-image.jpg">
                <meta name="twitter:card" content="summary_large_image">
                <meta name="twitter:title" content="Twitter Title">
                <meta property="fb:app_id" content="123456789">
            </head>
            <body></body>
        </html>
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        result = await self.agent._extract_social_media(soup, "https://example.com", {})
        
        assert result["operation"] == "extract_social_media"
        social_data = result["social_data"]
        
        assert result["has_open_graph"] is True
        assert result["has_twitter_card"] is True
        
        # Check Open Graph data
        og_data = social_data["open_graph"]
        assert og_data["title"] == "Open Graph Title"
        assert og_data["description"] == "OG Description"
        assert og_data["image"] == "https://example.com/og-image.jpg"
        
        # Check Twitter Card data
        twitter_data = social_data["twitter_card"]
        assert twitter_data["card"] == "summary_large_image"
        assert twitter_data["title"] == "Twitter Title"
        
        # Check Facebook data
        fb_data = social_data["facebook"]
        assert fb_data["app_id"] == "123456789"
    
    @pytest.mark.asyncio
    async def test_extract_contact_info(self):
        """Test contact information extraction."""
        html = """
        <html>
            <body>
                <p>Contact us at test@example.com or support@company.org</p>
                <p>Call us: (555) 123-4567 or 555.987.6543</p>
                <p>International: +1-555-123-4567</p>
                <a href="https://facebook.com/company">Facebook</a>
                <a href="https://twitter.com/company">Twitter</a>
                <a href="https://linkedin.com/company/company">LinkedIn</a>
            </body>
        </html>
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        result = await self.agent._extract_contact_info(soup, "https://example.com", {})
        
        assert result["operation"] == "extract_contact_info"
        contact_info = result["contact_info"]
        
        # Check email extraction
        assert result["emails_found"] == 2
        assert "test@example.com" in contact_info["emails"]
        assert "support@company.org" in contact_info["emails"]
        
        # Check phone extraction
        assert result["phones_found"] >= 2  # Should find multiple formats
        
        # Check social links
        assert result["social_links_found"] == 3
        social_platforms = [link["platform"] for link in contact_info["social_links"]]
        assert "facebook" in social_platforms
        assert "twitter" in social_platforms
        assert "linkedin" in social_platforms
    
    @pytest.mark.asyncio
    async def test_extract_by_selectors(self):
        """Test extraction using custom CSS selectors."""
        html = """
        <html>
            <body>
                <h1>Main Title</h1>
                <div class="content">
                    <p class="intro">Introduction paragraph</p>
                    <img src="/image.jpg" alt="Test Image">
                    <a href="/link">Test Link</a>
                </div>
                <ul class="items">
                    <li>Item 1</li>
                    <li>Item 2</li>
                    <li>Item 3</li>
                </ul>
            </body>
        </html>
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        selectors = {
            "title": "h1",
            "intro": ".intro",
            "image": ".content img",
            "link": ".content a",
            "items": ".items li",
            "nonexistent": ".missing"
        }
        
        result = await self.agent._extract_by_selectors(soup, selectors, "https://example.com", {})
        
        assert result["operation"] == "extract_by_selectors"
        data = result["data"]
        
        # Check single element extractions
        assert data["title"] == "Main Title"
        assert data["intro"] == "Introduction paragraph"
        
        # Check image extraction (single element, special handling)
        assert isinstance(data["image"], dict)
        assert data["image"]["src"] == "https://example.com/image.jpg"
        assert data["image"]["alt"] == "Test Image"
        
        # Check link extraction (single element, special handling)
        assert isinstance(data["link"], dict)
        assert data["link"]["url"] == "https://example.com/link"
        assert data["link"]["text"] == "Test Link"
        
        # Check multiple elements extraction
        assert isinstance(data["items"], list)
        assert len(data["items"]) == 3
        assert data["items"][0] == "Item 1"
        
        # Check nonexistent selector
        assert data["nonexistent"] is None
        
        # Check statistics
        stats = result["extraction_stats"]
        assert stats["successful"] == 4  # title, intro, image, link, items
        assert stats["empty"] == 1  # nonexistent
        assert stats["failed"] == 0
        assert result["success_rate"] == 4/6  # 4 successful out of 6 selectors
    
    @pytest.mark.asyncio
    async def test_full_page_scrape(self):
        """Test comprehensive full page scraping."""
        html = """
        <html lang="en">
            <head>
                <title>Full Page Test</title>
                <meta name="description" content="Test description">
                <meta property="og:title" content="OG Title">
            </head>
            <body>
                <h1>Main Content</h1>
                <p>Paragraph content</p>
                <a href="/link">Internal Link</a>
                <img src="/image.jpg" alt="Test Image">
                <table>
                    <tr><th>Header</th></tr>
                    <tr><td>Data</td></tr>
                </table>
            </body>
        </html>
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        result = await self.agent._full_page_scrape(soup, "https://example.com", {})
        
        assert result["operation"] == "full_page_scrape"
        
        # Check that all extraction methods were called
        assert "text_content" in result
        assert "links" in result
        assert "images" in result
        assert "metadata" in result
        assert "tables" in result
        assert "structured_data" in result
        assert "social_media" in result
        
        # Verify some content
        assert result["text_content"]["operation"] == "extract_text"
        assert result["links"]["operation"] == "extract_links"
        assert result["images"]["operation"] == "extract_images"
        assert result["metadata"]["operation"] == "extract_metadata"
    
    @pytest.mark.asyncio
    @patch('web_scraping_agent.WebScrapingAgent._fetch_page')
    async def test_execute_job_logic_success(self, mock_fetch_page):
        """Test successful job execution."""
        # Mock page fetch
        html_content = '<html><body><h1>Test Page</h1><p>Content here</p></body></html>'
        response_metadata = {
            "status_code": 200,
            "content_type": "text/html",
            "content_length": len(html_content),
            "encoding": "utf-8"
        }
        mock_fetch_page.return_value = (html_content, response_metadata)
        
        # Create job data
        job_data = WebScrapingJobData(
            url="https://example.com",
            selectors={"title": "h1", "content": "p"},
            options={"operation": "extract_by_selectors"}
        )
        
        # Execute job
        result = await self.agent._execute_job_logic(job_data)
        
        # Verify result
        assert result.success is True
        assert "extract_by_selectors" in result.result
        assert result.metadata["job_type"] == "web_scraping"
        assert result.metadata["url"] == "https://example.com"
        assert result.metadata["operation"] == "extract_by_selectors"
        assert result.metadata["response_status"] == 200
        
        # Verify extracted data
        result_data = json.loads(result.result)
        assert result_data["operation"] == "extract_by_selectors"
        assert result_data["data"]["title"] == "Test Page"
        assert result_data["data"]["content"] == "Content here"
    
    @pytest.mark.asyncio
    @patch('web_scraping_agent.WebScrapingAgent._fetch_page')
    async def test_execute_job_logic_network_error(self, mock_fetch_page):
        """Test job execution with network error."""
        # Mock network error
        mock_fetch_page.side_effect = Exception("Network timeout")
        
        job_data = WebScrapingJobData(url="https://example.com")
        
        result = await self.agent._execute_job_logic(job_data)
        
        assert result.success is False
        assert "Web scraping failed" in result.error_message
        assert "Network timeout" in result.error_message
        assert result.metadata["job_type"] == "web_scraping"
        assert result.metadata["url"] == "https://example.com"
        assert result.metadata["error_type"] == "Exception"
    
    @pytest.mark.asyncio
    @patch('web_scraping_agent.WebScrapingAgent._fetch_page')
    async def test_execute_job_logic_with_different_operations(self, mock_fetch_page):
        """Test job execution with different operation types."""
        html_content = '''
        <html>
            <body>
                <h1>Test Title</h1>
                <a href="/link">Test Link</a>
                <img src="/image.jpg" alt="Test Image">
            </body>
        </html>
        '''
        response_metadata = {"status_code": 200, "content_type": "text/html"}
        mock_fetch_page.return_value = (html_content, response_metadata)
        
        # Test different operations
        operations = [
            "extract_text",
            "extract_links", 
            "extract_images",
            "extract_metadata",
            "full_page_scrape"
        ]
        
        for operation in operations:
            job_data = WebScrapingJobData(
                url="https://example.com",
                options={"operation": operation}
            )
            
            result = await self.agent._execute_job_logic(job_data)
            
            assert result.success is True
            assert result.metadata["operation"] == operation
            
            result_data = json.loads(result.result)
            assert result_data["operation"] == operation


class TestWebScrapingAgentIntegration:
    """Integration tests for WebScrapingAgent with BaseAgent."""
    
    def setup_method(self):
        """Set up test environment before each test."""
        self.agent = WebScrapingAgent(name="integration_test_scraper")
    
    @pytest.mark.asyncio
    @patch('web_scraping_agent.create_agent')
    @patch('web_scraping_agent.DatabaseClient')
    @patch('web_scraping_agent.WebScrapingAgent._fetch_page')
    async def test_full_job_execution_integration(self, mock_fetch_page, mock_db_client, mock_create_agent):
        """Test full job execution through BaseAgent interface."""
        # Mock dependencies
        mock_adk_agent = MagicMock()
        mock_create_agent.return_value = mock_adk_agent
        mock_db_instance = AsyncMock()
        mock_db_client.return_value = mock_db_instance
        
        # Mock page fetch
        html_content = '<html><body><h1>Integration Test</h1></body></html>'
        response_metadata = {"status_code": 200, "content_type": "text/html"}
        mock_fetch_page.return_value = (html_content, response_metadata)
        
        # Create job data
        job_data = WebScrapingJobData(
            url="https://example.com/test",
            options={"operation": "extract_text"}
        )
        
        # Execute job through BaseAgent interface
        result = await self.agent.execute_job("test-job-id", job_data, "test-user-id")
        
        # Verify result
        assert result.success is True
        assert "extract_text" in result.result
        assert result.execution_time is not None
        assert result.metadata["job_type"] == "web_scraping"
        
        # Verify agent state
        assert self.agent.execution_count == 1
        assert self.agent.last_execution_time is not None
        
        # Verify database updates
        assert mock_db_instance.update_job.call_count == 2  # running, then completed
    
    @pytest.mark.asyncio
    async def test_agent_info_includes_scraping_operations(self):
        """Test that agent info includes scraping capabilities."""
        info = await self.agent.get_agent_info()
        
        assert info["name"] == "integration_test_scraper"
        assert info["supported_job_types"] == ["web_scraping"]
        assert "web scraping agent" in info["description"]
    
    @pytest.mark.asyncio
    @patch('web_scraping_agent.create_agent')
    @patch('web_scraping_agent.DatabaseClient')
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
        assert health["agent_name"] == "integration_test_scraper"
        assert health["checks"]["adk_agent"] == "healthy"
        assert health["checks"]["database"] == "healthy"


class TestWebScrapingJobDataValidation:
    """Test job data validation for web scraping."""
    
    def test_web_scraping_job_data_valid(self):
        """Test valid WebScrapingJobData creation."""
        job_data = WebScrapingJobData(
            url="https://example.com",
            selectors={"title": "h1", "content": ".main"},
            options={"timeout": 60, "operation": "extract_by_selectors"}
        )
        
        assert job_data.job_type == JobType.web_scraping
        assert job_data.url == "https://example.com"
        assert job_data.selectors["title"] == "h1"
        assert job_data.options["timeout"] == 60
    
    def test_web_scraping_job_data_url_validation(self):
        """Test URL validation in WebScrapingJobData."""
        # Valid URLs
        valid_urls = [
            "https://example.com",
            "http://example.com",
            "https://example.com/path?query=value"
        ]
        
        for url in valid_urls:
            job_data = WebScrapingJobData(url=url)
            assert job_data.url == url
        
        # Invalid URLs
        invalid_urls = [
            "ftp://example.com",
            "example.com",
            "invalid-url"
        ]
        
        for url in invalid_urls:
            with pytest.raises(ValueError):
                WebScrapingJobData(url=url)
    
    def test_web_scraping_job_data_optional_fields(self):
        """Test optional fields in WebScrapingJobData."""
        # Minimal data
        job_data = WebScrapingJobData(url="https://example.com")
        assert job_data.selectors is None
        assert job_data.options is None
        
        # With optional fields
        job_data = WebScrapingJobData(
            url="https://example.com",
            selectors={"title": "h1"},
            options={"timeout": 30}
        )
        assert job_data.selectors is not None
        assert job_data.options is not None


if __name__ == "__main__":
    pytest.main([__file__]) 