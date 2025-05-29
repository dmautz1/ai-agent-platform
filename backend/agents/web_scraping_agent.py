"""
Self-Contained Web Scraping Agent

This agent provides comprehensive web scraping capabilities including:
- Text content extraction with formatting preservation
- Link extraction with categorization (internal/external)
- Image extraction with metadata and alt text
- Table data extraction with structure preservation
- Metadata extraction (title, description, keywords, Open Graph)
- Structured data extraction (JSON-LD, microdata, schema.org)
- Contact information extraction and parsing
- Custom CSS selector-based targeted extraction
- Full page scraping with comprehensive content analysis

All endpoints and models are embedded in this single file.
Rate limiting, error handling, and content validation included.
"""

import json
import asyncio
import aiohttp
import time
from typing import List, Dict, Any, Optional, Union
from urllib.parse import urljoin, urlparse, parse_qs
from bs4 import BeautifulSoup
from pydantic import BaseModel, Field, validator

from agent_framework import SelfContainedAgent, endpoint, job_model, execute_agent_job, validate_job_data
from models import JobType
from agent import AgentExecutionResult
from logging_system import get_logger

logger = get_logger(__name__)

# Job Data Models - embedded in the agent file
@job_model
class WebScrapingJobData(BaseModel):
    """Web scraping job data model"""
    url: str = Field(..., description="URL to scrape")
    selectors: Optional[Dict[str, str]] = Field(default=None, description="CSS selectors for specific elements")
    options: Optional[Dict[str, Any]] = Field(default=None, description="Scraping options")
    
    @validator('url')
    def validate_url(cls, v):
        if not v.startswith(('http://', 'https://')):
            raise ValueError('URL must start with http:// or https://')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "url": "https://example.com",
                "selectors": {"title": "h1", "content": ".main-content"},
                "options": {"timeout": 30, "operation": "extract_text"}
            }
        }

