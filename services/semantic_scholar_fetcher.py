import httpx
import urllib.parse

async def fetch_latest_papers(topic: str, max_results: int = 3) -> list[dict]:
    """Queries Semantic Scholar's REST API for the latest papers on a given topic."""
    
    # URL encode the topic
    safe_topic = urllib.parse.quote(topic)
    
    # Semantic Scholar allows us to specify exactly which fields we want returned
    fields = "title,url,abstract,year,authors"
    
    # The official Academic Graph API search endpoint
    url = f"https://api.semanticscholar.org/graph/v1/paper/search?query={safe_topic}&limit={max_results}&fields={fields}"
    
    async with httpx.AsyncClient(timeout=15.0) as client:
        # We don't strictly need a User-Agent here, but it's good practice
        headers = {
            "User-Agent": "PULSE_Knowledge_Engine_MVP/1.0"
        }
        
        response = await client.get(url, headers=headers)
        response.raise_for_status()
        
        # The API returns a JSON object with a 'data' array containing the papers
        data = response.json()
        raw_papers = data.get("data", [])
        
        papers = []
        for paper in raw_papers:
            # Semantic Scholar occasionally returns papers without abstracts, so we provide a fallback
            abstract = paper.get("abstract")
            if not abstract:
                abstract = "No abstract provided by the publisher."
                
            papers.append({
                "title": paper.get("title", "Unknown Title"),
                "url": paper.get("url", "No URL available"),
                "abstract": abstract.replace('\n', ' ').strip(),
                "published": str(paper.get("year", "Unknown"))
            })
            
        return papers