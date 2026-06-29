import os
import json
import asyncio
from typing import List

from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from sqlalchemy.orm import sessionmaker

from core.database import engine
from core.models import User, UserProfile
from core.security import decrypt_api_key

from services.crawler import fetch_and_extract_url
from services.openalex_fetcher import fetch_latest_papers
from services.rss_fetcher import fetch_all_rss_feeds
from services.processor import process_and_store_articles
from services.web_search import fetch_urls_for_topic


async def safe_fetch_url(url: str) -> dict:
    """Wraps your crawler with a Circuit Breaker to prevent garbage data."""
    try:
        data = await fetch_and_extract_url(url)
        text = data.get("text", "")
        
        # CIRCUIT BREAKER 1: Too short
        if len(text) < 300:
            print(f"[CIRCUIT BREAKER] Dropped {url}: Text too short ({len(text)} chars).")
            return None
            
        # CIRCUIT BREAKER 2: Paywall detection
        paywall_flags = ["please log in", "access denied", "enable javascript", "subscribe to read"]
        if any(flag in text.lower() for flag in paywall_flags):
            print(f"[CIRCUIT BREAKER] Dropped {url}: Paywall detected.")
            return None
            
        return {
            "title": data.get("title", "Unknown Webpage"),
            "url": data.get("url", url),
            "abstract": text 
        }
    except Exception as e:
        print(f"[CRAWLER ERROR] Failed on {url}: {e}")
        return None

async def run_autonomous_crawler():
    """Multi-Tenant Engine which loops through all users, decrypts keys and runs personalised pipelines"""
    print("[AUTONOMOUS CRAWLER] Waking up. Fetching all active users from PostgreSQL...")
    
    # Create a background database session
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Fetch all users who actually have an LLM API key saved
        statement = select(User).where(User.encrypted_llm_api_key != None)
        result = await session.execute(statement)
        active_users = result.scalars().all()
        
        if not active_users:
            print("[AUTONOMOUS CRAWLER] No active users with API keys found. Going back to sleep.")
            return

        print(f"[AUTONOMOUS CRAWLER] Found {len(active_users)} active users. Commencing extraction...")

        # Loop through every user sequentially
        # TODO: find a better method for search. this might break with large number of users
    for user in active_users:
        print(f"\n{'='*50}\n[CRAWLING FOR USER]: {user.email}\n{'='*50}")
        
        # Fetch their Brain
        profile_statement = select(UserProfile).where(UserProfile.user_id == user.id)
        profile_result = await session.execute(profile_statement)
        profile = profile_result.scalars().first()
    
        if not profile:
            continue

        # Decrypt their API keys
        llm_key = decrypt_api_key(user.encrypted_llm_api_key)
        tavily_key = decrypt_api_key(user.encrypted_tavily_api_key)
        
        # Combine core interests and focus areas
        topics = profile.core_interests + profile.focus_areas
        rss_feeds = profile.rss_feeds
        
        if not topics and not rss_feeds:
            print(f"[SKIP] User {user.email} has no topics configured.")
            continue

        # DISCOVERY PHASE (Pass the decrypted Tavily key)
        print(f"[PHASE 1] Discovering URLs for {user.email}...")
        search_tasks = [fetch_urls_for_topic(topic, tavily_key) for topic in topics] if tavily_key else []
        paper_tasks = [fetch_latest_papers(topic) for topic in topics]
        rss_tasks = [fetch_all_rss_feeds(rss_feeds, max_per_feed=2)] if rss_feeds else []
        
        discovered_url_lists = await asyncio.gather(*search_tasks, return_exceptions=True)
        discovered_papers_lists = await asyncio.gather(*paper_tasks, return_exceptions=True)
        discovered_rss_lists = await asyncio.gather(*rss_tasks, return_exceptions=True)
        
        target_urls = []
        for url_list in discovered_url_lists:
            if isinstance(url_list, list):
                target_urls.extend(url_list)
                
        for rss_list in discovered_rss_lists:
            if isinstance(rss_list, list):
                target_urls.append(rss_list)

        # EXTRACTION PHASE
        print(f"[PHASE 2] Extracting Text for {user.email}...")
        url_fetch_tasks = [safe_fetch_url(url) for url in target_urls]
        url_results = await asyncio.gather(*url_fetch_tasks, return_exceptions=True)
        
        # Consolidate surviving articles
        final_articles = []
        for res in url_results:
            if isinstance(res, dict): final_articles.append(res)
        for paper_list in discovered_papers_lists:
            if isinstance(paper_list, list):
                for paper in paper_list:
                    if len(paper.get("abstract", "")) > 100: final_articles.append(paper)

        if not final_articles:
            print(f"[ABORT] No valid articles survived for {user.email}.")
            continue
        
        topics = profile.core_interests + profile.focus_areas
        context_string = ", ".join(topics)
        
        # PROCESSING PHASE
        print(f"[PHASE 3] Summarizing and Vaulting data for {user.email}...")
        # Hand the decrypted LLM key to the processor so Groq bills the user, not you!
        await process_and_store_articles(final_articles, user_id=user.id, llm_api_key=llm_key, user_context=context_string)
            
    print("\n[AUTONOMOUS CRAWLER] Global run complete. Going back to sleep.")