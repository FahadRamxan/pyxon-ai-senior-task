"""ReAct-style agent with search and URL/API fetch tools, powered by GPT-4o-mini."""

from langchain.agents import create_agent
from langchain_openai import ChatOpenAI

from app.config import settings
from app.core.constants import DEFAULT_LLM_MODEL, DEFAULT_LLM_TEMPERATURE
from app.tools import get_search_tool, get_url_fetch_tool, get_url_post_tool

SYSTEM_PROMPT = """You can search the web and call URLs/APIs to get data. Use the results to answer the user.

- **Search**: Use the search tool for current events or general questions.
- **URLs/APIs**: Use the fetch (GET) tool to get content from a URL or API. You receive the response as text (HTML or JSON). Interpret that content and use it to answer questions, e.g. "What does this API return?", "Summarize the content at this URL", or explain what the page says.
- **POST**: When an API requires a POST body, use the POST tool with a JSON string containing "url" and "data".

When the user message includes "Relevant context from previous searches and fetched pages", use that context to ground your answer and cite it when possible (e.g. mention "from search results" or "according to the fetched page" or the source/URL if shown). Always use tool output and any provided context to formulate your reply; cite or summarize sources when relevant."""


def get_llm() -> ChatOpenAI:
    """Build ChatOpenAI with configured model and temperature."""
    return ChatOpenAI(
        model=DEFAULT_LLM_MODEL,
        api_key=settings.OPENAI_API_KEY,
        temperature=DEFAULT_LLM_TEMPERATURE,
    )


def get_chat_agent():
    """Build an agent with search and URL fetch (GET + POST) tools."""
    llm = get_llm()
    tools = [
        get_search_tool(),
        get_url_fetch_tool(),
        get_url_post_tool(),
    ]
    graph = create_agent(
        llm,
        tools,
        system_prompt=SYSTEM_PROMPT,
    )
    return graph
