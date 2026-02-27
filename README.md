# Pyxon AI – Senior AI Engineer Entry Task

## Overview

This repository implements an **agentic chatbot** that meets all three task requirements plus optional and extra features: an agent with **search** and **URL/API** tools, an **agent swarm** (multi-agent system) with LangGraph, **RAG** over company content (including Pyxon website scraping with CrewAI and ethical robots.txt compliance) and over search/URL results, **file upload and analysis**, and a **coding agent**. The app exposes a FastAPI backend, a full-page chat UI, and an embeddable widget. **Session tracking** is built in: each chat has a unique session ID and message IDs; when the user ends the chat (or after 5 minutes of inactivity), **start time**, **end time**, **duration**, **user name/email**, and **feedback** are written to a **session log file** in the project folder. Tool outputs are **truncated** to avoid exceeding the model’s context length.

---

## Features Implemented

### Required (deliverables)

| Deliverable | Status | Description |
|-------------|--------|-------------|
| **1. Agent with search/data source + LLM** | ✅ | **General** mode: ReAct-style agent with SerpAPI (or Google CSE) search. Queries search, consumes results, LLM synthesizes answer. `app/agents/chat_agent.py`, `app/tools/search.py`. |
| **2. Agent that requests URLs/APIs + LLM** | ✅ | **General** mode: `RequestsGetTool` and `RequestsPostTool`. Fetches URLs/APIs, interprets content, LLM answers. `app/agents/chat_agent.py`, `app/tools/url_fetch.py`. |
| **3. Agent swarm (multi-agent)** | ✅ | **Swarm** mode: LangGraph supervisor → researcher (search), fetcher (URL), analyst (file), coder (Python), synthesizer. `app/swarm/graph.py`, `app/swarm/state.py`. |
| **4. Full end-to-end example + small benchmark** | ✅ | **E2E script:** `examples/run_e2e_example.py` — takes a question, uses agent(s) to fetch (search/URL or swarm), optional RAG, LLM answer (and swarm trace). **Small benchmark:** `test_chat_file.py` — fixed Q&A pairs across General, RAG, and Swarm (and optional file upload); verifies HTTP 200 and non-empty output. See “How to Run” steps 6 and 8. |
| **5. README (run, architecture, examples)** | ✅ | This document: exact run commands (Windows/macOS/Linux), architecture, RAG detail, testing guide, example questions and sample outputs, deliverables checklist. |

### Optional and extra

| Feature | Status | Description |
|---------|--------|-------------|
| **RAG over search/URL results** | ✅ | General mode: search and URL tool outputs persisted to Qdrant (`pyxon_search_results`); retrieved before each reply for grounding. `app/rag/search_store.py`. |
| **RAG over company content (Pyxon)** | ✅ | Intent-based RAG: Pyxon website scraping (CrewAI) with **ethical scraping** (robots.txt); Qdrant; chunking and embeddings as below. Also PDFs in `Pyxon Data RAG/` ingested the same way. `app/rag/`. |
| **File upload and analysis** | ✅ | Swarm: user can attach a file (paperclip in widget or multipart API); **analyst** agent summarizes/answers questions about the file; synthesizer uses analysis in the answer. |
| **Coding agent** | ✅ | Swarm: **coder** agent generates and runs Python (safe subprocess, timeout, output limit); results fed to synthesizer. `app/tools/code.py`, `app/swarm/graph.py`. |
| **Embeddable widget** | ✅ | Floating chat bubble + panel at `/widget`; iframe or `embed.js`. Multilingual (EN/AR), theme toggle, mode toggle (General/RAG/Swarm), file attach. |
| **Session tracking & log file** | ✅ | Each chat has a **session ID**; each message has a **message ID**. On end chat (or skip), **start time**, **end time**, **duration**, **user name**, **user email**, **rating**, **options**, and **message IDs** are appended to **`data/chat_sessions.txt`** in the project folder. See "Session tracking and session log" below. |
| **5-minute idle auto-end** | ✅ | If the user sends no message for 5 minutes, the feedback modal is shown automatically and the session can be closed (submit or skip). |
| **Context length safeguard** | ✅ | General-mode tool outputs (search, URL fetch) are truncated to **12,000 characters** per response so the agent stays within the model's context limit (e.g. 128k tokens). `app/agents/chat_agent.py`, `app/core/constants.py` (`MAX_TOOL_OUTPUT_CHARS`). |
| **Tests / benchmark** | ✅ | `test_chat_file.py` runs fixed Q&A pairs across General, RAG, and Swarm (and optional file upload); verifies HTTP 200 and non-empty output. See step 8 in How to Run. |
| **Docker / K8s outline** | ⚠️ Outline | Deployment outline in “Optional: Deployment” section below; no Dockerfile or Helm in repo. |

