import httpx
import trafilatura

async def fetch_and_extract_url(url: str) -> str:
    """Safely fetches a URL and extracts the core article text."""
    print(f"[CRAWLER] Initiating fetch for: {url}")
    
    # realistic User-Agent so websites don't block as a basic bot.
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, follow_redirects=True, timeout=15.0)
            response.raise_for_status() # Throws an error if we get a 404 or 403
            
        print("[CRAWLER] HTML downloaded successfully. Extracting clean text...")
        
        clean_text = trafilatura.extract(response.text)
        
        if not clean_text:
            raise ValueError("Trafilatura could not find meaningful article text on this page.")
            
        print(f"[CRAWLER] Successfully extracted {len(clean_text)} characters.")
        return clean_text

    except Exception as e:
        print(f"[CRAWLER] FAILED to process {url}: {e}")
        raise e