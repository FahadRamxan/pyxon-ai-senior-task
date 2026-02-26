# Pyxon AI - Senior AI Engineer Entry Task

## Overview

We are looking for a highly motivated **Senior AI Engineer** to join our team. In this role, you will act as a critical bridge between our core AI platform and our enterprise clients. You will lead the end-to-end deployment of cutting-edge **Agentic AI** and **Generative AI** solutions in complex, secure environments, working directly with customers to solve real-world problems in sectors like finance, healthcare, and telecommunications.

This entry task focuses on **agentic systems**: building agents that use external data sources (e.g., web search, URLs/APIs), reason over that data, and answer user questions—aligned with RAG, agent swarms, and production-grade deployment.

---

## Quick Start (How to Run)

1. **Create a virtual environment and activate it**
   ```bash
   python -m venv .venv
   .venv\Scripts\activate   # Windows
   # source .venv/bin/activate  # macOS/Linux
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**
   - Copy or create a `.env` file in the project root (see example below). **Do not commit `.env`**; it is in `.gitignore`.
   - Required for the chatbot: `OPENAI_API_KEY`, `GOOGLE_API_KEY`, `GOOGLE_CSE_ID`.

4. **Run the FastAPI app**
   ```bash
   uvicorn app.main:app --port 8002 --reload
   ```
   - API: <http://localhost:8002>
   - Full-page chat: <http://localhost:8002/>
   - **Embeddable widget:** <http://localhost:8002/widget> (floating bubble + panel; use in iframe or add `<script src="http://localhost:8002/embed.js" data-base="http://localhost:8002"></script>` to any page)
   - Docs: <http://localhost:8002/docs>
   - Chat API: `POST /chat/` with body `{"message": "Your question here"}`

**Example `.env` (do not commit):**
```env
OPENAI_API_KEY=your-openai-key
GOOGLE_API_KEY=your-google-api-key
GOOGLE_CSE_ID=your-cse-id
# Optional: RAG (Qdrant). Defaults to http://localhost:6333 if not set.
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=
```

### RAG mode (Qdrant)

The chat supports **mode=rag**: an orchestration pipeline over the PDFs in `Pyxon Data RAG/`. An intent classifier routes the query to one or more sub-agents (General, Cloud & Automation, Smart IoT, AI Solutions, Cybersecurity); each sub-agent uses its own Qdrant collection and GPT-4o-mini. Multi-intent queries run sub-agents in parallel, then a synthesizer merges the answers.

1. **Run Qdrant** (e.g. Docker): `docker run -p 6333:6333 qdrant/qdrant`
2. **Ingest PDFs** into Qdrant (once):  
   `python -m app.rag.ingest_cli` or `python -m app.rag.ingest_cli all`  
   Or ingest one agent: `python -m app.rag.ingest_cli general`
3. In the widget, select **RAG** and ask questions; or call `POST /chat/` with `{"message": "...", "mode": "rag"}`.

### General mode: search/URL + persist & retrieve (RAG over search results)

In **mode=general**, the agent uses SerpAPI search and URL (GET/POST) tools. Search and URL results are **persisted** into a Qdrant collection (`pyxon_search_results`) and **retrieved** before each reply for better grounding and reuse:

1. **Retrieve:** The user message is embedded and used to query the `pyxon_search_results` collection; any matching past search/URL content is added as context to the prompt.
2. **Run agent:** The agent runs with that context and may call search/URL tools again.
3. **Persist:** All tool outputs (search snippets, fetched page/API text) are chunked, embedded, and upserted into `pyxon_search_results` for future turns.

So the first time you ask e.g. "Class B license rules in Germany", the agent searches and the results are stored; a follow-up like "What's the minimum age?" can be answered using the retrieved context. Requires Qdrant (same as RAG mode).

### Swarm mode (multi-agent)

**mode=swarm** runs a LangGraph multi-agent swarm: a **supervisor** routes to **researcher** (search), **fetcher** (URL GET), and **synthesizer** (writer). Data from search and URLs flows into shared state and the synthesizer produces the final answer.

- **Widget:** Choose **Swarm** at start or in the chat mode toggle. Each reply shows a **Flow** line at the bottom (e.g. `supervisor → researcher → supervisor → synthesizer → supervisor → finish`).
- **API:** `POST /chat/` with `{"message": "...", "mode": "swarm", "include_trace": true}`. The response includes `output` and optionally `trace` (list of steps: node, decision, result_preview, etc.).
- **Server console:** When the app runs with `uvicorn`, each swarm step is logged (e.g. `INFO ... swarm step 1: supervisor`, `swarm supervisor decision: researcher`). Watch the terminal to see the flow live.

---

## Role Context

### Key Responsibilities (from the role)

- **Lead End-to-End Deployments:** Architect and lead the deployment of an AI workspace platform in private cloud, hybrid, and on-premises environments.
- **Develop Agentic & Generative AI Solutions:** Design and build features for an AI workspace, including autonomous agents that interact with sensitive enterprise data and generate multi-modal outputs.
- **Model Customization & Fine-Tuning:** Customize base models via fine-tuning (e.g., LoRA, QLoRA) and, where applicable, TTS models for custom voices or domain-specific acoustics.
- **Partner with Enterprise Clients:** Work with client IT/engineering teams on infrastructure, security, and data management as a trusted technical advisor.
- **Ensure Security and Compliance:** Design deployment strategies that meet data privacy, security standards, and regulatory compliance.
- **Full Lifecycle Ownership:** From conceptualizing features from customer feedback to troubleshooting and resolving issues in production.
- **Experiment and Innovate:** Operate at high velocity and experiment with new approaches to engage customers and exceed expectations.

### Relevant Required Skills

- **Agentic AI & RAG:** Building and deploying highly performant RAG applications and AI agents using modern frameworks and techniques.
- **Deployment & Orchestration:** Production Kubernetes, Helm, DevOps, CI/CD.
- **Infrastructure:** Strong expertise in at least one major cloud (AWS, Azure, GCP); networking, security, virtualization.
- **Application Development:** Production-grade code, with a strong preference for **Python**; ability to read, understand, and fix issues across the stack.
- **Fine-Tuning:** Experience with LLM fine-tuning (e.g., LoRA, QLoRA) and optionally TTS fine-tuning.
- **Customer-Facing:** Experience working directly with customers, gathering requirements, and guiding complex technical implementations.
- **Technical Knowledge:** Transformers, prompt engineering, security best practices for AI, infrastructure-as-code (e.g., Terraform, Pulumi).

**Nice-to-have:** Multi-modal AI (speech/audio), traditional ML/DL, model quantization/edge deployment, other AI frameworks (LangChain, LlamaIndex), embedding models.

---

## Task Requirements

Your task is to demonstrate **agentic AI** skills by building one or more agents that use **external data sources** and an **LLM** to answer user questions. You may use **LangChain** (and related packages such as **LangGraph**) or another framework of your choice.

### 1. Agent with Search / Data Source (e.g., Google)

Build an **agent that has access to a data source such as Google Search** and uses an LLM to answer questions based on that data.

- The agent should be able to **query the data source** (e.g., run search queries).
- The agent should **consume the returned content** (snippets, links, or full pages) and use the **LLM** to synthesize an answer.
- Optionally, combine with **RAG**: persist search results (or fetched pages) into a vector store and use retrieval before generation for better grounding and citations.

**Does LangChain support this?** Yes. LangChain provides:

- **Google Search:** e.g. `GoogleSearchAPIWrapper` (requires `GOOGLE_API_KEY` and `GOOGLE_CSE_ID`). You can expose it as a tool and use it with an agent.
- **Agent + tools:** Use `load_tools(["google-search"], llm=llm)` and an agent (e.g. ReAct) so the LLM decides when to search and how to use results to answer.

You are free to use another search provider (e.g., SerpAPI, Bing, Tavily) if you prefer.

### 2. Agent That Requests URLs and Processes Them (e.g., APIs / Web Pages)

Build an **agent that can make HTTP requests to URLs**, process the response (e.g., HTML or JSON from an API), **understand what is there**, and use that information to **answer user questions**.

- The agent should be able to **call URLs** (GET and, if useful, POST) and get response content.
- The agent should **interpret** the content (e.g., parse JSON, extract text from HTML) and feed it to the LLM.
- The LLM should use this content to **answer questions** or perform tasks (e.g., “What does this API return?” or “Summarize the content at this URL”).

**Does LangChain support this?** Yes. LangChain provides:

- **Requests tools:** e.g. `RequestsGetTool` (GET a URL and return response text). Load via `load_tools(["requests_all"], allow_dangerous_requests=True)` (opt-in for security). Similar tools exist for POST, PATCH, PUT, DELETE.
- You can also build **custom tools** that call `requests` or `httpx`, parse JSON/HTML, and return a string for the LLM.

Use these (or custom tools) inside an agent so the LLM decides which URLs to call and how to use the responses.

### 3. Agent Swarm (Multi-Agent System) with LangChain / LangGraph

Create an **agent swarm** (multi-agent system) using **LangChain** (and optionally **LangGraph**).

- **Multiple agents** with distinct roles (e.g., one for search, one for URL fetching, one for synthesis or coding).
- **Coordination:** agents can hand off tasks, use each other as tools, or be orchestrated by a router/supervisor.
- **Data flow:** ensure that data from external sources (search, URLs/APIs) is used by the swarm to answer user questions.

**Does LangChain/LangGraph support this?** Yes. LangGraph provides:

- **Multi-agent patterns:** subagents, handoffs, router, or custom workflows.
- **Swarm-style coordination:** e.g. `langgraph-swarm` with `create_swarm()` for multiple agents (graphs) working together.
- **Examples:** multi-agent collaboration, multi-agent networks (e.g., inspired by AutoGen-style designs).

Your swarm should demonstrate at least one of: search-backed answers, URL/API-backed answers, or a clear division of labor (e.g., researcher + writer + critic).

---

## Deliverables

Provide the following in your submission:

1. **Working code** for:
   - An agent that uses a search/data source (e.g., Google) + LLM to answer questions, and/or  
   - An agent that requests URLs (and optionally APIs), processes the content, and uses the LLM to answer, and/or  
   - An agent swarm (multi-agent system) that uses external data (search and/or URLs) and an LLM to answer questions.

2. **One full end-to-end example** (script or notebook) that:
   - Takes a **user question** (e.g., “What is the current weather in Amman?” or “Summarize the content at https://example.com” or “What does the API at https://api.example.com/status return?”).
   - Uses your agent(s) to **fetch data** (search and/or URL/API).
   - **Processes** the data (parse, optionally store in a vector store for RAG).
   - Uses the **LLM** to produce a clear **answer** (and optionally citations/sources).

3. **README** (or section in a README) that explains:
   - How to run the code (dependencies, env vars, e.g. `GOOGLE_API_KEY`, `GOOGLE_CSE_ID`, LLM API keys).
   - Architecture: which agents/tools you used, how data flows from search/URLs to the LLM.
   - One or two example questions and the expected behavior (or sample outputs).

4. **Optional but valued:**
   - Simple **RAG** integration (e.g., index search results or URL content in a vector store, then retrieve before generating).
   - **Tests** or a small **benchmark** (e.g., a few fixed Q&A pairs) to verify behavior.
   - **Docker** or **Kubernetes/Helm** outline for running the agent in a container or cluster (aligned with the role’s deployment focus).

---

## Full Example Outline (Reference)

Below is a **minimal structure** for a single agent that uses **Google Search** and **URL fetching** to answer questions. You can extend this into a swarm or add RAG.

```python
# Example structure (pseudocode – adapt to your preferred LangChain/LangGraph APIs)

