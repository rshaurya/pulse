# 🧠 PULSE: The Autonomous AI Knowledge Engine (v0.2)

PULSE is a self-hosted, continuous-learning recommendation engine. It is your personal autonomous researcher, waking up daily, hunting the web and academic journals for content tailored to your exact interests, summarizing the noise, and delivering a highly personalized digest straight to your inbox.  


## v0.2 Upgrades  
The v0.2 release focuses on system resilience, data security, and multi-tenant scaling.
* **Passwordless Authentication:** Implemented a secure Magic Link (JWT) login system to eliminate password fatigue and securely establish user sessions.
* **API Encryption:** Third-party API keys (Groq, Tavily) are not stored in plain text. They are secured in PostgreSQL using an **AES-128 Fernet Encryption Engine** and are only decrypted into memory during a user's specific processing loop.
* **Decoupled Orchestration:** Ingestion (write path) and Retireval (read path) are fully separated. 
  * **2:00 AM UTC:** The autonomous crawler wakes up, decrypts keys, sends out API requests (RSS, OpenAlex, Tavily, Groq), processes embeddings, and stores vectors.
  * **6:00 AM UTC:** The Dispatcher wakes up, runs a semantic similarity search against Qdrant, filters out previously sent articles via a PostgreSQL ledger, and dispatches the email.
* **Resilient LLM Pipelines:** Built with Fault Isolation and Exponential Backoff in order to handle LLM provider rate limits (429s) without crashing the ingestion server.
* **Concept Drift (Sliding Window):** The user's  "brain" dynamically tunes itself based on feedback via email webhooks.  
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

* **v0.2:** is for everyone :) Other architectural upgrades are mentioned above.  

---

## How to Use PULSE

### Quick Start Setup

**1. Clone the repository**
```bash
git clone https://github.com/rshaurya/pulse.git
cd pulse
```

**2. Configure the Environment**  
Rename the `.env_template` file in the `backend/` folder  to `.env` and fill in your API keys (Qdrant Cloud, Qdrant). 
- Make sure you're in the `backend/` directory and run `pip install -r requirements.txt`    
- To generate your `JWT_SECRET_KEY`, run:
`python -c "import secrets; print(secrets.token_hex(32))"`   
- To generate your `ENCRYPTION_MASTER_KEY`, run:
`python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`  
- To get your `DATABASE_URL`, go to [neon.com](neon.com), sign up and create a new database and paste the url.  
!! Important changes to make:  
your url might look something like this `postgresql://neondb_owner:npg_iuebfyewb@siefbsbsjde.ap-southeast-2.aws.neon.tech/neondb?sslmode=require` (not exactly)  
you have to make the following changes:  
1. add `postgresql+asyncpg` before the `:`  
2. change `sslmode=require` (or whatever it is showing in your case) to `ssl=require`  

It is advised to leave the `LLM_API_KEY` and `TAVILY_API_KEY` as is.  


**3. Spin up Backend Server**  
Spin up the FastAPI server in the background:
```bash
cd backend
docker compose up -d --build
```

**5. Install Frontend Dependencies and Run Server**  
```bash
cd ../frontend
npm install
npm run dev
```  

**6. Usage**
You can interact with PULSE in two ways: through the Next.js UI (recommended), or directly via the Backend API documentation.  
- If using the UI, navigate to `http://localhost:3000` and enter your email. You will receive an authentication link. Click on it and you'll be taken to your dashboard where you'll have to enter Tavily API Key and Groq API Key (both of which are available for free on their respective websites). You're all set! wait for the digest to arrive at your inbox in the morning :)  

- If you're using the Swagger UI, navigate to `http://localhost:8000/docs` in your browser.  
- Locate the `POST /api/auth/request` endpoint and enter your email address.  
- Check your terminal logs (or your email inbox) for the secure Magic Link. Click it to verify your session and generate your unique `user_id`.  
- In the Swagger UI, locate the `PATCH /api/users/{user_id}/settings` endpoint.  
- Input your `user_id` and pass a JSON payload containing your personal Groq/Tavily API keys and an array of your `core_interests`.  
- Note: You can view the logs via this command: `docker logs -f pulse-app`  

By default, the internal APScheduler will run the Master Crawler at 2:00 AM UTC and the Email Dispatcher at 6:00 AM UTC.  
To test it immediately, manually trigger the `POST /api/ingest/autonomous` endpoint in Swagger UI to watch the engine decrypt your keys, scour the web, summarize the findings, and vault the vectors into Qdrant.  

## File System Architecture
For those looking under the hood, the architecture is modular:  
High Level Overview: 
```
pulse/
├── backend/                  # FastAPI Application Engine
│   ├── core/                 # DB connections, Security, Pydantic Models
│   ├── services/             # LLM logic, Scrapers, Qdrant setup, Email handlers
│   ├── scripts/              # Dispatchers and Cron job tasks
│   ├── main.py               # API Entry point and Scheduler
│   └── requirements.txt      # Python dependencies
│
├── frontend/                 # Next.js UI
│   ├── app/                  # App Router (pages, layouts, /verify routing)
│   ├── components/           # Reusable UI elements (Loaders, Dashboards)
│   ├── public/               # Static assets
│   ├── package.json          # Node dependencies
│   └── tailwind.config.ts    # Styling configurations
│
└── README.md
```

Backend folder:  
```
backend/  
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
├── .dockerignore                    
├── docker-compose.yml          # Container orchestrator (FastAPI, Postgres)
├── Dockerfile                  # Container build instructions  
└── requirements.txt            # Python dependencies
```
**Notes**  
While this is self hosted and runs locally, it does require one to keep their device (laptop or PC) up and running at all times. If, like me, you can't do that, I'd recommend forking this repo and connecting it to Render. The setup is pretty simple and straightforward. One additional thing you'd have to do is to set up cron jobs (I use [this](https://cron-job.org/en/)) every 14 minutes to your render web service to keep it up an running.   


## The Future of PULSE (v0.3 and Beyond)

**Upcoming Features:**

- With the web interface and core engine locked in, the next phase will focus on scaling: introducing Celery/Redis for distributed task queuing, and building a user analytics dashboard to visually map out how your interests have shifted over time. 
- Agents will be introduced to reason which article is the best according to the user's current interests before inserting the article to Groq  
- Implement parsing to extract text from websites without rss feeds  


## Support & Feedback 
**Not getting the results you want?**  
AI is unpredictable. If you are a researcher in a highly specific niche and PULSE isn't finding good articles or the summaries feel shallow, drop me an email at [shaurya.r.pethe@gmail.com](mailto:shaurya.r.pethe@gmail.com). I want to study your edge cases to make the extraction pipeline better.

**Open Source Contributions:**  
Contributions are most welcome. Please raise a detailed PR describing what it is that you would like to do (feature improvement, bug fix, new feature, etc.) 

## The Story Behind PULSE

Keeping up with tech and AI research right now feels overwhelming (atleast for me).

Every day, there are lots of new papers, hundreds of blog posts, and thousands of tweets. I built PULSE because I was suffering from information overload. I didn't want to spend 2 hours a day scrolling through X or Reddit or the news trying to keep up with the industry. I wanted to automate it. 

I didn't go with news letters because I thought that I'll still miss something lol. I wanted information according to *my* *specific* current interests. (And I couldn't find a good resource to stay updated, if you are using something like that, please let me know). That's how PULSE was born. 

# Thanks
A massive thank you to the open-source communities behind FastAPI, Trafilatura, Qdrant, and the OpenAlex initiative for making this kind of autonomous knowledge curation possible.  
(and thanks to my coffee too)
