"""Orchestrator: classify intent, run sub-agents in parallel, synthesize response."""

from concurrent.futures import ThreadPoolExecutor, as_completed

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from app.config import settings
from app.rag.agents import run_sub_agent
from app.rag.config import RAG_AGENTS, RAG_LLM_MODEL
from app.rag.intent import classify_intents

SYNTHESIS_PROMPT = """You are a coordinator. The user asked a question, and multiple specialist agents have each provided an answer based on the company knowledge base. Combine their answers into one clear, coherent response. Do not contradict the specialists. If different agents gave overlapping info, merge it. If they gave different aspects, include both. Do not add information that was not in the specialist answers.

**Formatting:** Use Markdown: `##` or `###` for section titles. Use **bold** sparingly. **Line breaks:** After each section heading use exactly one blank line, then list the items. Between list items (addresses, contact lines) use only a single line break—no blank line between them. Between sections use exactly one blank line. Do not put blank lines between consecutive list items.

User question: {query}

Specialist answers:
{agent_answers}

Provide a single, well-structured answer. Section headings with ##, bullets for lists, minimal bold, tight line spacing."""


def _run_agents_parallel(query: str, intents: list[str]) -> dict[str, str]:
    """Run each intent's sub-agent; return agent_key -> answer."""
    result: dict[str, str] = {}
    with ThreadPoolExecutor(max_workers=min(len(intents), 5)) as ex:
        futures = {ex.submit(run_sub_agent, key, query): key for key in intents}
        for fut in as_completed(futures):
            key = futures[fut]
            try:
                result[key] = fut.result()
            except Exception as e:
                result[key] = f"[Error from {RAG_AGENTS[key]['name']}]: {e}"
    return result


def _synthesize(query: str, agent_answers: dict[str, str]) -> str:
    """Single LLM call to merge sub-agent answers into one response."""
    parts = [
        f"**{RAG_AGENTS[k]['name']}:**\n{v}"
        for k, v in agent_answers.items()
    ]
    combined = "\n\n".join(parts)
    llm = ChatOpenAI(
        model=RAG_LLM_MODEL,
        api_key=settings.OPENAI_API_KEY,
        temperature=0.0,
    )
    prompt = ChatPromptTemplate.from_messages([("human", SYNTHESIS_PROMPT)])
    chain = prompt | llm
    msg = chain.invoke({"query": query, "agent_answers": combined})
    return msg.content if hasattr(msg, "content") else str(msg)


def rag_answer(query: str) -> str:
    """
    Full RAG orchestration: classify intents, run sub-agents in parallel, synthesize.
    """
    query = (query or "").strip()
    if not query:
        return "Please ask a question."
    intents = classify_intents(query)
    if not intents:
        intents = ["general"]
    if len(intents) == 1:
        return run_sub_agent(intents[0], query)
    agent_answers = _run_agents_parallel(query, intents)
    return _synthesize(query, agent_answers)
