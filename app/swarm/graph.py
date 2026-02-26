"""LangGraph swarm: supervisor, researcher, fetcher, synthesizer with flow trace."""

import logging
from typing import Literal

logger = logging.getLogger(__name__)

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph

from app.config import settings
from app.core.constants import DEFAULT_LLM_MODEL
from app.swarm.state import SwarmState
from app.tools import get_search_tool, get_url_fetch_tool, run_python

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
MAX_STEPS = 10

SUPERVISOR_PROMPT = """You are the supervisor of an agent swarm. The user asked a question or uploaded a file. Choose exactly one next step.

Current state:
- User question: {query}
- Search results: {search_count} item(s)
- URL fetch results: {url_count} item(s)
- Uploaded files: {file_count} (analysis: {analysis_count} item(s))
- Code execution results: {code_count} item(s)
- Answer drafted: {has_answer}

Reply with exactly one word: researcher, fetcher, analyst, coder, synthesizer, finish

- researcher: get web search results (when we need more search data).
- fetcher: fetch a URL. If you choose fetcher, add a second line: URL: <exact URL>.
- analyst: analyze uploaded file(s) or extract questions from them (use when there are uploaded files and we have not analyzed them yet).
- coder: run code for calculation, data processing, or when the user asks to compute/code something.
- synthesizer: produce the final answer from all evidence (search, URL, analysis, code).
- finish: we are done.

Rules: Call analyst at most ONCE (only when there are uploaded files and analysis_count is 0). Call synthesizer at most ONCE when we have evidence. Use "coder" when the user asks for code or computation. Do not call researcher more than 2 times. After analyst or synthesizer has run, choose synthesizer or finish next, not analyst again."""

RESEARCHER_PROMPT = """You are the Researcher agent. Your only job is to run a web search for the user's question and return the results. Do not answer the question yourself.

User question: {query}

Run the Search tool with an appropriate search query (one that will find information to answer the question). Return the raw tool output."""

FETCHER_PROMPT = """You are the Fetcher agent. Your only job is to fetch the content from the given URL and return it. Do not answer the question yourself.

URL to fetch: {url}

Run the requests_get tool with this URL. Return the raw tool output (or a short summary if the page is very long)."""

ANALYST_PROMPT = """You are the Analysis agent. The user has uploaded one or more files. Analyze the file content and either: (1) summarize the document and extract key points, or (2) extract questions that the document answers or raises. If the user asked a specific question about the file, answer it based on the content. Return a clear, structured analysis (use bullet points or short sections). Do not invent content not in the file.

User question: {query}

File content (filename: {filename}):
{content}

Your analysis:"""

CODER_PROMPT = """You are the Coding agent. The user needs code to be run (calculation, data processing, or a small script). Generate only valid Python code that does what the user asked. Return ONLY the code, no markdown and no explanation. The code will be executed; print() the result so we can see it.

User request: {query}

Python code:"""

SYNTHESIZER_PROMPT = """You are the Synthesizer (Writer) agent. You have no tools. Use ONLY the following evidence to write a clear, concise answer to the user's question. Cite sources (e.g. "According to search results...", "From the file analysis...", "The code output shows...").

User question: {query}

Search results:
{search_block}

URL fetch results:
{url_block}

File analysis:
{analysis_block}

Code execution results:
{code_block}

Write a single, well-structured answer. Do not invent information not present in the evidence above."""


def _get_llm():
    return ChatOpenAI(
        model=DEFAULT_LLM_MODEL,
        api_key=settings.OPENAI_API_KEY,
        temperature=0.0,
    )


def _parse_supervisor_output(text: str) -> tuple[str, str]:
    """Parse supervisor reply: next_agent and optional URL."""
    text = (text or "").strip().lower()
    lines = [ln.strip() for ln in text.split("\n") if ln.strip()]
    next_agent = "finish"
    next_url = ""
    for line in lines:
        if line in ("researcher", "fetcher", "synthesizer", "analyst", "coder", "finish"):
            next_agent = line
            break
    if next_agent == "fetcher":
        for line in lines[1:]:
            if line.startswith("url:"):
                next_url = line[4:].strip()
                break
    return next_agent, next_url


