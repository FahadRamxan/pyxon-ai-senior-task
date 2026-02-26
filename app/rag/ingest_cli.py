"""CLI to ingest Pyxon PDFs into Qdrant. Run: python -m app.rag.ingest_cli [--all | agent_key]."""

import argparse
import sys

from app.rag.config import RAG_AGENTS
from app.rag.ingestion import ingest_agent, ingest_all


def main() -> int:
    parser = argparse.ArgumentParser(description="Ingest Pyxon RAG PDFs into Qdrant.")
    parser.add_argument(
        "agent",
        nargs="?",
        choices=list(RAG_AGENTS.keys()) + ["all"],
        default="all",
        help="Agent to ingest, or 'all' (default).",
    )
    args = parser.parse_args()
    try:
        if args.agent == "all":
            counts = ingest_all()
            for k, n in counts.items():
                print(f"  {k}: {n} chunks")
            print("Done.")
        else:
            n = ingest_agent(args.agent)
            print(f"  {args.agent}: {n} chunks. Done.")
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
