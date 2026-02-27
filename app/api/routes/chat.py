"""Chat API: send a message to the agent and get a response."""

import uuid
from typing import Any, Literal, Optional

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from pydantic import BaseModel, Field

from app.agents import get_chat_agent
from app.rag import rag_answer
from app.rag.search_store import persist_search_content, retrieve_search_context
from app.session_store import add_message_id, get_or_create_session
from app.swarm import run_swarm
from app.utils.file_extract import extract_text_from_file

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    """Request body for the chat endpoint (JSON)."""

    message: str = Field(..., min_length=1, max_length=32_000, description="User message for the agent.")
    mode: Literal["general", "rag", "swarm"] = Field(
        default="general",
        description="general = search/URL + persist; rag = PDF RAG; swarm = multi-agent (supervisor + researcher + fetcher + analyst + coder + synthesizer).",
    )
    include_trace: bool = Field(default=False, description="If true and mode=swarm, include flow trace in response.")
    session_id: Optional[str] = Field(default=None, description="Chat session ID; created if omitted.")


class ChatResponse(BaseModel):
    """Response body for the chat endpoint."""

    output: str = Field(..., description="Agent's reply.")
    success: bool = Field(default=True, description="Whether the request succeeded.")
    trace: list[dict] | None = Field(default=None, description="Swarm flow steps (only when mode=swarm and include_trace=true).")
    session_id: Optional[str] = Field(default=None, description="Session ID for this chat (use for feedback).")
    message_id: Optional[str] = Field(default=None, description="ID of the assistant message just produced.")


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


def _chat_handle(
    message: str,
    mode: Literal["general", "rag", "swarm"],
    include_trace: bool = False,
    uploaded_files: list[dict] | None = None,
) -> ChatResponse:
    """Shared logic for chat: message, mode, optional files (for swarm)."""
    try:
        if mode == "rag":
            output = rag_answer(message)
            return ChatResponse(output=output, success=True)
        if mode == "swarm":
            output, steps = run_swarm(message, uploaded_files=uploaded_files)
            trace = steps if include_trace else None
            return ChatResponse(output=output or "No answer produced.", success=True, trace=trace)
        # General mode
        context = retrieve_search_context(message)
        if context:
            user_content = (
                "Relevant context from previous searches and fetched pages:\n\n"
                f"{context}\n\nUser question: {message}"
            )
        else:
            user_content = message
        agent = get_chat_agent()
        result = agent.invoke({"messages": [HumanMessage(content=user_content)]})
        messages = result.get("messages", [])
        _persist_tool_results(messages, message)
        output = _last_ai_content(messages)
        return ChatResponse(output=output, success=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/", response_model=ChatResponse)
async def chat(request: Request) -> ChatResponse:
    """
    Send a message to the agent. Accepts either JSON or multipart/form-data (with optional file for swarm).
    Modes: general (search/URL + persist), rag (PDF RAG), swarm (multi-agent with analyst, coder, file analysis).
    """
    content_type = (request.headers.get("content-type") or "").split(";")[0].strip().lower()
    if content_type == "multipart/form-data" or content_type == "application/x-www-form-urlencoded":
        try:
            form = await request.form()
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid form: {e}") from e
        message = (form.get("message") or "").strip()
        if not message:
            raise HTTPException(status_code=400, detail="message is required")
        mode = (form.get("mode") or "general").strip() or "general"
        if mode not in ("general", "rag", "swarm"):
            mode = "general"
        include_trace = form.get("include_trace") in ("true", "1", "yes")
        session_id = (form.get("session_id") or "").strip() or None
        uploaded_files: list[dict] = []
        file = form.get("file")
        if file and getattr(file, "filename", None) and callable(getattr(file, "read", None)):
            try:
                raw = await file.read()
                text = extract_text_from_file(file.filename, raw)
                uploaded_files.append({"filename": file.filename, "content": text})
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"File read failed: {e}") from e
        sid = get_or_create_session(session_id)
        add_message_id(sid, str(uuid.uuid4()))  # user message id
        resp = _chat_handle(message=message, mode=mode, include_trace=include_trace, uploaded_files=uploaded_files or None)
        assistant_msg_id = str(uuid.uuid4())
        add_message_id(sid, assistant_msg_id)
        resp.session_id = sid
        resp.message_id = assistant_msg_id
        return resp

    try:
        body = await request.json()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {e}") from e
    req = ChatRequest.model_validate(body)
    sid = get_or_create_session(req.session_id)
    add_message_id(sid, str(uuid.uuid4()))  # user message id
    resp = _chat_handle(
        message=req.message,
        mode=req.mode,
        include_trace=req.include_trace,
        uploaded_files=None,
    )
    assistant_msg_id = str(uuid.uuid4())
    add_message_id(sid, assistant_msg_id)
    resp.session_id = sid
    resp.message_id = assistant_msg_id
    return resp
