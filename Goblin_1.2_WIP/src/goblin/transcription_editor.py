"""Online transcription editing helpers driven by prompt config."""

from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path
from typing import Any

from openai import AuthenticationError, OpenAI, OpenAIError

from goblin.credentials import load_saved_openai_api_key


_CONFIG_PATH = Path(__file__).resolve().with_name("editor_prompts.json")
_FRONTMATTER_RE = re.compile(r"^---\n.*?\n---\n", flags=re.DOTALL)
_TRIPLE_FENCE_RE = re.compile(r"^```(?:md|markdown)?\n(.*)\n```\s*$", flags=re.DOTALL | re.IGNORECASE)

_DEFAULT_EDITOR_CONFIG: dict[str, Any] = {
    "model": "gpt-4.1-mini",
    "temperature": 0.2,
    "max_tokens": 4096,
    "system_prompt": (
        "You are a careful editorial assistant. Rewrite only from the transcription provided. "
        "Do not invent facts, do not add context, and do not omit meaningful information. "
        "Keep the response in the same language as the transcription. Return only Markdown content. "
        "Do not add any introduction, explanation, commentary, suggestions, code fences, or meta text."
    ),
    "presets": {
        "interview": {
            "label": "Interview",
            "slug": "interview",
            "prompt": (
                "Rewrite the transcription as an interview in the style of a magazine or newspaper interview. "
                "Do not correct spelling, grammar, punctuation, or wording. Do not add, remove, or omit anything. "
                "Preserve all errors and repetitions exactly as they appear. Only reformat the transcription as an interview."
            ),
        },
        "resume": {
            "label": "Résumé",
            "slug": "resume",
            "prompt": (
                "Summarize the transcription by extracting the relevant information and writing a relatively short and clear text. "
                "Keep only the facts present in the transcription. Do not invent anything. Do not add recommendations or commentary."
            ),
        },
        "documentation": {
            "label": "Documentation",
            "slug": "documentation",
            "prompt": (
                "Rewrite the transcription as a structured and clear document. Present the information like technical documentation, a report, or a field note. "
                "Organize the content with useful Markdown headings and sections. Keep only the information that is present in the transcription. "
                "Do not invent or infer anything."
            ),
        },
        "custom": {
            "label": "Personnalisé",
            "slug": "custom",
            "prompt": (
                "Apply the user's custom formatting instructions exactly. Keep only information present in the transcription. "
                "Do not invent facts, do not add context, and do not omit meaningful information. Return only Markdown content, with no introduction, "
                "no explanation, no suggestions, and no meta text. The output must remain in the same language as the transcription."
            ),
        },
    },
}


def load_editor_config() -> dict[str, Any]:
    """Load the transcription editor configuration from the bundled JSON file."""
    data = dict(_DEFAULT_EDITOR_CONFIG)
    if _CONFIG_PATH.exists():
        try:
            file_data = json.loads(_CONFIG_PATH.read_text(encoding="utf-8"))
            if isinstance(file_data, dict):
                data.update({k: v for k, v in file_data.items() if k != "presets"})
                file_presets = file_data.get("presets")
                if isinstance(file_presets, dict):
                    merged_presets = dict(_DEFAULT_EDITOR_CONFIG["presets"])
                    merged_presets.update(file_presets)
                    data["presets"] = merged_presets
        except Exception:
            # Fall back to the in-code defaults if the JSON file is missing or malformed.
            pass
    if "presets" not in data or not isinstance(data["presets"], dict):
        raise ValueError("editor_prompts.json must define a 'presets' mapping")
    return data


def get_editor_presets() -> list[dict[str, str]]:
    """Return the presets as a list suitable for templates."""
    config = load_editor_config()
    presets = []
    for key, preset in config["presets"].items():
        if key == "custom":
            continue
        presets.append(
            {
                "key": key,
                "label": str(preset.get("label", key)).strip(),
                "slug": str(preset.get("slug", key)).strip(),
            }
        )
    return presets


def get_editor_custom_mode() -> dict[str, str]:
    """Return the custom-mode metadata for the template."""
    config = load_editor_config()
    preset = config["presets"].get("custom", {})
    return {
        "key": "custom",
        "label": str(preset.get("label", "Personnalisé")).strip(),
        "slug": str(preset.get("slug", "custom")).strip(),
    }


def _strip_frontmatter(text: str) -> str:
    return _FRONTMATTER_RE.sub("", text, count=1)


def read_transcription_body(path: Path) -> str:
    """Read a saved transcription file and return the markdown body only."""
    text = path.read_text(encoding="utf-8")
    return _strip_frontmatter(text).strip()


def _normalize_model_response(text: str) -> str:
    cleaned = text.strip()
    match = _TRIPLE_FENCE_RE.match(cleaned)
    if match:
        cleaned = match.group(1).strip()
    return cleaned.strip()


def _slugify_text(text: str, max_words: int = 5) -> str:
    normalized = unicodedata.normalize("NFKD", text)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    words = re.findall(r"[A-Za-z0-9]+", ascii_text.lower())
    selected = [word for word in words if len(word) > 2][:max_words]
    if not selected:
        return "prompt"
    return "_".join(selected)


def build_edited_transcription_filename(
    original_filename: str,
    preset_slug: str,
    custom_prompt: str | None = None,
) -> str:
    """Build a stable filename for an edited transcription."""
    source = Path(original_filename)
    if preset_slug == "custom":
        custom_suffix = _slugify_text(custom_prompt or "")
        return f"{source.stem}__custom_{custom_suffix}.md"
    return f"{source.stem}__{preset_slug}.md"


def rewrite_transcription(
    transcription: str,
    preset_key: str,
    custom_prompt: str | None = None,
) -> tuple[str, dict[str, Any]]:
    """Rewrite a transcription using the configured online preset or a custom format."""
    load_saved_openai_api_key()
    api_key = None
    try:
        import os

        api_key = os.environ.get("OPENAI_API_KEY")
    except Exception:
        api_key = None

    if not api_key:
        raise AuthenticationError("OPENAI_API_KEY is required for transcription editing")

    config = load_editor_config()
    preset = config["presets"].get(preset_key)
    if not preset:
        raise ValueError(f"Unknown transcription edit preset: {preset_key}")

    if preset_key == "custom":
        custom_prompt = (custom_prompt or "").strip()
        if not custom_prompt:
            raise ValueError("A custom format prompt is required when using the custom preset")

    client = OpenAI()
    user_parts = [
        f"Preset: {preset.get('label', preset_key)}",
        "",
        f"Instructions:\n{preset.get('prompt', '')}",
        "",
    ]
    if preset_key == "custom":
        user_parts.extend([
            f"User format request:\n{custom_prompt}",
            "",
        ])
    user_parts.extend([
        "Transcription to rewrite:",
        transcription,
    ])

    response = client.chat.completions.create(
        model=str(config.get("model", "gpt-4.1-mini")),
        temperature=float(config.get("temperature", 0.2)),
        max_tokens=int(config.get("max_tokens", 4096)),
        messages=[
            {
                "role": "system",
                "content": str(config.get("system_prompt", "")),
            },
            {
                "role": "user",
                "content": "\n".join(user_parts).strip(),
            },
        ],
    )
    content = response.choices[0].message.content or ""
    edited = _normalize_model_response(content)

    usage = getattr(response, "usage", None)
    metadata = {
        "model": str(config.get("model", "gpt-4.1-mini")),
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

    return edited, metadata
