import os
import json

from typing import List, Optional
from fastapi import BackgroundTasks, FastAPI, HTTPException, Query, Depends
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, HttpUrl
from contextlib import asynccontextmanager
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from qdrant_client import AsyncQdrantClient
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from core.config import settings
from core.models import SQLModel, User, UserProfile
from core.database import engine, get_session
from core.security import create_magic_token, verify_magic_token

from services.llm import summarize_text, generate_embedding
from services.qdrant import initialize_collection, insert_document
from services.scraper import extract_text_from_url
from services.web_search import fetch_urls_for_topic
from services.openalex_fetcher import fetch_latest_papers
from services.rss_fetcher import fetch_all_rss_feeds
from services.processor import process_and_store_articles
from services.crawler import fetch_and_extract_url
from services.orchestrator import run_autonomous_crawler
from services.email import send_magic_link_email

from scripts.dispatcher import generate_daily_digest

scheduler = AsyncIOScheduler()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager to handle startup and shutdown events."""
    print("[SYSTEM] Booting up PULSE Automation Heartbeat...")
    
    await initialize_collection()
    
    print("[DATABASE] Ensuring PostgreSQL tables exist...")
    async with engine.begin() as conn:
        # This looks at models.py and automatically creates the tables if they don't exist!
        await conn.run_sync(SQLModel.metadata.create_all)
    
    # THE SCHEDULE: 
    # For testing right now, we will set it to run every 2 minutes.
    scheduler.add_job(
        generate_daily_digest, 
        trigger='interval', 
        minutes=2, 
        id="test_digest_job",
        replace_existing=True
    )

    # uncomment below line and comment the above scheduler.add_job in prod
    # scheduler.add_job(generate_daily_digest, trigger=CronTrigger(hour=7, minute=0), id="daily_digest_job")
    
    scheduler.start()
    print("[SYSTEM] Scheduler running. Waiting for next tick...")
    
    yield
    
    print("[SYSTEM] Shutting down Scheduler...")
    scheduler.shutdown()


app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan)

@app.get("/")
async def root():
    return {
        "status": "online", 
        "message": f"Welcome to {settings.PROJECT_NAME}",
        "llm_model": settings.LLM_MODEL
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Data models for API endpoints
class URLInput(BaseModel):
    url: HttpUrl

class TopicInput(BaseModel):
    topic: str
    
class URLPayload(BaseModel):
    url: str
    
class MasterIngestPayload(BaseModel):
    urls: Optional[List[str]] = []
    topics: Optional[List[str]] = [] 
    rss_feeds: Optional[List[str]] = []
    
class MagicLinkRequest(BaseModel):
    email: str


# API Endpoints


# Endpoint to search for articles / blogs / resources of a topic using web search and scrape the top results
@app.post("/api/research-topic-on-web")
async def research_topic(data: TopicInput, background_tasks: BackgroundTasks):
    """Topic -> Web Search -> Get Links -> Scrape"""
    
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


# Endpoint to fetch latest papers from OpenAlex API on given topic and extract abstracts (if available)
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

# Endpoint to fetch and process articles from RSS feeds of important blogs    
@app.post("/api/research-rss")
async def research_rss(background_tasks: BackgroundTasks):
    """Pipeline C: Direct RSS Track -> Extract Content (Queued for LLM later)"""
    
    # my list of important sources (change as per your interests!)
    target_feeds = [
        "https://openai.com/blog/rss.xml",              # OpenAI Official Blog
        "https://engineering.fb.com/feed/",             # Meta Engineering
        "https://krebsonsecurity.com/feed/"             # Top Cybersecurity Blog
        # add anthropic blog, google ai blog, arxiv cs rss feed, etc. as per your interests!
        # ADD OTHER MAJOR BLOGS HERE!
    ]
    
    articles = await fetch_all_rss_feeds(target_feeds, max_per_feed=2)
    
    # background task to summarise and upsert to Qdrant
    background_tasks.add_task(process_and_store_articles, articles)
    
    # redis_queue.enqueue("summarize_task", articles)
    
    return {
        "feeds_checked": len(target_feeds),
        "articles_found": len(articles),
        "data": articles
    }    
    

# Endpoint that takes any user-provided URL and scrapes the text
@app.post("/api/ingest-url")
async def ingest_url_endpoint(payload: URLPayload):
    try:
        # Crawl and Extract
        article_data = await fetch_and_extract_url(payload.url)
        
        # summarization
        summary = await summarize_text(article_data["text"])
        
        # FastEmbed embeddings
        vector = await generate_embedding(summary)
        
        # Qdrant Storage
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


# Endpoint to receive user feedback from email interactions and update the user_profile.json accordingly
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
        
        profile_path = os.path.join(os.path.dirname(__file__), "user_profile.json")
        with open(profile_path, "r") as f:
            profile = json.load(f)
            
        # adjust the user_profile.json based on the click
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
            
        with open(profile_path, "w") as f:
            json.dump(profile, f, indent=4)
            
        return f"<html><body style='font-family: sans-serif; padding: 40px; text-align: center;'>{response_text}</body></html>"
        
    except Exception as e:
        print(f"[WEBHOOK] CRITICAL ERROR: {e}")
        return "<html><body><h3>System Error logging feedback.</h3></body></html>"

@app.post("/api/ingest/autonomous")
async def trigger_autonomous_crawler(background_tasks: BackgroundTasks):
    """Acts as a manual trigger for the autonomous web crawler."""
    
    # Fire and Forget: Wake up the agent in the background
    background_tasks.add_task(run_autonomous_crawler)
    
    return {
        "status": "processing", 
        "message": "Autonomous Crawler triggered. It is currently reading user_profile.json and hunting for data."
    }

@app.post("/api/auth/request")
async def request_magic_link(
    payload: MagicLinkRequest, 
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session)
):
    """Generates the VIP pass and 'emails' it to the user."""
    
    email = payload.email.lower().strip()
    
    # Does this user exist in db
    statement = select(User).where(User.email == email)
    result = await session.exec(statement)
    user = result.one_or_none()
    
    # If they don't exist, create an account for them automatically!
    if not user:
        print(f"[AUTH] Creating new account for {email}")
        user = User(email=email)
        session.add(user)
        await session.commit()
        await session.refresh(user)
        
        # Create a blank JSON use profile 
        profile = UserProfile(user_id=user.id)
        session.add(profile)
        await session.commit()

    # Create the cryptographic token
    token = create_magic_token(email)
    
    # Construct the Magic Link
    # In production, this will be frontend URL (e.g., https://pulse.com/verify?token=...)
    magic_link = f"http://localhost:8000/api/auth/verify?token={token}"
    
    # TODO: email this link using services/email.py!
    # right now, print it to the terminal so we can click it
    print(f"\\n{'='*50}\\n[MAGIC LINK FOR {email}]:\\n{magic_link}\\n{'='*50}\\n")
    
    background_tasks.add_task(send_magic_link_email, email, magic_link)
    
    return {"status": "success", "message": "Check your email for the magic link!"}
    


@app.get("/api/auth/verify")
async def verify_login(token: str, session: AsyncSession = Depends(get_session)):
    """The user clicks the link in their email and hits this endpoint."""
    
    # check the token
    email = verify_magic_token(token)
    
    if not email:
        raise HTTPException(status_code=401, detail="Link is invalid or has expired.")
        
    statement = select(User).where(User.email == email)
    result = await session.exec(statement)
    user = result.one_or_none()
    
    if not user:
         raise HTTPException(status_code=404, detail="User not found.")
    
    return {
        "status": "authenticated", 
        "user_id": str(user.id),
        "email": user.email,
        "message": "Welcome to PULSE. You are securely logged in."
    }