import uuid
from qdrant_client import AsyncQdrantClient, models
from qdrant_client.http.models import Distance, VectorParams

from services.llm import generate_embedding

from core.config import settings


async def initialize_collection():
    print(f"[QDRANT] Connecting to Qdrant Cloud...")
    
    db_client = AsyncQdrantClient(
        url=settings.QDRANT_URL,
        api_key=settings.QDRANT_API_KEY
    )
    
    # THE SRE FIX: Ask for the guest list instead of relying on try/except!
    response = await db_client.get_collections()
    
    # Extract just the names of the collections into a simple Python list
    existing_collections = [col.name for col in response.collections]
    print(f"[QDRANT] Existing collections: {existing_collections}")
    
    if settings.COLLECTION_NAME not in existing_collections:
        print("[QDRANT] Collection not found. Creating a new one for FastEmbed (384 dims)...")
        await db_client.create_collection(
            collection_name=settings.COLLECTION_NAME,
            vectors_config=models.VectorParams(
                size=384, 
                distance=models.Distance.COSINE
            )
        )
        
        print("[QDRANT] Building Payload Index for 'emailed' field...")
        await db_client.create_payload_index(
            collection_name=settings.COLLECTION_NAME,
            field_name="emailed",
            field_schema=models.PayloadSchemaType.BOOL,
        )
        print("[QDRANT] Initialization complete.")
    else:
        print(f"[QDRANT] Collection '{settings.COLLECTION_NAME}' verified and ready for ingestion.")

async def insert_document(title: str, url: str, text: str, summary: str, embedding: list[float]) -> str:
    """Inserts a vectorized document and its metadata into the database."""
    
    print(f"[QDRANT] Storing document: {title[:30]}...")
    
    db_client = client = AsyncQdrantClient(
        url=settings.QDRANT_URL,
        api_key=settings.QDRANT_API_KEY
    )
    
    doc_id = str(uuid.uuid4())
    
    await db_client.upsert(
        collection_name=settings.COLLECTION_NAME,
        points=[
            {
                "id": doc_id,
                "vector": embedding,
                "payload": {
                    "title": title,
                    "url": url,
                    "raw_text": text,
                    "summary": summary,
                    "emailed": False 
                }
            }
        ]
    )
    return doc_id

async def search_documents(query_text: str, limit: int = 5):
    """Embeds a search query and returns the closest matching articles from Qdrant."""
    
    db_client = client = AsyncQdrantClient(
        url=settings.QDRANT_URL,
        api_key=settings.QDRANT_API_KEY
    )
    
    print(f"[QDRANT] Searching for: '{query_text}'...")
    
    # 1. Convert the human query into vector math
    query_vector = await generate_embedding(query_text)
    
    # 2. Search the database
    client = AsyncQdrantClient(
        url=settings.QDRANT_URL,
        api_key=settings.QDRANT_API_KEY 
    )
    
    try:
        results = await client.search(
            collection_name=settings.COLLECTION_NAME,
            query_vector=query_vector,
            limit=limit,
            with_payload=True # we need urls too
        )
        print(f"[QDRANT] Found {len(results)} relevant articles.")
        return results
    except Exception as e:
        print(f"[QDRANT] Search failed: {e}")
        return []
    