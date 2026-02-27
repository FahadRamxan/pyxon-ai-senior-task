# Deliverables Checklist

This document maps the **submission deliverables** to the codebase and marks completion status. Use it to verify that all required and optional items are available.

---

## 1. Working code

Provide working code for at least one of (or all of):

| Requirement | Status | Location | Notes |
|-------------|--------|----------|--------|
| **Agent with search/data source (e.g. Google) + LLM** | ✅ Done | `app/agents/chat_agent.py`, `app/tools/search.py` | **General** mode: ReAct-style agent with SerpAPI (or Google CSE) search tool. Agent queries search, consumes snippets/results, LLM synthesizes answer. |
| **Agent that requests URLs (and optionally APIs)** | ✅ Done | `app/agents/chat_agent.py`, `app/tools/url_fetch.py` | **General** mode: `RequestsGetTool` and `RequestsPostTool`. Agent can call URLs, interpret HTML/JSON, use LLM to answer (e.g. “Summarize this URL”, “What does this API return?”). |
| **Agent swarm (multi-agent)** | ✅ Done | `app/swarm/graph.py`, `app/swarm/state.py` | **Swarm** mode: LangGraph supervisor → researcher (search), fetcher (URL), analyst (file), coder (Python), synthesizer. Data from search/URLs/files/code flows to synthesizer for final answer. |

**Summary:** All three are implemented. General mode covers search + URL; Swarm mode adds multi-agent coordination with distinct roles.

---

## 2. Full end-to-end example (script or notebook)

One runnable example that:

- Takes a **user question**
- Uses agent(s) to **fetch data** (search and/or URL/API)
- **Processes** data (parse; optionally store in vector store for RAG)
- Uses the **LLM** to produce a clear **answer** (and optionally citations/sources)

| Item | Status | Location | Notes |
|------|--------|----------|--------|
| Script that runs question → fetch → answer | ✅ Done | `examples/run_e2e_example.py` | Accepts a question and `--mode general` or `--mode swarm`. General: optional RAG (retrieve → agent → persist), then prints answer. Swarm: runs swarm, prints answer and trace. |
| Optional: Jupyter notebook | ⚪ Not provided | — | Same flow can be run via the script or via the API (see README “Testing guide”). |

**How to run the example:**

```bash
# From project root, with .env configured (OPENAI_API_KEY, SERPAPI_API_KEY or GOOGLE_*)
python examples/run_e2e_example.py "What is the capital of Japan?"
python examples/run_e2e_example.py "Summarize the content at https://example.com" --mode general
python examples/run_e2e_example.py "What does https://api.github.com return? Describe main keys." --mode general
python examples/run_e2e_example.py "What is 15% of 240?" --mode swarm
```

---

## 3. README (or section in README) — detailed run instructions

README (or a section) must explain how to run, architecture, and example questions. The main `README.md` covers all three. Below are **exact commands** for all supported platforms.

### 3.1 Requirements

- **Python:** 3.10+ (3.11 or 3.12 recommended)
- **Env vars:** `OPENAI_API_KEY` (required). For search: `SERPAPI_API_KEY` **or** `GOOGLE_API_KEY` + `GOOGLE_CSE_ID`. For RAG: `QDRANT_URL` (default `http://localhost:6333`), optional `QDRANT_API_KEY`.

### 3.2 Step-by-step: create venv and install dependencies

**Windows (PowerShell or CMD):**

```powershell
cd C:\path\to\pyxon-ai-senior-task
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

**Windows (Git Bash / Unix-like shell):**

```bash
cd /c/path/to/pyxon-ai-senior-task
python -m venv .venv
source .venv/Scripts/activate
pip install -r requirements.txt
```

**macOS / Linux:**

```bash
cd /path/to/pyxon-ai-senior-task
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3.3 Configure environment (.env)

Create a `.env` file in the **project root** (do not commit it). Example:

```env
OPENAI_API_KEY=sk-your-openai-key
SERPAPI_API_KEY=your-serpapi-key
# OR for Google Custom Search:
# GOOGLE_API_KEY=your-google-api-key
# GOOGLE_CSE_ID=your-cse-id
# Optional for RAG and General-mode persist/retrieve:
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=
```

**Windows (PowerShell)** — create from template (optional):

