"""Ingest PDFs into Qdrant: chunk by paragraph/heading, embed with text-embedding-3-large."""

import re
import uuid
from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from qdrant_client.models import PointStruct

from app.rag.config import (
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    RAG_AGENTS,
    RAG_DATA_DIR,
)
from app.rag.embeddings import get_embeddings
from app.rag.qdrant_client import ensure_collections, get_qdrant_client


def _split_by_heading_then_paragraph(text: str) -> list[str]:
    """
    Split text into semantic chunks: prefer section boundaries (headings),
    then paragraphs. Keeps headings with their following content when small enough.
    """
    # Normalize: collapse multiple newlines, strip
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    if not text:
        return []

    chunks: list[str] = []
    # Split on likely heading boundaries: line that is short and/or ends with colon, or all-caps
    parts = re.split(r"\n(?=(?:\d+\.\s*)?[A-Z][^\n]{0,80}(?:\s*:\s*)?\n)", text)
    for part in parts:
        part = part.strip()
        if not part:
            continue
        if len(part) <= CHUNK_SIZE + CHUNK_OVERLAP:
            chunks.append(part)
        else:
            # Split by paragraphs first
            paras = re.split(r"\n\n+", part)
            current: list[str] = []
            current_len = 0
            for p in paras:
                p = p.strip()
                if not p:
                    continue
                if current_len + len(p) + 2 > CHUNK_SIZE and current:
                    chunks.append("\n\n".join(current))
                    # Keep overlap: last paragraph may start next chunk
                    overlap_candidate = current[-1] if current else ""
                    current = [overlap_candidate] if len(overlap_candidate) < CHUNK_OVERLAP else []
                    current_len = sum(len(x) for x in current)
                current.append(p)
                current_len += len(p) + 2
            if current:
                chunks.append("\n\n".join(current))
    return chunks


def load_and_chunk_pdf(pdf_path: Path, source_label: str) -> list[dict]:
    """Load PDF, split by heading/paragraph, return list of {content, metadata}."""
    loader = PyPDFLoader(str(pdf_path))
    docs = loader.load()
    full_text_by_page: list[tuple[str, int]] = []
    for d in docs:
        full_text_by_page.append((d.page_content, d.metadata.get("page", 0)))
    # Combine with page markers so we can attach page to chunks
    combined = "\n\n".join(
        f"[Page {p}] {t}" for t, p in full_text_by_page if (t and t.strip())
    )
    raw_chunks = _split_by_heading_then_paragraph(combined)
    # Fallback: if regex produced one huge chunk, use RecursiveCharacterTextSplitter
    if len(raw_chunks) == 1 and len(raw_chunks[0]) > CHUNK_SIZE * 2:
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            separators=["\n\n", "\n", ". ", " ", ""],
        )
        raw_chunks = splitter.split_text(raw_chunks[0])
    out: list[dict] = []
    for c in raw_chunks:
        c = c.strip()
        if not c or len(c) < 30:
            continue
        out.append({"content": c, "metadata": {"source": source_label}})
    return out


def ingest_agent(agent_key: str) -> int:
    """Ingest one agent's PDF into its Qdrant collection. Returns number of chunks indexed."""
    if agent_key not in RAG_AGENTS:
        raise ValueError(f"Unknown agent: {agent_key}")
    conf = RAG_AGENTS[agent_key]
    pdf_path = RAG_DATA_DIR / conf["pdf"]
    if not pdf_path.is_file():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")
    chunks = load_and_chunk_pdf(pdf_path, source_label=conf["name"])
    if not chunks:
        return 0
    texts = [c["content"] for c in chunks]
    embeddings_model = get_embeddings()
    vectors = embeddings_model.embed_documents(texts)
    client = get_qdrant_client()
    ensure_collections(client)
    collection = conf["collection"]
    points = [
        PointStruct(
            id=str(uuid.uuid4()),
            vector=vec,
            payload={"content": c["content"], "source": c["metadata"]["source"]},
        )
        for c, vec in zip(chunks, vectors)
    ]
    client.upsert(collection_name=collection, points=points)
    return len(points)


def ingest_all() -> dict[str, int]:
    """Ingest all five agents' PDFs. Returns agent_key -> count."""
    client = get_qdrant_client()
    ensure_collections(client)
    result: dict[str, int] = {}
    for agent_key in RAG_AGENTS:
        result[agent_key] = ingest_agent(agent_key)
    return result