### Choosing a mode (General vs RAG vs Swarm)

**Yes, the choice affects which pipeline runs.** The system does not automatically pick a mode for you.

- **General** — Single agent with search and URL tools. Use for: web search, “summarize this URL”, “what does this API return?”. Optional: past search/URL results are retrieved from Qdrant and passed as context (RAG over search results).
- **RAG** — Company knowledge only. Use for: questions about Pyxon (services, offices, cybersecurity, IoT, AI, etc.). Requires Qdrant and ingested PDFs. Intent classifier routes to one or more sub-agents; no search or URL fetch in this mode.
- **Swarm** — Multi-agent (supervisor → researcher / fetcher / analyst / coder → synthesizer). Use for: search + synthesis, URL fetch + synthesis, file upload + analysis, or code execution (e.g. “what is 2+2?”, “first 5 primes”). The supervisor decides which specialist(s) to call; you do not choose them.

Pick the mode that matches your goal. For “weather in Riyadh” or “T20 score” use **General** (search). For “what does Pyxon offer?” use **RAG** (company docs) or **General** (search). For “summarize https://python.org/about” use **General** (URL) or **Swarm** (fetcher + synthesizer).

---

## How to Run

Commands below are for **Windows (PowerShell/CMD)**, **Windows (Git Bash)**, and **macOS/Linux**. Use the block that matches your environment.

### Requirements

- **Python:** 3.10+ (3.11 or 3.12 recommended)
- **Env vars:** `OPENAI_API_KEY` (required). For search: `SERPAPI_API_KEY` **or** `GOOGLE_API_KEY` + `GOOGLE_CSE_ID`. For RAG/General persist: `QDRANT_URL` (default `http://localhost:6333`), optional `QDRANT_API_KEY`.

### 1. Virtual environment and dependencies

**Windows (PowerShell or CMD):**

```powershell
cd C:\path\to\pyxon-ai-senior-task
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

**Windows (Git Bash):**

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

### 2. Environment variables (.env)

Create a `.env` file in the project root (do not commit it). Example:

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

**Windows (PowerShell)** — optional template copy:

```powershell
Copy-Item .env.example .env
# Then edit .env (e.g. notepad .env)
```

**macOS / Linux:**

```bash
cp .env.example .env
# Edit: nano .env  (or vim, code, etc.)
```

### 3. Qdrant (for RAG and General-mode persist/retrieve)

**All platforms (Docker):**

```bash
docker run -p 6333:6333 qdrant/qdrant
```

Leave this running in a separate terminal. API: `http://localhost:6333`.

### 4. Ingest RAG data (PDFs into Qdrant)

PDFs must be in the `Pyxon Data RAG/` folder (see `app/rag/config.py` for expected filenames).

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

Single-agent ingest (optional):

```bash
python -m app.rag.ingest_cli general
python -m app.rag.ingest_cli cybersecurity
```

Valid agent keys: `general`, `cloud_automation`, `smart_iot`, `ai_solutions`, `cybersecurity`.

### 5. Start the FastAPI app

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

- **API:** http://localhost:8002  
- **Full-page chat:** http://localhost:8002/  
- **Widget:** http://localhost:8002/widget  
- **API docs:** http://localhost:8002/docs  
- **Chat API:** `POST /chat/` with JSON `{"message": "...", "mode": "general"|"rag"|"swarm", "include_trace": true|false, "session_id": "optional"}` or multipart with optional `file`. Response includes `session_id` and `message_id`. **Session start:** `POST /session/start` with optional `session_id`, `user_name`, `user_email` to record start time and user name/email. **Feedback:** `POST /feedback/` with `session_id`, optional `rating`, `options`, `feedback` to record end time, duration, and append a line to the session log file.

### 6. Run the end-to-end example script (no server required)

One-shot script: pass a question and optional `--mode`; it uses the agent(s) to fetch data and produce an answer. No server needed.

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

### 7. Test the API (server must be running)

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

### 8. Run the small benchmark (fixed Q&A tests)

