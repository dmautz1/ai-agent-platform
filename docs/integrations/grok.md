# Grok (xAI) Integration

> **Grok by xAI Setup** - Configure Grok for real-time data access and research capabilities

## Overview

Grok by xAI offers real-time information access and web search capabilities, making it ideal for current events and research tasks that require up-to-date information.

**Key Features:**
- **Real-time Data**: Access to current web information and live updates
- **Web Search**: Built-in search capabilities for comprehensive research
- **Conversational**: Designed for natural, engaging dialogue
- **Current Events**: Excellent for recent information and breaking news
- **X Platform Integration**: Enhanced understanding of social media context
- **Unique Perspective**: Conversational AI with humor and personality

## Quick Setup

### 1. Create xAI Account

1. Go to [xAI Console](https://console.x.ai/)
2. Sign up with your account credentials
3. Complete verification process
4. Subscribe to API access plan

### 2. Generate API Key

1. Navigate to **API Keys** section
2. Create new API key
3. Copy the generated key (starts with `xai-`)

```bash
# Your Grok API key
GROK_API_KEY=xai-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### 3. Configure Environment

Add to `backend/.env`:

```bash
# Grok Configuration
GROK_API_KEY=xai-your-key-here
GROK_MODEL=grok-2  # Default model
GROK_MAX_TOKENS=4000
GROK_TEMPERATURE=0.7
```

### 4. Test Connection

```bash
# Start backend
cd backend && python main.py

# Test Grok connection
curl -X POST http://localhost:8000/ai/test \
  -H "Content-Type: application/json" \
  -d '{"provider": "grok", "prompt": "What are the latest tech news today?"}'
```

## Available Models

### Grok-2 (Latest Model)
- **Model**: `grok-2`
- **Best for**: General conversation, analysis, and real-time information
- **Strengths**: Latest model with improved reasoning and knowledge
- **Context**: Large context window for detailed conversations

### Grok-2 Vision (Multimodal)
- **Model**: `grok-2-vision`
- **Best for**: Image analysis, visual question answering
- **Strengths**: Combines text and image understanding
- **Context**: Processes both text and visual inputs

### Grok-1.5 (Previous Generation)
- **Model**: `grok-1.5`
- **Best for**: Standard conversational tasks
- **Strengths**: Proven reliability, good performance
- **Context**: Stable option for production use

### Model Configuration

```bash
# Latest model (default)
GROK_MODEL=grok-2

# Vision-enabled model
GROK_MODEL=grok-2-vision

# Previous generation model
GROK_MODEL=grok-1.5
```

## Using Grok in Agents

### Basic Usage

```python
from services.llm_service import get_unified_llm_service

@job_model
class GrokJobData(BaseModel):
    prompt: str = Field(..., description="Query for Grok")
    include_realtime: bool = Field(default=True, description="Include real-time data")
    search_web: bool = Field(default=False, description="Perform web search")

class GrokAgent(SelfContainedAgent):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.llm = get_unified_llm_service()
    
    async def _execute_job_logic(self, job_data: GrokJobData):
        # Grok excels at real-time information
        result = await self.llm.query(
            prompt=job_data.prompt,
            provider="grok",
            model="grok-2",
            extra_params={
                "realtime_data": job_data.include_realtime,
                "web_search": job_data.search_web
            }
        )
        
        return AgentExecutionResult(
            success=True,
            result=result,
            metadata={
                "provider": "grok",
                "realtime_enabled": job_data.include_realtime,
                "search_enabled": job_data.search_web
            }
        )
```

## Best Use Cases

### Current Events Analysis

```python
async def analyze_current_events(self, topic: str):
    prompt = f"""
    Provide a current analysis of: {topic}
    
    Include:
    1. Latest developments (last 24-48 hours)
    2. Key players and stakeholders
    3. Current public sentiment
    4. Potential implications
    5. Relevant social media discussions
    
    Use the most recent information available.
    """
    
    return await self.llm.query(
        prompt=prompt,
        provider="grok",
        extra_params={"realtime_data": True, "web_search": True}
    )
```

### Market Research with Real-Time Data

```python
async def market_research(self, company: str):
    prompt = f"""
    Analyze the current market position of {company}:
    
    1. Recent news and announcements
    2. Stock performance (if public)
    3. Competitor activities
    4. Industry trends
    5. Social media sentiment
    6. Recent product launches or updates
    """
    
    return await self.llm.query(
        prompt=prompt,
        provider="grok",
        extra_params={"realtime_data": True}
    )
```

### Breaking News Monitoring

```python
async def monitor_breaking_news(self, category: str = "technology"):
    prompt = f"""
    What are the most significant breaking news stories in {category} today?
    
    For each story, provide:
    1. Brief summary
    2. Time of breaking
    3. Key sources
    4. Potential impact
    5. Related developments
    
    Focus on stories from the last 6 hours.
    """
    
    return await self.llm.query(
        prompt=prompt,
        provider="grok",
        extra_params={"realtime_data": True, "web_search": True}
    )
```

### Social Media Sentiment Analysis

```python
async def analyze_social_sentiment(self, topic: str):
    prompt = f"""
    Analyze current social media sentiment around: {topic}
    
    Provide:
    1. Overall sentiment (positive/negative/neutral)
    2. Key discussion points
    3. Trending hashtags or phrases
    4. Notable influencer opinions
    5. Sentiment trends over the last week
    
    Use the most recent social media data available.
    """
    
    return await self.llm.query(
        prompt=prompt,
        provider="grok",
        extra_params={"realtime_data": True}
    )
```

### Research Assistant with Web Search

```python
async def research_with_sources(self, research_question: str):
    prompt = f"""
    Research this question comprehensively: {research_question}
    
    Provide:
    1. Direct answer to the question
    2. Supporting evidence from recent sources
    3. Different perspectives or viewpoints
    4. Data and statistics (if relevant)
    5. Credible source citations
    
    Use current web sources and provide links where possible.
    """
    
    return await self.llm.query(
        prompt=prompt,
        provider="grok",
        extra_params={"web_search": True, "realtime_data": True}
    )
```

### Image Analysis with Grok Vision

```python
async def analyze_image_with_context(self, image_url: str, context: str):
    prompt = f"""
    Analyze this image in the context of: {context}
    
    Provide:
    1. Detailed description of what you see
    2. Relevance to the given context
    3. Any text or numbers visible
    4. Notable details or anomalies
    5. Insights or implications
    
    Image: {image_url}
    """
    
    return await self.llm.query(
        prompt=prompt,
        provider="grok",
        model="grok-2-vision",
        extra_params={"image_url": image_url}
    )
```

## Pricing and Cost Optimization

### Pricing Structure

Grok operates on a subscription model rather than pay-per-token:

| Plan | Price | Features |
|------|-------|----------|
| **Basic** | $8/month | Limited queries, standard access |
| **Premium** | $16/month | Higher limits, priority access |
| **Pro** | Custom | Enterprise features, dedicated support |

### Cost Optimization Strategies

```python
# Use Grok for time-sensitive queries only
def should_use_grok(query_type: str, urgency: str) -> bool:
    """
    Determine if Grok is the best choice for this query
    """
    grok_optimal_cases = [
        "current_events",
        "breaking_news", 
        "real_time_data",
        "social_sentiment",
        "market_updates"
    ]
    
    return query_type in grok_optimal_cases or urgency == "urgent"

# Route queries intelligently
async def intelligent_ai_routing(self, query: str, query_type: str):
    if should_use_grok(query_type, "normal"):
        return await self.llm.query(query, provider="grok")
    else:
        # Use more cost-effective provider for general queries
        return await self.llm.query(query, provider="google")
```

### Subscription Management

```python
async def track_grok_usage(self):
    """
    Monitor Grok usage to optimize subscription plan
    """
    usage_metrics = {
        "daily_queries": 0,
        "query_types": [],
        "peak_hours": [],
        "response_times": []
    }
    
    # Track usage patterns to optimize plan selection
    return usage_metrics
```

## Error Handling

```python
import grok

async def robust_grok_query(prompt: str):
    try:
        result = await self.llm.query(prompt, provider="grok")
        return result
    except grok.AuthenticationError:
        logger.error("Grok authentication failed - check API key and subscription")
        raise
    except grok.RateLimitError as e:
        logger.warning(f"Grok rate limit hit: {e}")
        # Implement backoff or fallback
        await asyncio.sleep(60)  # Wait longer for subscription limits
        return await self.llm.query(prompt, provider="google")  # Fallback
    except grok.APIError as e:
        logger.error(f"Grok API error: {e}")
        # Fallback to another provider for real-time data
        return await self.llm.query(prompt, provider="anthropic")
```

## Best Practices

### 1. Query Optimization for Real-Time Data

```python
def optimize_grok_prompt(base_prompt: str, time_sensitivity: str) -> str:
    """
    Optimize prompts for Grok's real-time capabilities
    """
    if time_sensitivity == "urgent":
        return f"""
        [URGENT - REAL-TIME REQUIRED]
        {base_prompt}
        
        Please use the most current information available and indicate
        the timestamp of the data you're using.
        """
    elif time_sensitivity == "recent":
        return f"""
        {base_prompt}
        
        Focus on information from the last 24-48 hours.
        """
    else:
        return base_prompt
```

### 2. Leveraging X Platform Integration

```python
async def analyze_x_platform_trends(self, topic: str):
    prompt = f"""
    Analyze current trends and discussions about {topic} on X (Twitter):
    
    1. Trending hashtags related to this topic
    2. Most engaging posts (high likes/retweets)
    3. Key influencers discussing this topic
    4. Sentiment analysis of the conversation
    5. Emerging sub-topics or angles
    
    Use your enhanced understanding of X platform dynamics.
    """
    
    return await self.llm.query(
        prompt=prompt,
        provider="grok",
        extra_params={"x_platform_focus": True}
    )
```

### 3. Combining Real-Time with Analysis

```python
async def comprehensive_topic_analysis(self, topic: str):
    """
    Combine real-time data gathering with deep analysis
    """
    
    # First, gather current information
    current_info = await self.llm.query(
        f"What is the current status and latest developments regarding {topic}?",
        provider="grok",
        extra_params={"realtime_data": True, "web_search": True}
    )
    
    # Then, perform deep analysis
    analysis = await self.llm.query(
        f"""
        Based on this current information about {topic}:
        {current_info}
        
        Provide a comprehensive analysis including:
        1. Historical context and how we got here
        2. Key trends and patterns
        3. Potential future implications
        4. Stakeholder perspectives
        5. Risk assessment
        """,
        provider="grok"
    )
    
    return {
        "current_status": current_info,
        "detailed_analysis": analysis,
        "timestamp": datetime.now().isoformat()
    }
```

## Troubleshooting

### Common Issues

**Authentication Errors**
```bash
# Check API key format
echo $GROK_API_KEY | grep "^xai-"

# Verify subscription status in xAI console
```

**Subscription Limits**
```python
# Implement usage tracking
def track_daily_usage():
    usage_count = get_daily_grok_usage()
    if usage_count > daily_limit * 0.8:
        logger.warning("Approaching daily Grok usage limit")
        return False
    return True

# Use fallback providers when near limits
if not track_daily_usage():
    return await self.llm.query(prompt, provider="google")
```

**Real-Time Data Not Available**
```python
# Handle cases where real-time data isn't accessible
async def fallback_for_realtime(prompt: str):
    try:
        return await self.llm.query(prompt, provider="grok", 
                                  extra_params={"realtime_data": True})
    except grok.DataUnavailableError:
        logger.info("Real-time data unavailable, using general knowledge")
        return await self.llm.query(
            f"{prompt}\n\nNote: Please provide the best answer based on your knowledge, "
            f"and indicate if the information might not be current.",
            provider="grok"
        )
```

### Performance Optimization

**Response Time Optimization**
```python
async def optimize_grok_response_time(prompt: str):
    """
    Optimize for faster responses when needed
    """
    # Use shorter prompts for faster responses
    if len(prompt) > 1000:
        prompt = prompt[:800] + "... (provide a concise answer)"
    
    return await self.llm.query(
        prompt,
        provider="grok",
        extra_params={
            "max_tokens": 500,  # Limit response length
            "temperature": 0.3   # More focused responses
        }
    )
```

**Caching for Repeated Real-Time Queries**
```python
from datetime import datetime, timedelta
import hashlib

class GrokCachedAgent(SelfContainedAgent):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.cache = {}
        self.cache_duration = timedelta(minutes=15)  # Cache real-time data briefly
    
    async def cached_realtime_query(self, prompt: str):
        # Create cache key
        cache_key = hashlib.md5(prompt.encode()).hexdigest()
        
        # Check if we have recent cached data
        if cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if datetime.now() - timestamp < self.cache_duration:
                logger.info("Using cached Grok real-time data")
                return cached_data
        
        # Query Grok for fresh data
        result = await self.llm.query(
            prompt,
            provider="grok",
            extra_params={"realtime_data": True}
        )
        
        # Cache the result
        self.cache[cache_key] = (result, datetime.now())
        return result
```

---

**Next Steps**: Return to [Multi-Provider Setup](ai-providers.md) or explore [DeepSeek Integration](deepseek.md) 