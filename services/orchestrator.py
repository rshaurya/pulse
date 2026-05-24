import os
import json
import asyncio
from typing import List

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
    """The True Web Crawler: Reads the profile, hunts for data, and processes it."""
    print("[AUTONOMOUS CRAWLER] Waking up. Reading User Brain...")
    
    # 1. READ THE BRAIN
    profile_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "user_profile.json")
    try:
        with open(profile_path, "r") as f:
            profile = json.load(f)
    except Exception as e:
        print(f"[AUTONOMOUS CRAWLER] CRITICAL: Could not load user profile. {e}")
        return

    # Combine core interests and focus areas
    topics = profile.get("core_interests", []) + profile.get("summary_preferences", {}).get("focus_areas", [])
    
    # Let's assume you add an "rss_feeds" array to your JSON in the future. 
    # For now, we default to an empty list if it's not there.
    rss_feeds = profile.get("rss_feeds", []) 
    
    if not topics and not rss_feeds:
        print("[AUTONOMOUS CRAWLER] No topics or feeds found in profile. Going back to sleep.")
        return

    print(f"[AUTONOMOUS CRAWLER] Hunting for topics: {topics}")

    # 2. DISCOVERY PHASE: Find the URLs and Papers concurrently
    print("[AUTONOMOUS CRAWLER] Phase 1: Discovery (Tavily & OpenAlex)...")
    search_tasks = [fetch_urls_for_topic(topic, max_results=2) for topic in topics]
    paper_tasks = [fetch_latest_papers(topic, max_results=2) for topic in topics]
    
    # Gather discovery results
    discovered_url_lists = await asyncio.gather(*search_tasks, return_exceptions=True)
    discovered_papers_lists = await asyncio.gather(*paper_tasks, return_exceptions=True)
    
    # Flatten the list of lists into a single list of URLs
    target_urls = []
    for url_list in discovered_url_lists:
        if isinstance(url_list, list):
            target_urls.extend(url_list)

    # 3. EXTRACTION PHASE: Download the webpage text and RSS feeds
    print(f"[AUTONOMOUS CRAWLER] Phase 2: Extraction. Fetching {len(target_urls)} URLs and {len(rss_feeds)} Feeds...")
    url_fetch_tasks = [safe_fetch_url(url) for url in target_urls]
    rss_task = fetch_all_rss_feeds(rss_feeds, max_per_feed=2) if rss_feeds else None
    
    url_results = await asyncio.gather(*url_fetch_tasks, return_exceptions=True)
    
    rss_results = []
    if rss_task:
        try:
            rss_results = await rss_task
        except Exception as e:
            print(f"[RSS ERROR] {e}")

    # 4. AGGREGATION & CIRCUIT BREAKERS
    final_articles = []
    
    # Add surviving Web URLs
    for res in url_results:
        if isinstance(res, dict): 
            final_articles.append(res)
            
    # Add surviving Academic Papers
    for paper_list in discovered_papers_lists:
        if isinstance(paper_list, list):
            for paper in paper_list:
                if len(paper.get("abstract", "")) > 100:
                    final_articles.append(paper)

    # Add surviving RSS Feeds
    for article in rss_results:
        if len(article.get("content_snippet", "")) > 100:
            final_articles.append(article)

    if not final_articles:
        print("[AUTONOMOUS CRAWLER] No valid articles survived extraction. Aborting.")
        return

    print(f"[AUTONOMOUS CRAWLER] Extraction complete. {len(final_articles)} high-quality articles survived.")
    
    # 5. SEQUENTIAL PROCESSING (The LLM Summarizer)
    print("[AUTONOMOUS CRAWLER] Handing over to sequential LLM processor...")
    await process_and_store_articles(final_articles)
    print("[AUTONOMOUS CRAWLER] Run complete. Going back to sleep.")