# 1. Tools
# - Google Search: GoogleSearchAPIWrapper or load_tools(["google-search"], llm=llm)
# - URL fetch: RequestsGetTool or load_tools(["requests_all"], allow_dangerous_requests=True)
# - Optional: custom tool that GETs a URL, parses JSON/HTML, returns a string

# 2. Agent
# - Create an agent (e.g. create_react_agent or AgentExecutor) with tools = [search_tool, requests_tool]
# - System message: "You can search the web and fetch URLs. Use the results to answer the user's question."

# 3. Run
# - user_question = "What is the latest news about X?" or "What does https://api.example.com/info return?"
# - result = agent.invoke({"input": user_question})
# - Print result["output"] and, if available, citations/sources
```

**LangChain/LangGraph references (as of 2024):**

- **Google Search:** [LangChain Google Search integration](https://python.langchain.com/docs/integrations/tools/google_search/)  
- **Requests (URL fetch):** [LangChain Requests tools](https://python.langchain.com/docs/integrations/tools/requests/) (use `allow_dangerous_requests=True` where required)  
- **Multi-agent / swarm:** [LangGraph multi-agent](https://langchain-ai.github.io/langgraph/agents/multi-agent/), [LangGraph Swarm](https://reference.langchain.com/python/langgraph/swarm/)  
- **RAG:** LangChain retrieval chains and vector stores (e.g., from document loaders or from fetched URL content)

You may implement in **Python** with **LangChain/LangGraph** or another framework (e.g., LlamaIndex, custom orchestration); the above is a suggested path that matches the “LangChain agent with Google + URL requests” idea.

---

## Technical Specifications

### Technology Stack

- **Language:** Python preferred (per role).
- **Frameworks:** LangChain, LangGraph, LlamaIndex, or equivalent agent/RAG frameworks.
- **LLM:** Any compatible model (OpenAI, Anthropic, local models, etc.); specify in README.
- **Search:** Google Search API (or SerpAPI, Tavily, Bing, etc.).
- **URL/HTTP:** `requests` or `httpx`; LangChain’s Requests tools or custom tools.
- **Optional:** Vector store (Chroma, FAISS, etc.) for RAG; Docker/K8s for deployment.

### Security and Safety

- Do **not** hardcode API keys; use environment variables or a secrets manager.
- If using `requests_all` or similar, be aware of the security implications (arbitrary URL fetch); use `allow_dangerous_requests` only where necessary and document it.
- For deployment, consider network policies, private endpoints, and least-privilege access (aligned with the role’s security and compliance focus).

---

## Submission Guidelines

### Process

1. **Fork this repository** to your GitHub account.
2. **Implement** the required agent(s) and the full example as described above.
3. **Add a README** :
   - How to run the code (install, env vars, commands).
   - Architecture and data flow (search → agent, URL → agent, or swarm).
   - Example questions and expected behavior (or sample outputs).
4. **Create a Pull Request** with:
   - **Contact information** (email or phone).
   - **Summary** of what was implemented (which of the three tasks: search agent, URL agent, swarm).
   - **How to run** and any **assumptions** (e.g., which search provider, which LLM).
   - **Optional:** Demo link (e.g., Streamlit/Gradio app), benchmark results, or deployment notes.

### PR Description Template

```markdown
## Summary
Brief overview: e.g., "Agent using Google Search + URL fetch + LLM; optional swarm with LangGraph."

