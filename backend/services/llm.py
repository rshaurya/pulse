import httpx
from fastembed import TextEmbedding
from core.config import settings


# USER_PROFILE = load_user_profile()

# def build_system_prompt() -> str:
#     """Constructs a highly specific system prompt based on the JSON profile."""
#     if not USER_PROFILE:
#         return "You are a helpful AI summarizer. Extract the key information according to the given context."
        
#     prefs = "\n- ".join(USER_PROFILE.get("formatting_preferences", []))
#     interests = ", ".join(USER_PROFILE.get("core_interests", []))
    
#     return f"""You are a highly technical AI assistant serving a user with the following profile:
#     - Technical Level: {USER_PROFILE.get('technical_level')}
#     - Core Focus Areas: {interests}
    
#     You are tasked with summarizing incoming articles and data to keep the user aware about recent developments in their field of interest. 
#     You MUST adhere to these strict formatting rules:
#     - {prefs}
#     """


print("[SYSTEM] Booting CPU Vector Engine (FastEmbed)...")
embedding_model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")

async def summarize_text(text: str, api_key: str, user_context: str = "") -> str:
    """Sends the text to Groq API and returns a personalised summary."""
    
    if not api_key:
        raise ValueError("Cannot summarize: User has not configured an LLM API key.")
        
    print("[LLM] Generating context-aware summary via Groq...")
    
    system_prompt = "You are an elite technical research assistant. Your job is to summarize the provided text for this person.They want to know recent updates and increase their knowledge on the topic. "
    
    if user_context:
        system_prompt += f"Focus heavily on these core interests if they appear in the text: {user_context}. When summarizing, adhere to tjeir interests. Have a clear and concise tone. Highlight specific areas if applicable. Look for any recent developments or insights that would be particularly relevant to their interests. Make sure they don't miss out on any critical information that could impact their learning or projects in these areas"
    
    
    # headers = {
    #     "Authorization": f"Bearer {settings.LLM_API_KEY}",
    #     "Content-Type": "application/json"
    # }
    
    # system_prompt = build_system_prompt()
    
    # Standard OpenAI-compatible payload (Used by Groq, Together AI, OpenAI, etc.)
    payload = {
        "model": settings.LLM_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text}
        ],
        "temperature": 0.3 # Keep it low for factual summaries
    }
    
    # Inject the API key into the headers
    headers = {"Content-Type": "application/json"}
    if settings.LLM_API_KEY:
        headers["Authorization"] = f"Bearer {api_key}"
    
    # We can drop the timeout back down to 30s because Cloud APIs don't have "cold boots"!
    # async with httpx.AsyncClient(timeout=30.0) as client:
    #     response = await client.post(
    #         settings.LLM_BASE_URL, 
    #         json=payload,
    #         headers=headers
    #     )
    #     response.raise_for_status()
    #     data = response.json()
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                settings.LLM_BASE_URL,
                headers=headers,
                json=payload,
                timeout=30.0
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"[LLM] FAILED to generate summary: {e}")
            raise e
        
        # Parse the standard cloud response format
        # return data["choices"][0]["message"]["content"]

async def generate_embedding(text: str) -> list[float]:
    """Generates 384-dimensional vectors locally on the CPU using FastEmbed."""
    
    # FastEmbed returns a generator. We convert it to a list and grab the first array.
    embeddings = list(embedding_model.embed([text]))
    
    return embeddings[0].tolist()
