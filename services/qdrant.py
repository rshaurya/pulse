import uuid
from qdrant_client import AsyncQdrantClient
from qdrant_client.http.models import Distance, VectorParams

from core.config import settings

# Initialize the async client pointing to our local Docker container
db_client = AsyncQdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)


async def initialize_collection():
    """Creates the collection and sets up payload indexes per the blueprint."""
    exists = await db_client.collection_exists(settings.COLLECTION_NAME)
    
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
                    "emailed": False # Default state per our blueprint
                }
            }
        ]
    )
    return doc_id