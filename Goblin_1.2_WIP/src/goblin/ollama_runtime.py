"""Shared Ollama helpers for Goblin's local Qwen editor flow."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from shutil import which
import subprocess
from typing import Any


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
    jobs[model] = {"status": "pulling", "message": "starting"}
    try:
        process = subprocess.Popen(
            ["ollama", "pull", model],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        last_line = ""
        if process.stdout is not None:
            for line in process.stdout:
                last_line = line.strip()
                jobs[model]["message"] = last_line
        return_code = process.wait()
        if return_code == 0:
            jobs[model] = {"status": "done", "message": "completed"}
        else:
            jobs[model] = {"status": "failed", "message": f"returncode:{return_code}"}
    except Exception as exc:  # noqa: BLE001
        jobs[model] = {"status": "failed", "message": str(exc)}


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

    jobs[model] = {"status": "queued", "message": "queued"}
    executor.submit(_pull_ollama_model_background, model, jobs)
    jobs[model] = {"status": "pulling", "message": "started"}
    return {"ok": True, "status": "pulling"}


def get_ollama_pull_status(model: str, jobs: dict[str, dict[str, Any]] | None = None) -> dict[str, Any]:
    """Return the current pull status for *model*."""
    jobs = jobs or {}
    job = jobs.get(model) or {"status": "idle", "message": ""}
    return {"ok": True, "status": job.get("status"), "message": job.get("message")}