def _supervisor_node(state: SwarmState) -> dict:
    """Decide next agent or finish. Append step to trace."""
    query = state.get("query") or ""
    search_results = state.get("search_results") or []
    url_results = state.get("url_results") or []
    uploaded_files = state.get("uploaded_files") or []
    analysis_results = state.get("analysis_results") or []
    code_results = state.get("code_results") or []
    answer = state.get("answer") or ""
    steps = list(state.get("steps") or [])
    step_count = state.get("step_count") or 0

    step_count += 1
    logger.info("swarm step %s: supervisor", step_count)
    if step_count > MAX_STEPS:
        steps.append({"node": "supervisor", "decision": "finish", "reason": "max_steps"})
        return {"next_agent": "finish", "steps": steps, "step_count": step_count}

    llm = _get_llm()
    prompt = ChatPromptTemplate.from_messages([("human", SUPERVISOR_PROMPT)])
    chain = prompt | llm
    out = chain.invoke(
        {
            "query": query,
            "search_count": len(search_results),
            "url_count": len(url_results),
            "file_count": len(uploaded_files),
            "analysis_count": len(analysis_results),
            "code_count": len(code_results),
            "has_answer": "yes" if answer else "no",
        }
    )
    content = out.content if hasattr(out, "content") else str(out)
    next_agent, next_url = _parse_supervisor_output(content)
    logger.info("swarm supervisor decision: %s (url=%s)", next_agent, next_url or "(none)")
    steps.append({"node": "supervisor", "decision": next_agent, "next_url": next_url or None})
    return {
        "next_agent": next_agent,
        "next_url": next_url,
        "steps": steps,
        "step_count": step_count,
    }


def _researcher_node(state: SwarmState) -> dict:
    """Run search tool, append result to search_results, append step."""
    query = state.get("query") or ""
    search_results = list(state.get("search_results") or [])
    steps = list(state.get("steps") or [])

    tool = get_search_tool()
    try:
        result = tool.invoke(query)
        text = result if isinstance(result, str) else str(result)
    except Exception as e:
        text = f"Search error: {e}"
    logger.info("swarm step: researcher (query=%s)", query[:50])
    search_results.append(text[:8000])
    steps.append({"node": "researcher", "result_preview": text[:200] + "..." if len(text) > 200 else text})
    return {"search_results": search_results, "steps": steps}


def _fetcher_node(state: SwarmState) -> dict:
    """Fetch URL from state['next_url'], append to url_results, append step."""
    next_url = (state.get("next_url") or "").strip()
    url_results = list(state.get("url_results") or [])
    steps = list(state.get("steps") or [])

    if not next_url or not next_url.startswith("http"):
        logger.info("swarm step: fetcher skipped (no valid URL)")
        steps.append({"node": "fetcher", "skip": "no_valid_url", "next_url": next_url or None})
        return {"url_results": url_results, "steps": steps}
    logger.info("swarm step: fetcher (url=%s)", next_url[:60])

    tool = get_url_fetch_tool()
    try:
        result = tool.invoke(next_url)
        text = result if isinstance(result, str) else str(result)
    except Exception as e:
        text = f"Fetch error: {e}"
    url_results.append(text[:8000])
    steps.append({"node": "fetcher", "url": next_url, "result_preview": text[:200] + "..." if len(text) > 200 else text})
    return {"url_results": url_results, "steps": steps}


def _analyst_node(state: SwarmState) -> dict:
    """Analyze uploaded file(s): summarize, extract questions, or answer a question about the file."""
    query = state.get("query") or ""
    uploaded_files = state.get("uploaded_files") or []
    analysis_results = list(state.get("analysis_results") or [])
    steps = list(state.get("steps") or [])

    if not uploaded_files:
        logger.info("swarm step: analyst skipped (no uploaded files)")
        steps.append({"node": "analyst", "skip": "no_files"})
        return {"analysis_results": analysis_results, "steps": steps}

    logger.info("swarm step: analyst (files=%s)", len(uploaded_files))
    llm = _get_llm()
    for f in uploaded_files:
        filename = f.get("filename", "file")
        content = (f.get("content") or "")[:15000]
        if not content.strip():
            analysis_results.append(f"[{filename}] (empty or unreadable)")
            continue
        prompt = ChatPromptTemplate.from_messages([("human", ANALYST_PROMPT)])
        chain = prompt | llm
        out = chain.invoke({"query": query, "filename": filename, "content": content})
        analysis = out.content if hasattr(out, "content") else str(out)
        analysis_results.append(f"[{filename}]\n{analysis}")
    steps.append({"node": "analyst", "result_preview": analysis_results[-1][:200] + "..." if analysis_results else "ok"})
    return {"analysis_results": analysis_results, "steps": steps}


def _coder_node(state: SwarmState) -> dict:
    """Generate and run Python code for the user's request."""
    query = state.get("query") or ""
    code_results = list(state.get("code_results") or [])
    steps = list(state.get("steps") or [])

    logger.info("swarm step: coder (query=%s)", query[:50])
    llm = _get_llm()
    prompt = ChatPromptTemplate.from_messages([("human", CODER_PROMPT)])
    chain = prompt | llm
    out = chain.invoke({"query": query})
    code = (out.content if hasattr(out, "content") else str(out)).strip()
    # Remove markdown code fence if present
    if code.startswith("```"):
        lines = code.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        code = "\n".join(lines)
    try:
        result = run_python.invoke(code)
        text = result if isinstance(result, str) else str(result)
    except Exception as e:
        text = f"Execution error: {e}"
    code_results.append(text[:8000])
    steps.append({"node": "coder", "result_preview": text[:200] + "..." if len(text) > 200 else text})
    return {"code_results": code_results, "steps": steps}