```powershell
Copy-Item .env.example .env
# Then edit .env with your keys (e.g. notepad .env)
```

**macOS / Linux:**

```bash
cp .env.example .env
# Edit .env: nano .env  (or vim, code, etc.)
```

### 3.4 Run Qdrant (required for RAG and for General-mode persist/retrieve)

**All platforms (Docker):**

```bash
docker run -p 6333:6333 qdrant/qdrant
```

Leave this running in a separate terminal. API: `http://localhost:6333`.

### 3.5 Ingest RAG data (PDFs into Qdrant)

Run from project root with venv activated. PDFs must be in the `Pyxon Data RAG/` folder (see `app/rag/config.py` for expected filenames).

**Windows:**

```powershell
.\.venv\Scripts\activate
python -m app.rag.ingest_cli all
```

**macOS / Linux:**

```bash
source .venv/bin/activate
python -m app.rag.ingest_cli all
```

To ingest a single agent only:

```bash
python -m app.rag.ingest_cli general
python -m app.rag.ingest_cli cybersecurity
```

(Valid agent keys: `general`, `cloud_automation`, `smart_iot`, `ai_solutions`, `cybersecurity`.)

### 3.6 Start the FastAPI application

**Windows:**

```powershell
.\.venv\Scripts\activate
uvicorn app.main:app --port 8002 --reload
```

**macOS / Linux:**

```bash
source .venv/bin/activate
uvicorn app.main:app --port 8002 --reload
```

- API base: **http://localhost:8002**
- Full-page chat: **http://localhost:8002/**
- Widget: **http://localhost:8002/widget**
- API docs: **http://localhost:8002/docs**

### 3.7 Run the end-to-end example script (no server needed for script)

From project root, venv activated, `.env` configured:

**Windows:**

```powershell
.\.venv\Scripts\activate
python examples/run_e2e_example.py "What is the capital of Japan?"
python examples/run_e2e_example.py "Summarize the content at https://example.com" --mode general
python examples/run_e2e_example.py "What is 15% of 240?" --mode swarm
```

**macOS / Linux:**

```bash
source .venv/bin/activate
python examples/run_e2e_example.py "What is the capital of Japan?"
python examples/run_e2e_example.py "Summarize the content at https://example.com" --mode general
python examples/run_e2e_example.py "What is 15% of 240?" --mode swarm
```

### 3.8 Test the API (server must be running)

**Windows (PowerShell):**

```powershell
Invoke-RestMethod -Uri "http://localhost:8002/chat/" -Method POST -ContentType "application/json" -Body '{"message":"What is the capital of France?","mode":"general"}'
```

**macOS / Linux (curl):**

```bash
curl -X POST http://localhost:8002/chat/ \
  -H "Content-Type: application/json" \
  -d '{"message":"What is the capital of France?","mode":"general"}'
```

**Swarm with trace:**

```bash
curl -X POST http://localhost:8002/chat/ \
  -H "Content-Type: application/json" \
  -d '{"message":"What is 2+2?","mode":"swarm","include_trace":true}'
```

### 3.9 README coverage summary

| Item | Status | Location |
|------|--------|----------|
| How to run (dependencies, env vars, commands) | ✅ Done | `README.md` → “Quick Start”; this section (exact commands above). |
| Architecture (agents, tools, data flow) | ✅ Done | `README.md` → “General mode”, “Swarm mode”, “RAG mode”. |
| Example questions and expected behavior | ✅ Done | `README.md` → “Testing guide: prompts for each feature”. |

---

## 4. Optional but valued

| Item | Status | Location | Notes |
|------|--------|----------|--------|
| **RAG** (index search/URL content in vector store, retrieve before generating) | ✅ Done | See **4.1** below | Company RAG over Pyxon content (website scraping via CrewAI + ethical robots.txt; Qdrant). General mode also persists search/URL results to Qdrant. |
| **Tests or small benchmark** (fixed Q&A pairs) | ⚠️ Partial | `test_chat_file.py` | One script that tests swarm + file upload via the API. No pytest suite or formal benchmark of fixed Q&A pairs. |
| **Docker or Kubernetes/Helm outline** | ⚠️ Outline only | **4.2** below | No Dockerfile or Helm chart in repo; deployment outline is described for reference. |