A **small benchmark** runs a set of **fixed example questions** against the live API to verify behavior: each question is sent to `POST /chat/` in the appropriate mode (General, RAG, or Swarm), and the script checks for **HTTP 200** and **non-empty output**. This acts as a regression/acceptance test for the three pipelines and optional file upload.

**Requires the server to be running** (step 5). From project root, venv activated:

**Windows:**

```powershell
.\.venv\Scripts\activate
python test_chat_file.py
```

**macOS / Linux:**

```bash
source .venv/bin/activate
python test_chat_file.py
```

**What the benchmark covers:** General (search, e.g. weather/T20; URL, e.g. summarize python.org, GitHub API), RAG (Pyxon services/offices — needs Qdrant + ingest), Swarm (exchange rate, httpbin fetch, LangChain Wikipedia, first 5 primes, 2+2). Optional file-upload test when `--file <path>` is passed (default: `test_upload.txt` if present).

**Options:** `--quick` runs a smaller subset with a shorter timeout (30s). `--file <path>` sets the file for the swarm file-upload test.

---

## Architecture and Data Flow

### General mode (search + URL + optional RAG)

1. **Retrieve (optional):** User message is embedded and used to query the Qdrant collection `pyxon_search_results`; matching past search/URL content is added as context.
2. **Agent:** ReAct agent with tools: search (SerpAPI or Google CSE), URL GET, URL POST. Agent may call tools and use context to answer.
3. **Persist (optional):** Tool outputs (search snippets, fetched pages) are chunked, embedded, and upserted into `pyxon_search_results` for future turns.

**Code:** `app/agents/chat_agent.py`, `app/tools/search.py`, `app/tools/url_fetch.py`, `app/rag/search_store.py`, `app/api/routes/chat.py`.

### Swarm mode (multi-agent)

- **Supervisor** (LLM) decides the next step: `researcher`, `fetcher`, `analyst`, `coder`, `synthesizer`, or `finish`.
- **Researcher:** Runs search tool, appends result to shared state.
- **Fetcher:** Fetches one URL from state, appends result.
- **Analyst:** Analyzes uploaded file(s), appends analysis to state (runs when user attached a file).
- **Coder:** Generates Python, runs it via `run_python`, appends output to state.
- **Synthesizer:** Reads all evidence (search, URL, analysis, code) and produces the final answer.
- After each specialist, control returns to the supervisor until `finish`. Router overrides prevent redundant analyst/synthesizer runs.

**Code:** `app/swarm/graph.py`, `app/swarm/state.py`, `app/tools/code.py`, `app/utils/file_extract.py`.

### RAG mode (company knowledge)

1. **Intent classifier** (GPT-4o-mini): Maps query to one or more intents (`general`, `cloud_automation`, `smart_iot`, `ai_solutions`, `cybersecurity`).
2. **Sub-agents:** For each intent, retrieve top-k chunks from that intent’s Qdrant collection, then generate an answer with GPT-4o-mini using only that context.
3. **Synthesizer:** If multiple intents, sub-agent answers are merged into one response.

**Code:** `app/rag/orchestrator.py`, `app/rag/intent.py`, `app/rag/agents.py`, `app/rag/qdrant_client.py`.

---

## Session tracking and session log

Each chat has a **session ID** (generated when the user clicks "Begin chat" in the widget, or on first message). Each message gets a unique **message ID** (assigned by the backend). When the user **ends the chat** (clicks "End chat" and submits or skips feedback) or the **5-minute idle** timer fires and they close the feedback modal, the backend:

1. Computes **end time** and **duration** (end − start).
2. Appends one **tab-separated line** to the session log file.

**Log file location:** **`data/chat_sessions.txt`** in the **project folder** (the directory containing the `app` package). The path is resolved from the app’s install location, so the file is always written there regardless of the process working directory.

**Columns (header + one line per ended session):**  
`session_id`, `start_time_utc`, `end_time_utc`, `duration_seconds`, `message_count`, `rating`, `options`, `feedback_snippet`, `user_name`, `user_email`, `message_ids`

**APIs:**

- **`POST /session/start`** — Call when the user enters the chat (e.g. after name/email). Body: optional `session_id`, optional `user_name`, `user_email`. Creates the session and records start time (and name/email) so they are included when the session is written to the log.
- **`POST /chat/`** — Request may include `session_id`; response includes `session_id` and `message_id` for the assistant reply. If no session_id is sent, one is created and returned.
- **`POST /feedback/`** — Body: optional `session_id`, optional `rating` (1–5), optional `options` (list of feedback option keys), optional `feedback` (text). If `session_id` is provided and the session exists, the session is closed and one line is appended to `data/chat_sessions.txt`.

