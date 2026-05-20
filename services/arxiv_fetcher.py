import arxiv
import asyncio

async def fetch_latest_arxiv_papers(topic: str, max_results: int = 3) -> list[dict]:
    """Queries the arXiv API using the dedicated Python package."""
    
    def _fetch():
        search = arxiv.Search(
            query=topic,
            max_results=max_results,
            sort_by=arxiv.SortCriterion.SubmittedDate
        )
        
        # THE SRE FIX: Configure the client to be incredibly polite
        client = arxiv.Client(
            page_size=max_results, # Don't ask for 100 if we only need 1 or 3!
            delay_seconds=3.0,     # arXiv officially demands 3 seconds between requests
            num_retries=5          # If we get a 429, wait and silently try again up to 5 times
        )
        
        papers = []
        for result in client.results(search):
            papers.append({
                "title": result.title.replace('\n', ' ').strip(),
                "url": result.entry_id, 
                "abstract": result.summary.replace('\n', ' ').strip(),
                "published": str(result.published)
            })
            
        return papers

    return await asyncio.to_thread(_fetch)