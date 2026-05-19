import httpx
from core.config import settings

async def fetch_urls_for_topic(topic: str, max_results: int = 3) -> list[str]:
    """Queries Tavily to find the most relevant article URLs for a given topic."""
    
    if not settings.TAVILY_API_KEY or settings.TAVILY_API_KEY.startswith("tvly-YOUR"):
        raise ValueError("Tavily API Key is missing. Please add it to core/config.py")

    url = "https://api.tavily.com/search"
    payload = {
        "api_key": settings.TAVILY_API_KEY,
        "query": f"Latest detailed articles or blog posts about {topic}",
        "search_depth": "basic",
        "max_results": max_results,
        "include_domains": [],
        "exclude_domains": ["youtube.com", "twitter.com", "instagram.com", "reddit.com"] # Exclude video/social sites
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload)
        response.raise_for_status()
        
        data = response.json()
        
        # Extract just the URLs from the search results
        urls = [result["url"] for result in data.get("results", [])]
        return urls