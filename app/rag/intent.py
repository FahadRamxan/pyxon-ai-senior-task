"""Intent classifier: route queries to one or more RAG sub-agents."""

import json
import re

from langchain_openai import ChatOpenAI

from app.config import settings
from app.rag.config import RAG_AGENTS, RAG_LLM_MODEL

INTENT_KEYS = list(RAG_AGENTS.keys())

CLASSIFIER_PROMPT = """You are an intent classifier for a company knowledge base. The user query can touch one or more of these domains. Return a JSON array of intent keys that are relevant to answering the query. Only include intents that are clearly relevant.

Intent keys (use exactly these): general, cloud_automation, smart_iot, ai_solutions, cybersecurity.

- general: company overview, home, who we are, what we do, general info.
- cloud_automation: cloud, automation, DevOps, infrastructure.
- smart_iot: smart solutions, IoT, connected devices, sensors.
- ai_solutions: AI, machine learning, ML, artificial intelligence solutions.
- cybersecurity: security, cyber, compliance, risk, secure.

If the query is generic (e.g. "hello", "what can you do") or could be answered by company overview alone, return ["general"].
If the query clearly spans multiple domains, return multiple keys, e.g. ["general", "cybersecurity"].

User query: "{query}"

Respond with ONLY a JSON array of strings, e.g. ["general"] or ["ai_solutions", "cybersecurity"]. No other text."""


def classify_intents(query: str) -> list[str]:
    """Return list of intent keys (one or more) for the query."""
    llm = ChatOpenAI(
        model=RAG_LLM_MODEL,
        api_key=settings.OPENAI_API_KEY,
        temperature=0.0,
    )
    prompt = CLASSIFIER_PROMPT.format(query=query.strip())
    response = llm.invoke(prompt)
    text = (response.content or "").strip()
    # Extract JSON array (allow for markdown code block)
    match = re.search(r"\[[\s\S]*?\]", text)
    if not match:
        return ["general"]
    try:
        arr = json.loads(match.group())
        if isinstance(arr, list):
            out = [k for k in arr if k in RAG_AGENTS]
            return out if out else ["general"]
    except json.JSONDecodeError:
        pass
    return ["general"]
