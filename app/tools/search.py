"""Web search tool for the agent. Uses SerpAPI when SERPAPI_API_KEY is set."""

from langchain_core.tools import Tool
from langchain_community.utilities.serpapi import SerpAPIWrapper

from app.config import settings


def get_search_tool() -> Tool:
    """Build search tool using SerpAPI (SERPAPI_API_KEY)."""
    wrapper = SerpAPIWrapper(
        serpapi_api_key=settings.SERPAPI_API_KEY or "",
    )
    return Tool(
        name="Search",
        description=(
            "A search engine. Useful for when you need to answer questions about "
            "current events. Input should be a search query."
        ),
        func=wrapper.run,
        coroutine=wrapper.arun,
    )
