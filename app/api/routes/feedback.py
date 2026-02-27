"""Feedback API: submit rating, selected options, and optional text after end chat."""

import logging
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(prefix="/feedback", tags=["feedback"])
logger = logging.getLogger(__name__)


class FeedbackRequest(BaseModel):
    """Request body for feedback submission."""

    rating: int = Field(..., ge=1, le=5, description="Star rating 1-5.")
    options: Optional[list[str]] = Field(default=None, description="Selected feedback option keys.")
    feedback: Optional[str] = Field(default=None, max_length=2000, description="Optional text feedback.")


@router.post("/", status_code=200)
def submit_feedback(request: FeedbackRequest) -> dict:
    """
    Submit end-chat feedback (rating, selected options, optional text). Returns success.
    Logged for now; can be persisted to DB or analytics later.
    """
    logger.info(
        "Feedback: rating=%s, options=%s, feedback=%s",
        request.rating,
        request.options,
        (request.feedback or "")[:200],
    )
    return {"success": True, "message": "Thank you for your feedback."}
