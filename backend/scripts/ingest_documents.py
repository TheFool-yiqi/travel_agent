"""Compatibility entry point for rebuilding the local RAG vector store.

Prefer `init_rag.py` for the canonical implementation. This wrapper exists so
older docs or operator muscle memory do not land on a silent empty script.
"""

from __future__ import annotations

from init_rag import main


if __name__ == "__main__":
    main()
