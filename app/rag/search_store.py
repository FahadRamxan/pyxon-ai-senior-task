"""Persist search/URL tool results into Qdrant and retrieve for RAG before generation."""

import uuid

from langchain_text_splitters import RecursiveCharacterTextSplitter
from qdrant_client.models import PointStruct

from app.rag.config import (
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    SEARCH_RESULTS_COLLECTION,
    SEARCH_RAG_TOP_K,
)
from app.rag.embeddings import get_embeddings
from app.rag.qdrant_client import get_qdrant_client, ensure_search_results_collection


def persist_search_content(
    text: str,
    source: str,
    query: str = "",
    url: str = "",
) -> int:
    """
    Chunk text from a search or URL tool, embed it, and upsert into the search results collection.
    Returns the number of chunks stored.
    """
    if not text or not text.strip():
        return 0
    text = text.strip()
    if len(text) < 50:
        chunks = [text]
    else:
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            separators=["\n\n", "\n", ". ", " ", ""],
        )
        chunks = splitter.split_text(text)
    if not chunks:
        return 0
    embeddings = get_embeddings()
    vectors = embeddings.embed_documents(chunks)
    client = get_qdrant_client()
    ensure_search_results_collection(client)
    payloads = [
        {
            "content": c,
            "source": source,
            "query": query or "",
            "url": url or "",
        }
        for c in chunks
    ]
    points = [
        PointStruct(
            id=str(uuid.uuid4()),
            vector=vec,
            payload=p,
        )
        for vec, p in zip(vectors, payloads)
    ]
    client.upsert(collection_name=SEARCH_RESULTS_COLLECTION, points=points)
    return len(points)


def retrieve_search_context(query: str, top_k: int = SEARCH_RAG_TOP_K) -> str:
    """
    Embed the query, search the search-results collection, and return concatenated
    content for use as context before generation.
    """
    if not query or not query.strip():
        return ""
    client = get_qdrant_client()
    if not client.collection_exists(SEARCH_RESULTS_COLLECTION):
        return ""
    embeddings = get_embeddings()
    query_vector = embeddings.embed_query(query.strip())
    response = client.query_points(
        collection_name=SEARCH_RESULTS_COLLECTION,
        query=query_vector,
        limit=top_k,
    )
    points = getattr(response, "points", []) or []
    parts = []
    for p in points:
        if not p.payload:
            continue
        content = p.payload.get("content", "")
        if content:
            source = p.payload.get("source", "")
            url = p.payload.get("url", "")
            if url:
                parts.append(f"[{source}] {content}\n(Source: {url})")
            else:
                parts.append(f"[{source}] {content}")
    return "\n\n".join(parts) if parts else ""
