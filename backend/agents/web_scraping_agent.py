"""
Web Scraping Agent

A comprehensive agent that scrapes websites, analyzes content using AI,
and provides structured JSON output with insights and summaries.
"""

import json
import re
import time
from typing import Dict, List, Optional, Any
from urllib.parse import urljoin, urlparse
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup, Tag
from pydantic import BaseModel, Field, field_validator

from agent_framework import SelfContainedAgent, endpoint, job_model, validate_job_data
from agent import AgentExecutionResult
from services.google_ai_service import get_google_ai_service
from logging_system import get_logger

logger = get_logger(__name__)

@job_model
class WebScrapingJobData(BaseModel):
    """Web scraping job data model"""
    url: str = Field(..., description="URL of the website to scrape")
    max_depth: int = Field(default=1, description="Maximum depth for following links (1 = single page)")
    include_links: bool = Field(default=True, description="Whether to extract and include links")
    include_images: bool = Field(default=True, description="Whether to extract image information")
    analyze_content: bool = Field(default=True, description="Whether to perform AI analysis of content")
    summary_length: str = Field(default="medium", description="Length of AI summary (short, medium, long)")
    extract_keywords: bool = Field(default=True, description="Whether to extract key topics/keywords")
    custom_selectors: Optional[Dict[str, str]] = Field(default=None, description="Custom CSS selectors for specific content")
    
    @field_validator('url')
    @classmethod
    def validate_url(cls, v):
        if not v.startswith(('http://', 'https://')):
            raise ValueError('URL must start with http:// or https://')
        return v
    
    @field_validator('max_depth')
    @classmethod
    def validate_depth(cls, v):
        if v < 1 or v > 3:
            raise ValueError('max_depth must be between 1 and 3')
        return v
    
    @field_validator('summary_length')
    @classmethod
    def validate_summary_length(cls, v):
        if v not in ['short', 'medium', 'long']:
            raise ValueError('summary_length must be short, medium, or long')
        return v

