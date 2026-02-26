"""Sub-agents: retrieve from per-agent Qdrant collection and generate answer with GPT-4o-mini."""

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from app.config import settings
from app.rag.config import RAG_AGENTS, RAG_LLM_MODEL, RAG_TOP_K
from app.rag.embeddings import get_embeddings
from app.rag.qdrant_client import get_qdrant_client

SUBAGENT_PROMPT = """You are the {agent_name}. Use ONLY the following retrieved context from the company knowledge base to answer the user question. Do not invent information.

**When the context contains the answer:** Reply in clear Markdown. Use `##` or `###` for section titles (e.g. Locations, Contact Information). Use **bold** sparingly—only for one or two key terms, never for whole lines.

**Line breaks (strict):** After a section heading, use exactly one blank line, then list the items. Between list items (e.g. two addresses, or several contact lines) use only a single line break—no blank line between them. Between sections use exactly one blank line. Example format:
## Locations

First address
Second address

## Contact Information

Line one
Line two
Line three

**When the context does NOT contain the answer:** Reply in one short sentence, e.g. "We'll get back to you with that information." Use the same tone for any missing topic.

Context:
---
{context}
---

User question: {query}

Answer:"""


def retrieve_chunks(agent_key: str, query: str, top_k: int = RAG_TOP_K) -> list[str]:
    """Retrieve top_k chunks from the agent's Qdrant collection."""
    if agent_key not in RAG_AGENTS:
        return []
    coll = RAG_AGENTS[agent_key]["collection"]
    embeddings = get_embeddings()
    query_vector = embeddings.embed_query(query)
    client = get_qdrant_client()
    response = client.query_points(
        collection_name=coll,
        query=query_vector,
        limit=top_k,
    )
    points = getattr(response, "points", []) or []
    return [p.payload.get("content", "") for p in points if p.payload]


def run_sub_agent(agent_key: str, query: str) -> str:
    """Run one sub-agent: retrieve from its collection, then generate answer."""
    agent_name = RAG_AGENTS[agent_key]["name"]
    chunks = retrieve_chunks(agent_key, query)
    if not chunks:
        return f"**We'll get back to you with that information.**"
    context = "\n\n".join(chunks)
    llm = ChatOpenAI(
        model=RAG_LLM_MODEL,
        api_key=settings.OPENAI_API_KEY,
        temperature=0.0,
    )
    prompt = ChatPromptTemplate.from_messages([("human", SUBAGENT_PROMPT)])
    chain = prompt | llm
    msg = chain.invoke({
        "agent_name": agent_name,
        "context": context,
        "query": query,
    })
    return msg.content if hasattr(msg, "content") else str(msg)