### 4.1 RAG: Pyxon website scraping (CrewAI), ethical scraping, and Qdrant — full detail

We built RAG on **Pyxon website scraping results** using **CrewAI** to orchestrate the scraping workflow. **Ethical scraping** was enforced by checking **robots.txt** at the base URL (e.g. `https://pyxon.com/robots.txt`) before crawling: we respect `Disallow` and `Crawl-delay` (where applicable) and only scrape paths that are not prohibited. For the vector store we use **Qdrant**. The same RAG pipeline (chunking, embedding, retrieval, generation) is used for both website-derived content and for the PDFs in this repository; below we describe the full pipeline and models.

#### Data source and ethical scraping

- **Source:** Pyxon website content, obtained via **CrewAI**-orchestrated scraping (tasks and agents for discovering URLs, fetching pages, and extracting text).
- **Ethical scraping:** Before scraping any site we:
  - Fetch and parse **robots.txt** at the base URL (e.g. `https://<domain>/robots.txt`).
  - Respect `Disallow` directives and do not request disallowed paths.
  - Optionally respect `Crawl-delay` if present and honor rate limits to avoid overloading the server.
- **Result:** Only allowed pages are scraped; extracted text is then chunked and indexed into Qdrant using the pipeline below.

#### Vector store: Qdrant

- **Qdrant** is used for all RAG collections.
- **Collections:** One per sub-agent (e.g. `pyxon_general`, `pyxon_cybersecurity`, etc.) for company RAG; plus `pyxon_search_results` for General-mode search/URL persist and retrieve.
- **Configuration:** `QDRANT_URL` (default `http://localhost:6333`), optional `QDRANT_API_KEY`. See `app/rag/config.py` and `app/rag/qdrant_client.py`.

#### Chunking strategy

- **Goal:** Semantic, readable chunks that respect section boundaries (headings, paragraphs).
- **Algorithm (implemented in `app/rag/ingestion.py`):**
  1. **Normalize** text (collapse multiple newlines, strip).
  2. **Split on heading boundaries:** Regex detects likely headings (short lines, lines ending with colon, numbered headings). Split so each part starts with a heading and keeps its following content.
  3. **Per part:** If length ≤ `CHUNK_SIZE + CHUNK_OVERLAP`, keep as one chunk. Otherwise **split by paragraphs** (`\n\n`), then merge paragraphs into chunks of size ≤ `CHUNK_SIZE`, with **overlap**: the last paragraph of a chunk can be repeated at the start of the next (up to `CHUNK_OVERLAP` characters) for context continuity.
  4. **Fallback:** If the above yields a single very long chunk, we use LangChain’s **RecursiveCharacterTextSplitter** with `chunk_size=CHUNK_SIZE`, `chunk_overlap=CHUNK_OVERLAP`, and separators `["\n\n", "\n", ". ", " ", ""]`.
- **Parameters (from `app/rag/config.py`):**
  - **CHUNK_SIZE:** 600 characters.
  - **CHUNK_OVERLAP:** 80 characters.
- **Filtering:** Chunks shorter than 30 characters are dropped. Each chunk is stored with metadata (e.g. `source` label) for filtering or display.

#### Embedding model

- **Model:** **OpenAI `text-embedding-3-large`** (via LangChain `OpenAIEmbeddings`).
- **Dimension:** 3072 (`EMBEDDING_DIMENSION` in config).
- **Usage:** All ingested text (from PDFs or from scraped website content processed the same way) is embedded with this model; vectors are stored in Qdrant. Query embedding uses the same model for retrieval.

#### LLMs used in RAG

- **Intent classifier:** **GPT-4o-mini** (`RAG_LLM_MODEL`). Classifies user query into one or more intents (e.g. `general`, `cloud_automation`, `smart_iot`, `ai_solutions`, `cybersecurity`) so the right Qdrant collection(s) are queried. See `app/rag/intent.py`.
- **Sub-agents (retrieve + generate):** **GPT-4o-mini**. Each sub-agent retrieves `RAG_TOP_K` chunks (default 6) from its Qdrant collection, then generates an answer using only that context. See `app/rag/agents.py`.
- **Synthesizer (multi-intent):** **GPT-4o-mini**. When the classifier returns multiple intents, sub-agents run in parallel; the synthesizer merges their answers into one response. See `app/rag/orchestrator.py`.

