"""Transcription audio via l'API OpenAI Whisper."""

from pathlib import Path
from typing import Any, Optional, Tuple

from openai import OpenAI

#: Extensions audio prises en charge par l'API Whisper.
SUPPORTED_AUDIO_EXTENSIONS = frozenset(
    {".flac", ".m4a", ".mp3", ".mp4", ".mpeg", ".mpga", ".ogg", ".wav", ".webm"}
)


def is_audio_file(file_path: str) -> bool:
    """Return True if *file_path* has a supported audio extension."""
    return Path(file_path).suffix.lower() in SUPPORTED_AUDIO_EXTENSIONS


def _extract_usage(usage: Any) -> dict[str, Optional[int]]:
    if usage is None:
        return {"prompt_tokens": None, "completion_tokens": None, "total_tokens": None}

    prompt_tokens = getattr(usage, "prompt_tokens", None)
    completion_tokens = getattr(usage, "completion_tokens", None)
    total_tokens = getattr(usage, "total_tokens", None)

    if total_tokens is None and prompt_tokens is not None and completion_tokens is not None:
        try:
            total_tokens = int(prompt_tokens) + int(completion_tokens)
        except (TypeError, ValueError):
            total_tokens = None

    return {
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
    }


def transcribe_audio(
    file_path: str,
    language: Optional[str] = None,
    return_metadata: bool = False,
) -> Any:
    """Transcribe *file_path* with the OpenAI Whisper API.

    Args:
        file_path: Path to the audio file.
        language: ISO-639-1 language code (e.g. ``"fr"`` or ``"en"``).
                  Pass *None* to let Whisper auto-detect the language.

    Returns:
        The plain-text transcription.

    Raises:
        openai.OpenAIError: On API errors.
        FileNotFoundError: If the file does not exist.
    """
    client = OpenAI()  # reads OPENAI_API_KEY from environment

    with open(file_path, "rb") as audio_file:
        response = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            language=language,
            response_format="text",
        )

    # The SDK returns a str when response_format="text"
    transcription = str(response)
    if not return_metadata:
        return transcription

    metadata = {
        "model": "whisper-1",
        "usage": _extract_usage(getattr(response, "usage", None)),
    }
    return transcription, metadata
