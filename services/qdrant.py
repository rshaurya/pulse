import uuid
from qdrant_client import AsyncQdrantClient
from qdrant_client.http.models import Distance, VectorParams

from services.llm import generate_embedding

from core.config import settings


async def initialize_collection():
    """Creates the collection and sets up payload indexes per the blueprint."""
    
    db_client = client = AsyncQdrantClient(
        url=settings.QDRANT_URL,
        api_key=settings.QDRANT_API_KEY
    )
    
    try:
        await db_client.get_collection(settings.COLLECTION_NAME)
        exists = True
    except Exception:
        exists = False
    
    if not exists:
        # Create the collection with the correct vector size and mathematical distance
        await db_client.create_collection(
            collection_name=settings.COLLECTION_NAME,
            vectors_config=VectorParams(size=settings.VECTOR_SIZE, distance=Distance.COSINE),
        )
        
        # Blueprint Requirement: State Tracking (Solving Repetition)
        # We index the 'emailed' field for fast must_not filtering
        await db_client.create_payload_index(
            collection_name=settings.COLLECTION_NAME,
            field_name="emailed",
            field_schema="bool",
        )
        print(f"Created Qdrant collection: {settings.COLLECTION_NAME}")

async def insert_document(text: str, summary: str, embedding: list[float]) -> str:
    """Inserts a vectorized document and its metadata into the database."""
    
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
    