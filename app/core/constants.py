"""Application-wide constants. Keeps magic strings and config in one place."""

# LLM
DEFAULT_LLM_MODEL: str = "gpt-4o-mini"
DEFAULT_LLM_TEMPERATURE: float = 0.0

# Security: URL fetch tools (documented in README; use with care in production)
ALLOW_DANGEROUS_REQUESTS: bool = True

# Context: cap tool output so agent messages stay under model context limit (e.g. 128k)
MAX_TOOL_OUTPUT_CHARS: int = 12_000