def _synthesizer_node(state: SwarmState) -> dict:
    """Produce final answer from all evidence: search, URL, analysis, code."""
    query = state.get("query") or ""
    search_results = state.get("search_results") or []
    url_results = state.get("url_results") or []
    analysis_results = state.get("analysis_results") or []
    code_results = state.get("code_results") or []
    steps = list(state.get("steps") or [])

    logger.info("swarm step: synthesizer (writing answer)")
    search_block = "\n\n".join(search_results) if search_results else "(none)"
    url_block = "\n\n".join(url_results) if url_results else "(none)"
    analysis_block = "\n\n".join(analysis_results) if analysis_results else "(none)"
    code_block = "\n\n".join(code_results) if code_results else "(none)"

    llm = _get_llm()
    prompt = ChatPromptTemplate.from_messages([("human", SYNTHESIZER_PROMPT)])
    chain = prompt | llm
    out = chain.invoke(
        {
            "query": query,
            "search_block": search_block[:10000],
            "url_block": url_block[:10000],
            "analysis_block": analysis_block[:10000],
            "code_block": code_block[:5000],
        }
    )
    answer = out.content if hasattr(out, "content") else str(out)
    steps.append({"node": "synthesizer", "answer_preview": answer[:150] + "..." if len(answer) > 150 else answer})
    return {"answer": answer, "steps": steps}


def _route_after_supervisor(state: SwarmState):
    """Route from supervisor to next node or END. Override to avoid redundant analyst/synthesizer runs."""
    next_agent = (state.get("next_agent") or "finish").strip().lower()
    analysis_results = state.get("analysis_results") or []
    uploaded_files = state.get("uploaded_files") or []
    has_data = bool(
        state.get("search_results")
        or state.get("url_results")
        or analysis_results
        or state.get("code_results")
    )
    has_answer = bool(state.get("answer"))

    # Already have file analysis → don't run analyst again; go to synthesizer
    if next_agent == "analyst" and len(analysis_results) >= 1 and len(uploaded_files) > 0:
        next_agent = "synthesizer"
    # Already have final answer → finish, don't run synthesizer again
    if next_agent == "synthesizer" and has_answer:
        return END

    if next_agent == "finish":
        if not has_answer and has_data:
            return "synthesizer"
        return END
    if next_agent == "researcher":
        return "researcher"
    if next_agent == "fetcher":
        return "fetcher"
    if next_agent == "analyst":
        return "analyst"
    if next_agent == "coder":
        return "coder"
    if next_agent == "synthesizer":
        return "synthesizer"
    return END


def _start_route(state: SwarmState):
    """When user uploaded files and we have no analysis yet, run analyst first to save a supervisor round."""
    if state.get("uploaded_files") and not state.get("analysis_results"):
        return "analyst"
    return "supervisor"


def build_swarm_graph():
    """Build and compile the LangGraph swarm."""
    builder = StateGraph(SwarmState)
    builder.add_node("supervisor", _supervisor_node)
    builder.add_node("researcher", _researcher_node)
    builder.add_node("fetcher", _fetcher_node)
    builder.add_node("analyst", _analyst_node)
    builder.add_node("coder", _coder_node)
    builder.add_node("synthesizer", _synthesizer_node)

    builder.add_conditional_edges(START, _start_route, {"analyst": "analyst", "supervisor": "supervisor"})
    builder.add_conditional_edges("supervisor", _route_after_supervisor)
    builder.add_edge("researcher", "supervisor")
    builder.add_edge("fetcher", "supervisor")
    builder.add_edge("analyst", "supervisor")
    builder.add_edge("coder", "supervisor")
    builder.add_edge("synthesizer", "supervisor")

    return builder.compile()


def run_swarm(
    query: str,
    uploaded_files: list[dict] | None = None,
) -> tuple[str, list[dict]]:
    """
    Run the swarm for one user query. Optionally pass uploaded file(s) with keys filename, content (text).
    Returns (final_answer, steps_trace).
    """
    graph = build_swarm_graph()
    initial: SwarmState = {
        "query": query,
        "search_results": [],
        "url_results": [],
        "uploaded_files": uploaded_files or [],
        "analysis_results": [],
        "code_results": [],
        "answer": "",
        "next_agent": "",
        "next_url": "",
        "steps": [],
        "step_count": 0,
    }
    result = graph.invoke(initial)
    answer = result.get("answer") or ""
    steps = result.get("steps") or []
    return answer, steps