## Contact Information
📧 Email: [your-email@example.com] or 📱 Phone: [your-phone-number]

## Features Implemented
- [ ] Agent with search data source (e.g., Google) + LLM answers
- [ ] Agent that requests URLs/APIs and uses content to answer
- [ ] Agent swarm (multi-agent) with LangChain/LangGraph
- [ ] Full end-to-end example (question → data → answer)
- [ ] README with run instructions and architecture
- [ ] (Optional) RAG, tests, or Docker/K8s notes

## Architecture
Description of agents, tools, and data flow.

## How to Run
Dependencies, env vars, and commands.

## Example Questions & Behavior
1–2 example questions and what the agent(s) do.

## Assumptions
Any assumptions about APIs, models, or environment.
```

---

## Evaluation Criteria

Submissions will be evaluated on:

1. **Functionality:** Agent(s) correctly use search and/or URL/API data and produce coherent, grounded answers.
2. **Code quality:** Clear, maintainable, and documented code.
3. **Design:** Sensible choice of tools, prompts, and (if applicable) swarm coordination.
4. **Completeness:** Full runnable example and README; no placeholders for critical paths.
5. **Security awareness:** No hardcoded secrets; documentation of any dangerous options.
6. **Bonus:** RAG integration, tests, or deployment-oriented notes (Docker/K8s) as differentiators.

---

## Summary of “Does LangChain have that?”

| Requirement | LangChain/LangGraph support |
|-------------|-----------------------------|
| Agent with access to data source like Google | ✅ Yes – e.g. `GoogleSearchAPIWrapper`, `load_tools(["google-search"])` with an agent. |
| Agent uses LLM to answer based on that data | ✅ Yes – agent uses tool results as context for the LLM to generate answers. |
| Agent can request URLs and process like APIs | ✅ Yes – e.g. `RequestsGetTool` / `requests_all`; custom tools for parsing JSON/HTML. |
| Agent swarm / multi-agent | ✅ Yes – LangGraph multi-agent patterns and `langgraph-swarm` (e.g. `create_swarm()`). |
| Full example | ✅ This README provides an outline; your submission should provide a full runnable example. |

Good luck. We look forward to your implementation.
