"""Session API: start a chat session so start_time is recorded before first message."""

from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.session_store import get_or_create_session

router = APIRouter(prefix="/session", tags=["session"])


class SessionStartRequest(BaseModel):
    """Optional session_id; if omitted, server generates one. Optional user name and email are stored with the session."""

    session_id: Optional[str] = Field(default=None, description="Client-generated session ID, or omit to get a new one.")
    user_name: Optional[str] = Field(default=None, max_length=500, description="User's name (stored in session log).")
    user_email: Optional[str] = Field(default=None, max_length=500, description="User's email (stored in session log).")


class SessionStartResponse(BaseModel):
    """Session ID to use for subsequent /chat/ and /feedback/ calls."""

    session_id: str = Field(..., description="Session ID (existing or newly created).")


@router.post("/start", response_model=SessionStartResponse)
def start_session(body: SessionStartRequest) -> SessionStartResponse:
    """
    Start a chat session. Call when the user enters the chat (e.g. clicks "Begin chat").
    Records start_time and optional user_name/user_email. Use the returned session_id in POST /chat/ and POST /feedback/.
    """
    sid = get_or_create_session(
        body.session_id,
        user_name=body.user_name,
        user_email=body.user_email,
    )
    return SessionStartResponse(session_id=sid)
