import httpx
from core.config import settings

async def fetch_urls_for_topic(topic: str, api_key: str, max_results: int = 5) -> list[str]:
    """Queries Tavily to find the most relevant article URLs for a given topic."""
    
    if not api_key:
        print(f"[SEARCH] Skipping Tavily search for '{topic}': No API key provided by user.")
        return []

    url = "https://api.tavily.com/search"
    payload = {
        "api_key": api_key,
        "query": f"Latest detailed articles or blog posts about {topic}",
        "search_depth": "basic",
        "max_results": max_results,
        "include_domains": [],
        "exclude_domains": ["youtube.com", "x.com", "instagram.com"]
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            
            data = response.json()
            # Extract just the URLs from the search results
            urls = [result["url"] for result in data.get("results", [])]
            return urls
    except:
        print(f"[SEARCH ERROR] Tavily request failed: {e}")
        return []