import asyncio
from qdrant_client import AsyncQdrantClient
from core.config import settings
from services.email import send_daily_digest

async def generate_daily_digest():
    print("[DISPATCHER] Waking up. Fetching unread articles from Qdrant...")
    
    client = AsyncQdrantClient(
        url=settings.QDRANT_URL,
        api_key=settings.QDRANT_API_KEY
    )
    
    try:
        # We perform a basic Scroll to grab the latest 3 articles that haven't been emailed yet.
        # Note: use vector similarity to search based on your JSON profile!
        results, _ = await client.scroll(
            collection_name=settings.COLLECTION_NAME,
            limit=3,
            with_payload=True
        )
        
        if not results:
            print("[DISPATCHER] No new articles to send today.")
            return

        print(f"[DISPATCHER] Found {len(results)} articles. Sending to email service...")
        
        # Convert Qdrant Record objects to standard dictionaries for the email service
        articles_to_send = [{"id": res.id, "payload": res.payload} for res in results]
        
        send_daily_digest(articles_to_send)
        
    except Exception as e:
        print(f"[DISPATCHER] CRITICAL ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(generate_daily_digest())