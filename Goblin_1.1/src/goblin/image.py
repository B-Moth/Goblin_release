"""Transcription de texte manuscrit via l'API OpenAI Vision (GPT-4o-mini)."""

import base64
import io
import logging
from pathlib import Path

from openai import AuthenticationError, OpenAIError, OpenAI
from PIL import Image

from typing import Any, Optional, Tuple

from goblin.credentials import load_saved_openai_api_key

logger = logging.getLogger(__name__)

#: Extensions image prises en charge.
SUPPORTED_IMAGE_EXTENSIONS = frozenset(
    {".bmp", ".gif", ".jpeg", ".jpg", ".png", ".tif", ".tiff", ".webp"}
)

_TRANSCRIPTION_PROMPT = (
    "Transcribe this handwritten note exactly.\n"
    "Keep original line breaks.\n"
    "If a word is unclear, write [?].\n"
    "Return only the transcription."
)


def _preprocess_image_for_api(file_path: str) -> bytes:
    """Preprocess image: resize to max 1600px longest side, convert to JPEG quality 75.
    
    Optimizes image for API upload while maintaining readability for OCR.
    
    Args:
        file_path: Path to the image file.
        
    Returns:
        JPEG image data as bytes.
    """
    img = Image.open(file_path).convert("RGB")
    original_size = img.size
    
    # Resize if longest side exceeds 1600px
    max_side = 1600
    if max(img.size) > max_side:
        ratio = max_side / max(img.size)
        new_size = (int(img.width * ratio), int(img.height * ratio))
        img = img.resize(new_size, Image.Resampling.LANCZOS)
        logger.info(
            "Image resized from %sx%s to %sx%s for API upload",
            original_size[0],
            original_size[1],
            new_size[0],
            new_size[1],
        )
    
    # Convert to JPEG with quality 75
    jpeg_buffer = io.BytesIO()
    img.save(jpeg_buffer, format="JPEG", quality=75, optimize=True)
    jpeg_buffer.seek(0)
    return jpeg_buffer.read()


def is_image_file(file_path: str) -> bool:
    """Return True if *file_path* has a supported image extension."""
    return Path(file_path).suffix.lower() in SUPPORTED_IMAGE_EXTENSIONS


def transcribe_image(
    file_path: str,
    return_metadata: bool = False,
) -> Any:
    """Transcribe handwritten text from *file_path* using GPT-4o-mini Vision.

    The image is:
    1. Resized to max 1600px longest side
    2. Converted to JPEG (quality 75) for efficient upload
    3. Base64-encoded and sent to the OpenAI Chat Completions API

    Args:
        file_path: Path to the image file.

    Returns:
        The transcribed text.

    Raises:
        AuthenticationError: If the API key is invalid, expired, or missing.
        openai.OpenAIError: On other API errors (rate limit, quota, etc.).
        FileNotFoundError: If the file does not exist.
    """
    load_saved_openai_api_key()
    client = OpenAI()  # reads OPENAI_API_KEY from environment

    # Preprocess image: resize and convert to JPEG
    jpeg_data = _preprocess_image_for_api(file_path)
    image_b64 = base64.b64encode(jpeg_data).decode("utf-8")

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": _TRANSCRIPTION_PROMPT},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_b64}",
                            },
                        },
                    ],
                }
            ],
            max_tokens=2048,
        )
        transcription = response.choices[0].message.content or ""
        if not return_metadata:
            return transcription

        usage = getattr(response, "usage", None)
        metadata = {
            "model": "gpt-4o-mini",
            "usage": {
                "prompt_tokens": getattr(usage, "prompt_tokens", None) if usage is not None else None,
                "completion_tokens": getattr(usage, "completion_tokens", None) if usage is not None else None,
                "total_tokens": getattr(usage, "total_tokens", None) if usage is not None else None,
            },
        }
        if metadata["usage"]["total_tokens"] is None:
            prompt_tokens = metadata["usage"]["prompt_tokens"]
            completion_tokens = metadata["usage"]["completion_tokens"]
            if prompt_tokens is not None and completion_tokens is not None:
                try:
                    metadata["usage"]["total_tokens"] = int(prompt_tokens) + int(completion_tokens)
                except (TypeError, ValueError):
                    pass
        return transcription, metadata
    
    except AuthenticationError as exc:
        error_msg = (
            "OpenAI API authentication failed. Your API key is invalid, expired, or missing.\n\n"
            "To fix this:\n"
            "1. Check your API key at https://platform.openai.com/account/api-keys\n"
            "2. If expired, generate a new one\n"
            "3. Update Goblin: paste the new key in the Online mode panel (or set OPENAI_API_KEY environment variable)\n"
            "4. To transcribe this file locally, toggle to Offline mode and use TrOCR+PaddleOCR"
        )
        logger.error(error_msg)
        logger.error("Original OpenAI error: %s", exc)
        raise exc from None
    
    except OpenAIError as exc:
        error_msg = f"OpenAI API error: {exc}"
        logger.error(error_msg)
        raise
