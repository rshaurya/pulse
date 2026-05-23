import os
import json

from fastapi import BackgroundTasks, FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, HttpUrl
from contextlib import asynccontextmanager

from qdrant_client import AsyncQdrantClient

from core.config import settings
from services.llm import summarize_text, generate_embedding
from services.qdrant import initialize_collection, insert_document
from services.scraper import extract_text_from_url
from services.web_search import fetch_urls_for_topic
# from services.semantic_scholar_fetcher import fetch_latest_papers
from services.openalex_fetcher import fetch_latest_papers
from services.rss_fetcher import fetch_all_rss_feeds
from services.processor import process_and_store_articles
from services.crawler import fetch_and_extract_url

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

# @app.post("/api/ingest-test")
# async def ingest_test(doc: DocumentInput):
#     """The Full Slice: Text -> Summary -> Vector -> Qdrant"""
    
#     # 1. Summarize
#     summary = await summarize_text(doc.text)
    
#     # 2. Embed
#     embedding = await generate_embedding(summary)
    
#     # 3. Store
#     doc_id = await insert_document(title = doc.title ,text=doc.text, summary=summary, embedding=embedding)
    
#     return {
#         "message": "Document successfully ingested",
#         "doc_id": doc_id,
#         "summary": summary
#     }

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
async def research_topic(data: TopicInput, background_tasks: BackgroundTasks):
    """Pipeline B: Topic -> Web Search -> Scrape"""
    
    # 1. Fetch URLs for the topic
    try:
        urls = await fetch_urls_for_topic(data.topic, max_results = 2)
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
        
    articles_to_queue = []
    
    # 2. Process each URL
    for url in urls:
        try:
            # Scrape
            clean_text = await extract_text_from_url(url)
            
            articles_to_queue.append({
                "url": url,
                "scraped_text_length": len(clean_text),
                "content_snippet": clean_text[:3000] + "..."
            })
        except Exception as e:
            continue
            
    return {
        "topic": data.topic,
        "successful_articles": len(articles_to_queue),
        "data": articles_to_queue
    }


@app.post("/api/research-openalex")    
async def research_openalex(data: TopicInput, background_tasks: BackgroundTasks):
    """Pipeline B: Topic -> OpenAlex API -> Extract Abstract """

    try:
        # 1. Fetch the latest papers
        papers = await fetch_latest_papers(data.topic, max_results=2)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OpenAlex fetch failed: {str(e)}")
        
    if papers:
        background_tasks.add_task(process_and_store_articles, papers)
        
    return {
        "topic": data.topic,
        "papers_found": len(papers),
        "data": papers
    }
    
@app.post("/api/research-rss")
async def research_rss(background_tasks: BackgroundTasks):
    """Pipeline C: Direct RSS Track -> Extract Content (Queued for LLM later)"""
    
    # my list of important sources (change as per your interests!)
    target_feeds = [
        "https://openai.com/blog/rss.xml",              # OpenAI Official Blog
        "https://engineering.fb.com/feed/",             # Meta Engineering
        "https://krebsonsecurity.com/feed/"             # Top Cybersecurity Blog
    ]
    
    # Fetch all feeds at exactly the same time
    articles = await fetch_all_rss_feeds(target_feeds, max_per_feed=2)
    
    # background task to summarise and upsert to Qdrant
    background_tasks.add_task(process_and_store_articles, articles)
    
    # redis_queue.enqueue("summarize_task", articles)
    
    return {
        "feeds_checked": len(target_feeds),
        "articles_found": len(articles),
        "data": articles
    }    
    
class URLPayload(BaseModel):
    url: str

@app.post("/api/ingest-url")
async def ingest_url_endpoint(payload: URLPayload):
    try:
        # Step 1: Crawl and Extract
        article_data = await fetch_and_extract_url(payload.url)
        
        # Step 2: The Brain (Groq Summarization)
        summary = await summarize_text(article_data["text"])
        
        # Step 3: The Calculator (FastEmbed Vectorization)
        vector = await generate_embedding(summary)
        
        # Step 4: The Gatekeeper (Qdrant Storage)
        # Note: In the future we will pass the URL as metadata here!
        doc_id = await insert_document(
            title=article_data["title"],
            url=article_data["url"],
            text=article_data["text"],
            summary=summary,
            embedding=vector
        )
        
        return {
            "status": "success", 
            "message": "URL crawled, summarized, and stored successfully!",
            "title": article_data["title"],
            "doc_id": doc_id
        }
        
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/api/feedback", response_class=HTMLResponse)

async def register_feedback(doc_id: str = Query(...), action: str = Query(...)):
    """Webhook to receive user feedback directly from the email digest."""
    
    print(f"[WEBHOOK] Received feedback: {action} for Document ID: {doc_id}")
    
    client = AsyncQdrantClient(url=settings.QDRANT_URL, api_key=settings.QDRANT_API_KEY)
    
    try:
        points = await client.retrieve(
            collection_name=settings.COLLECTION_NAME,
            ids=[doc_id],
            with_payload=True
        )
        
        if not points:
            return "<html><body><h3>Error: Article not found in database.</h3></body></html>"
            
        article_title = points[0].payload.get("title", "this topic")
        
        # 2. Open the User Profile Brain
        profile_path = os.path.join(os.path.dirname(__file__), "user_profile.json")
        with open(profile_path, "r") as f:
            profile = json.load(f)
            
        # 3. Adjust the Brain based on the click
        if action == "explore":
            # Add it to focus areas if it isn't already there
            if article_title not in profile["summary_preferences"]["focus_areas"]:
                profile["summary_preferences"]["focus_areas"].append(article_title)
            response_text = f"<h3>Feedback Logged!</h3><p>PULSE will actively hunt for more technical depth regarding: <b>{article_title}</b></p>"
            
        elif action == "prune":
            # Add a strict negative constraint to the system prompt
            if "avoid_topics" not in profile["summary_preferences"]:
                profile["summary_preferences"]["avoid_topics"] = []
            if article_title not in profile["summary_preferences"]["avoid_topics"]:
                profile["summary_preferences"]["avoid_topics"].append(article_title)
            response_text = f"<h3>Topic Pruned.</h3><p>PULSE will filter out articles related to: <b>{article_title}</b></p>"
            
        # 4. Save the Brain back to the hard drive
        with open(profile_path, "w") as f:
            json.dump(profile, f, indent=4)
            
        return f"<html><body style='font-family: sans-serif; padding: 40px; text-align: center;'>{response_text}</body></html>"
        
    except Exception as e:
        print(f"[WEBHOOK] CRITICAL ERROR: {e}")
        return "<html><body><h3>System Error logging feedback.</h3></body></html>"
    
