"""RAG orchestration config: agent definitions, collection names, and data paths."""

from pathlib import Path

# Base path: project root (parent of app/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
RAG_DATA_DIR = PROJECT_ROOT / "Pyxon Data RAG"

# Sub-agents: intent key -> (display name, Qdrant collection name, PDF filename in RAG_DATA_DIR)
RAG_AGENTS = {
    "general": {
        "name": "General Agent",
        "collection": "pyxon_general",
        "pdf": "PYXON_Home_Page.pdf",
    },
    "cloud_automation": {
        "name": "Cloud and Automation Agent",
        "collection": "pyxon_cloud_automation",
        "pdf": "PYXON_Cloud & Automation.pdf",
    },
    "smart_iot": {
        "name": "Smart and IOT Solutions Agent",
        "collection": "pyxon_smart_iot",
        "pdf": "PYXON_Smart  IoT Solutions.pdf",
    },
    "ai_solutions": {
        "name": "AI Solutions Agent",
        "collection": "pyxon_ai_solutions",
        "pdf": "PYXON_Solutions_AI.pdf",
    },
    "cybersecurity": {
        "name": "Cybersecurity Agent",
        "collection": "pyxon_cybersecurity",
        "pdf": "PYXON_Cybersecurity_Solutions.pdf",
    },
}

# Embedding model (OpenAI); dimension for text-embedding-3-large is 3072
EMBEDDING_MODEL = "text-embedding-3-large"
EMBEDDING_DIMENSION = 3072

# LLM for sub-agents and orchestrator
RAG_LLM_MODEL = "gpt-4o-mini"

# Retrieval
RAG_TOP_K = 6
RAG_MIN_SCORE = 0.0  # optional score threshold

# Chunking (paragraph/heading-oriented)
CHUNK_SIZE = 600
CHUNK_OVERLAP = 80

# Search/URL results persisted for RAG (general agent)
SEARCH_RESULTS_COLLECTION = "pyxon_search_results"
SEARCH_RAG_TOP_K = 5
