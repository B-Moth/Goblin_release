"""Shared Ollama helpers for Goblin's local Qwen editor flow.

This module centralises small, well-documented helpers used by both the
Flask app and installer scripts to check for the presence of the `ollama`
CLI, start background pulls and report simple progress status. The
implementation intentionally keeps the job-tracking state as a plain
dictionary so it can be easily inspected and serialized in HTTP responses.

Notes on concurrency and safety:
- The `jobs` dict is a lightweight shared structure mutated by the
    background pull worker. We rely on the fact the ThreadPoolExecutor used
    by the application is sized conservatively (one worker by default), so
    races are unlikely in normal operation. If you scale the executor later
    consider protecting `jobs` with a threading.Lock for correctness.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from shutil import which
import subprocess
from typing import Any

from goblin.ollama_progress import OllamaProgressTracker


def ollama_is_installed() -> bool:
    """Return True when the `ollama` CLI is available on PATH."""
    return which("ollama") is not None


def ensure_ollama_model_available(model: str) -> None:
    """Ensure an Ollama model is present locally; pull it on first use if necessary."""
    if not ollama_is_installed():
        raise RuntimeError(
            "Le mode local nécessite Ollama (outil système) — installez-le (Homebrew: `brew install ollama`) et relancez."
        )

    try:
        result = subprocess.run(["ollama", "list"], capture_output=True, text=True, check=False)
        output = (result.stdout or "") + (result.stderr or "")
        if model in output:
            return
    except Exception:
        # If the check fails, continue and attempt to pull the model.
        pass

    try:
        # Blocking pull for first-use convenience. This is used in CLI
        # invocations and in places where the caller expects the model to
        # be available before continuing (e.g. a synchronous rewrite
        # request). For UI-driven flows we prefer start_ollama_pull which
        # schedules a background worker instead.
        print(f"ℹ Pulling Ollama model '{model}' (first use). This may take a while...")
        subprocess.check_call(["ollama", "pull", model])
        print(f"✓ Ollama model '{model}' pulled successfully.")
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(
            f"Échec du téléchargement du modèle local '{model}'. Vérifiez votre connexion ou installez le modèle manuellement avec 'ollama pull {model}'."
        ) from exc


def check_ollama_model(model: str, jobs: dict[str, dict[str, Any]] | None = None) -> dict[str, Any]:
    """Report whether *model* is installed and whether a pull is in progress."""
    jobs = jobs or {}
    if not ollama_is_installed():
        return {"ok": True, "present": False, "message": "ollama_not_installed"}

    job = jobs.get(model)
    if job and job.get("status") == "done":
        return {"ok": True, "present": True}
    if job and job.get("status") == "pulling":
        return {"ok": True, "present": False, "message": "pulling"}

    try:
        result = subprocess.run(["ollama", "list"], capture_output=True, text=True, check=False)
        output = (result.stdout or "") + (result.stderr or "")
        return {"ok": True, "present": model in output}
    except Exception:
        return {"ok": True, "present": False, "message": "check_failed"}


def _pull_ollama_model_background(model: str, jobs: dict[str, dict[str, Any]]) -> None:
    # Mark the model as currently being pulled and stream subprocess
    # output back into the job's `progress` field so the frontend can show
    # detailed download progress. Any exception sets a 'failed' status so
    # callers can present a helpful error to the user.
    tracker = OllamaProgressTracker()
    jobs[model] = {"status": "pulling", "progress": tracker.to_dict()}
    try:
        process = subprocess.Popen(
            ["ollama", "pull", model],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        if process.stdout is not None:
            for line in process.stdout:
                tracker.parse_line(line)
                # Update shared job with parsed progress
                jobs[model]["progress"] = tracker.to_dict()
        return_code = process.wait()
        if return_code == 0:
            tracker.status = "success"
            jobs[model] = {"status": "done", "progress": tracker.to_dict()}
        else:
            tracker.status = "error"
            jobs[model] = {"status": "failed", "progress": tracker.to_dict()}
    except Exception as exc:  # noqa: BLE001
        tracker.status = "error"
        tracker.to_dict()["error"] = str(exc)
        jobs[model] = {"status": "failed", "progress": tracker.to_dict()}


def start_ollama_pull(
    model: str,
    executor: ThreadPoolExecutor,
    jobs: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Start a background pull if needed and return the current job status."""
    if not ollama_is_installed():
        return {"ok": False, "error": "ollama_not_installed"}

    job = jobs.get(model)
    if job and job.get("status") == "done":
        return {"ok": True, "status": "done"}
    if job and job.get("status") == "pulling":
        return {"ok": True, "status": "pulling"}

    # Schedule the background pull. We write an initial 'queued' state and
    # then submit the worker. A small race exists where the worker may
    # start immediately; callers should treat both 'queued' and 'pulling'
    # as valid non-finished states.
    jobs[model] = {"status": "queued", "message": "queued"}
    executor.submit(_pull_ollama_model_background, model, jobs)
    jobs[model] = {"status": "pulling", "message": "started"}
    return {"ok": True, "status": "pulling"}


def get_ollama_pull_status(model: str, jobs: dict[str, dict[str, Any]] | None = None) -> dict[str, Any]:
    """Return the current pull status for *model* with detailed progress info."""
    jobs = jobs or {}
    job = jobs.get(model) or {"status": "idle", "progress": {"percentage": 0, "status": "idle"}}
    return {
        "ok": True,
        "status": job.get("status"),
        "progress": job.get("progress", {"percentage": 0, "status": "idle"}),
    }
