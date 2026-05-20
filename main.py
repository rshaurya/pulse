from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl
from contextlib import asynccontextmanager

from core.config import settings
from services.llm import summarize_text, generate_embedding
from services.qdrant import initialize_collection, insert_document
from services.scraper import extract_text_from_url
from services.web_search import fetch_urls_for_topic
from services.arxiv_fetcher import fetch_latest_arxiv_papers
from services.semantic_scholar_fetcher import fetch_latest_papers

# Lifespan context manager runs code right before the server starts
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure Qdrant is ready and formatted before taking requests
    await initialize_collection()
    yield

app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan)

# Data Model for our incoming request
class DocumentInput(BaseModel):
    text: str


@app.get("/")
async def root():
    return {
        "status": "online", 
        "message": f"Welcome to {settings.PROJECT_NAME}",
        "llm_model": settings.LLM_MODEL
    }

@app.post("/api/ingest-test")
async def ingest_test(doc: DocumentInput):
    """The Full Slice: Text -> Summary -> Vector -> Qdrant"""
    
    # 1. Summarize
    summary = await summarize_text(doc.text)
    
    # 2. Embed
    embedding = await generate_embedding(summary)
    
    # 3. Store
    doc_id = await insert_document(text=doc.text, summary=summary, embedding=embedding)
    
    return {
        "message": "Document successfully ingested",
        "doc_id": doc_id,
        "summary": summary
    }

@app.get("/health")
async def health_check():
    # Later, we will add Qdrant and Ollama ping checks here
    return {"status": "healthy"}

@app.post("/api/test-llm")
async def test_llm_pipeline(doc: DocumentInput):
    """Temporary endpoint to test Ollama summarization and embedding."""
    
    # 1. Summarize the text
    summary = await summarize_text(doc.text)
    
    # 2. Convert the summary into a vector
    embedding = await generate_embedding(summary)
    
    return {
        "original_length": len(doc.text),
        "summary": summary,
        # We just return the length of the embedding so we don't flood your screen with thousands of numbers
        "embedding_dimensions": len(embedding) 
    }
    
class URLInput(BaseModel):
    url: HttpUrl

@app.post("/api/summarize-url")
async def summarize_url_only(data: URLInput):
    """Temporary endpoint: Fetch URL -> Extract Text -> Summarize (No DB insertion)"""
    try:
        # 1. Scrape the clean text
        clean_text = await extract_text_from_url(str(data.url))
        
        # 2. Generate the summary
        summary = await summarize_text(clean_text)
        
        return {
            "url": str(data.url),
            "original_character_count": len(clean_text),
            "summary": summary
        }
        
    except ValueError as e:
        # Catch Trafilatura extraction failures
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        # Catch network errors (bad url, timeout, etc)
        raise HTTPException(status_code=400, detail=f"Failed to fetch URL: {str(e)}")    

class TopicInput(BaseModel):
    topic: str

@app.post("/api/research-topic")
async def research_topic(data: TopicInput):
    """Pipeline B: Topic -> Web Search -> Scrape"""
    
    # 1. Fetch URLs for the topic
    try:
        urls = await fetch_urls_for_topic(data.topic, max_results = 2)
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
        
    results = []
    
    # 2. Process each URL
    for url in urls:
        try:
            # Scrape
            clean_text = await extract_text_from_url(url)
            
            results.append({
                "url": url,
                "scraped_text_length": len(clean_text),
                "content_snippet": clean_text[:500] + "..."
            })
        except Exception as e:
            print(f"Failed to process {url}: {e}")
            continue
            
    return {
        "topic": data.topic,
        "successful_articles": len(results),
        "data": results
    }


@app.post("/api/research-arxiv")
async def research_arxiv(data: TopicInput): # Re-using the TopicInput from before
    """Pipeline A: Topic -> arXiv API -> Extract Abstract -> Summarize"""
    print(f"\n--- Starting arXiv Pipeline for: '{data.topic}' ---")
    
    try:
        # 1. Fetch the latest papers
        print("1. Fetching from arXiv API...")
        papers = await fetch_latest_arxiv_papers(data.topic, max_results=1)
        print(f"   [SUCCESS] Found {len(papers)} papers!")
    except Exception as e:
        print(f"   [FAILED] arXiv fetch failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"arXiv fetch failed: {str(e)}")
        
    print("--- Pipeline Finished! Returning data to user. ---\n")        
    return {
        "topic": data.topic,
        "papers_found": len(papers),
        "data": papers
    }
    
@app.post("/api/research-semantic-scholar")
async def research_semantic_scholar(data: TopicInput):
    """Pipeline B: Topic -> Semantic Scholar API -> Extract Abstract """
    print(f"\n--- Starting Semantic Scholar Pipeline for: '{data.topic}' ---")

    try:
        # 1. Fetch the latest papers
        print("1. Fetching from Semantic Scholar API...")
        papers = await fetch_latest_papers(data.topic, max_results=2)
        print(f"   [SUCCESS] Found {len(papers)} papers!")
    except Exception as e:
        print(f"   [FAILED] Semantic Scholar fetch failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Semantic Scholar fetch failed: {str(e)}")
        
    print("--- Pipeline Finished! Returning data to user. ---\n")        
    return {
        "topic": data.topic,
        "papers_found": len(papers),
        "data": papers
    }
