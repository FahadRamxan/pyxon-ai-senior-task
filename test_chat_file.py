#!/usr/bin/env python3
"""
Test script for the chatbot API: runs example questions across General, RAG, and Swarm modes.

Usage (server must be running on port 8002):
  python test_chat_file.py
  python test_chat_file.py --quick   # fewer tests, shorter timeout

Each test POSTs to /chat/ and checks for status 200 and non-empty output.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    import requests
except ImportError:
    print("Install requests: pip install requests", file=sys.stderr)
    sys.exit(1)

BASE_URL = "http://localhost:8002/chat/"
HEALTH_URL = "http://localhost:8002/health"
DEFAULT_TIMEOUT = 90
QUICK_TIMEOUT = 30


def check_server() -> bool:
    """Return True if the server is reachable (e.g. GET /health). Otherwise print message and return False."""
    try:
        r = requests.get(HEALTH_URL, timeout=5)
        if r.status_code == 200:
            return True
    except requests.exceptions.RequestException:
        pass
    print("Server is not running or not reachable at http://localhost:8002", file=sys.stderr)
    print("Start it first, e.g.:", file=sys.stderr)
    print("  uvicorn app.main:app --port 8002 --reload", file=sys.stderr)
    return False

# Test cases: (message, mode, description [, file_path for multipart])
TESTS = [
    # General (search)
    ("What is the current weather in Riyadh?", "general", "General: weather search"),
    ("What is the T20 World Cup live score?", "general", "General: T20 score search"),
    # General (URL)
    ("Summarize the content at https://www.python.org/about/", "general", "General: summarize URL"),
    ("What does https://api.github.com/ return? Describe the main keys.", "general", "General: GitHub API"),
    # RAG (requires Qdrant + ingest)
    ("What services does Pyxon offer and where are the offices located?", "rag", "RAG: Pyxon services and offices"),
    # Swarm (search / synthesis)
    ("What is the current exchange rate of EUR to USD?", "swarm", "Swarm: exchange rate"),
    ("Fetch https://httpbin.org/json and summarize what it returns.", "swarm", "Swarm: httpbin JSON"),
    ("Find the Wikipedia page for LangChain and in one paragraph tell me what it is.", "swarm", "Swarm: LangChain Wikipedia"),
    # Swarm (coder)
    ("Generate a list of the first 5 prime numbers using Python.", "swarm", "Swarm: first 5 primes"),
    ("What is 2 + 2?", "swarm", "Swarm: simple math"),
]


def run_test(
    message: str,
    mode: str,
    _description: str,
    timeout: int,
    file_path: Path | None = None,
    include_trace: bool = False,
) -> tuple[bool, str, int]:
    """
    POST to /chat/. Returns (success, output_preview, status_code).
    """
    if file_path and file_path.is_file():
        data = {"message": message, "mode": mode, "include_trace": "true" if include_trace else "false"}
        with open(file_path, "rb") as f:
            files = {"file": (file_path.name, f, "text/plain")}
            try:
                r = requests.post(BASE_URL, data=data, files=files, timeout=timeout)
            except requests.exceptions.RequestException as e:
                return False, str(e), 0
    else:
        payload = {
            "message": message,
            "mode": mode,
            "include_trace": include_trace and mode == "swarm",
        }
        try:
            r = requests.post(BASE_URL, json=payload, timeout=timeout)
        except requests.exceptions.RequestException as e:
            return False, str(e), 0

    status = r.status_code
    if status != 200:
        return False, r.text[:300] if r.text else "No body", status

    try:
        j = r.json()
    except ValueError:
        return False, "Invalid JSON response", status

    output = j.get("output") or ""
    if not output.strip():
        return False, "(empty output)", status

    preview = output[:120].replace("\n", " ") + ("..." if len(output) > 120 else "")
    return True, preview, status


def main() -> int:
    parser = argparse.ArgumentParser(description="Test chatbot API with example questions.")
    parser.add_argument("--quick", action="store_true", help="Run fewer tests with shorter timeout")
    parser.add_argument("--file", type=Path, default=None, help="Path to file for swarm file-upload test")
    args = parser.parse_args()

    if not check_server():
        return 2  # exit 2 = server not running

    timeout = QUICK_TIMEOUT if args.quick else DEFAULT_TIMEOUT
    if args.quick:
        # Subset: one general, one URL, one swarm, one RAG
        tests_subset = [
            TESTS[0],   # weather
            TESTS[3],   # GitHub API
            TESTS[5],   # exchange rate
            TESTS[4],   # Pyxon RAG
        ]
    else:
        tests_subset = list(TESTS)

    print(f"Testing {len(tests_subset)} cases (timeout={timeout}s). Base URL: {BASE_URL}")
    print("-" * 60)

    passed = 0
    failed = 0

    for message, mode, description in tests_subset:
        ok, preview, status = run_test(message, mode, description, timeout, include_trace=(mode == "swarm"))
        if ok:
            passed += 1
            print(f"  PASS  [{mode}] {description}")
            print(f"        -> {preview}")
        else:
            failed += 1
            print(f"  FAIL  [{mode}] {description}")
            print(f"        status={status} | {preview}")
        print()

    # Optional: swarm + file upload test
    file_path = args.file or Path(__file__).parent / "test_upload.txt"
    if file_path.is_file() and not args.quick:
        message = "Summarize this file and what is the net profit?"
        ok, preview, status = run_test(
            message, "swarm", "Swarm: file upload + analyst", timeout, file_path=file_path, include_trace=True
        )
        if ok:
            passed += 1
            print("  PASS  [swarm+file] Swarm: file upload + analyst")
            print(f"        -> {preview}")
        else:
            failed += 1
            print(f"  FAIL  [swarm+file] status={status} | {preview}")
        print()

    print("-" * 60)
    print(f"Result: {passed} passed, {failed} failed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