**How to view the log:** Open `data/chat_sessions.txt` in the project folder, or run `Get-Content .\data\chat_sessions.txt` (PowerShell) / `type data\chat_sessions.txt` (CMD) from the project root. The file is created after the first session is ended (feedback submitted or skipped). The `data/` directory is in `.gitignore` by default so the log is not committed.

**Code:** `app/session_store.py`, `app/api/routes/session.py`, `app/api/routes/feedback.py`, widget in `app/static/widget.html`.

---

## RAG: Pyxon Website Scraping (CrewAI), Ethical Scraping, and Qdrant — Full Detail

We built RAG on **Pyxon website scraping results** using **CrewAI** to orchestrate the scraping workflow. **Ethical scraping** was enforced by checking **robots.txt** at the base URL (e.g. `https://pyxon.com/robots.txt`) before crawling: we respect `Disallow` and `Crawl-delay` (where applicable) and only scrape paths that are not prohibited. The vector store is **Qdrant**. The same RAG pipeline (chunking, embedding, retrieval, generation) is used for website-derived content and for the PDFs in this repo.

### Data source and ethical scraping

- **Source:** Pyxon website content, obtained via **CrewAI**-orchestrated scraping (tasks/agents for discovering URLs, fetching pages, extracting text).
- **Ethical scraping:** Before scraping we:
  - Fetch and parse **robots.txt** at the base URL (e.g. `https://<domain>/robots.txt`).
  - Respect `Disallow` and do not request disallowed paths.
  - Optionally respect `Crawl-delay` and rate limits.
- **Result:** Only allowed pages are scraped; extracted text is then chunked and indexed into Qdrant.

### Vector store: Qdrant

- All RAG collections use **Qdrant**.
- **Collections:** One per sub-agent (e.g. `pyxon_general`, `pyxon_cybersecurity`) for company RAG; `pyxon_search_results` for General-mode search/URL persist and retrieve.
- **Config:** `QDRANT_URL` (default `http://localhost:6333`), optional `QDRANT_API_KEY`. See `app/rag/config.py`, `app/rag/qdrant_client.py`.

### Chunking strategy

- **Goal:** Semantic chunks that respect headings and paragraphs.
- **Algorithm** (`app/rag/ingestion.py`):
  1. Normalize text (collapse newlines, strip).
  2. Split on heading boundaries (regex: short lines, colon endings, numbered headings).
  3. For each part: if length ≤ `CHUNK_SIZE + CHUNK_OVERLAP`, keep as one chunk; else split by paragraphs (`\n\n`), merge into chunks of size ≤ `CHUNK_SIZE` with overlap (last paragraph can start the next chunk, up to `CHUNK_OVERLAP`).
  4. **Fallback:** If one very long chunk remains, use LangChain **RecursiveCharacterTextSplitter** with `chunk_size=CHUNK_SIZE`, `chunk_overlap=CHUNK_OVERLAP`, separators `["\n\n", "\n", ". ", " ", ""]`.
- **Parameters** (`app/rag/config.py`): **CHUNK_SIZE** 600, **CHUNK_OVERLAP** 80. Chunks &lt; 30 characters are dropped. Metadata (e.g. `source`) is stored with each chunk.

### Embedding model

- **Model:** **OpenAI `text-embedding-3-large`** (LangChain `OpenAIEmbeddings`).
- **Dimension:** 3072. Same model for indexing and query. See `app/rag/embeddings.py`.

### LLMs used in RAG

- **Intent classifier:** **GPT-4o-mini** — classifies query into one or more intents. `app/rag/intent.py`.
- **Sub-agents:** **GPT-4o-mini** — each retrieves **RAG_TOP_K** (default 6) chunks from its collection and generates an answer. `app/rag/agents.py`.
- **Synthesizer (multi-intent):** **GPT-4o-mini** — merges sub-agent answers. `app/rag/orchestrator.py`.

### End-to-end RAG flow

1. **Ingest:** Scraped website content or PDFs in `Pyxon Data RAG/` → chunk → embed with `text-embedding-3-large` → upsert into Qdrant.
2. **Query:** User question → intent classifier → one or more intent keys.
3. **Retrieve:** For each intent, embed query, query Qdrant for top-k chunks.
4. **Generate:** Sub-agents generate answers; synthesizer merges if multiple intents.
5. **Response:** Single answer (and optionally citations from chunk metadata).

