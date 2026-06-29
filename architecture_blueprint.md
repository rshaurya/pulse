# Architecture Blueprint: Personalized AI Knowledge Engine

## 1. System Overview
A self-hosted, continuous-learning recommendation engine that curates, summarizes, and delivers a highly personalized daily email digest. The system learns passively through granular user feedback on the daily emails, actively tuning its ingestion, summarization depth, and recommendation algorithms without requiring manual intervention.

**Core Stack:**
* **Backend Framework:** FastAPI (Python)
* **Local LLM:** Ollama (for zero-cost summarization and NLP tasks)
* **Vector Database:** Qdrant (for semantic search, recommendation API, and deduplication)
* **Task Scheduling:** Cron / APScheduler (Daily 2 AM execution)

---

## 2. The Hybrid Ingestion Pipeline
To bypass social media scraping restrictions and API paywalls while maintaining high signal-to-noise ratio, data is fetched concurrently from three distinct sources.

### Pipeline A: The Academic Track
* **Purpose:** Deep, peer-reviewed knowledge and highly technical research.
* **Sources:** arXiv API, Semantic Scholar API.
* **Mechanism:** Queries based on active advanced interests in the user's vector profile. Free and highly structured.

### Pipeline B: The Web Track
* **Purpose:** Broad industry news, trending development blogs, and tutorials.
* **Sources:** Tavily API (Free Tier) / NewsAPI.
* **Mechanism:** Searches the broader web for general topics. Returns clean, parsed text content optimized for LLM ingestion.

### Pipeline C: The Direct RSS Track
* **Purpose:** High-fidelity, user-curated specific domains.
* **Sources:** Python `feedparser` querying custom RSS XML feeds (e.g., specific cybersecurity or engineering blogs).
* **Mechanism:** Zero-cost, guaranteed retrieval of favorite authors or domains.

*Execution:* All three pipelines fire simultaneously at 2:00 AM daily, dumping raw text into a combined Candidate Pool.

---

## 3. Context-Aware Summarization (Ollama)
Instead of generic summaries, the local LLM tailors its output to the user's current technical standing.

* **The Living System Prompt:** The FastAPI backend maintains a `user_profile.json` detailing the user's skills (e.g., "Proficient in Python, building RAG architectures").
* **Dynamic Injection:** When Ollama is called to summarize a candidate article, the system prompt is injected to ensure the LLM skips beginner definitions and focuses purely on advanced architectural insights or relevant data.

---

## 4. Vector Filtering & Recommendation (Qdrant)
Qdrant acts as the absolute gatekeeper, ensuring only 3-5 highly relevant articles reach the user's inbox daily.

* **State Tracking (Solving Repetition):** Once an article is embedded and emailed, its metadata payload in Qdrant is updated with `{"emailed": true}`. Future queries apply a strict filter (`must_not`) against this flag.
* **The Recommendation API:** Uses Qdrant's native `recommend()` endpoint, accepting `positive` and `negative` vectors based on user feedback to mathematically shift the search space.

---

## 5. The Daily Digest & Granular Feedback Loop
The user receives a daily email containing 3-5 summaries and links of the respective source. Each summary includes specific action buttons that hit FastAPI webhooks to adjust the system.

### The Feedback Webhooks:
1.  **"Interesting" (The Maintainer)**
    * *Intent:* "Keep this in my general orbit."
    * *Action:* Submits the article's vector ID to Qdrant as a `positive` example. Maintains current vector center of gravity.
2.  **"Would like to know more about this" (The Explorer)**
    * *Intent:* "Dive deeper into this specific rabbit hole."
    * *Action:* Submits a `positive` vector to Qdrant AND updates `user_profile.json` to instruct the LLM to look for deeper/advanced content on this extracted topic in future runs.
3.  **"Show fewer articles like this" (The Pruner)**
    * *Intent:* "I'm bored of this / Irrelevant."
    * *Action:* Submits the article's vector ID to Qdrant as a strict `negative` example, pushing future queries away from this cluster.

---

## 6. Mitigating Concept Drift (Recency Bias)
To ensure the system evolves as the user's interests change (e.g., dropping a topic after a month):

* **30-Day Sliding Window:** The Qdrant recommendation calculations and `user_profile.json` updates are weighted to heavily favor interactions from the last 30 days.
* **Graceful Forgetting:** If a user stops clicking "Interesting" on a once-favorite topic, those older positive vectors naturally age out of the sliding window. The topic gently fades from the daily digest without requiring explicit negative feedback.

and if the user adds more resources of their interest, those sources will go through the same pipeline every week or every 3 days. basically, user's json file will be updated every week.