#### End-to-end RAG flow

1. **Ingest (one-time or periodic):** Scraped Pyxon website content (or PDFs in `Pyxon Data RAG/`) → chunk with the strategy above → embed with `text-embedding-3-large` → upsert into the appropriate Qdrant collection(s).
2. **Query:** User question → intent classifier (GPT-4o-mini) → one or more intent keys.
3. **Retrieve:** For each intent, embed the query with `text-embedding-3-large`, query the corresponding Qdrant collection for top-k chunks.
4. **Generate:** Each sub-agent gets its chunks and generates an answer with GPT-4o-mini; if multiple intents, synthesizer merges answers.
5. **Response:** Single coherent answer (and optionally citations/sources from chunk metadata).

#### Where this is implemented

- **Chunking and ingestion:** `app/rag/ingestion.py` (PDF path; same chunking can be applied to scraped HTML/text).
- **Embeddings:** `app/rag/embeddings.py` (OpenAI `text-embedding-3-large`).
- **Config (sizes, model names, collections):** `app/rag/config.py`.
- **Qdrant client and collections:** `app/rag/qdrant_client.py`.
- **Intent classification:** `app/rag/intent.py`.
- **Sub-agents and retrieval:** `app/rag/agents.py`.
- **Orchestrator and synthesis:** `app/rag/orchestrator.py`.
- **CLI to ingest PDFs into Qdrant:** `python -m app.rag.ingest_cli all` (see Section 3.5).

**Summary:** RAG was built on Pyxon website scraping (CrewAI) with ethical scraping (robots.txt checks). We use Qdrant for storage; chunking (600/80, heading/paragraph + RecursiveCharacterTextSplitter fallback), embeddings (text-embedding-3-large), and LLMs (GPT-4o-mini for classifier, sub-agents, and synthesizer) are as above. The repo demonstrates the pipeline using PDFs in `Pyxon Data RAG/`; the same pipeline applies to website-derived content.

### 4.2 Deployment outline (optional)

- **Docker:** Use a Dockerfile that installs dependencies from `requirements.txt`, sets `ENV` or mounts `.env`, and runs `uvicorn app.main:app --host 0.0.0.0 --port 8000`. Optionally use a multi-stage build and non-root user. Qdrant can be a separate container or external service.
- **Kubernetes/Helm:** Deploy the app as a Deployment (or Helm chart) with ConfigMap/Secret for env vars, Service (ClusterIP or LoadBalancer), and optional Ingress. Run Qdrant as a separate Deployment or use a managed vector DB. Document `allow_dangerous_requests` and network policies if URL fetch is used in production.

---

## Quick reference: where to find what

| Deliverable | Where to look |
|-------------|----------------|
| Search + LLM agent | General mode → `app/agents/chat_agent.py`, `app/tools/search.py` |
| URL/API agent | General mode → `app/agents/chat_agent.py`, `app/tools/url_fetch.py` |
| Agent swarm | Swarm mode → `app/swarm/graph.py`, `app/swarm/state.py` |
| End-to-end example | `examples/run_e2e_example.py` |
| Run instructions & env vars | `README.md` → Quick Start |
| Architecture & data flow | `README.md` → General / RAG / Swarm sections |
| Example questions & behavior | `README.md` → Testing guide |
| RAG over search/URL | `app/rag/search_store.py`, General mode in README |
| RAG (Pyxon scraping, CrewAI, robots.txt, Qdrant, chunking, models) | **Section 4.1** in this document; code: `app/rag/` |
| File-upload test | `test_chat_file.py` (swarm + file) |

---

## PR description checklist (for submission)

When opening the PR, you can use:

- **Features implemented:** All three (search agent, URL agent, swarm) + full e2e example + README with run, architecture, and examples. Optional: RAG ✅; tests partial; Docker/K8s outline in this file.
- **How to run:** See README Quick Start and `examples/run_e2e_example.py`.
- **Example questions & behavior:** See README “Testing guide”.
- **Assumptions:** SerpAPI or Google CSE for search; OpenAI for LLM; Qdrant optional for RAG and General-mode persist/retrieve.
