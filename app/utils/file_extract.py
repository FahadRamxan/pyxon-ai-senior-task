"""Extract plain text from uploaded files for swarm analysis."""

import io
from pypdf import PdfReader


def extract_text_from_file(filename: str, content: bytes) -> str:
    """
    Extract text from file content. Supports PDF, .txt, .csv, .json.
    Returns decoded/extracted text or empty string on failure.
    """
    if not content:
        return ""
    ext = (filename or "").lower().split(".")[-1] if "." in (filename or "") else ""
    try:
        if ext == "pdf":
            reader = PdfReader(io.BytesIO(content))
            parts = []
            for page in reader.pages:
                t = page.extract_text()
                if t:
                    parts.append(t)
            return "\n\n".join(parts)
        # txt, csv, json, md, etc.: decode as UTF-8
        return content.decode("utf-8", errors="replace")
    except Exception:
        return ""