### Implementation locations

- Chunking/ingestion: `app/rag/ingestion.py`
- Embeddings: `app/rag/embeddings.py`
- Config: `app/rag/config.py`
- Qdrant client: `app/rag/qdrant_client.py`
- Intent: `app/rag/intent.py`
- Sub-agents: `app/rag/agents.py`
- Orchestrator: `app/rag/orchestrator.py`
- Ingest CLI: `python -m app.rag.ingest_cli all`

---

## Testing Guide: Example Prompts and API

Use the **widget** (http://localhost:8002/widget) or **API** (`POST /chat/` with `message`, `mode`) to try the following.

### 1. Agent with search (General)

| What to test | Example prompt |
|--------------|----------------|
| Search and answer | `What is the capital of Japan?` |
| Synthesize from snippets | `What are the main benefits of renewable energy?` |
| RAG over search (two turns; needs Qdrant) | 1) `What are the rules for a Class B driving license in Germany?` → 2) `What is the minimum age for that?` |

```bash
curl -X POST http://localhost:8002/chat/ -H "Content-Type: application/json" -d "{\"message\": \"What is the population of Berlin?\", \"mode\": \"general\"}"
```

### 2. Agent that requests URLs (General)

| What to test | Example prompt |
|--------------|----------------|
| Summarize URL | `Summarize the content at https://www.python.org/about/` |
| Explain API response | `What does https://api.github.com/ return? Describe the main keys.` |
| Search then fetch | `Find the official Python 3.12 release notes page and tell me the release date.` |

```bash
curl -X POST http://localhost:8002/chat/ -H "Content-Type: application/json" -d "{\"message\": \"What is on the front page of https://example.com?\", \"mode\": \"general\"}"
```

### 3. Agent swarm — search, URL, synthesis (Swarm)

| What to test | Example prompt |
|--------------|----------------|
| Researcher + synthesizer | `What is the current exchange rate of EUR to USD?` |
| Fetcher + synthesizer | `Fetch https://httpbin.org/json and summarize what it returns.` |
| Researcher + fetcher + synthesizer | `Find the Wikipedia page for "LangChain" and in one paragraph tell me what it is.` |

```bash
curl -X POST http://localhost:8002/chat/ -H "Content-Type: application/json" -d "{\"message\": \"What is 15% of 240?\", \"mode\": \"swarm\", \"include_trace\": true}"
```

### 4. Swarm — coding agent (Swarm)

| What to test | Example prompt |
|--------------|----------------|
| Run Python | `What is 2 + 2?` or `Compute the factorial of 5.` |
| Data-style computation | `Generate a list of the first 5 prime numbers using Python.` |

### 5. Swarm — file upload and analysis (Swarm + file)

Attach a file (paperclip in widget or multipart `file` in API).

| What to test | Example prompt (with file attached) |
|--------------|-------------------------------------|
| Summarize file | `Summarize this document.` |
| Question about file | `What is the net profit mentioned in this file?` |
| Recommendations/conclusion | `List the main recommendations and the conclusion.` |

```bash
curl -X POST http://localhost:8002/chat/ -F "message=Summarize this file and what is the net profit?" -F "mode=swarm" -F "include_trace=true" -F "file=@/path/to/report.pdf"
```

### 6. RAG mode (company PDFs)

Requires Qdrant and ingested PDFs: `python -m app.rag.ingest_cli all`.

| What to test | Example prompt |
|--------------|----------------|
| Company overview | `What does Pyxon do?` or `What solutions does the company offer?` |
| Domain-specific | `What cybersecurity solutions does Pyxon provide?` |
| Multi-intent | `Tell me about Pyxon's IoT solutions and their AI solutions in one answer.` |

```bash
curl -X POST http://localhost:8002/chat/ -H "Content-Type: application/json" -d "{\"message\": \"What are Pyxon cybersecurity offerings?\", \"mode\": \"rag\"}"
```

### Quick checklist

| Requirement | Mode | What to run |
|-------------|------|-------------|
| Search / data source | General | e.g. capital of Japan, benefits of renewable energy |
| URL / API requests | General | Summarize a URL or “What does this API return?” |
| Agent swarm | Swarm | Exchange rate, fetch httpbin, or “What is 2+2?” |
| RAG over search | General | Two turns: search question then follow-up (needs Qdrant) |
| File analysis | Swarm + file | Attach file + “Summarize” or “What is the net profit?” |
| Company RAG | RAG | Questions about Pyxon (needs Qdrant + ingest) |

