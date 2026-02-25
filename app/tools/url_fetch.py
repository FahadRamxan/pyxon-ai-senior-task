"""URL/HTTP fetch tools for the agent. GET and POST to arbitrary URLs/APIs."""

from langchain_community.tools.requests.tool import RequestsGetTool, RequestsPostTool
from langchain_community.utilities.requests import TextRequestsWrapper

from app.core.constants import ALLOW_DANGEROUS_REQUESTS

_REQUEST_WRAPPER = TextRequestsWrapper()

# Descriptions tuned so the LLM uses these to fetch, interpret, and answer from URL/API content.
GET_DESCRIPTION = (
    "Fetch content from a URL (web page or API). Input is a single URL string (e.g. https://example.com). "
    "Returns the response body as text (HTML or JSON). Use this to summarize a page, answer "
    "'what does this URL say?', or interpret what an API returns."
)
POST_DESCRIPTION = (
    "Send a POST request to a URL with a JSON body. Input must be a JSON string with two keys: "
    '"url" (string) and "data" (object). Example: {"url": "https://api.example.com/echo", "data": {"key": "value"}}. '
    "Returns the response body as text. Use for APIs that require POST."
)


def get_url_fetch_tool() -> RequestsGetTool:
    """Build a GET-request tool. Fetches URL/API and returns response as text for the LLM."""
    tool = RequestsGetTool(
        requests_wrapper=_REQUEST_WRAPPER,
        allow_dangerous_requests=ALLOW_DANGEROUS_REQUESTS,
    )
    tool.description = GET_DESCRIPTION
    return tool


def get_url_post_tool() -> RequestsPostTool:
    """Build a POST-request tool. Sends JSON body to URL and returns response text."""
    tool = RequestsPostTool(
        requests_wrapper=_REQUEST_WRAPPER,
        allow_dangerous_requests=ALLOW_DANGEROUS_REQUESTS,
    )
    tool.description = POST_DESCRIPTION
    return tool
