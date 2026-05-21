import asyncio
from services.llm import summarize_text, generate_embedding
from services.qdrant import insert_document

async def process_and_store_articles(articles: list[dict]):
    """Background worker that processes raw articles and stores them in Qdrant."""
    
    print(f"\n[BACKGROUND WORKER] Started processing {len(articles)} articles...")
    
    successful_inserts = 0
    
    for article in articles:
        try:
            print(f" -> Processing: {article.get('title', 'Unknown')}...")
            
            # 1. Grab the raw text (we'll use abstract or content_snippet)
            raw_text = article.get('abstract') or article.get('content_snippet') or article.get('title')
            
            # 2. Generate the Summary
            summary = await summarize_text(raw_text)
            print(f"\n--- AI Summary Preview ---\n{summary}\n--------------------------\n")
            
            # 3. Generate the Vector Embedding
            embedding = await generate_embedding(summary)
            
            # 4. Store in Qdrant (We save the URL/Title as part of the payload text so we don't lose it)
            full_payload_text = f"Title: {article.get('title')}\nURL: {article.get('url')}\nContent: {raw_text}"
            
            await insert_document(
                text=full_payload_text, 
                summary=summary, 
                embedding=embedding
            )
            
            successful_inserts += 1
            print(f"   [SUCCESS] Saved to Qdrant!")
            
        except Exception as e:
            print(f"   [FAILED] Could not process {article.get('title')}: {e}")
            continue
            
    print(f"[BACKGROUND WORKER] Finished! Successfully stored {successful_inserts}/{len(articles)} documents in Qdrant.\n")