---

## Example Questions and Sample Outputs

Below are example questions and representative answers produced by the chatbot. Use **General** for search/URL questions, **RAG** for Pyxon company questions (with Qdrant + ingest), and **Swarm** for multi-agent (search, URL fetch, or code). See “Choosing a mode” above.

**Greeting (after name/email in widget):**  
*Hi Fahad Ramzan! How can I help you today?*

---

### 1. What is the current weather in Riyadh?  
**Mode:** General (search)

**Sample output:**

> The current weather in Riyadh, Saudi Arabia, is mostly sunny with a temperature of 82°F. The humidity is at 16%, and there is no precipitation expected. Winds are blowing at 12 mph.

---

### 2. What is the T20 World Cup live score?  
**Mode:** General (search)

**Sample output:**

> As of the latest updates from the ICC Men's T20 World Cup, here are the recent match results:
>
> 1. **India vs. Zimbabwe** — India 256/4 (20 overs) defeated Zimbabwe 184/6 (20 overs). India won by 72 runs.  
> 2. **West Indies vs. South Africa** — West Indies 176/8 lost to South Africa 177/1 (16.1 overs). South Africa won by 9 wickets.  
> 3. **New Zealand vs. Sri Lanka** — New Zealand 168/7 defeated Sri Lanka 107/8. New Zealand won by 61 runs.  
> 4. **Pakistan vs. England** — Pakistan 164/9 lost to England 166/8 (19.1 overs). England won by 2 wickets.  
> 5. **West Indies vs. Zimbabwe** — West Indies 254/6 defeated Zimbabwe 147 (17.4 overs). West Indies won by 107 runs.  
> 6. **South Africa vs. India** — South Africa 187/7 defeated India 111 (18.5 overs). South Africa won by 76 runs.
>
> If you need live scores for ongoing matches, please specify the teams or matches you are interested in!

---

### 3. What services does Pyxon offer and where are the offices located?  
**Mode:** RAG (company knowledge; requires Qdrant + ingested PDFs)

**Sample output:**

> **Pyxon services:**  
> Pyxon offers digital transformation services, including:  
> 1. **AI innovations** — Enterprise-grade Arabic AI with emphasis on data privacy.  
> 2. **IoT solutions** — Intelligent connected systems for transportation, healthcare, and industrial applications.  
> 3. **Cybersecurity** — AI-powered defense, zero trust architecture, compliance automation.  
> 4. **Cloud DevOps & RPA** — Cloud migration, DevOps, RPA, Microsoft Business Applications.
>
> **Office locations:**  
> Pyxon is headquartered in **Riyadh, Saudi Arabia**. They serve clients across the Middle East and Africa (UAE, Egypt, Qatar, Kuwait, Bahrain, Oman, Jordan, Lebanon).

---

### 4. Summarize the content at https://www.python.org/about/  
**Mode:** General (URL fetch) or Swarm (fetcher + synthesizer)

**Sample output:**

> The “About Python” page highlights Python as a powerful, fast, and easy-to-learn open-source language that runs on many platforms. Key points: **Getting started** — guides for programmers and non-programmers, installation, code samples. **Applications** — web development, databases, scientific computing, education, software development; PyPI hosts thousands of third-party modules. **Community** — conferences, workshops, documentation, mailing lists, IRC. **Open source** — OSI-approved license, free for commercial use. The **Python Software Foundation (PSF)** promotes and supports the community.

---

### 5. What does https://api.github.com/ return? Describe the main keys.  
**Mode:** General (URL fetch) or Swarm (fetcher + synthesizer)

**Sample output:**

> The GitHub API root returns a JSON object with URLs for various resources. Main keys include: `current_user_url`, `authorizations_url`, `code_search_url`, `commit_search_url`, `emails_url`, `emojis_url`, `events_url`, `feeds_url`, `followers_url`, `following_url`, `gists_url`, `hub_url`, `issue_search_url`, `issues_url`, `keys_url`, `notifications_url`, `organization_url`, `public_gists_url`, `rate_limit_url`, `repository_url`, `user_url`, and others. These provide structured access to user accounts, repositories, issues, search, and more.

---

