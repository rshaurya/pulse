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
    
    response = await db_client.get_collections()
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
    else:
        print("[QDRANT] Collection already exists. Skipping creation.")

    try:
        print("[QDRANT] Building/Verifying Payload Index for 'user_id'...")
        await db_client.create_payload_index(
            collection_name=settings.COLLECTION_NAME,
            field_name="user_id",
            field_schema=models.PayloadSchemaType.KEYWORD,
        )
        print("[QDRANT] Index active.")
    except Exception as e:
        # If Qdrant says "Index already exists", it throws an error. 
        # can safely catch and ignore it 
        pass

async def insert_document(title: str, url: str, text: str, summary: str, embedding: list[float], user_id: str) -> str:
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
                    "emailed": False,
                    "user_id": user_id
                }
            }
        ]
    )
    return doc_id
