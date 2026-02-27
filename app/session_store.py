"""In-memory chat session store and persistence to a text file on session end."""

import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)

# In-memory: session_id -> { "start_time": datetime, "message_ids": list[str] }
_sessions: dict[str, dict] = {}

# Always write under the project folder (where this file's package lives: app/session_store.py -> project root)
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_SESSIONS_FILE = os.path.join(_PROJECT_ROOT, "data", "chat_sessions.txt")


def _ensure_data_dir() -> None:
    d = os.path.dirname(_SESSIONS_FILE)
    if d and not os.path.isdir(d):
        os.makedirs(d, exist_ok=True)


def get_or_create_session(
    session_id: Optional[str] = None,
    user_name: Optional[str] = None,
    user_email: Optional[str] = None,
) -> str:
    """
    Return existing session_id or create a new session. If session_id is provided and exists, return it
    (and update user_name/user_email if provided). If session_id is None or unknown, create a new session.
    """
    if session_id and session_id in _sessions:
        if user_name is not None:
            _sessions[session_id]["user_name"] = user_name
        if user_email is not None:
            _sessions[session_id]["user_email"] = user_email
        return session_id
    new_id = session_id if session_id else str(uuid.uuid4())
    if new_id not in _sessions:
        _sessions[new_id] = {
            "start_time": datetime.now(timezone.utc),
            "message_ids": [],
            "user_name": user_name or "",
            "user_email": user_email or "",
        }
    else:
        if user_name is not None:
            _sessions[new_id]["user_name"] = user_name
        if user_email is not None:
            _sessions[new_id]["user_email"] = user_email
    return new_id


def add_message_id(session_id: str, message_id: str) -> None:
    """Append a message ID to the session's list."""
    if session_id in _sessions:
        _sessions[session_id].setdefault("message_ids", []).append(message_id)


def get_session(session_id: str) -> Optional[dict]:
    """Return session dict (start_time, message_ids) or None."""
    return _sessions.get(session_id)


def pop_session(session_id: str) -> Optional[dict]:
    """Remove and return session dict, or None."""
    return _sessions.pop(session_id, None)


def _sanitize_tsv(s: str, max_len: int = 500) -> str:
    """Replace tab and newline so the value is one line for TSV."""
    if not s:
        return ""
    return (s[:max_len] or "").replace("\t", " ").replace("\r", " ").replace("\n", " ").strip()


def write_session_to_file(
    session_id: str,
    start_time: datetime,
    end_time: datetime,
    message_ids: list[str],
    rating: Optional[int] = None,
    options: Optional[list[str]] = None,
    feedback_text: Optional[str] = None,
    user_name: Optional[str] = None,
    user_email: Optional[str] = None,
) -> None:
    """
    Append one line to the sessions log file with session_id, start/end times, duration, message count, user name/email.
    """
    duration_seconds = (end_time - start_time).total_seconds()
    message_count = len(message_ids)
    msg_ids_str = "|".join(message_ids) if message_ids else ""
    start_iso = start_time.isoformat()
    end_iso = end_time.isoformat()
    opts_str = ",".join(options) if options else ""
    feedback_snippet = _sanitize_tsv((feedback_text or "")[:200])
    name_safe = _sanitize_tsv((user_name or "")[:200])
    email_safe = _sanitize_tsv((user_email or "")[:200])
    line = (
        f"{session_id}\t{start_iso}\t{end_iso}\t{duration_seconds:.1f}\t{message_count}\t"
        f"{rating or ''}\t{opts_str}\t{feedback_snippet}\t{name_safe}\t{email_safe}\t{msg_ids_str}\n"
    )
    try:
        _ensure_data_dir()
        write_header = not os.path.isfile(_SESSIONS_FILE)
        with open(_SESSIONS_FILE, "a", encoding="utf-8") as f:
            if write_header:
                f.write(
                    "session_id\tstart_time_utc\tend_time_utc\tduration_seconds\tmessage_count\trating\toptions\tfeedback_snippet\tuser_name\tuser_email\tmessage_ids\n"
                )
            f.write(line)
        logger.info("Session logged: %s duration=%.1fs messages=%s", session_id, duration_seconds, message_count)
    except OSError as e:
        logger.warning("Failed to write session to file: %s", e)