### 6. What is the current exchange rate of EUR to USD?  
**Mode:** Swarm (researcher + synthesizer) or General (search)

**Sample output:**

> The current exchange rate is approximately 1 EUR to 1.18 USD.

---

### 7. Fetch https://httpbin.org/json and summarize what it returns.  
**Mode:** Swarm (fetcher + synthesizer) or General (URL fetch)

**Sample output:**

> The response from https://httpbin.org/json returns a JSON object with a sample **slideshow** structure: **Author:** "Yours Truly". **Date:** "date of publication". **Slides:** an array of slide objects — e.g. Slide 1: title "Wake up to WonderWidgets!", type "all"; Slide 2: title "Overview", type "all", items including "Why WonderWidgets are great" and "Who buys WonderWidgets". It is a simple representation of a slideshow for a fictional product.

---

### 8. Find the Wikipedia page for "LangChain" and in one paragraph tell me what it is.  
**Mode:** Swarm (researcher + fetcher + synthesizer) or General (search + URL)

**Sample output:**

> LangChain is a software framework designed to integrate large language models (LLMs) into applications. It simplifies connecting language models to specific tasks and supports use cases such as document analysis and other advanced language processing applications.

---

### 9. Generate a list of the first 5 prime numbers using Python.  
**Mode:** Swarm (coder + synthesizer)

**Sample output:**

> You can generate the first 5 prime numbers in Python with a small script (e.g. an `is_prime` check and a loop). When run, the output is: **[2, 3, 5, 7, 11]**.

---

## Deliverables Checklist

| Deliverable | Status | Location / notes |
|-------------|--------|------------------|
| Working code: search agent + LLM | ✅ | `app/agents/chat_agent.py`, `app/tools/search.py` |
| Working code: URL/API agent + LLM | ✅ | `app/agents/chat_agent.py`, `app/tools/url_fetch.py` |
| Working code: agent swarm | ✅ | `app/swarm/graph.py`, `app/swarm/state.py` |
| Full end-to-end example | ✅ | `examples/run_e2e_example.py` (step 6 in How to Run) |
| Small benchmark (fixed Q&A) | ✅ | `test_chat_file.py` — fixed questions for General, RAG, Swarm + optional file; verifies 200 and non-empty output (step 8) |
| README: how to run | ✅ | This document, “How to Run” (Windows/macOS/Linux) |
| README: architecture | ✅ | “Architecture and Data Flow”, “RAG: … Full Detail” |
| README: example questions | ✅ | “Testing Guide” |
| Optional: RAG | ✅ | Company RAG (CrewAI, robots.txt, Qdrant); General persist/retrieve |
| Optional: tests/benchmark | ✅ | Small benchmark above; see step 8 in How to Run |
| Optional: Docker/K8s | ⚠️ Outline | See “Optional: Deployment” |

---

## Additional Features (Not Required by Deliverables)

The following were implemented in addition to the requested deliverables (end-to-end example, README with run/architecture/examples, and optional RAG/tests/Docker outline). They are **not** required by the task specification.

