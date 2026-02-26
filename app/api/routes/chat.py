"""Chat API: send a message to the agent and get a response."""

from typing import Any, Literal

from fastapi import APIRouter, HTTPException
from langchain_core.messages import AIMessage, HumanMessage
from pydantic import BaseModel, Field

from app.agents import get_chat_agent
from app.rag import rag_answer

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


@router.post("/", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    """
    Send a message to the agent. Use mode="general" for search/URL agent,
    mode="rag" for RAG orchestration over Pyxon PDFs (intent → sub-agents → synthesis).
    """
    try:
        if request.mode == "rag":
            output = rag_answer(request.message)
            return ChatResponse(output=output, success=True)
        agent = get_chat_agent()
        result = agent.invoke(
            {"messages": [HumanMessage(content=request.message)]}
        )
        messages = result.get("messages", [])
        output = _last_ai_content(messages)
        return ChatResponse(output=output, success=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
