"""Application-wide constants. Keeps magic strings and config in one place."""

# LLM
DEFAULT_LLM_MODEL: str = "gpt-4o-mini"
DEFAULT_LLM_TEMPERATURE: float = 0.0

# Security: URL fetch tools (documented in README; use with care in production)
ALLOW_DANGEROUS_REQUESTS: bool = True
