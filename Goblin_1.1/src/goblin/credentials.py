"""Local persistence helpers for Goblin secrets."""

from __future__ import annotations

import os
import re
from pathlib import Path


_OPENAI_API_KEY_PATH = Path.home() / ".config" / "goblin" / "openai_api_key"
_OPENAI_API_KEY_PATTERN = re.compile(r"^sk-(?:proj-)?[A-Za-z0-9_-]{20,}$")


def get_openai_api_key_path() -> Path:
    """Return the local file used to persist the OpenAI API key."""
    return _OPENAI_API_KEY_PATH


def is_valid_openai_api_key(key: str) -> bool:
    """Return ``True`` when *key* looks like a real OpenAI API key."""
    cleaned = key.strip()
    return bool(cleaned) and not any(ch.isspace() for ch in cleaned) and bool(_OPENAI_API_KEY_PATTERN.match(cleaned))


def load_saved_openai_api_key() -> str | None:
    """Load a previously saved OpenAI API key into the process environment."""
    key = os.environ.get("OPENAI_API_KEY")
    if key and is_valid_openai_api_key(key):
        return key
    if key and not is_valid_openai_api_key(key):
        os.environ.pop("OPENAI_API_KEY", None)

    try:
        key = _OPENAI_API_KEY_PATH.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        return None

    if key and is_valid_openai_api_key(key):
        os.environ["OPENAI_API_KEY"] = key
        return key

    if key:
        try:
            _OPENAI_API_KEY_PATH.unlink()
        except OSError:
            pass

    return None


def save_openai_api_key(key: str) -> None:
    """Persist an OpenAI API key locally with restrictive permissions."""
    cleaned = key.strip()
    if not cleaned:
        raise ValueError("OPENAI_API_KEY cannot be empty")
    if not is_valid_openai_api_key(cleaned):
        raise ValueError("OPENAI_API_KEY doit ressembler à une clé OpenAI valide (ex. 'sk-...').")

    _OPENAI_API_KEY_PATH.parent.mkdir(parents=True, exist_ok=True)
    _OPENAI_API_KEY_PATH.write_text(cleaned + "\n", encoding="utf-8")

    try:
        os.chmod(_OPENAI_API_KEY_PATH, 0o600)
    except OSError:
        # Best effort: the file is still saved even if permissions cannot be tightened.
        pass


def delete_openai_api_key() -> None:
    """Delete the locally saved OpenAI API key and unset the env var.

    This is best-effort and will not raise if the file is already absent.
    """
    try:
        if _OPENAI_API_KEY_PATH.exists():
            _OPENAI_API_KEY_PATH.unlink()
    except OSError:
        # Ignore errors when removing the file; nothing we can do reliably.
        pass

    # Also remove from environment if present
    os.environ.pop("OPENAI_API_KEY", None)
