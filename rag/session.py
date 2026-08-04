"""Persistent storage for the most recently classified document type."""

import json
from pathlib import Path


SESSION_FILE = Path(__file__).resolve().parent.parent / "document_session.json"


def set_document_type(document_type: str) -> None:
    """Persist the current uploaded document type across process restarts."""
    if not isinstance(document_type, str) or not document_type.strip():
        raise ValueError("document_type must be a non-empty string")

    temporary_file = SESSION_FILE.with_suffix(".tmp")
    temporary_file.write_text(
        json.dumps({"document_type": document_type}, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary_file.replace(SESSION_FILE)


def get_document_type() -> str | None:
    """Return the persisted document type, or None when no value is stored."""
    try:
        session_data = json.loads(SESSION_FILE.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return None

    document_type = session_data.get("document_type")
    return document_type if isinstance(document_type, str) else None
