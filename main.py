from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl
from contextlib import asynccontextmanager

from core.config import settings
from services.llm import summarize_text, generate_embedding
from services.qdrant import initialize_collection, insert_document
from services.scraper import extract_text_from_url
from services.web_search import fetch_urls_for_topic
from services.arxiv_fetcher import fetch_latest_arxiv_papers

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
    """Pipeline B: Topic -> Web Search -> Scrape -> Summarize"""
    
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
            
            # truncate text for TESTING only - remove this in production 
            truncated_text = clean_text[:3000]
            
            # Summarize
            summary = await summarize_text(truncated_text)
            
            results.append({
                "url": url,
                "summary": summary
            })
        except Exception as e:
            # If one URL fails to scrape, we just skip it and move to the next one
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
    
    try:
        # 1. Fetch the latest papers
        papers = await fetch_latest_arxiv_papers(data.topic)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"arXiv fetch failed: {str(e)}")
        
    results = []
    
    # 2. Process the abstracts through our LLM
    for paper in papers:
        try:
            # we skip the scraper entirely. just summarize the abstract.
            prompt_text = f"Title: {paper['title']}\nAbstract: {paper['abstract']}"
            summary = await summarize_text(prompt_text)
            
            results.append({
                "title": paper["title"],
                "url": paper["url"],
                "published_date": paper["published"],
                "ai_summary": summary
            })
        except Exception as e:
            print(f"Failed to process paper {paper['title']}: {e}")
            continue
            
    return {
        "topic": data.topic,
        "papers_found": len(results),
        "data": results
    }
