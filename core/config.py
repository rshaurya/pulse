from pydantic import BaseModel

class Settings(BaseModel):
    PROJECT_NAME: str = "PULSE Knowledge Engine"
    # Qdrant is running locally via Docker
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    COLLECTION_NAME: str = "knowledge_base"
    VECTOR_SIZE: int = 3072
    
    # Ollama is running locally via Docker
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    LLM_MODEL: str = "phi3:mini" 

settings = Settings()