"""Qdrant client and collection management. One collection per sub-agent."""

from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams

from app.config import settings
from app.rag.config import EMBEDDING_DIMENSION, RAG_AGENTS, SEARCH_RESULTS_COLLECTION


def get_qdrant_client() -> QdrantClient:
    """Build Qdrant client from settings (URL + optional API key)."""
    url = (settings.QDRANT_URL or "http://localhost:6333").rstrip("/")
    return QdrantClient(
        url=url,
        api_key=settings.QDRANT_API_KEY,
    )


def ensure_collections(client: QdrantClient) -> None:
    """Create each RAG collection if it does not exist."""
    for agent_key, agent_config in RAG_AGENTS.items():
        coll = agent_config["collection"]
        if not client.collection_exists(coll):
            client.create_collection(
                collection_name=coll,
                vectors_config=VectorParams(
                    size=EMBEDDING_DIMENSION,
                    distance=Distance.COSINE,
                ),
            )


def ensure_search_results_collection(client: QdrantClient) -> None:
    """Create the search/URL results collection if it does not exist."""
    if not client.collection_exists(SEARCH_RESULTS_COLLECTION):
        client.create_collection(
            collection_name=SEARCH_RESULTS_COLLECTION,
            vectors_config=VectorParams(
                size=EMBEDDING_DIMENSION,
                distance=Distance.COSINE,
            ),
        )
