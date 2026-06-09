# 🧠 PULSE: The Autonomous AI Knowledge Engine (v0.2)
under construction! still going on with a few enhancements. should be done soon :)

PULSE is a self-hosted, continuous-learning recommendation engine. It is your personal autonomous researcher, waking up daily, hunting the web and academic journals for content tailored to your exact interests, summarizing the noise, and delivering a highly personalized digest straight to your inbox.

**Link of PULSE goes here**

## The Story Behind PULSE

Keeping up with tech and AI research right now feels overwhelming (atleast for me).

Every day, there are lots of new papers, hundreds of blog posts, and thousands of tweets. I built PULSE because I was suffering from information overload. I didn't want to spend 2 hours a day scrolling through X or Reddit or the news trying to keep up with the industry. I wanted to automate it. 

I didn't go with news letters because I thought that I'll still miss something lol. I wanted information according to *my* *specific* current interests. (And I couldn't find a good resource to stay updated, if you are using something like that, please let me know). That's how PULSE was born. 

## v0.2 Upgrades  
The v0.2 release focuses on system resilience, data security, and multi-tenant scaling.
* **Passwordless Authentication:** Implemented a secure Magic Link (JWT) login system to eliminate password fatigue and securely establish user sessions.
* **API Encryption:** Third-party API keys (Groq, Tavily) are not stored in plain text. They are secured in PostgreSQL using an **AES-128 Fernet Encryption Engine** and are only decrypted into memory during a user's specific processing loop.
* **Decoupled Orchestration:** Ingestion (write path) and Retireval (read path) are fully separated. 
  * **2:00 AM UTC:** The autonomous crawler wakes up, decrypts keys, sends out API requests (RSS, OpenAlex, Tavily, Groq), processes embeddings, and stores vectors.
  * **6:00 AM UTC:** The Dispatcher wakes up, runs a semantic similarity search against Qdrant, filters out previously sent articles via a PostgreSQL ledger, and dispatches the email.
* **Resilient LLM Pipelines:** Built with Fault Isolation and Exponential Backoff in order to handle LLM provider rate limits (429s) without crashing the ingestion server.
* **Concept Drift (Sliding Window):** The user's  "brain" dynamically tunes itself based on feedback via email webhooks. To prevent LLM prompt bloat, the PostgreSQL arrays use a sliding window, automatically forgetting old interests as new ones are explored.
* **Semantic Gatekeeping:** Qdrant payload indexing (`user_id` as KEYWORD) guarantees O(1) lookup speeds, and a `0.40` Cosine Similarity threshold ensures the system refuses to send irrelevant articles.

## Tech Stack
* **API Framework:** FastAPI (Python 3.11)
* **Relational Database:** PostgreSQL & SQLModel (Connection Pooled)
* **Vector Database:** Qdrant (Semantic Search & Payloads)
* **Embeddings:** FastEmbed (384-dimensional vectors, running locally on CPU)
* **LLM Engine:** Groq API (Llama-3 for high-speed, low-cost summarization)
* **Task Scheduling:** APScheduler (Async Background Workers)
* **Infrastructure:** Docker & Docker Compose (Deployed on DigitalOcean)

## Past versions

* **v0.1 - The Personal Edition:** was geared toward people who were comfortable with local env setups. It lacked a GUI. One had to configure your "brain" using a local JSON file, and then boot the engine using Docker. This version had `.env` files, API keys, etc. and PULSE would run on their local machine.   

* **v0.2:** is for everyone :) v0.2 has a UI and is deployed fully. Other architectural upgrades are mentioned above.  

---

## How to Use PULSE

### Quick Start Setup

**1. Clone the repository**
```bash
git clone https://github.com/rshaurya/pulse.git
cd pulse
```

**2. Configure the Environment**  
Rename the `.env_template` file to `.env` and fill in your API keys (Groq, Tavily, Qdrant) and your SMTP Email credentials. And a newly generated 32-byte Base64 string for your ENCRYPTION_KEY (to lock the Fernet Vault).  

**3. Boot the Infrastructure**  
Spin up the FastAPI server and the PostgreSQL database in the background:
```bash
docker compose up -d --build
```

