"""Feedback API: submit rating, selected options, and optional text after end chat. Records session end and duration to file."""

import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.session_store import pop_session, write_session_to_file

router = APIRouter(prefix="/feedback", tags=["feedback"])
logger = logging.getLogger(__name__)


class FeedbackRequest(BaseModel):
    """Request body for feedback submission."""

    session_id: Optional[str] = Field(default=None, description="Chat session ID; if provided, session end time and duration are recorded.")
    rating: Optional[int] = Field(default=None, ge=1, le=5, description="Star rating 1-5 (optional when just ending session).")
    options: Optional[list[str]] = Field(default=None, description="Selected feedback option keys.")
    feedback: Optional[str] = Field(default=None, max_length=2000, description="Optional text feedback.")


@router.post("/", status_code=200)
def submit_feedback(request: FeedbackRequest) -> dict:
    """
    Submit end-chat feedback (rating, selected options, optional text). If session_id is provided,
    computes chat end time and duration, then appends one line to data/chat_sessions.txt.
    """
    end_time = datetime.now(timezone.utc)
    if request.session_id:
        session = pop_session(request.session_id)
        if session:
            start_time = session["start_time"]
            message_ids = session.get("message_ids") or []
            write_session_to_file(
                session_id=request.session_id,
                start_time=start_time,
                end_time=end_time,
                message_ids=message_ids,
                rating=request.rating,
                options=request.options,
                feedback_text=request.feedback,
                user_name=session.get("user_name") or "",
                user_email=session.get("user_email") or "",
            )
        else:
            logger.debug("Feedback for unknown or already-ended session: %s", request.session_id)
    logger.info(
        "Feedback: session_id=%s rating=%s options=%s feedback=%s",
        request.session_id,
        request.rating,
        request.options,
        (request.feedback or "")[:200],
    )
    return {"success": True, "message": "Thank you for your feedback."}
