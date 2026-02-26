"""Swarm graph state: shared data between supervisor and specialist agents."""

from typing import Any, TypedDict


class SwarmState(TypedDict, total=False):
    """State for the agent swarm. All fields optional for partial updates."""

    query: str
    search_results: list[str]
    url_results: list[str]
    uploaded_files: list[dict[str, Any]]
    analysis_results: list[str]
    code_results: list[str]
    answer: str
    next_agent: str
    next_url: str
    steps: list[dict]
    step_count: int
