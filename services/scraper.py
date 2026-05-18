import httpx
import trafilatura

async def extract_text_from_url(url: str) -> str:
    """Fetches a webpage and extracts only the core article text."""
    
    # Using a browser-like User-Agent to avoid basic anti-bot blocks
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    # Fetch asynchronously so we don't block the FastAPI server
    async with httpx.AsyncClient(headers=headers, follow_redirects=True) as client:
        response = await client.get(url)
        response.raise_for_status() # Throw an error if the page is a 404 or 500
        
        clean_text = trafilatura.extract(response.text)
        
        if not clean_text:
            raise ValueError("Trafilatura could not find article text on this page.")
            
        return clean_text