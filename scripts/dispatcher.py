import asyncio
import json
import os

from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models
from core.config import settings
from services.email import send_daily_digest
from services.llm import generate_embedding

async def generate_daily_digest():
    print("[DISPATCHER] Waking up. Reading User Brain...")
    
    # 1. Load the dynamic user profile
    profile_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "user_profile.json")
    try:
        with open(profile_path, "r") as f:
            profile = json.load(f)
    except Exception as e:
        print(f"[DISPATCHER] FAILED to load user_profile.json: {e}")
        return

    # 2. Construct the "Persona Query"
    interests = ", ".join(profile.get("core_interests", []))
    focus = ", ".join(profile.get("summary_preferences", {}).get("focus_areas", []))
    
    query_text = f"Highly technical content regarding {interests}. Focus areas include: {focus}."
    print(f"[DISPATCHER] Synthesizing Persona Vector for: '{query_text}'")
    
    # Convert your brain into a 384-dimensional mathematical coordinate
    query_vector = await generate_embedding(query_text)
    
    client = AsyncQdrantClient(
        url=settings.QDRANT_URL,
        api_key=settings.QDRANT_API_KEY
    )
    
    try:
        print("[DISPATCHER] Hunting Qdrant Cloud for optimal semantic matches...")
        
        # 3. semantic search
        results = await client.search(
            collection_name=settings.COLLECTION_NAME,
            query_vector=query_vector,
            query_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="emailed",
                        match=models.MatchValue(value=False) 
                    )
                ]
            ),
            limit=4,
            with_payload=True
        )
        
        if not results:
            print("[DISPATCHER] No new relevant articles to send today.")
            return

        print(f"[DISPATCHER] Found {len(results)} highly relevant articles. Dispatching...")
        
        # print the "Score" (0.0 to 1.0) to see how perfectly it matches your profile!
        for res in results:
            print(f" -> Match Score: {res.score:.4f} | Title: {res.payload.get('title')}")
        
        articles_to_send = [{"id": res.id, "payload": res.payload} for res in results]
        
        # Dispatch the email
        send_daily_digest(articles_to_send)
        
        point_ids = [res.id for res in results]
        await client.set_payload(
            collection_name=settings.COLLECTION_NAME,
            payload={"emailed": True},
            points=point_ids
        )
        print("[DISPATCHER] Database updated. Articles marked as emailed.")
        
    except Exception as e:
        print(f"[DISPATCHER] CRITICAL ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(generate_daily_digest())