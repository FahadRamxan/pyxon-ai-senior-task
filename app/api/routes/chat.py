"""Chat API: send a message to the agent and get a response."""

from typing import Any, Literal

from fastapi import APIRouter, HTTPException
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from pydantic import BaseModel, Field

from app.agents import get_chat_agent
from app.rag import rag_answer
from app.rag.search_store import persist_search_content, retrieve_search_context

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    """Request body for the chat endpoint."""

    message: str = Field(..., min_length=1, max_length=32_000, description="User message for the agent.")
    mode: Literal["general", "rag"] = Field(default="general", description="general = search/URL agent; rag = RAG orchestration over Pyxon PDFs.")


class ChatResponse(BaseModel):
    """Response body for the chat endpoint."""

    output: str = Field(..., description="Agent's reply.")
    success: bool = Field(default=True, description="Whether the request succeeded.")


def _last_ai_content(messages: list[Any]) -> str:
    """Extract content from the last AI message in state."""
    for m in reversed(messages):
        if isinstance(m, AIMessage) and m.content:
            return m.content if isinstance(m.content, str) else str(m.content)
    return "No response generated."


def _persist_tool_results(messages: list[Any], user_query: str) -> None:
    """Extract tool outputs from agent messages and persist into search-results vector store."""
    try:
        for m in messages:
            if isinstance(m, ToolMessage) and getattr(m, "content", None):
                content = m.content if isinstance(m.content, str) else str(m.content)
                source = getattr(m, "name", None) or "tool"
                persist_search_content(
                    text=content,
                    source=source,
                    query=user_query,
                    url="",
                )
    except Exception:
        pass


@router.post("/", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    """
    Send a message to the agent. Use mode="general" for search/URL agent (with persist + retrieve
    of search/URL results in a vector store); mode="rag" for RAG over Pyxon PDFs.
    """
    try:
        if request.mode == "rag":
            output = rag_answer(request.message)
            return ChatResponse(output=output, success=True)
        # General mode: retrieve from search-results store, then run agent, then persist tool outputs
        context = retrieve_search_context(request.message)
        if context:
            user_content = (
                "Relevant context from previous searches and fetched pages:\n\n"
                f"{context}\n\nUser question: {request.message}"
            )
        else:
            user_content = request.message
        agent = get_chat_agent()
        result = agent.invoke({"messages": [HumanMessage(content=user_content)]})
        messages = result.get("messages", [])
        _persist_tool_results(messages, request.message)
        output = _last_ai_content(messages)
        return ChatResponse(output=output, success=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
