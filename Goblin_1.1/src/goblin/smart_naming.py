"""Smart naming of transcriptions using GPT-3.5-turbo based on content."""

import logging
import os
import re
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def generate_smart_name(text_excerpt: str, model_size: str) -> Optional[str]:
    """Generate a smart filename based on transcription content using GPT-3.5-turbo.

    Args:
        text_excerpt: First ~100 alphanumeric characters of the transcription for context.
        model_size: The Whisper model used (tiny, base, medium) to include in the filename.

    Returns:
        A filesystem-safe name (max 50 chars), or None if the API call fails.
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        logger.debug("No API key available; smart naming skipped.")
        return None

    try:
        from openai import OpenAI
    except ImportError:
        logger.warning("openai package not available for smart naming")
        return None

    try:
        client = OpenAI(api_key=api_key)
    except Exception as e:
        logger.warning("Failed to create OpenAI client: %s", e)
        return None

    prompt = (
        "You are naming a transcript file. Create a short, descriptive slug that captures "
        "the main topic of the excerpt.\n\n"
        "Rules:\n"
        "- Return only the slug, no quotes, no punctuation, no extra text.\n"
        "- Use lowercase words separated by underscores.\n"
        "- Prefer 4 to 7 meaningful words.\n"
        "- Keep it under 60 characters if possible.\n"
        "- Avoid generic words like transcription, note, audio, or document unless they are essential.\n"
        "- If the excerpt is in French, answer in French words.\n\n"
        f"Excerpt:\n{text_excerpt}\n"
    )

    try:
        logger.debug("Calling GPT-3.5-turbo for smart naming with excerpt: %s", text_excerpt[:50])
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=80,
            temperature=0.3,
        )
        name = response.choices[0].message.content.strip()
        logger.debug("GPT returned: %s", name)
        # Sanitize: keep only alphanumerics and underscores, truncate to 60 chars
        name = re.sub(r"[^a-zA-Z0-9_]", "", name)[:60]
        if name:
            logger.debug("Smart name finalized: %s", name)
            return name
        logger.debug("Smart name was empty after sanitization")
    except Exception as exc:
        logger.warning("Smart naming API call failed: %s", exc)
        return None

    return None


def extract_excerpt(text: str, max_length: int = 240) -> str:
    """Extract the first ~max_length alphanumeric characters from text."""
    # Remove leading/trailing whitespace and newlines
    text = text.strip()
    # Keep only alphanumerics and spaces for context
    alphanumeric_only = re.sub(r"[^a-zA-Z0-9\s]", "", text)
    # Return the first max_length characters
    return alphanumeric_only[:max_length]
