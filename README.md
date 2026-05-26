# 🧠 PULSE: The Autonomous AI Knowledge Engine (v0.1)

PULSE is a self-hosted, continuous-learning recommendation engine. It is your personal autonomous researcher, waking up daily, hunting the web and academic journals for content tailored to your exact interests, summarizing the noise, and delivering a highly personalized digest straight to your inbox.

## 📖 The Story Behind PULSE

Keeping up with tech and AI research right now feels overwhelming (atleast for me).

Every day, there are lots of new papers, hundreds of blog posts, and thousands of tweets. I built PULSE because I was suffering from severe information overload. I didn't want to spend 2 hours a day scrolling through X or HackerNews trying to find signal in the noise. I wanted a machine to do it for me. 

I didn't want a generic newsletter. I wanted an AI that deeply understood *my* *specific* current interests, read the internet for me, dropped the garbage content, and gave me just the technical abstracts I actually needed to learn (And I couldn't find a good resource to stay updated, if you are using something like that, please let me know). That's how PULSE was born.  

## 🎯 Who is this for? (v0.1 Personal Edition)

Currently, PULSE is heavily geared toward **Developers and Researchers, tech people in general**. 

Because this is the "Personal Edition" (v0.1), there is no graphical user interface (GUI) yet. You configure your "brain" using a local JSON file, and you boot the engine using Docker. If you are comfortable with `.env` files, API keys, and terminals, you can have this running on your local machine in a few minutes.

---

## ⚙️ How to Use PULSE

### The Tech Stack
* **Backend:** FastAPI (Python)
* **LLM Engine:** Groq
* **Vector Database:** Qdrant
* **Discovery:** Tavily API & OpenAlex API

### Quick Start Setup

**1. Clone the repository**
```bash
git clone https://github.com/rshaurya/pulse.git
cd pulse
```

**2. Configure the Environment**  
Rename the `.env_template` file to `.env` and fill in your API keys (Groq, Tavily, Qdrant) and your SMTP Email credentials.

**3. Define your Brain**  
Open `user_profile.json` and type in your core technical interests, your specific focus areas, any RSS feeds you want PULSE to monitor with other details mentioned in the file.

**4. Boot the Engine**
```bash
docker-compose up -d --build
```
PULSE will now run in the background. The internal scheduler will automatically trigger the crawler based on your code settings.

## 📂 File System Architecture
For those looking under the hood, the architecture is modular:

```
pulse/  
│  
├── core/                       # System Configurations  
│   ├── __init__.py  
│   └── config.py               # Loads .env variables into a Pydantic Settings class  
│  
├── scripts/                    # Standalone/Background Jobs  
│   ├── __init__.py  
│   └── dispatcher.py           # Email dispatch script  
│
├── services/                   # The ETL Pipeline (Extract, Transform, Load)  
│   ├── __init__.py  
│   ├── crawler.py              # Single URL extraction   
│   ├── discovery.py            # RSS feeds, papers and url extraction from the web  
│   ├── email.py                # HTML formatting and SMTP dispatch  
│   ├── llm.py                  # Groq summarization and embeddings  
│   ├── openalex_fetcher.py     # Academic paper ingestion  
│   ├── orchestrator.py         # The Autonomous Agent (Fan-Out/Fan-In logic)  
│   ├── processor.py            # Sequential LLM processing   
│   ├── qdrant.py               # Vector database logic  
│   ├── rss_fetcher.py          # Asynchronous XML feed parsing  
│   ├── scraper.py              # Extraction of text from a given url  
│   └── web_search.py           # Tavily discovery integration  
│  
├── .env                        # Your actual API keys (DO NOT COMMIT to GitHub)  
├── .env_template               # Blank template for new users to fill out  
├── .gitignore                    
├── docker-compose.yml          # Container orchestrator  
├── Dockerfile                  # Container build instructions  
├── LICENSE                     # MIT License  
├── main.py                     # FastAPI server  
├── README.md                   # Project story, architecture, and setup guide  
├── requirements.txt            # Python dependencies  
└── user_profile.json           # The dynamic AI "Brain" (Mapped via Docker Volume)  
```

## 🚀 The Future of PULSE (v0.2 and Beyond)
This v0.1 release is for people in the technical field. But I am already building the next version. PULSE will soon be available for everyone, irrespective of their field.

**Upcoming Features:**

- Clean Frontend UI hosted on cloud. accessible to anyone.

- PostgreSQL Integration: Keeping your API keys, personal profile and emails safe.

- Weekly Batch Updates: A smarter, slower-moving recommendation algorithm to prevent recency bias.

- And a few others I'm not able to name :)

## 📬 Get Early Access to the Next Version
If you are a non-technical user, or you just want to wait for the web app version of PULSE,  
[Send me an email here](mailto:shaurya.r.pethe@gmail.com). I will notify you the moment the cloud version goes live. (the email donesn't have to be anything fancy. Just send the field you're working in or have interest in).

## 🤝 Support & Feedback 
**Not getting the results you want?**  
AI is unpredictable. If you are a researcher in a highly specific niche and PULSE isn't finding good articles or the summaries feel shallow, drop me an email at [shaurya.r.pethe@gmail.com](mailto:shaurya.r.pethe@gmail.com). I want to study your edge cases to make the extraction pipeline better.

**Open Source Contributions:**  
Currently, pull requests are closed because I will be  working on the features mentioned above for v0.2. 
Code contributions will officially open with the release of v0.2.

# 🙏 Thanks
A massive thank you to the open-source communities behind FastAPI, Trafilatura, Qdrant, and the OpenAlex initiative for making this kind of autonomous knowledge curation possible.
