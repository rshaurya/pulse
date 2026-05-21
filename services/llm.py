import json
import os 
import httpx
from fastembed import TextEmbedding
from core.config import settings

# 1. Load the profile into memory once when the server starts
PROFILE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'user_profile.json')

def load_user_profile():
    try:
        with open(PROFILE_PATH, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("[WARNING] user_profile.json not found. Using default persona.")
        return {}

USER_PROFILE = load_user_profile()

def build_system_prompt() -> str:
    """Constructs a highly specific system prompt based on the JSON profile."""
    if not USER_PROFILE:
        return "You are a helpful AI summarizer. Extract the key information according to the given context."
        
    prefs = "\n- ".join(USER_PROFILE.get("formatting_preferences", []))
    interests = ", ".join(USER_PROFILE.get("core_interests", []))
    
    return f"""You are a highly technical AI assistant serving a user with the following profile:
    - Technical Level: {USER_PROFILE.get('technical_level')}
    - Core Focus Areas: {interests}
    
    You are tasked with summarizing incoming articles and data to keep the user aware about recent developments in their field of interest. 
    You MUST adhere to these strict formatting rules:
    - {prefs}
    """


print("[SYSTEM] Booting CPU Vector Engine (FastEmbed)...")
embedding_model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")

async def summarize_text(text: str) -> str:
    """Sends the text and the user persona to a Cloud LLM."""
    
    system_prompt = build_system_prompt()
    
    # Standard OpenAI-compatible payload (Used by Groq, Together AI, OpenAI, etc.)
    payload = {
        "model": settings.LLM_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Summarize this:\n\n{text}"}
        ],
        "temperature": 0.3 # Keep it low for factual summaries
    }
    
    # Inject the API key into the headers
    headers = {"Content-Type": "application/json"}
    if settings.LLM_API_KEY:
        headers["Authorization"] = f"Bearer {settings.LLM_API_KEY}"
    
    # We can drop the timeout back down to 30s because Cloud APIs don't have "cold boots"!
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            settings.LLM_BASE_URL, 
            json=payload,
            headers=headers
        )
        response.raise_for_status()
        data = response.json()
        
        # Parse the standard cloud response format
        return data["choices"][0]["message"]["content"]

async def generate_embedding(text: str) -> list[float]:
    """Generates 384-dimensional vectors locally on the CPU using FastEmbed."""
    
    # FastEmbed returns a generator. We convert it to a list and grab the first array.
    embeddings = list(embedding_model.embed([text]))
    
    return embeddings[0].tolist()