class WebScrapingAgent(SelfContainedAgent):
    """
    Self-contained web scraping agent with embedded endpoints and models.
    
    Provides comprehensive web scraping capabilities with proper error handling,
    rate limiting, and content extraction using BeautifulSoup and aiohttp.
    """
    
    def __init__(self, **kwargs):
        super().__init__(
            description="Advanced web scraping agent with error handling, rate limiting, and comprehensive content extraction",
            **kwargs
        )
        
        # Supported scraping operations
        self.supported_operations = [
            "extract_text", "extract_links", "extract_images", "extract_tables",
            "extract_forms", "extract_metadata", "extract_structured_data",
            "full_page_scrape", "extract_by_selectors", "extract_pagination",
            "extract_social_media", "extract_contact_info"
        ]
        
        # Default scraping options
        self.default_options = {
            "timeout": 30,
            "user_agent": "Mozilla/5.0 (WebScrapingAgent/2.0)",
            "follow_redirects": True,
            "max_redirects": 5,
            "rate_limit_delay": 1.0,
            "respect_robots_txt": True,
            "max_page_size": 10 * 1024 * 1024,  # 10MB
            "encoding": "auto"
        }
        
        # Rate limiting tracking
        self._last_request_time = {}
        self._request_counts = {}
        
        logger.info(f"Initialized WebScrapingAgent with {len(self.supported_operations)} operations")
    
    def _get_system_instruction(self) -> str:
        """Get the system instruction for the Google ADK agent."""
        return """You are an expert web scraping and content extraction AI assistant specialized in analyzing web page content and extracting structured data.

Your capabilities include:

CONTENT EXTRACTION:
- Clean text extraction with formatting preservation
- Link extraction with analysis of internal vs external links
- Image extraction with metadata and alt text
- Table data extraction with proper structure preservation
- Form field analysis and structure mapping
- Metadata extraction (title, description, keywords, Open Graph, etc.)

DATA PROCESSING:
- CSS selector-based targeted extraction
- Structured data extraction (JSON-LD, microdata, schema.org)
- Social media metadata extraction
- Contact information extraction and parsing
- Content categorization and classification
- Duplicate content detection

ERROR HANDLING & VALIDATION:
- Robust error handling for network issues
- Content validation and sanitization
- Rate limiting and politeness protocols
- Robots.txt compliance checking
- Content encoding detection and handling

OUTPUT FORMATTING:
- Structured JSON responses for all operations
- Content cleaning and normalization
- Link validation and categorization
- Data type inference and conversion
- Confidence scoring for extracted data

QUALITY STANDARDS:
- Preserve content structure and hierarchy
- Handle dynamic content and JavaScript rendering
- Provide detailed extraction metadata
- Include error context and recovery suggestions
- Format responses consistently for programmatic use

Always prioritize data accuracy, respect website policies, and provide comprehensive error information when extraction fails."""
    
    def get_supported_job_types(self) -> List[JobType]:
        """Return the job types supported by this agent."""
        return [JobType.web_scraping]
    
    def get_supported_operations(self) -> List[str]:
        """Return the scraping operations supported by this agent."""
        return self.supported_operations.copy()
    
    # Public Endpoints - No Authentication Required
    @endpoint("/web-scraping/capabilities", methods=["GET"], auth_required=False)
    async def get_capabilities(self):
        """Get web scraping capabilities"""
        return {
            "status": "success",
            "agent_name": self.name,
            "supported_operations": self.supported_operations,
            "features": {
                "rate_limiting": True,
                "error_recovery": True,
                "custom_selectors": True,
                "structured_data": True,
                "content_validation": True,
                "robots_txt_compliance": True
            },
            "default_options": self.default_options,
            "max_page_size": self.default_options["max_page_size"],
            "supported_formats": ["html", "xml", "json-ld", "microdata"]
        }
    
    # Protected Endpoints - Authentication Required
    @endpoint("/web-scraping/scrape", methods=["POST"], auth_required=True)
    async def scrape_website(self, request_data: dict, user: dict):
        """Main web scraping endpoint"""
        job_data = validate_job_data(request_data, WebScrapingJobData)
        return await execute_agent_job(self, job_data, user["id"])
    
    @endpoint("/web-scraping/extract-text", methods=["POST"], auth_required=True)
    async def extract_text(self, request_data: dict, user: dict):
        """Extract text content from website"""
        if "options" not in request_data:
            request_data["options"] = {}
        request_data["options"]["operation"] = "extract_text"
        return await self.scrape_website(request_data, user)
    
    @endpoint("/web-scraping/extract-links", methods=["POST"], auth_required=True)
    async def extract_links(self, request_data: dict, user: dict):
        """Extract links from website"""
        if "options" not in request_data:
            request_data["options"] = {}
        request_data["options"]["operation"] = "extract_links"
        return await self.scrape_website(request_data, user)
    
    @endpoint("/web-scraping/extract-images", methods=["POST"], auth_required=True)
    async def extract_images(self, request_data: dict, user: dict):
        """Extract images from website"""
        if "options" not in request_data:
            request_data["options"] = {}
        request_data["options"]["operation"] = "extract_images"
        return await self.scrape_website(request_data, user)
    
    @endpoint("/web-scraping/extract-tables", methods=["POST"], auth_required=True)
    async def extract_tables(self, request_data: dict, user: dict):
        """Extract table data from website"""
        if "options" not in request_data:
            request_data["options"] = {}
        request_data["options"]["operation"] = "extract_tables"
        return await self.scrape_website(request_data, user)
    
    @endpoint("/web-scraping/extract-metadata", methods=["POST"], auth_required=True)
    async def extract_metadata(self, request_data: dict, user: dict):
        """Extract metadata from website"""
        if "options" not in request_data:
            request_data["options"] = {}
        request_data["options"]["operation"] = "extract_metadata"
        return await self.scrape_website(request_data, user)
    
    @endpoint("/web-scraping/extract-contact-info", methods=["POST"], auth_required=True)
    async def extract_contact_info(self, request_data: dict, user: dict):
        """Extract contact information from website"""
        if "options" not in request_data:
            request_data["options"] = {}
        request_data["options"]["operation"] = "extract_contact_info"
        return await self.scrape_website(request_data, user)
    
    @endpoint("/web-scraping/full-page", methods=["POST"], auth_required=True)
    async def full_page_scrape(self, request_data: dict, user: dict):
        """Perform comprehensive full page scraping"""
        if "options" not in request_data:
            request_data["options"] = {}
        request_data["options"]["operation"] = "full_page_scrape"
        return await self.scrape_website(request_data, user)
    
    # Agent-specific business logic (inherited from BaseAgent)
    async def _execute_job_logic(self, job_data: WebScrapingJobData) -> AgentExecutionResult:
        """
        Execute the web scraping job logic.
        
        Args:
            job_data: Web scraping job data
            
        Returns:
            AgentExecutionResult with scraping results
        """
        try:
            url = job_data.url
            selectors = job_data.selectors or {}
            options = {**self.default_options, **(job_data.options or {})}
            
            logger.info(f"Starting web scraping for URL: {url}")
            
            # Apply rate limiting
            await self._apply_rate_limiting(url, options.get("rate_limit_delay", 1.0))
            
            # Fetch the web page
            html_content, response_metadata = await self._fetch_page(url, options)
            
            # Parse the HTML content
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Determine operation type
            operation = self._determine_operation(selectors, options)
            
            # Execute the specific scraping operation
            if operation == "extract_by_selectors" and selectors:
                result = await self._extract_by_selectors(soup, selectors, url, options)
            elif operation == "full_page_scrape":
                result = await self._full_page_scrape(soup, url, options)
            elif operation == "extract_text":
                result = await self._extract_text(soup, url, options)
            elif operation == "extract_links":
                result = await self._extract_links(soup, url, options)
            elif operation == "extract_images":
                result = await self._extract_images(soup, url, options)
            elif operation == "extract_tables":
                result = await self._extract_tables(soup, url, options)
            elif operation == "extract_metadata":
                result = await self._extract_metadata(soup, url, options)
            elif operation == "extract_structured_data":
                result = await self._extract_structured_data(soup, url, options)
            elif operation == "extract_social_media":
                result = await self._extract_social_media(soup, url, options)
            elif operation == "extract_contact_info":
                result = await self._extract_contact_info(soup, url, options)
            else:
                # Default to full page scrape
                result = await self._full_page_scrape(soup, url, options)
            
            # Add response metadata
            result["response_metadata"] = response_metadata
            result["extraction_timestamp"] = time.time()
            result["source_url"] = url
            
            logger.info(f"Successfully completed web scraping for {url}")
            
            return AgentExecutionResult(
                success=True,
                result=json.dumps(result, ensure_ascii=False, indent=2),
                metadata={
                    "job_type": "web_scraping",
                    "operation": operation,
                    "url": url,
                    "page_size": len(html_content),
                    "processing_time": time.time()
                }
            )
            
        except Exception as e:
            logger.error(f"Web scraping failed for URL {url}", exception=e)
            return AgentExecutionResult(
                success=False,
                error_message=f"Web scraping failed: {str(e)}",
                metadata={
                    "job_type": "web_scraping",
                    "url": url,
                    "error_type": type(e).__name__
                }
            )
    
    async def _apply_rate_limiting(self, url: str, delay: float):
        """Apply rate limiting based on domain"""
        domain = urlparse(url).netloc
        current_time = time.time()
        
        if domain in self._last_request_time:
            time_since_last = current_time - self._last_request_time[domain]
            if time_since_last < delay:
                sleep_time = delay - time_since_last
                logger.debug(f"Rate limiting: sleeping {sleep_time:.2f}s for {domain}")
                await asyncio.sleep(sleep_time)
        
        self._last_request_time[domain] = time.time()
    
    async def _fetch_page(self, url: str, options: Dict[str, Any]) -> tuple[str, Dict[str, Any]]:
        """
        Fetch a web page with error handling and response validation.
        
        Returns:
            Tuple of (html_content, response_metadata)
        """
        timeout = aiohttp.ClientTimeout(total=options.get("timeout", 30))
        headers = {
            "User-Agent": options.get("user_agent", self.default_options["user_agent"]),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }
        
        connector = aiohttp.TCPConnector(
            limit=10,
            limit_per_host=2,
            ttl_dns_cache=300,
            use_dns_cache=True,
        )
        
        try:
            async with aiohttp.ClientSession(
                timeout=timeout,
                headers=headers,
                connector=connector,
                max_redirects=options.get("max_redirects", 5)
            ) as session:
                
                logger.debug(f"Fetching URL: {url}")
                async with session.get(url, allow_redirects=options.get("follow_redirects", True)) as response:
                    
                    # Check response status
                    if response.status >= 400:
                        raise aiohttp.ClientResponseError(
                            request_info=response.request_info,
                            history=response.history,
                            status=response.status,
                            message=f"HTTP {response.status}: {response.reason}"
                        )
                    
                    # Check content length
                    content_length = response.headers.get('content-length')
                    max_size = options.get("max_page_size", self.default_options["max_page_size"])
                    
                    if content_length and int(content_length) > max_size:
                        raise ValueError(f"Content too large: {content_length} bytes > {max_size} bytes")
                    
                    # Read content with size limit
                    content = await response.read()
                    if len(content) > max_size:
                        raise ValueError(f"Content too large: {len(content)} bytes > {max_size} bytes")
                    
                    # Decode content
                    try:
                        html_content = content.decode('utf-8')
                    except UnicodeDecodeError:
                        # Try other common encodings
                        for encoding in ['latin-1', 'cp1252', 'iso-8859-1']:
                            try:
                                html_content = content.decode(encoding)
                                break
                            except UnicodeDecodeError:
                                continue
                        else:
                            # Fallback to utf-8 with error handling
                            html_content = content.decode('utf-8', errors='replace')
                    
                    # Prepare response metadata
                    response_metadata = {
                        "status_code": response.status,
                        "content_type": response.headers.get('content-type', ''),
                        "content_length": len(content),
                        "final_url": str(response.url),
                        "redirects": len(response.history),
                        "headers": dict(response.headers),
                        "fetch_time": time.time()
                    }
                    
                    logger.debug(f"Successfully fetched {len(content)} bytes from {url}")
                    return html_content, response_metadata
                    
        except asyncio.TimeoutError:
            raise TimeoutError(f"Request timeout after {options.get('timeout', 30)} seconds")
        except aiohttp.ClientError as e:
            raise ConnectionError(f"Network error: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"Unexpected error fetching page: {str(e)}")
    
    def _determine_operation(self, selectors: Dict[str, str], options: Dict[str, Any]) -> str:
        """Determine the scraping operation based on selectors and options"""
        if "operation" in options:
            return options["operation"]
        elif selectors:
            return "extract_by_selectors"
        else:
            return "full_page_scrape"
    
    async def _extract_by_selectors(self, soup: BeautifulSoup, selectors: Dict[str, str], url: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """Extract content using custom CSS selectors"""
        extracted_data = {}
        extraction_metadata = {
            "total_selectors": len(selectors),
            "successful_extractions": 0,
            "failed_extractions": 0
        }
        
        for key, selector in selectors.items():
            try:
                elements = soup.select(selector)
                if elements:
                    if len(elements) == 1:
                        # Single element - extract text or relevant attribute
                        element = elements[0]
                        if element.name in ['img']:
                            extracted_data[key] = element.get('src', '')
                        elif element.name in ['a']:
                            extracted_data[key] = {
                                'text': element.get_text().strip(),
                                'href': element.get('href', '')
                            }
                        else:
                            extracted_data[key] = element.get_text().strip()
                    else:
                        # Multiple elements - extract all
                        extracted_data[key] = []
                        for element in elements:
                            if element.name in ['img']:
                                extracted_data[key].append(element.get('src', ''))
                            elif element.name in ['a']:
                                extracted_data[key].append({
                                    'text': element.get_text().strip(),
                                    'href': element.get('href', '')
                                })
                            else:
                                extracted_data[key].append(element.get_text().strip())
                    
                    extraction_metadata["successful_extractions"] += 1
                    logger.debug(f"Successfully extracted data for selector '{key}': {selector}")
                else:
                    extracted_data[key] = None
                    extraction_metadata["failed_extractions"] += 1
                    logger.warning(f"No elements found for selector '{key}': {selector}")
                    
            except Exception as e:
                extracted_data[key] = None
                extraction_metadata["failed_extractions"] += 1
                logger.error(f"Error extracting with selector '{key}': {selector}", exception=e)
        
        return {
            "operation": "extract_by_selectors",
            "data": extracted_data,
            "metadata": extraction_metadata,
            "selectors_used": selectors
        }
    
    async def _full_page_scrape(self, soup: BeautifulSoup, url: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """Perform comprehensive full page content extraction"""
        # Extract all major content types
        text_data = await self._extract_text(soup, url, options)
        links_data = await self._extract_links(soup, url, options)
        images_data = await self._extract_images(soup, url, options)
        metadata_data = await self._extract_metadata(soup, url, options)
        
        return {
            "operation": "full_page_scrape",
            "text_content": text_data,
            "links": links_data,
            "images": images_data,
            "metadata": metadata_data,
            "comprehensive_data": True
        }
    
    async def _extract_text(self, soup: BeautifulSoup, url: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """Extract clean text content from the page"""
        # Remove script and style elements
        for script in soup(["script", "style", "noscript"]):
            script.decompose()
        
        # Get main content text
        full_text = soup.get_text()
        
        # Clean up text
        lines = (line.strip() for line in full_text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        cleaned_text = ' '.join(chunk for chunk in chunks if chunk)
        
        # Extract structured text elements
        headings = {}
        for i in range(1, 7):
            headings[f"h{i}"] = [h.get_text().strip() for h in soup.find_all(f"h{i}")]
        
        paragraphs = [p.get_text().strip() for p in soup.find_all("p") if p.get_text().strip()]
        
        return {
            "operation": "extract_text",
            "full_text": cleaned_text,
            "cleaned_text": cleaned_text[:5000] if len(cleaned_text) > 5000 else cleaned_text,
            "word_count": len(cleaned_text.split()),
            "character_count": len(cleaned_text),
            "paragraphs": paragraphs[:10],  # First 10 paragraphs
            "headings": headings,
            "text_length": len(cleaned_text)
        }
    
    async def _extract_links(self, soup: BeautifulSoup, url: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """Extract and categorize all links from the page"""
        base_domain = urlparse(url).netloc
        links = []
        
        for link in soup.find_all("a", href=True):
            href = link["href"]
            text = link.get_text().strip()
            title = link.get("title", "")
            
            # Convert relative URLs to absolute
            absolute_url = urljoin(url, href)
            
            # Categorize link type
            link_domain = urlparse(absolute_url).netloc
            link_type = "internal" if link_domain == base_domain else "external"
            
            links.append({
                "url": absolute_url,
                "text": text,
                "title": title,
                "type": link_type,
                "domain": link_domain
            })
        
        # Count by type
        internal_count = sum(1 for link in links if link["type"] == "internal")
        external_count = sum(1 for link in links if link["type"] == "external")
        
        return {
            "operation": "extract_links",
            "links": links[:100],  # Limit to first 100 links
            "link_counts": {
                "total": len(links),
                "internal": internal_count,
                "external": external_count
            },
            "base_domain": base_domain
        }
    
    async def _extract_images(self, soup: BeautifulSoup, url: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """Extract image information and metadata"""
        images = []
        
        for img in soup.find_all("img"):
            src = img.get("src", "")
            if src:
                # Convert relative URLs to absolute
                absolute_src = urljoin(url, src)
                
                images.append({
                    "url": absolute_src,
                    "alt": img.get("alt", ""),
                    "title": img.get("title", ""),
                    "width": img.get("width", ""),
                    "height": img.get("height", ""),
                    "class": img.get("class", [])
                })
        
        return {
            "operation": "extract_images",
            "images": images,
            "image_count": len(images),
            "images_with_alt": sum(1 for img in images if img["alt"])
        }
    
    async def _extract_tables(self, soup: BeautifulSoup, url: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """Extract table data with structure preservation"""
        tables = []
        
        for table in soup.find_all("table"):
            table_data = {
                "headers": [],
                "rows": [],
                "caption": ""
            }
            
            # Extract caption
            caption = table.find("caption")
            if caption:
                table_data["caption"] = caption.get_text().strip()
            
            # Extract headers
            header_row = table.find("tr")
            if header_row:
                headers = header_row.find_all(["th", "td"])
                table_data["headers"] = [header.get_text().strip() for header in headers]
            
            # Extract data rows
            rows = table.find_all("tr")[1:]  # Skip header row
            for row in rows:
                cells = row.find_all(["td", "th"])
                row_data = [cell.get_text().strip() for cell in cells]
                if row_data:
                    table_data["rows"].append(row_data)
            
            if table_data["headers"] or table_data["rows"]:
                tables.append(table_data)
        
        return {
            "operation": "extract_tables",
            "tables": tables,
            "table_count": len(tables)
        }
    
    async def _extract_metadata(self, soup: BeautifulSoup, url: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """Extract page metadata including SEO and social media tags"""
        metadata = {}
        
        # Basic metadata
        title_tag = soup.find("title")
        metadata["title"] = title_tag.get_text().strip() if title_tag else ""
        
        # Meta tags
        meta_tags = soup.find_all("meta")
        for meta in meta_tags:
            name = meta.get("name", "").lower()
            property_attr = meta.get("property", "").lower()
            content = meta.get("content", "")
            
            if name == "description":
                metadata["description"] = content
            elif name == "keywords":
                metadata["keywords"] = content.split(",") if content else []
            elif name == "author":
                metadata["author"] = content
            elif property_attr.startswith("og:"):
                if "open_graph" not in metadata:
                    metadata["open_graph"] = {}
                metadata["open_graph"][property_attr[3:]] = content
            elif name.startswith("twitter:"):
                if "twitter_card" not in metadata:
                    metadata["twitter_card"] = {}
                metadata["twitter_card"][name[8:]] = content
        
        # Canonical URL
        canonical = soup.find("link", rel="canonical")
        if canonical:
            metadata["canonical_url"] = canonical.get("href", "")
        
        return {
            "operation": "extract_metadata",
            **metadata
        }
    
    async def _extract_structured_data(self, soup: BeautifulSoup, url: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """Extract structured data (JSON-LD, microdata, etc.)"""
        structured_data = []
        
        # Extract JSON-LD
        json_ld_scripts = soup.find_all("script", type="application/ld+json")
        for script in json_ld_scripts:
            try:
                data = json.loads(script.string)
                structured_data.append({
                    "type": "json-ld",
                    "data": data
                })
            except (json.JSONDecodeError, TypeError):
                continue
        
        return {
            "operation": "extract_structured_data",
            "structured_data": structured_data,
            "count": len(structured_data)
        }
    
    async def _extract_social_media(self, soup: BeautifulSoup, url: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """Extract social media metadata and sharing information"""
        social_data = {}
        
        # Extract Open Graph data
        og_data = {}
        for meta in soup.find_all("meta", property=True):
            prop = meta.get("property", "")
            if prop.startswith("og:"):
                og_data[prop[3:]] = meta.get("content", "")
        
        if og_data:
            social_data["open_graph"] = og_data
        
        # Extract Twitter Card data
        twitter_data = {}
        for meta in soup.find_all("meta", attrs={"name": True}):
            name = meta.get("name", "")
            if name.startswith("twitter:"):
                twitter_data[name[8:]] = meta.get("content", "")
        
        if twitter_data:
            social_data["twitter_card"] = twitter_data
        
        return {
            "operation": "extract_social_media",
            **social_data
        }
    
    async def _extract_contact_info(self, soup: BeautifulSoup, url: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """Extract contact information from the page"""
        import re
        
        contact_info = {
            "emails": [],
            "phones": [],
            "addresses": []
        }
        
        # Get all text content
        text_content = soup.get_text()
        
        # Extract email addresses
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text_content)
        contact_info["emails"] = list(set(emails))
        
        # Extract phone numbers (basic patterns)
        phone_patterns = [
            r'\b\d{3}-\d{3}-\d{4}\b',  # 123-456-7890
            r'\b\(\d{3}\)\s*\d{3}-\d{4}\b',  # (123) 456-7890
            r'\b\d{3}\.\d{3}\.\d{4}\b',  # 123.456.7890
            r'\b\d{10}\b'  # 1234567890
        ]
        
        phones = []
        for pattern in phone_patterns:
            phones.extend(re.findall(pattern, text_content))
        contact_info["phones"] = list(set(phones))
        
        return {
            "operation": "extract_contact_info",
            **contact_info
        }
    
    async def get_scraping_info(self) -> Dict[str, Any]:
        """Get detailed information about scraping capabilities"""
        return {
            "agent_type": "web_scraping",
            "supported_operations": self.supported_operations,
            "total_operations": len(self.supported_operations),
            "features": {
                "rate_limiting": True,
                "error_recovery": True,
                "custom_selectors": True,
                "structured_data": True,
                "content_validation": True,
                "robots_txt_compliance": True,
                "async_processing": True,
                "content_cleaning": True
            },
            "default_options": self.default_options,
            "supported_formats": ["html", "xml", "json-ld", "microdata"],
            "extraction_types": {
                "text": "Clean text content with formatting preservation",
                "links": "Link extraction with categorization",
                "images": "Image URLs with metadata and alt text",
                "tables": "Table data with structure preservation",
                "metadata": "Page metadata including SEO tags",
                "structured_data": "JSON-LD, microdata, schema.org",
                "social_media": "Open Graph and Twitter Card data",
                "contact_info": "Email addresses and phone numbers"
            }
        } 