class WebScrapingAgent(SelfContainedAgent):
    """Agent that scrapes websites and provides AI-powered analysis"""
    
    def __init__(self, **kwargs):
        super().__init__(
            name="web_scraping",
            description="Scrapes websites, analyzes content with AI, and provides structured JSON output",
            result_format="json",
            **kwargs
        )
        self.google_ai = get_google_ai_service()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; WebScrapingAgent/1.0)'
        })
    
    def _get_system_instruction(self) -> str:
        """Return the system instruction for the agent"""
        return """You are a web content analysis specialist. Your job is to analyze scraped web content and provide:
1. Clear, concise summaries
2. Key insights and important information
3. Extracted keywords and topics
4. Content categorization
5. Actionable takeaways when relevant

Focus on extracting meaningful information and presenting it in a structured, useful format."""

    async def _execute_job_logic(self, job_data: WebScrapingJobData) -> AgentExecutionResult:
        """Execute the web scraping and analysis job"""
        try:
            logger.info(f"Starting web scraping for URL: {job_data.url}")
            logger.debug(f"Job parameters: analyze_content={job_data.analyze_content}, summary_length={job_data.summary_length}, extract_keywords={job_data.extract_keywords}")
            
            # Scrape the website
            scraped_data = await self._scrape_website(job_data)
            logger.info(f"Web scraping completed. Content length: {len(scraped_data.get('content', ''))}")
            
            # Analyze content if requested
            if job_data.analyze_content:
                if scraped_data.get('content'):
                    logger.info("Starting AI content analysis")
                    try:
                        analysis = await self._analyze_content(
                            scraped_data['content'], 
                            job_data.summary_length,
                            job_data.extract_keywords
                        )
                        scraped_data['ai_analysis'] = analysis
                        logger.info("AI content analysis completed successfully")
                        if 'error' in analysis:
                            logger.warning(f"AI analysis returned error: {analysis['error']}")
                    except Exception as analysis_error:
                        logger.error(f"AI content analysis failed with exception: {analysis_error}")
                        scraped_data['ai_analysis'] = {
                            'error': f"Analysis failed with exception: {str(analysis_error)}",
                            'summary': 'Analysis unavailable due to error',
                            'insights': [],
                            'content_type': 'unknown',
                            'tone': 'unknown',
                            'target_audience': 'unknown',
                            'keywords': []
                        }
                else:
                    logger.warning("AI analysis requested but no content was extracted from the website")
                    scraped_data['ai_analysis'] = {
                        'error': 'No content available for analysis',
                        'summary': 'No content extracted',
                        'insights': [],
                        'content_type': 'unknown',
                        'tone': 'unknown',
                        'target_audience': 'unknown',
                        'keywords': []
                    }
            else:
                logger.info("AI analysis disabled - skipping content analysis")
            
            # Structure the final JSON output
            result = self._structure_output(scraped_data, job_data)
            
            logger.info(f"Web scraping completed successfully for: {job_data.url}")
            logger.debug(f"Final result includes AI analysis: {'ai_analysis' in result}")
            
            return AgentExecutionResult(
                success=True,
                result=result,
                metadata={
                    "agent": self.name,
                    "url": job_data.url,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "content_length": len(scraped_data.get('content', '')),
                    "links_found": len(scraped_data.get('links', [])),
                    "images_found": len(scraped_data.get('images', [])),
                    "ai_analysis_requested": job_data.analyze_content,
                    "ai_analysis_included": 'ai_analysis' in scraped_data
                },
                result_format=self.result_format
            )
            
        except Exception as e:
            logger.error(f"Web scraping failed for {job_data.url}: {e}")
            return AgentExecutionResult(
                success=False,
                error_message=f"Web scraping failed: {str(e)}",
                metadata={"agent": self.name, "url": job_data.url}
            )

    async def _scrape_website(self, job_data: WebScrapingJobData) -> Dict[str, Any]:
        """Scrape the website and extract content"""
        try:
            # Fetch the main page
            response = self.session.get(job_data.url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract basic metadata
            scraped_data = {
                'url': job_data.url,
                'title': self._extract_title(soup),
                'description': self._extract_description(soup),
                'content': self._extract_content(soup, job_data.custom_selectors),
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'status_code': response.status_code
            }
            
            # Extract links if requested
            if job_data.include_links:
                scraped_data['links'] = self._extract_links(soup, job_data.url)
            
            # Extract images if requested
            if job_data.include_images:
                scraped_data['images'] = self._extract_images(soup, job_data.url)
            
            # Extract custom elements if selectors provided
            if job_data.custom_selectors:
                scraped_data['custom_data'] = self._extract_custom_data(soup, job_data.custom_selectors)
            
            return scraped_data
            
        except requests.RequestException as e:
            raise Exception(f"Failed to fetch URL: {str(e)}")
        except Exception as e:
            raise Exception(f"Failed to parse content: {str(e)}")

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract page title"""
        title = soup.find('title')
        if title:
            return title.get_text().strip()
        
        # Fallback to h1
        h1 = soup.find('h1')
        if h1:
            return h1.get_text().strip()
        
        return "No title found"

    def _extract_description(self, soup: BeautifulSoup) -> str:
        """Extract page description from meta tags"""
        # Try meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            return meta_desc['content'].strip()
        
        # Try Open Graph description
        og_desc = soup.find('meta', attrs={'property': 'og:description'})
        if og_desc and og_desc.get('content'):
            return og_desc['content'].strip()
        
        # Fallback to first paragraph
        first_p = soup.find('p')
        if first_p:
            text = first_p.get_text().strip()
            return text[:200] + "..." if len(text) > 200 else text
        
        return "No description found"

    def _extract_content(self, soup: BeautifulSoup, custom_selectors: Optional[Dict[str, str]]) -> str:
        """Extract main text content from the page"""
        # Remove script and style elements
        for element in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
            element.decompose()
        
        # Try to find main content area
        main_content = None
        
        # Look for common main content selectors
        content_selectors = [
            'main', 'article', '.content', '#content', '.main', '#main',
            '.post-content', '.entry-content', '.article-content'
        ]
        
        for selector in content_selectors:
            main_content = soup.select_one(selector)
            if main_content:
                break
        
        # If no main content found, use body
        if not main_content:
            main_content = soup.find('body')
        
        if not main_content:
            return "No content found"
        
        # Extract text and clean it
        text = main_content.get_text(separator=' ', strip=True)
        
        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text

    def _extract_links(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, str]]:
        """Extract all links from the page"""
        links = []
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            text = link.get_text().strip()
            
            # Convert relative URLs to absolute
            absolute_url = urljoin(base_url, href)
            
            # Skip empty links and anchors
            if not href or href.startswith('#'):
                continue
            
            links.append({
                'url': absolute_url,
                'text': text,
                'type': self._classify_link(absolute_url)
            })
        
        return links

    def _extract_images(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, str]]:
        """Extract image information from the page"""
        images = []
        
        for img in soup.find_all('img'):
            src = img.get('src')
            if not src:
                continue
            
            # Convert relative URLs to absolute
            absolute_url = urljoin(base_url, src)
            
            images.append({
                'url': absolute_url,
                'alt': img.get('alt', ''),
                'title': img.get('title', ''),
                'width': img.get('width', ''),
                'height': img.get('height', '')
            })
        
        return images

    def _extract_custom_data(self, soup: BeautifulSoup, selectors: Dict[str, str]) -> Dict[str, Any]:
        """Extract data using custom CSS selectors"""
        custom_data = {}
        
        for name, selector in selectors.items():
            try:
                elements = soup.select(selector)
                if elements:
                    if len(elements) == 1:
                        custom_data[name] = elements[0].get_text().strip()
                    else:
                        custom_data[name] = [elem.get_text().strip() for elem in elements]
                else:
                    custom_data[name] = None
            except Exception as e:
                logger.warning(f"Failed to extract custom data for '{name}' with selector '{selector}': {e}")
                custom_data[name] = None
        
        return custom_data

    def _classify_link(self, url: str) -> str:
        """Classify link type based on URL"""
        parsed = urlparse(url)
        
        if parsed.scheme in ['mailto']:
            return 'email'
        elif parsed.scheme in ['tel']:
            return 'phone'
        elif any(ext in url.lower() for ext in ['.pdf', '.doc', '.docx', '.xls', '.xlsx']):
            return 'document'
        elif any(ext in url.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif', '.svg']):
            return 'image'
        else:
            return 'webpage'

    async def _analyze_content(self, content: str, summary_length: str, extract_keywords: bool) -> Dict[str, Any]:
        """Analyze content using AI"""
        try:
            logger.info(f"Starting AI content analysis. Content length: {len(content)} characters")
            
            # Check Google AI service availability
            if not self.google_ai:
                logger.error("Google AI service not initialized")
                return {
                    'error': "Google AI service not available",
                    'summary': 'Analysis unavailable - service not initialized',
                    'insights': [],
                    'content_type': 'unknown',
                    'tone': 'unknown',
                    'target_audience': 'unknown',
                    'keywords': []
                }
            
            # Test Google AI service connection
            try:
                service_info = self.google_ai.get_info()
                logger.debug(f"Google AI service info: {service_info}")
            except Exception as service_error:
                logger.error(f"Failed to get Google AI service info: {service_error}")
            
            # Prepare the analysis prompt
            length_instructions = {
                'short': 'Provide a brief 2-3 sentence summary',
                'medium': 'Provide a comprehensive paragraph summary',
                'long': 'Provide a detailed multi-paragraph analysis'
            }
            
            prompt = f"""
            Analyze the following web content and provide:
            
            1. SUMMARY: {length_instructions[summary_length]}
            2. KEY_INSIGHTS: List 3-5 main insights or important points
            3. CONTENT_TYPE: Classify the content (e.g., article, product page, blog post, news, documentation)
            4. TONE: Describe the tone (e.g., formal, casual, promotional, informational)
            5. TARGET_AUDIENCE: Who appears to be the target audience
            """
            
            if extract_keywords:
                prompt += "\n6. KEYWORDS: Extract 5-10 important keywords/topics"
            
            # Truncate content if too long to avoid token limits
            max_content_length = 4000
            truncated_content = content[:max_content_length]
            if len(content) > max_content_length:
                logger.warning(f"Content truncated from {len(content)} to {max_content_length} characters for AI analysis")
            
            prompt += f"\n\nContent to analyze:\n\n{truncated_content}"
            
            logger.debug(f"Sending prompt to Google AI. Prompt length: {len(prompt)} characters")
            
            # Make the AI service call
            response = await self.google_ai.query(
                prompt=prompt,
                temperature=0.3
            )
            
            logger.info(f"Received response from Google AI. Response length: {len(response)} characters")
            logger.debug(f"AI response preview: {response[:200]}...")
            
            # Parse the AI response into structured data
            analysis = self._parse_ai_response(response)
            
            logger.info("AI response parsed successfully")
            return analysis
            
        except Exception as e:
            logger.error(f"Content analysis failed: {e}", exc_info=True)
            return {
                'error': f"Analysis failed: {str(e)}",
                'summary': 'Analysis unavailable',
                'insights': [],
                'content_type': 'unknown',
                'tone': 'unknown',
                'target_audience': 'unknown',
                'keywords': []
            }

    def _parse_ai_response(self, response: str) -> Dict[str, Any]:
        """Parse AI response into structured data"""
        analysis = {
            'summary': '',
            'insights': [],
            'content_type': 'unknown',
            'tone': 'unknown',
            'target_audience': 'unknown',
            'keywords': []
        }
        
        try:
            # Simple parsing - look for sections
            lines = response.split('\n')
            current_section = None
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Check for section headers
                if 'SUMMARY:' in line.upper():
                    current_section = 'summary'
                    analysis['summary'] = line.split(':', 1)[1].strip() if ':' in line else ''
                elif 'KEY_INSIGHTS:' in line.upper():
                    current_section = 'insights'
                elif 'CONTENT_TYPE:' in line.upper():
                    current_section = 'content_type'
                    analysis['content_type'] = line.split(':', 1)[1].strip() if ':' in line else 'unknown'
                elif 'TONE:' in line.upper():
                    current_section = 'tone'
                    analysis['tone'] = line.split(':', 1)[1].strip() if ':' in line else 'unknown'
                elif 'TARGET_AUDIENCE:' in line.upper():
                    current_section = 'target_audience'
                    analysis['target_audience'] = line.split(':', 1)[1].strip() if ':' in line else 'unknown'
                elif 'KEYWORDS:' in line.upper():
                    current_section = 'keywords'
                    keywords_text = line.split(':', 1)[1].strip() if ':' in line else ''
                    if keywords_text:
                        analysis['keywords'] = [k.strip() for k in keywords_text.split(',')]
                else:
                    # Continue previous section
                    if current_section == 'summary' and not analysis['summary']:
                        analysis['summary'] = line
                    elif current_section == 'insights' and line.startswith(('-', '•', '*', '1.', '2.', '3.', '4.', '5.')):
                        insight = re.sub(r'^[-•*\d.]\s*', '', line).strip()
                        if insight:
                            analysis['insights'].append(insight)
                    elif current_section == 'keywords' and not analysis['keywords']:
                        analysis['keywords'] = [k.strip() for k in line.split(',')]
            
        except Exception as e:
            logger.warning(f"Failed to parse AI response: {e}")
        
        return analysis

    def _structure_output(self, scraped_data: Dict[str, Any], job_data: WebScrapingJobData) -> Dict[str, Any]:
        """Structure the final JSON output"""
        logger.debug("Structuring final output")
        
        output = {
            'scraping_metadata': {
                'url': scraped_data['url'],
                'timestamp': scraped_data['timestamp'],
                'agent': self.name,
                'job_config': {
                    'max_depth': job_data.max_depth,
                    'include_links': job_data.include_links,
                    'include_images': job_data.include_images,
                    'analyze_content': job_data.analyze_content,
                    'summary_length': job_data.summary_length,
                    'extract_keywords': job_data.extract_keywords
                }
            },
            'page_info': {
                'title': scraped_data['title'],
                'description': scraped_data['description'],
                'url': scraped_data['url'],
                'status_code': scraped_data['status_code']
            },
            'content': {
                'text': scraped_data['content'],
                'word_count': len(scraped_data['content'].split()) if scraped_data['content'] else 0,
                'character_count': len(scraped_data['content']) if scraped_data['content'] else 0
            }
        }
        
        # Add AI analysis if available
        if 'ai_analysis' in scraped_data:
            output['ai_analysis'] = scraped_data['ai_analysis']
            logger.info("AI analysis included in final output")
            
            # Log analysis summary for debugging
            analysis = scraped_data['ai_analysis']
            if 'error' in analysis:
                logger.warning(f"AI analysis contains error: {analysis['error']}")
            else:
                logger.debug(f"AI analysis summary: {analysis.get('summary', 'No summary')[:100]}...")
        else:
            logger.warning("AI analysis not available - not included in final output")
        
        # Add links if requested
        if job_data.include_links and 'links' in scraped_data:
            output['links'] = {
                'total_count': len(scraped_data['links']),
                'by_type': self._categorize_links(scraped_data['links']),
                'all_links': scraped_data['links']
            }
            logger.debug(f"Included {len(scraped_data['links'])} links in output")
        
        # Add images if requested
        if job_data.include_images and 'images' in scraped_data:
            output['images'] = {
                'total_count': len(scraped_data['images']),
                'all_images': scraped_data['images']
            }
            logger.debug(f"Included {len(scraped_data['images'])} images in output")
        
        # Add custom data if available
        if 'custom_data' in scraped_data:
            output['custom_data'] = scraped_data['custom_data']
            logger.debug("Included custom data in output")
        
        logger.info(f"Final output structured. Sections: {list(output.keys())}")
        return output

    def _categorize_links(self, links: List[Dict[str, str]]) -> Dict[str, int]:
        """Categorize links by type"""
        categories = {}
        for link in links:
            link_type = link.get('type', 'webpage')
            categories[link_type] = categories.get(link_type, 0) + 1
        return categories

    @endpoint("/web-scraping/scrape", methods=["POST"], auth_required=True)
    async def scrape_website(self, request_data: dict, user: dict):
        """Scrape a website and return structured JSON analysis"""
        try:
            job_data = validate_job_data(request_data, WebScrapingJobData)
        except Exception as e:
            return self.error_response(
                error_message=f"Validation failed: {str(e)}",
                message="Invalid request data",
                endpoint="/web-scraping/scrape"
            )
        
        try:
            logger.info(f"Processing web scraping request for: {job_data.url}")
            
            # Execute the scraping logic
            result = await self._execute_job_logic(job_data)
            
            if result.success:
                return self.success_response(
                    result={
                        "data": result.result,
                        "result_format": result.result_format,
                        "metadata": result.metadata
                    },
                    message="Website scraped and analyzed successfully",
                    endpoint="/web-scraping/scrape",
                    url=job_data.url,
                    content_analyzed=job_data.analyze_content
                )
            else:
                return self.error_response(
                    error_message=result.error_message,
                    message="Web scraping failed",
                    endpoint="/web-scraping/scrape",
                    url=job_data.url,
                    metadata=result.metadata
                )
                
        except Exception as e:
            logger.error(f"Failed to scrape website: {e}")
            return self.error_response(
                error_message=f"Failed to scrape website: {str(e)}",
                message="Web scraping operation failed",
                endpoint="/web-scraping/scrape",
                url=job_data.url if 'job_data' in locals() else "unknown"
            )

    @endpoint("/web-scraping/diagnose-ai", methods=["POST"], auth_required=True)
    async def diagnose_ai_analysis(self, request_data: dict, user: dict):
        """Diagnostic endpoint to test AI analysis functionality"""
        try:
            test_content = request_data.get("test_content", "This is a test article about artificial intelligence and machine learning technologies.")
            summary_length = request_data.get("summary_length", "medium")
            extract_keywords = request_data.get("extract_keywords", True)
            
            logger.info("Starting AI analysis diagnostic test")
            
            # Test Google AI service availability
            try:
                service_info = self.google_ai.get_info()
                logger.info(f"Google AI service available: {service_info}")
            except Exception as service_error:
                return self.error_response(
                    error_message=f"Google AI service unavailable: {str(service_error)}",
                    message="AI service diagnostic failed",
                    endpoint="/web-scraping/diagnose-ai",
                    diagnostic="google_ai_service_unavailable"
                )
            
            # Test AI analysis with simple content
            try:
                analysis_result = await self._analyze_content(test_content, summary_length, extract_keywords)
                
                diagnostic_info = {
                    "test_content_length": len(test_content),
                    "analysis_result": analysis_result,
                    "has_error": "error" in analysis_result,
                    "google_ai_service_info": self.google_ai.get_info(),
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                
                if "error" in analysis_result:
                    return self.error_response(
                        error_message=analysis_result["error"],
                        message="AI analysis returned error",
                        endpoint="/web-scraping/diagnose-ai",
                        diagnostic="ai_analysis_returned_error",
                        **diagnostic_info
                    )
                else:
                    return self.success_response(
                        result=diagnostic_info,
                        message="AI analysis diagnostic completed successfully",
                        endpoint="/web-scraping/diagnose-ai",
                        diagnostic="ai_analysis_successful"
                    )
                
            except Exception as analysis_error:
                logger.error(f"AI analysis diagnostic failed: {analysis_error}", exc_info=True)
                return self.error_response(
                    error_message=f"AI analysis failed: {str(analysis_error)}",
                    message="AI analysis diagnostic failed",
                    endpoint="/web-scraping/diagnose-ai",
                    diagnostic="ai_analysis_exception",
                    google_ai_service_info=self.google_ai.get_info() if self.google_ai else "unavailable"
                )
                
        except Exception as e:
            logger.error(f"AI diagnostic test failed: {e}", exc_info=True)
            return self.error_response(
                error_message=f"Diagnostic test failed: {str(e)}",
                message="Diagnostic operation failed",
                endpoint="/web-scraping/diagnose-ai",
                diagnostic="diagnostic_exception"
            )

    @endpoint("/web-scraping/info", methods=["GET"], auth_required=False)
    async def get_agent_info(self):
        """Get web scraping agent information"""
        try:
            agent_info = {
                "name": self.name,
                "description": self.description,
                "result_format": self.result_format,
                "capabilities": [
                    "Website content scraping",
                    "AI-powered content analysis",
                    "Link and image extraction",
                    "Custom CSS selector support",
                    "Structured JSON output",
                    "Content summarization",
                    "Keyword extraction"
                ],
                "supported_formats": ["HTML", "XHTML"],
                "max_depth": 3,
                "google_ai_service": self.google_ai.get_info() if self.google_ai else "unavailable",
                "status": "available"
            }
            
            return self.success_response(
                result=agent_info,
                message="Web scraping agent information retrieved successfully",
                endpoint="/web-scraping/info"
            )
            
        except Exception as e:
            logger.error(f"Failed to get agent info: {e}")
            return self.error_response(
                error_message=f"Failed to get agent info: {str(e)}",
                message="Agent info retrieval failed",
                endpoint="/web-scraping/info"
            ) 