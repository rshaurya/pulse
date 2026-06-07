import httpx
import feedparser
import asyncio

async def fetch_single_feed(feed_url: str, max_results: int = 2) -> list[dict]:
    """Fetches and parses a single RSS feed asynchronously."""
    try:
        # Spoof a browser just in case the blog has basic bot protection
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True, headers=headers) as client:
            response = await client.get(feed_url)
            response.raise_for_status()
            
            # Parse the raw XML text
            feed = feedparser.parse(response.text)
            
            articles = []
            for entry in feed.entries[:max_results]:
                # RSS feeds are notoriously messy. Some use 'summary', some use 'description'.
                # We use getattr() to safely grab whatever they provide without crashing.
                content = getattr(entry, 'summary', getattr(entry, 'description', 'No content available.'))
                
                articles.append({
                    "source_feed": feed_url,
                    "title": getattr(entry, 'title', 'Unknown Title'),
                    "url": getattr(entry, 'link', 'No URL'),
                    "content_snippet": content[:500] + "...", # Truncated for the MVP queue
                    "published": getattr(entry, 'published', 'Unknown Date')
                })
                
            return articles
            
    except Exception as e:
        print(f"   [FAILED] Could not fetch RSS from {feed_url}: {e}")
        return [] # If one blog is offline, return an empty list and don't crash the pipeline!

async def fetch_all_rss_feeds(feed_urls: list[str], max_per_feed: int = 2) -> list[dict]:
    """Fires off concurrent requests to all RSS feeds at the same time."""
    
    # Create a list of asynchronous tasks
    tasks = [fetch_single_feed(url, max_per_feed) for url in feed_urls]
    
    # Run them all simultaneously and wait for them all to finish
    results = await asyncio.gather(*tasks)
    
    # Results is a list of lists. We flatten it into one single list of articles.
    flattened_articles = [article for feed_list in results for article in feed_list]
    return flattened_articles