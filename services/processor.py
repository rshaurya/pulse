import asyncio
from services.llm import summarize_text, generate_embedding
from services.qdrant import insert_document

async def process_and_store_articles(articles: list[dict], user_id: str, llm_api_key: str):
    """Background worker that processes raw articles and stores them in Qdrant for a specific user."""
    
    print(f"\n[BACKGROUND WORKER] Processing {len(articles)} articles for User {user_id}...")
    successful_inserts = 0
    
    for article in articles:
        try:
            print(f" -> Processing: {article.get('title', 'Unknown')}...")
            
            raw_text = article.get('abstract') or article.get('content_snippet') or article.get('title')
            if len(raw_text) > 14000:
                raw_text = raw_text[:14000] + "... [TRUNCATED]"
            
            # Pass the decrypted API key to your LLM function
            summary = await summarize_text(raw_text, llm_api_key)
            embedding = await generate_embedding(summary)
            
            full_payload_text = f"Title: {article.get('title')}\nURL: {article.get('url')}\nContent: {raw_text}"
            
            # attach the user_id to the Qdrant payload!
            await insert_document(
                title=article.get('title', 'Untitled'),
                url=article.get('url', '#'),
                text=full_payload_text, 
                summary=summary, 
                embedding=embedding,
                user_id=str(user_id) 
            )
            
            successful_inserts += 1
            await asyncio.sleep(2) 
            
        except Exception as e:
            print(f"   [FAILED] Could not process {article.get('title')}: {e}")
            if "429" in str(e):
                await asyncio.sleep(10)
            continue
            
    print(f"[BACKGROUND WORKER] Finished User {user_id}! Stored {successful_inserts} documents.\n")