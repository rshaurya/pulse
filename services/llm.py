from ollama import AsyncClient
from core.config import settings

# Initialize the async client pointing to our local Docker container
client = AsyncClient(host=settings.OLLAMA_BASE_URL)

async def summarize_text(text: str) -> str:
    """Sends raw text to Ollama to extract core concepts."""
    prompt = f"Extract the core topics and provide a concise summary of the following text:\n\n{text}"
    
    response = await client.generate(
        model=settings.LLM_MODEL,
        prompt=prompt
    )
    return response['response']

async def generate_embedding(text: str) -> list[float]:
    """Converts text into a vector embedding using Ollama."""
    response = await client.embeddings(
        model=settings.LLM_MODEL,
        prompt=text
    )
    return response['embedding']