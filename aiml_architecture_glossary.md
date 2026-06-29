# AIML & System Architecture Glossary
*A deep-dive study guide for building the Personalized AI Knowledge Engine.*

## 1. Vector Databases & Information Retrieval

* **Vector Embeddings:** Dense mathematical representations (arrays of floats) of text, images, or audio. They capture semantic meaning, allowing machines to understand that "puppy" and "dog" are mathematically close, even if the letters are different.
* **Cosine Similarity & Euclidean Distance:** The mathematical metrics used by vector databases (like Qdrant) to calculate how close two embeddings are to each other in high-dimensional space. Cosine measures the angle between vectors; Euclidean measures the straight-line distance.
* **HNSW (Hierarchical Navigable Small World):** The underlying graph-based algorithm used by modern vector databases (including Qdrant) to perform incredibly fast Approximate Nearest Neighbor (ANN) searches across millions of vectors without comparing every single one.
* **Semantic Search vs. Lexical Search:** Lexical search looks for exact keyword matches (e.g., matching the string "Docker"). Semantic search looks for meaning (e.g., searching "containerization" will return results for "Docker" and "Kubernetes").
* **Metadata Filtering (Payloads):** Attaching standard JSON data (like `{"emailed": true}` or `{"author": "Jane Doe"}`) to a vector. It allows you to combine blazing-fast semantic search with traditional database filtering.

## 2. Recommendation Systems & Machine Learning

* **Concept Drift:** In machine learning, this happens when the statistical properties of the target variable change over time. In our context, it means a user's interests today are fundamentally different from their interests 6 months ago. The model must adapt to this drift.
* **Recency Bias / Time Decay:** A programmatic technique to combat Concept Drift. It applies a mathematical penalty to older data points so that recent user interactions carry significantly more weight in recommendation algorithms.
* **Cold Start Problem:** A classic recommendation system issue where a new system has no historical data on a user, making it impossible to recommend relevant content. (Our project partially solves this by initializing the system prompt with your known baseline skills).
* **Explicit vs. Implicit Feedback:**
    * *Explicit:* The user actively clicks a button saying "Show me more of this." (High signal).
    * *Implicit:* The system notices the user scrolled slowly through an article or didn't click away for 5 minutes. (Lower signal, harder to track).
* **Content-Based Filtering vs. Collaborative Filtering:**
    * *Content-Based:* Recommending items similar to what the user liked before (what we are building).
    * *Collaborative:* Recommending items that *similar users* liked (requires a massive user base, like Netflix or Spotify).

## 3. Large Language Models (LLMs) & NLP

* **Context Window:** The absolute limit of text (measured in tokens) that an LLM can hold in its working memory at one time. If an article is larger than the context window, the LLM will "forget" the beginning of the article by the time it reaches the end.
* **RAG (Retrieval-Augmented Generation):** The architecture we are using. Instead of relying on the LLM's static, pre-trained knowledge, we *retrieve* fresh facts (via APIs/DBs), *augment* the prompt with those facts, and ask the LLM to *generate* a response based only on that context.
* **System Prompt Injection (Dynamic Prompting):** Programmatically altering the hidden instructions given to an LLM before it sees the user prompt. We use this to inject your specific skill level before the summarization task.
* **Quantization (GGUF/GGML):** A technique used by local LLM runners (like Ollama) to compress massive neural networks by reducing the precision of their weights (e.g., from 16-bit floats to 4-bit integers). This allows advanced models to run on standard consumer hardware.
* **Tokenization:** The process of breaking down raw text into sub-word pieces (tokens) before feeding it into an LLM. Rule of thumb: 100 tokens ≈ 75 words.

## 4. Backend Architecture & Data Engineering

* **ETL Pipeline (Extract, Transform, Load):** The three-step process our 2 AM cron job performs: Extracting text from APIs/RSS, Transforming it via LLM summaries and vector embeddings, and Loading it into Qdrant.
* **Asynchronous I/O (Asyncio/Aiohttp):** A programming paradigm crucial in FastAPI. It allows the Python script to fire off a request to the Tavily API and immediately move on to processing the RSS feeds *without waiting* for Tavily to respond. It massively speeds up the pipeline.
* **Webhooks:** Simple HTTP POST endpoints designed specifically to receive automated data from external systems or user interactions (like clicking a button in an email).
* **Rate Limiting / Backoff Strategies:** Defensive programming techniques used when querying external APIs. If an API returns a 429 (Too Many Requests) error, the script automatically waits a progressively longer time (Exponential Backoff) before trying again.
