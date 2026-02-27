#!/usr/bin/env python3
"""
Full end-to-end example: user question → fetch data (search / URL) → process → LLM answer.

This script demonstrates:
- Taking a user question (e.g. search, URL summary, or API description).
- Using the agent (General mode) or swarm (Swarm mode) to fetch data.
- Optionally using RAG: retrieve past search/URL context from vector store, then persist new tool results.
- Producing a clear answer (and trace in swarm mode).

Run from project root with .env configured (OPENAI_API_KEY, SERPAPI_API_KEY or GOOGLE_*).
  python examples/run_e2e_example.py "What is the capital of Japan?"
  python examples/run_e2e_example.py "Summarize the content at https://example.com" --mode general
  python examples/run_e2e_example.py "What does https://api.github.com return? Describe main keys." --mode general
  python examples/run_e2e_example.py "What is 15% of 240?" --mode swarm
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Ensure project root is on path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _last_ai_content(messages: list) -> str:
    """Extract content from the last AI message."""
    from langchain_core.messages import AIMessage

    for m in reversed(messages):
        if isinstance(m, AIMessage) and m.content:
            return m.content if isinstance(m.content, str) else str(m.content)
    return "No response generated."


def run_general(question: str, use_rag: bool = True) -> str:
    """
    Run the General-mode agent: search + URL tools, optional RAG (retrieve → agent → persist).
    Fetches data via tools and uses the LLM to synthesize an answer.
    """
    from langchain_core.messages import HumanMessage

    from app.agents import get_chat_agent
    from app.rag.search_store import persist_search_content, retrieve_search_context

    # Optional RAG: retrieve previously stored search/URL content for grounding
    context = ""
    if use_rag:
        try:
            context = retrieve_search_context(question)
        except Exception:
            context = ""
    if context:
        user_content = (
            "Relevant context from previous searches and fetched pages:\n\n"
            f"{context}\n\nUser question: {question}"
        )
    else:
        user_content = question

    agent = get_chat_agent()
    result = agent.invoke({"messages": [HumanMessage(content=user_content)]})
    messages = result.get("messages", [])

    # Optional RAG: persist tool outputs for future retrieval
    if use_rag:
        try:
            from langchain_core.messages import ToolMessage

            for m in messages:
                if isinstance(m, ToolMessage) and getattr(m, "content", None):
                    content = m.content if isinstance(m.content, str) else str(m.content)
                    source = getattr(m, "name", None) or "tool"
                    persist_search_content(text=content, source=source, query=question, url="")
        except Exception:
            pass

    return _last_ai_content(messages)


def run_swarm_mode(question: str) -> tuple[str, list]:
    """
    Run the Swarm: supervisor → researcher / fetcher / coder / analyst → synthesizer.
    Returns (answer, steps_trace).
    """
    from app.swarm import run_swarm

    answer, steps = run_swarm(question, uploaded_files=None)
    return answer or "No answer produced.", steps


def main() -> None:
    parser = argparse.ArgumentParser(
        description="End-to-end example: question → fetch data → LLM answer.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "question",
        nargs="?",
        default="What is the capital of Japan?",
        help="User question (default: What is the capital of Japan?)",
    )
    parser.add_argument(
        "--mode",
        choices=["general", "swarm"],
        default="general",
        help="general = agent with search/URL + optional RAG; swarm = multi-agent (researcher, fetcher, coder, synthesizer)",
    )
    parser.add_argument("--no-rag", action="store_true", help="Disable RAG retrieve/persist in general mode")
    parser.add_argument("--no-trace", action="store_true", help="Do not print swarm trace")
    args = parser.parse_args()

    question = args.question.strip()
    if not question:
        print("Error: empty question", file=sys.stderr)
        sys.exit(1)

    print("Question:", question)
    print("Mode:", args.mode)
    print("-" * 60)

    try:
        if args.mode == "general":
            answer = run_general(question, use_rag=not args.no_rag)
            print("Answer:\n", answer)
        else:
            answer, trace = run_swarm_mode(question)
            print("Answer:\n", answer)
            if trace and not args.no_trace:
                print("\nTrace (steps):")
                for i, s in enumerate(trace[:15], 1):
                    node = s.get("node", "")
                    decision = s.get("decision")
                    preview = s.get("result_preview") or s.get("answer_preview") or ""
                    line = f"  {i}. {node}"
                    if decision:
                        line += f" → {decision}"
                    if preview:
                        line += f" | {preview[:80]}..."
                    print(line)
    except Exception as e:
        print("Error:", e, file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
