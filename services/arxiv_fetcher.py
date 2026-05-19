import httpx
import feedparser
import urllib.parse

async def fetch_latest_arxiv_papers(topic: str, max_results: int = 3) -> list[dict]:
    """Queries the arXiv API for the latest papers on a given topic."""
    
    # URL encode the topic (e.g., "Machine Learning" becomes "Machine+Learning")
    safe_topic = urllib.parse.quote(topic)
    
    # The exact filter you mentioned: sortBy=submittedDate
    url = f"https://export.arxiv.org/api/query?search_query=all:{safe_topic}&sortBy=submittedDate&sortOrder=descending&max_results={max_results}"
    
    async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client: # Added a timeout here!
        response = await client.get(url)
        response.raise_for_status()
        
        # feedparser turns the messy XML into a clean Python dictionary
        feed = feedparser.parse(response.text)
        
        papers = []
        for entry in feed.entries:
            papers.append({
                "title": entry.title.replace('\n', ' ').strip(),
                "url": entry.link,
                "abstract": entry.summary.replace('\n', ' ').strip(),
                "published": entry.published
            })
            
        return papers