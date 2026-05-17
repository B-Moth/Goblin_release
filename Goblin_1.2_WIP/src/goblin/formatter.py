"""Mise en forme et sauvegarde des transcriptions."""

import re
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

#: Header YAML front-matter + corps Markdown pour chaque transcription.
_TEMPLATE = """\
---
fichier_original: {original_filename}
date_creation: {creation_date}
date_transcription: {transcription_date}
type: {file_type}
mode_transcription: {transcription_mode}
modele_utilise: {transcription_model}
duree_transcription: {transcription_duration}
jetons_utilises: {transcription_tokens}
---

# Transcription : {original_filename}

| Champ | Valeur |
|---|---|
| **Fichier original** | {original_filename} |
| **Date de création** | {creation_date_human} |
| **Date de transcription** | {transcription_date_human} |
| **Type** | {file_type} |
| **Mode** | {transcription_mode} |
| **Modèle** | {transcription_model} |
| **Durée** | {transcription_duration} |
| **Jetons consommés** | {transcription_tokens} |

---

{transcription}
"""


def sanitize_filename(name: str) -> str:
    """Replace characters that are invalid in filenames with underscores."""
    return re.sub(r"[^\w\-.]", "_", name)


def build_output_filename(original_path: str, creation_date: datetime, model_name: str = "unknown") -> str:
    """Build the output filename from the original path and creation date.

    Format: ``YYYY-MM-DD_HH-MM_<stem>_<model>.md``

    Example: ``2024-03-15_10-30_interview_dupont_faster-whisper_base_int8.md``
    """
    date_prefix = creation_date.strftime("%Y-%m-%d_%H-%M")
    stem = sanitize_filename(Path(original_path).stem)
    model_slug = sanitize_filename(model_name.strip() or "unknown")
    return f"{date_prefix}_{stem}_{model_slug}.md"


def _format_tokens(metadata: Optional[dict[str, Any]]) -> str:
    if not metadata:
        return "—"

    total_tokens = metadata.get("total_tokens")
    prompt_tokens = metadata.get("prompt_tokens")
    completion_tokens = metadata.get("completion_tokens")

    parts = []
    if total_tokens is not None:
        parts.append(str(total_tokens))
    if prompt_tokens is not None or completion_tokens is not None:
        prompt = str(prompt_tokens) if prompt_tokens is not None else "?"
        completion = str(completion_tokens) if completion_tokens is not None else "?"
        parts.append(f"{prompt} + {completion}")

    return " / ".join(parts) if parts else "—"


def _format_duration(metadata: Optional[dict[str, Any]]) -> str:
    if not metadata:
        return "—"

    duration_seconds = metadata.get("duration_seconds")
    if duration_seconds is None:
        return "—"

    try:
        duration_value = float(duration_seconds)
    except (TypeError, ValueError):
        return "—"

    return f"{duration_value:.1f} s"


def save_transcription(
    transcription: str,
    original_path: str,
    creation_date: datetime,
    file_type: str,
    output_dir: str = "transcriptions",
    metadata: Optional[dict[str, Any]] = None,
) -> str:
    """Write *transcription* to a Markdown file in *output_dir*.

    Args:
        transcription: The transcribed text.
        original_path: Path to the source file (used for naming and metadata).
        creation_date: Original creation date/time of the source file.
        file_type: Human-readable type label (e.g. ``"enregistrement audio"``).
        output_dir: Directory where the output file is written.

    Returns:
        The absolute path of the saved output file.
    """
    output_dir_path = Path(output_dir).resolve()
    output_dir_path.mkdir(parents=True, exist_ok=True)

    transcription_date = datetime.now()
    metadata = metadata or {}
    filename = build_output_filename(original_path, creation_date, metadata.get("model", "unknown"))
    output_path = output_dir_path / filename

    content = _TEMPLATE.format(
        original_filename=Path(original_path).name,
        creation_date=creation_date.strftime("%Y-%m-%d %H:%M"),
        transcription_date=transcription_date.strftime("%Y-%m-%d %H:%M"),
        creation_date_human=creation_date.strftime("%d/%m/%Y à %H:%M"),
        transcription_date_human=transcription_date.strftime("%d/%m/%Y à %H:%M"),
        file_type=file_type,
        transcription_mode=metadata.get("mode", "—"),
        transcription_model=metadata.get("model", "—"),
        transcription_duration=_format_duration(metadata),
        transcription_tokens=_format_tokens(metadata),
        transcription=transcription.strip(),
    )

    output_path.write_text(content, encoding="utf-8")
    return str(output_path)
