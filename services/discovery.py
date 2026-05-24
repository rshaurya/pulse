import asyncio

from services.llm import load_user_profile
from services.web_search import fetch_urls_for_topic
from services.crawler import fetch_and_extract_url
from services.openalex_fetcher import fetch_latest_papers
from services.rss_fetcher import fetch_all_rss_feeds
from services.processor import process_and_store_articles

async def run_master_discovery():
    print("\n[DISCOVERY] Waking up. Reading User Brain...")
    
    # Load updated profile
    profile = load_user_profile()
    interests = profile.get("core_interests", [])
    focus_areas = profile.get("summary_preferences", {}).get("focus_areas", [])
    
    # top 2 interests and top 1 focus area to prevent API overload
    topics_to_search = interests[:2] + focus_areas[:1]
    
    # Your curated list of high-signal blogs
    rss_feeds = [
        "https://openai.com/blog/rss.xml",
        "https://engineering.fb.com/feed/",
        "https://krebsonsecurity.com/feed/",
        "https://www.anthropic.com/research"
    ]
    
    print(f"[DISCOVERY] Scouting the web for: {topics_to_search}")
    
    # 2. Fan-Out: Launch all API queries simultaneously
    tasks = [
        fetch_all_rss_feeds(rss_feeds, max_per_feed=2)
    ]
    
    for topic in topics_to_search:
        tasks.append(fetch_latest_papers(topic, max_results=2))
        tasks.append(fetch_urls_for_topic(topic, max_results=2))
        
    # Wait for all APIs to reply
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    all_articles = []
    
    # 3. Standardize and collect results
    # results[0] is the RSS feed list
    if isinstance(results[0], list):
        all_articles.extend(results[0])
        
    # the rest are interleaved OpenAlex papers and Tavily URLs
    for i in range(1, len(results)):
        res = results[i]
        if isinstance(res, Exception):
            continue
            
        if isinstance(res, list):
            # If it's a dictionary with 'abstract', it's OpenAlex data
            if len(res) > 0 and isinstance(res[0], dict) and 'abstract' in res[0]:
                all_articles.extend(res)
            # If it's a list of strings, it's Tavily URLs that need crawling
            elif len(res) > 0 and isinstance(res[0], str):
                for url in res:
                    try:
                        # Extract clean text from the URL
                        article_data = await fetch_and_extract_url(url)
                        all_articles.append(article_data)
                    except Exception as e:
                        print(f"[DISCOVERY] Dropped un-crawlable URL {url}: {e}")
                        
    print(f"[DISCOVERY] Scout returned {len(all_articles)} total items. Handing off to Semaphore Orchestrator...")
    
    # 4. Pass the massive payload to the bounded processor
    if all_articles:
        await process_and_store_articles(all_articles)