**4. Authenticate via Magic Link**
- Navigate to `http://localhost:8000/docs` in your browser.  
- Locate the `POST /api/auth/request` endpoint and enter your email address.  
- Check your terminal logs (or your email inbox) for the secure Magic Link. Click it to verify your session and generate your unique `user_id`.  

**5. Configure Your Brain**
- In the Swagger UI, locate the `PATCH /api/users/{user_id}/settings` endpoint.  
- Input your `user_id` and pass a JSON payload containing your personal Groq/Tavily API keys and an array of your `core_interests`.
- Note: Your API keys are instantly encrypted via AES-128 before saving to PostgreSQL.  

**6. Trigger the Engine**
By default, the internal APScheduler will run the Master Crawler at 2:00 AM UTC and the Email Dispatcher at 8:00 AM UTC.  
To test it immediately, manually trigger the `POST /api/ingest/autonomous` endpoint in Swagger UI to watch the engine decrypt your keys, scour the web, summarize the findings, and vault the vectors into Qdrant.

## File System Architecture
For those looking under the hood, the architecture is modular:

```
pulse/  
│  
├── core/                       # System Configurations & Database Schemas
│   ├── __init__.py  
│   ├── config.py               # Loads .env variables into a strict Pydantic Settings class  
│   ├── database.py             # PostgreSQL async engine and connection pooling
│   ├── models.py               # SQLModel schemas (User, UserProfile with JSONB, ArticleState)
│   └── security.py             # AES-128 Fernet Encryption Vault for API Keys
│  
├── scripts/                    # Standalone/Background Jobs  
│   ├── __init__.py  
│   └── dispatcher.py           # 8:00 AM Semantic Search & HTML Email Dispatcher
│
├── services/                   # ETL Pipeline (Extract, Transform, Load)  
│   ├── __init__.py  
│   ├── crawler.py              # Trafilatura web crawling & HTML stripping (Circuit Breaker)
│   ├── email.py                # SMTP dispatch & Passwordless Magic Link generation
│   ├── llm.py                  # Groq API summarization & FastEmbed local vectorization
│   ├── openalex_fetcher.py     # Academic paper ingestion track
│   ├── orchestrator.py         # Multi-Tenant Autonomous Agent (Fan-Out/Fan-In logic)
│   ├── processor.py            # Sequential LLM processing to prevent rate limits
│   ├── qdrant.py               # Vector database initialization & Payload indexing
│   ├── rss_fetcher.py          # Asynchronous XML feed parsing
│   ├── scraper.py              # Asynchronous text extraction from url
│   └── web_search.py           # Tavily discovery integration
│  
├── main.py                     # FastAPI entry point, Auth Webhooks, and APScheduler Clock
├── .env                        # Master keys and DB passwords   
├── .env_template               # Blank template for developers to fill out  
├── .gitignore                    
├── .dockerignore                    
├── docker-compose.yml          # Container orchestrator (FastAPI, Postgres)
├── Dockerfile                  # Container build instructions  
├── LICENSE                     # MIT License  
├── README.md                   # Project story, architecture, and setup guide  
└── requirements.txt            # Python dependencies
```

## The Future of PULSE (v0.3 and Beyond)
The below features will be implemented if user base becomes too large. 

**Upcoming Features:**

- With the web interface and core engine locked in, the next phase will focus on scaling: introducing Celery/Redis for distributed task queuing, and building a user analytics dashboard to visually map out how your interests have shifted over time.

## Support & Feedback 
**Not getting the results you want?**  
AI is unpredictable. If you are a researcher in a highly specific niche and PULSE isn't finding good articles or the summaries feel shallow, drop me an email at [shaurya.r.pethe@gmail.com](mailto:shaurya.r.pethe@gmail.com). I want to study your edge cases to make the extraction pipeline better.

**Open Source Contributions:**  
Contributions are most welcome. Please raise a detailed PR describing what it is that you would like to do (feature improvement, bug fix, new feature, etc.) 

# Thanks
A massive thank you to the open-source communities behind FastAPI, Trafilatura, Qdrant, and the OpenAlex initiative for making this kind of autonomous knowledge curation possible.  
(and thanks to my coffee too)