| Feature | Description |
|--------|-------------|
| **Session ID and message IDs** | Each chat has a unique **session ID** (created when the user starts the chat or on first message). Each user and assistant message is assigned a **message ID**. The widget sends `session_id` with every `POST /chat/` and `POST /feedback/`; the chat response includes `session_id` and `message_id`. |
| **Chat start/end time and duration** | Session **start time** is recorded when `POST /session/start` is called (or when the first message is sent). **End time** is set when `POST /feedback/` is called (submit or skip). **Duration** is computed as end − start and written to the session log. |
| **Session log file (project folder)** | When a session ends, one line is appended to **`data/chat_sessions.txt`** in the **project folder**. The path is absolute (derived from the app package location), so the file is always in the same place. Columns: session_id, start_time_utc, end_time_utc, duration_seconds, message_count, rating, options, feedback_snippet, **user_name**, **user_email**, message_ids. See "Session tracking and session log" above. |
| **End-chat feedback (modal + options)** | When the user clicks **End chat** in the widget, a **modal popup** appears (overlay + centered card). The user can give a **star rating (1–5)**, select one or more **clickable feedback options** (e.g. "Very helpful", "Fast response", "Answer was inaccurate", "Response was slow", "Could not find what I needed", "Other"), and optionally add free-text comments. Selections are sent to the backend with `session_id` and recorded in the log file. Modal is confined within the panel (no scroll). |
| **Feedback API** | `POST /feedback/` accepts JSON: optional `session_id`, optional `rating` (1–5), optional `options` (list of selected option keys), optional `feedback` (text). If `session_id` is provided, the session is closed and one line is appended to `data/chat_sessions.txt`. See `app/api/routes/feedback.py`. |
| **Session start API** | `POST /session/start` accepts optional `session_id`, optional `user_name`, optional `user_email`. Creates or reuses the session and stores start time and name/email so they appear in the log when the session ends. See `app/api/routes/session.py`. |
| **5-minute idle auto-end** | If the user sends no message for 5 minutes, the feedback modal is shown automatically. Submitting or skipping feedback then closes the session and writes the log line as usual. |
| **Widget onboarding and UX** | **Disclaimer** (terms of use) and **name/email form** before starting the chat; **theme toggle** (dark/light); **language toggle** (EN / عربي) with RTL support; **mode selector** (General / RAG / Swarm) on welcome and in chat; **file attachment** in the widget. The deliverables did not specify a full chat UI or embeddable widget UX. |
| **Compact feedback modal** | Feedback modal is sized to fit inside the chatbot panel (max-height 85% of panel, overflow hidden). Text and control sizes are reduced so the entire dialog fits without scrolling. |
| **Context length safeguard** | General-mode tool outputs (search, URL fetch) are truncated to 12,000 characters per response to avoid exceeding the model's context limit (e.g. 128k tokens). Configurable via `MAX_TOOL_OUTPUT_CHARS` in `app/core/constants.py`. |

**Summary:** The task asked for one end-to-end example, README (run, architecture, examples), and optional RAG/tests/Docker. The above features (session tracking, session log file with name/email, feedback flow and API, session start API, 5-min idle, widget onboarding and i18n/theme/mode, compact modal, and context-length truncation) are extra and not part of that scope.

---

## Quick Reference: Where to Find What

| Feature | Where to look |
|---------|----------------|
| Search + LLM agent | `app/agents/chat_agent.py`, `app/tools/search.py` |
| URL/API agent | `app/agents/chat_agent.py`, `app/tools/url_fetch.py` |
| Agent swarm | `app/swarm/graph.py`, `app/swarm/state.py` |
| End-to-end example | `examples/run_e2e_example.py` |
| RAG over search/URL | `app/rag/search_store.py` (General mode) |
| RAG (company, CrewAI, robots.txt, Qdrant, chunking, models) | “RAG: Pyxon Website Scraping…” above; `app/rag/` |
| File upload + analyst | `app/api/routes/chat.py` (multipart), `app/swarm/graph.py` (analyst), `app/utils/file_extract.py` |
| Coding agent | `app/tools/code.py`, `app/swarm/graph.py` (_coder_node) |
| Test script (example outcomes) | `test_chat_file.py` — run with server up; see “Run tests” in How to Run |

| Session store & log file | `app/session_store.py`; log file: **`data/chat_sessions.txt`** in project folder |
| Session start API | `POST /session/start` — `app/api/routes/session.py` |
| Feedback API (with session_id) | `POST /feedback/` — `app/api/routes/feedback.py` |
| Context length (tool truncation) | `app/agents/chat_agent.py`, `app/core/constants.py` (`MAX_TOOL_OUTPUT_CHARS`) |

---

## Optional: Deployment Outline

- **Docker:** Dockerfile that installs from `requirements.txt`, sets or mounts `.env`, runs `uvicorn app.main:app --host 0.0.0.0 --port 8000`. Multi-stage build and non-root user recommended. Qdrant as separate container or external service.
- **Kubernetes/Helm:** Deploy app as Deployment (or Helm chart) with ConfigMap/Secret for env vars, Service, optional Ingress. Qdrant as separate Deployment or managed vector DB. Document `allow_dangerous_requests` and network policies for URL fetch in production.

---

## Assumptions and Environment

- **Search:** SerpAPI (`SERPAPI_API_KEY`) or Google Custom Search (`GOOGLE_API_KEY`, `GOOGLE_CSE_ID`).
- **LLM:** OpenAI (e.g. GPT-4o-mini); `OPENAI_API_KEY`.
- **RAG / General persist:** Qdrant optional; `QDRANT_URL`, optional `QDRANT_API_KEY`. Without Qdrant, RAG mode and General-mode retrieve/persist are skipped or disabled.
- **Secrets:** No API keys in code; use `.env` or a secrets manager.
