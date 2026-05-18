"""Shared Ollama helpers for installer and uninstall scripts."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from shutil import which


def ensure_ollama_available() -> bool:
    """Attempt to make Ollama available on macOS via Homebrew.

    Returns True when Ollama is present or successfully installed, False otherwise.
    """
    if which("ollama") is not None:
        return True

    print("ℹ Ollama not found on PATH — attempting to install via Homebrew...")
    if which("brew") is None:
        print("⚠ Homebrew not found. Install Homebrew (https://brew.sh) and then Ollama (https://ollama.com).")
        return False

    try:
        subprocess.check_call(["brew", "install", "ollama"])
        print("✓ Ollama installed via Homebrew.")
        return which("ollama") is not None
    except Exception:
        print("✗ Failed to install Ollama via Homebrew. Please install Ollama manually: https://ollama.com")
        return False


def preload_default_models(src_dir: Path, model_names: list[str]) -> None:
    """Pre-pull the requested Ollama models if Ollama is available."""
    if which("ollama") is None:
        print("ℹ Skipping model pre-pull: Ollama not available.")
        return

    try:
        sys.path.insert(0, str(src_dir))
        from goblin.transcription_editor import load_editor_config
        cfg = load_editor_config()
        preload = list(model_names)

        default_model = cfg.get("local_default_model")
        if default_model and default_model not in preload:
            preload.insert(0, default_model)

        configured = cfg.get("preload_local_models") or []
        if isinstance(configured, list):
            for model in configured:
                if model and model not in preload:
                    preload.append(model)

        for model in preload:
            if not model:
                continue
            try:
                print(f"ℹ Pre-pulling Ollama model: {model} (installer)")
                subprocess.check_call(["ollama", "pull", model])
                print(f"✓ Pre-pulled: {model}")
            except Exception:
                print(f"! Failed to pre-pull model {model}; continue.")
    except Exception:
        print("! Could not preload Ollama models (config load failed)")


def purge_configured_models(src_dir: Path) -> None:
    """Remove configured Ollama models using `ollama rm` when available."""
    if which("ollama") is None:
        print("Ollama not found on PATH; skipping Ollama model removal.")
        return

    try:
        sys.path.insert(0, str(src_dir))
        from goblin.transcription_editor import load_editor_config
    except Exception:
        print("Skipping Ollama model purge: cannot import editor config.")
        return

    config = load_editor_config()
    local_models = config.get("local_models", {})
    if not isinstance(local_models, dict) or not local_models:
        print("No local models configured; skipping Ollama model removal.")
        return

    for model_key in list(local_models.keys()):
        try:
            print(f"Attempting to remove Ollama model: {model_key} ...")
            subprocess.run(["ollama", "rm", model_key], check=False)
            print(f"✓ Requested removal of Ollama model: {model_key}")
        except Exception:
            print(f"! Failed to remove Ollama model: {model_key} (you may need to remove it manually)")
