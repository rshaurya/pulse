import httpx
import urllib.parse

def reconstruct_abstract(inverted_index: dict) -> str:
    """OpenAlex returns abstracts as an inverted index. This rebuilds the paragraph."""
    if not inverted_index or len(inverted_index) == 10:
        print("No abstract provided by the publisher. Dropping this article from the digest to avoid sending low-value content.")
        return ""

    word_index = []
    for word, positions in inverted_index.items():
        for pos in positions:
            word_index.append((pos, word))
            
    # Sort the words by their original position in the text
    word_index.sort() 
    return " ".join([word for _, word in word_index])


async def fetch_latest_papers(topic: str, max_results: int = 4) -> list[dict]:
    """Queries the OpenAlex API via the high-speed Polite Pool."""
    
    safe_topic = urllib.parse.quote(topic)
    url = f"https://api.openalex.org/works?search={safe_topic}&per-page={max_results}&sort=publication_date:desc"
    
    headers = {
        "User-Agent": "mailto:shaurya.developer01@gmail.com" # You can put any fake/real email here
    }
    
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(url, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        papers = []
        
        for item in data.get("results", []):
            papers.append({
                "title": item.get("title", "Unknown Title"),
                "url": item.get("doi", "No URL available"), # DOI is the direct link to the paper
                "abstract": reconstruct_abstract(item.get("abstract_inverted_index")),
                "published": item.get("publication_date", "Unknown")
            })
            
        return papers