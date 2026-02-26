"""Embeddings using OpenAI text-embedding-3-large."""

from langchain_openai import OpenAIEmbeddings

from app.config import settings
from app.rag.config import EMBEDDING_MODEL


def get_embeddings() -> OpenAIEmbeddings:
    """Build OpenAI embeddings with text-embedding-3-large."""
    return OpenAIEmbeddings(
        model=EMBEDDING_MODEL,
        api_key=settings.OPENAI_API_KEY,
    )
