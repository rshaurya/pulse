import asyncio
from sqlalchemy.orm import sessionmaker
from services.llm import summarize_text, generate_embedding
from services.qdrant import insert_document
from core.database import AsyncSession, engine
from core.models import ArticleState

async def process_and_store_articles(articles: list[dict], user_id: str, llm_api_key: str, user_context: str = ""):
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
            summary = "Summary failed due to rate limits." # Default fallback
            max_retries = 3
            
            for attempt in range(max_retries):
                try:
                    summary = await summarize_text(raw_text, llm_api_key, user_context)
                    break # Success! Break out of the retry loop.
                except Exception as e:
                    if "429" in str(e):
                        # Calculate backoff: 10s, 20s, 40s
                        wait_time = 10 * (2 ** attempt) 
                        print(f"   [RATE LIMIT] Groq is throttling us. Backing off for {wait_time} seconds...")
                        await asyncio.sleep(wait_time)
                        if attempt == max_retries - 1:
                            print(f"   [ABORT] Max retries hit for '{article.get('title')}'. Saving without summary.")
                    else:
                        print(f"   [LLM ERROR] Non-429 error: {e}")
                        break # Break loop if it's a different kind of error (like an invalid API key)

            print(f"\n--- AI Summary Preview ---\n{summary[:100]}...\n--------------------------\n")
            
            full_payload_text = f"Title: {article.get('title')}\nURL: {article.get('url')}\nContent: {raw_text}"
            
            embedding = await generate_embedding(summary)
            
            # attach the user_id to the Qdrant payload!
            qdrant_id = await insert_document(
                title=article.get('title', 'Untitled'),
                url=article.get('url', '#'),
                text=full_payload_text, 
                summary=summary, 
                embedding=embedding,
                user_id=str(user_id) 
            )
            
            async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
            async with async_session() as session:
                new_article_state = ArticleState(
                    user_id=user_id,
                    qdrant_doc_id=str(qdrant_id),
                    emailed=False
                )
                session.add(new_article_state)
                await session.commit()
            
            
            successful_inserts += 1
            await asyncio.sleep(2) 
            
        except Exception as e:
            print(f"   [FAILED] Could not process {article.get('title')}: {e}")
            if "429" in str(e):
                await asyncio.sleep(10)
            continue
            
    print(f"[BACKGROUND WORKER] Finished User {user_id}! Stored {successful_inserts} documents.\n")