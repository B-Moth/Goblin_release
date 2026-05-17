"""Interface web Goblin – drag-and-drop + visualisation des transcriptions."""

import logging
import os
import re
import shutil
import sys
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from typing import Optional

import markdown
import subprocess
from mutagen import File as MutagenFile
from flask import Flask, jsonify, render_template, request, send_file, url_for
from markupsafe import escape
from openai import AuthenticationError
from send2trash import send2trash

from goblin.audio import is_audio_file, transcribe_audio
from goblin.credentials import (
    delete_openai_api_key,
    load_saved_openai_api_key,
    is_valid_openai_api_key,
    save_openai_api_key,
)
from goblin.formatter import save_transcription
from goblin.image import is_image_file, transcribe_image
from goblin.smart_naming import generate_smart_name, extract_excerpt
from goblin.metadata import get_file_creation_date
from goblin.offline import get_whisper_model_size
from goblin.offline import transcribe_audio_offline, transcribe_image_offline
from goblin.transcription_editor import (
    build_edited_transcription_filename,
    get_editor_custom_mode,
    get_editor_presets,
    load_editor_config,
    read_transcription_body,
    rewrite_transcription,
)
import json

logger = logging.getLogger(__name__)


def _template_folder() -> str:
    """Return the absolute path to the Jinja2 templates directory.

    Works both when running from source *and* when bundled with PyInstaller
    (which sets ``sys._MEIPASS`` to the temporary extraction directory).
    """
    if hasattr(sys, "_MEIPASS"):
        # PyInstaller extracts package data under sys._MEIPASS
        return os.path.join(sys._MEIPASS, "goblin", "templates")
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")


_SUPPORTED_EXTENSIONS = frozenset(
    {
        # audio
        ".flac", ".m4a", ".mp3", ".mp4", ".mpeg", ".mpga", ".ogg", ".wav", ".webm",
        # image
        ".bmp", ".gif", ".jpeg", ".jpg", ".png", ".tif", ".tiff", ".webp",
    }
)

_PREVIEW_DIRNAME = ".goblin-previews"
_IMAGE_EXTENSIONS = frozenset({".bmp", ".gif", ".jpeg", ".jpg", ".png", ".tif", ".tiff", ".webp"})
_AUDIO_EXTENSIONS = frozenset({".flac", ".m4a", ".mp3", ".mp4", ".mpeg", ".mpga", ".ogg", ".wav", ".webm"})


def _safe_output_dir(requested: str, default: str) -> str:
    """Resolve *requested* to an absolute path, falling back to *default*.

    Only bare directory names (no separators) are accepted from user input to
    prevent path traversal.  Absolute paths and paths with ``..`` components
    are rejected and replaced with *default*.
    """
    req = requested.strip()
    # Reject anything that looks like an absolute path or traversal attempt
    if not req or os.sep in req or (os.altsep and os.altsep in req) or ".." in req.split("/"):
        return default
    return req


def _list_transcriptions(output_dir: str) -> list[dict]:
    """Return a sorted list of transcription metadata dicts."""
    base = Path(output_dir).resolve()
    if not base.is_dir():
        return []
    files = sorted(
        base.glob("*.md"),
        key=lambda path: (path.stat().st_mtime, path.name),
        reverse=True,
    )
    result = []
    for f in files:
        mtime = datetime.fromtimestamp(f.stat().st_mtime).strftime("%d/%m/%Y %H:%M")
        result.append({"name": f.name, "display": f.stem, "mtime": mtime})
    return result


def _render_md(path: Path) -> str:
    """Render a Markdown file to sanitised HTML."""
    text = path.read_text(encoding="utf-8")
    # Strip YAML front-matter before rendering
    text = re.sub(r"^---\n.*?\n---\n", "", text, count=1, flags=re.DOTALL)
    return markdown.markdown(
        text,
        extensions=["tables", "fenced_code"],
    )


def _extract_frontmatter_value(path: Path, key: str) -> Optional[str]:
    """Extract a single front-matter value from a saved transcription."""
    text = path.read_text(encoding="utf-8")
    match = re.search(rf"^{re.escape(key)}:\s*(.+)$", text, flags=re.MULTILINE)
    if not match:
        return None
    value = match.group(1).strip()
    return value or None


def _preview_path(transcription_path: Path, original_filename: str) -> Path:
    """Return the local path of the stored preview asset for a transcription."""
    preview_dir = transcription_path.parent / _PREVIEW_DIRNAME
    return preview_dir / f"{transcription_path.stem}{Path(original_filename).suffix.lower()}"


def _parse_transcription_creation_date(transcription_path: Path) -> datetime:
    """Return the original file creation date stored in a transcription."""
    value = _extract_frontmatter_value(transcription_path, "date_creation")
    if value:
        for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S"):
            try:
                return datetime.strptime(value, fmt)
            except ValueError:
                continue
    return datetime.fromtimestamp(transcription_path.stat().st_mtime)


def _archive_folder_for_transcription(output_dir: Path, transcription_path: Path) -> Path:
    """Return the archive folder for a transcription based on original creation date."""
    creation_date = _parse_transcription_creation_date(transcription_path)
    return output_dir.parent / "archives" / creation_date.strftime("%Y-%m-%d")


def _transcription_matches_metadata(
    transcription_path: Path,
    original_filename: str,
    model_name: str,
) -> bool:
    """Return True when a transcription matches the original file and model."""
    return (
        _extract_frontmatter_value(transcription_path, "fichier_original") == original_filename
        and _extract_frontmatter_value(transcription_path, "modele_utilise") == model_name
    )


def _unique_archive_path(archive_dir: Path, filename: str) -> Path:
    """Return a non-colliding path inside *archive_dir* for *filename*."""
    candidate = archive_dir / filename
    if not candidate.exists():
        return candidate

    stem = Path(filename).stem
    suffix = Path(filename).suffix
    counter = 2
    while True:
        candidate = archive_dir / f"{stem}__{counter}{suffix}"
        if not candidate.exists():
            return candidate
        counter += 1


def _empty_transcription_output_dir(output_dir: Path) -> None:
    """Trash every generated item from the transcription output directory."""
    for child in list(output_dir.iterdir()):
        if child.is_dir():
            _empty_transcription_output_dir(child)
        send2trash(str(child))


def _render_preview_html(transcription_path: Path) -> str:
    """Render an image or audio preview block for a transcription, if available."""
    original_filename = _extract_frontmatter_value(transcription_path, "fichier_original")
    if not original_filename:
        return ""

    preview_path = _preview_path(transcription_path, original_filename)
    if not preview_path.exists():
        return ""

    preview_url = url_for("transcription_preview", filename=transcription_path.name)
    safe_name = escape(original_filename)
    suffix = Path(original_filename).suffix.lower()

    if suffix in _IMAGE_EXTENSIONS:
        return (
            f'<div class="transcription-preview">'
            f"<h3>Aperçu</h3>"
            f'<a href="{preview_url}" target="_blank" rel="noopener noreferrer" class="preview-link">'
            f'<img src="{preview_url}" alt="Aperçu de {safe_name}">'
            f"</a>"
            f"</div>"
        )

    if suffix in _AUDIO_EXTENSIONS:
        return (
            f'<div class="transcription-preview">'
            f"<h3>Lecture audio</h3>"
            f'<audio controls preload="metadata" src="{preview_url}"></audio>'
            f"</div>"
        )

    return ""


def _trash_transcription_files(transcription_path: Path) -> None:
    """Move a transcription and its stored preview asset to the OS trash."""
    original_filename = _extract_frontmatter_value(transcription_path, "fichier_original")
    if original_filename:
        preview_path = _preview_path(transcription_path, original_filename)
        if preview_path.exists():
            send2trash(str(preview_path))
    send2trash(str(transcription_path))


def _rename_with_smart_name(saved_path: str, excerpt: str, model_size: str) -> None:
    """Rename a transcription file using smart naming (runs in background)."""
    logger.info("Smart naming task started for %s", saved_path)
    try:
        saved_file = Path(saved_path)
        if not saved_file.exists():
            logger.warning("File %s no longer exists for smart naming", saved_path)
            return

        logger.debug("Generating smart name for %s (excerpt: %s)", saved_path, excerpt[:50])
        # Generate smart name from excerpt
        smart_name = generate_smart_name(excerpt, model_size)
        if not smart_name:
            logger.info("Smart naming returned no name for %s (API failure or no key)", saved_path)
            return

        logger.debug("Got smart name: %s", smart_name)
        # Parse the existing filename: YYYY-MM-DD_HH-MM_[name]_[model].md
        stem = saved_file.stem
        logger.debug("Parsing stem: %s", stem)
        parts = stem.split("_", 2)  # Split into [date, time, rest]
        logger.debug("Parsed parts: %s (count: %d)", parts, len(parts))
        if len(parts) < 3:
            logger.warning("Cannot parse filename %s for smart naming (got %d parts)", stem, len(parts))
            return

        date_part = parts[0]
        time_part = parts[1]
        # rest might be like "name_model" or just "model", we want to replace it
        new_stem = f"{date_part}_{time_part}_{smart_name}_{model_size}"
        new_path = saved_file.parent / f"{new_stem}.md"
        logger.debug("New filename would be: %s", new_path.name)

        # Avoid collision
        if new_path.exists() and new_path != saved_file:
            logger.debug("Target path exists, finding alternative")
            counter = 1
            while True:
                new_stem_versioned = f"{date_part}_{time_part}_{smart_name}_{model_size}_{counter}"
                new_path = saved_file.parent / f"{new_stem_versioned}.md"
                if not new_path.exists():
                    break
                counter += 1
            logger.debug("Using alternative: %s", new_path.name)

        saved_file.rename(new_path)
        logger.info("Smart-renamed %s → %s", saved_file.name, new_path.name)
    except Exception as exc:
        logger.exception("Smart naming failed for %s: %s", saved_path, exc)


def create_app(output_dir: str = "transcriptions", offline: bool = False) -> Flask:
    """Create and configure the Flask application.

    Args:
        output_dir: Directory where transcription Markdown files are stored
                    and where new transcriptions will be saved.
        offline:    If ``True`` (default), use local models (no API key needed).
                    If ``False``, use the OpenAI API (requires OPENAI_API_KEY).
    """
    load_saved_openai_api_key()
    app = Flask(__name__, template_folder=_template_folder())
    # Resolve to absolute path at startup so later comparisons are reliable
    app.config["OUTPUT_DIR"] = str(Path(output_dir).resolve())
    app.config["MAX_CONTENT_LENGTH"] = 200 * 1024 * 1024  # 200 MB
    # Default per-type modes. If the global `offline` flag is requested we
    # enable offline for both transcription types; otherwise use the
    # more granular defaults:
    # - Handwritten text: online by default (OFFLINE_HANDWRITING = False)
    # - Audio: offline by default (OFFLINE_AUDIO = True)
    if offline:
        app.config["OFFLINE_HANDWRITING"] = True
        app.config["OFFLINE_AUDIO"] = True
    else:
        app.config["OFFLINE_HANDWRITING"] = False
        app.config["OFFLINE_AUDIO"] = True

    # Thread pool for async smart naming
    app.smart_naming_executor = ThreadPoolExecutor(max_workers=1)

    # Whisper model size (for offline audio)
    from goblin.offline import get_whisper_model_size  # noqa: F401
    app.config["WHISPER_MODEL_SIZE"] = get_whisper_model_size()
    
    # Smart naming (optional async renaming based on content)
    app.config["SMART_NAMING_ENABLED"] = False

    @app.route("/")
    def index():
        out = app.config["OUTPUT_DIR"]
        transcriptions = _list_transcriptions(out)
        api_key_set = bool(os.environ.get("OPENAI_API_KEY"))
        handwriting_offline = app.config.get("OFFLINE_HANDWRITING", False)
        audio_offline = app.config.get("OFFLINE_AUDIO", True)
        whisper_model_size = app.config.get("WHISPER_MODEL_SIZE", "base")
        smart_naming_enabled = app.config.get("SMART_NAMING_ENABLED", False)
        return render_template(
            "index.html",
            transcriptions=transcriptions,
            selected=None,
            messages=[],
            api_key_set=api_key_set,
            handwriting_offline=handwriting_offline,
            audio_offline=audio_offline,
            whisper_model_size=whisper_model_size,
            smart_naming_enabled=smart_naming_enabled,
            editor_presets=get_editor_presets(),
            editor_custom_mode=get_editor_custom_mode(),
        )

    @app.route("/set-mode", methods=["POST"])
    def set_mode():
        data = request.get_json(force=True, silent=True) or {}

        # Backwards-compatible: if a single `offline` value is provided,
        # apply it to both transcription types.
        if "offline" in data:
            offline_val = bool(data.get("offline", False))
            app.config["OFFLINE_HANDWRITING"] = offline_val
            app.config["OFFLINE_AUDIO"] = offline_val
            return jsonify({
                "ok": True,
                "offline": offline_val,
                "handwriting_offline": app.config["OFFLINE_HANDWRITING"],
                "audio_offline": app.config["OFFLINE_AUDIO"],
            })

        # Granular updates
        if "handwriting_offline" in data:
            app.config["OFFLINE_HANDWRITING"] = bool(data.get("handwriting_offline"))

        if "audio_offline" in data:
            app.config["OFFLINE_AUDIO"] = bool(data.get("audio_offline"))

        return jsonify({
            "ok": True,
            "handwriting_offline": app.config["OFFLINE_HANDWRITING"],
            "audio_offline": app.config["OFFLINE_AUDIO"],
        })

    @app.route("/set-api-key", methods=["POST"])
    def set_api_key():
        data = request.get_json(force=True, silent=True) or {}
        key = (data.get("key") or "").strip()
        if key:
            if not is_valid_openai_api_key(key):
                return jsonify({
                    "ok": False,
                    "error": "La clé fournie ne ressemble pas à une clé OpenAI valide (ex. 'sk-...').",
                }), 400
            os.environ["OPENAI_API_KEY"] = key
            save_openai_api_key(key)
            return jsonify({"ok": True})
        return jsonify({"ok": False, "error": "Clé vide"}), 400

    @app.route("/delete-api-key", methods=["POST"])
    def delete_api_key():
        delete_openai_api_key()
        return jsonify({"ok": True})

    @app.route("/set-whisper-model", methods=["POST"])
    def set_whisper_model():
        """Set the offline whisper model size (tiny, base, small, medium, large)."""
        data = request.get_json(force=True, silent=True) or {}
        model_size = (data.get("model_size") or "").strip()
        if not model_size:
            return jsonify({"ok": False, "error": "model_size is required"}), 400
        
        try:
            from goblin.offline import set_whisper_model_size
            set_whisper_model_size(model_size)
            app.config["WHISPER_MODEL_SIZE"] = model_size
            return jsonify({"ok": True, "model_size": model_size})
        except ValueError as e:
            return jsonify({"ok": False, "error": str(e)}), 400

    @app.route("/set-smart-naming", methods=["POST"])
    def set_smart_naming():
        """Toggle smart naming feature."""
        # Check if API key is available
        has_api_key = bool(os.environ.get("OPENAI_API_KEY"))
        
        data = request.get_json(force=True, silent=True) or {}
        enabled = bool(data.get("enabled", False))
        
        if enabled and not has_api_key:
            logger.warning("Smart naming requested but no API key available")
            return jsonify({
                "ok": False,
                "enabled": False,
                "error": "Clé API OpenAI non trouvée. Définissez OPENAI_API_KEY.",
                "has_api_key": False
            })
        
        app.config["SMART_NAMING_ENABLED"] = enabled
        return jsonify({
            "ok": True,
            "enabled": enabled,
            "has_api_key": has_api_key
        })

    @app.route("/transcribe", methods=["POST"])
    def transcribe():
        # Per-file handling below determines whether the OpenAI API is required
        # (audio and image processing honor the per-type OFFLINE_* flags).
        has_api_key = bool(os.environ.get("OPENAI_API_KEY"))

        uploaded = request.files.getlist("files")
        # If no files were uploaded, preserve the previous behavior: when the
        # app is configured in (partial) online mode and no API key is set,
        # return an error so the UI can prompt the user to set a key.
        if not uploaded:
            requires_api = (not app.config.get("OFFLINE_HANDWRITING", False)) or (not app.config.get("OFFLINE_AUDIO", True))
            if requires_api and not has_api_key:
                return jsonify(
                    {
                        "messages": [
                            {
                                "type": "error",
                                "text": "Clé OPENAI_API_KEY non définie. Renseignez-la dans la bannière ou passez en mode hors-ligne.",
                            }
                        ],
                        "refresh": False,
                        "last_saved": None,
                    }
                ), 400
        language = request.form.get("language") or None

        # Always write to the app-configured output directory (never user-supplied path)
        out_dir = app.config["OUTPUT_DIR"]

        messages = []
        last_saved = None
        smart_naming_queued = False

        with tempfile.TemporaryDirectory() as tmp_dir:
            for upload in uploaded:
                original_name = Path(upload.filename or "fichier").name
                suffix = Path(original_name).suffix.lower()

                if suffix not in _SUPPORTED_EXTENSIONS:
                    messages.append(
                        {
                            "type": "error",
                            "text": f"Format non pris en charge : {original_name}",
                        }
                    )
                    continue

                # Save upload to a temp file that preserves the original name
                tmp_path = Path(tmp_dir) / original_name
                upload.save(str(tmp_path))

                try:
                    creation_date = get_file_creation_date(str(tmp_path))
                    start_time = time.perf_counter()

                    def _split_audio_into_chunks(input_path: Path, chunk_seconds: int = 60) -> list[Path]:
                        """Split *input_path* into WAV chunks using ffmpeg. Returns list of chunk Paths.

                        Falls back to returning the original file if ffmpeg is not available or splitting fails.
                        """
                        chunks_dir = Path(input_path).parent / (Path(input_path).stem + "_chunks")
                        chunks_dir.mkdir(parents=True, exist_ok=True)
                        out_pattern = str(chunks_dir / "chunk_%03d.wav")
                        cmd = [
                            "ffmpeg",
                            "-hide_banner",
                            "-loglevel",
                            "error",
                            "-i",
                            str(input_path),
                            "-vn",
                            "-ac",
                            "1",
                            "-ar",
                            "16000",
                            "-f",
                            "segment",
                            "-segment_time",
                            str(chunk_seconds),
                            "-reset_timestamps",
                            "1",
                            out_pattern,
                        ]
                        try:
                            subprocess.check_call(cmd)
                            chunks = sorted(chunks_dir.glob("chunk_*.wav"))
                            if chunks:
                                return chunks
                        except Exception:
                            logger.exception("Chunking failed for %s; falling back to single-file processing", input_path)
                        # Fallback: return the original file
                        return [input_path]

                    if is_audio_file(str(tmp_path)):
                        # Chunked processing to reduce potential loss on interruption
                        transcription_texts = []
                        transcription_metadata = {}
                        try:
                            mut = MutagenFile(str(tmp_path))
                            duration = getattr(mut.info, "length", None)
                        except Exception:
                            duration = None

                        chunks = [tmp_path]
                        if duration and duration > 120:
                            chunks = _split_audio_into_chunks(tmp_path, chunk_seconds=60)

                        total_chunk_duration = 0.0
                        model_size = get_whisper_model_size()
                        last_part_meta = {"mode": "hors-ligne", "model": f"faster-whisper {model_size} int8"}
                        for ci, chunk_path in enumerate(chunks):
                            if app.config.get("OFFLINE_AUDIO", True):
                                part_text = transcribe_audio_offline(str(chunk_path), language=language)
                                part_meta = {"mode": "hors-ligne", "model": f"faster-whisper {model_size} int8"}
                            else:
                                audio_result = transcribe_audio(str(chunk_path), language=language, return_metadata=True)
                                if isinstance(audio_result, tuple):
                                    part_text, api_metadata = audio_result
                                else:
                                    part_text = audio_result
                                    api_metadata = {"model": "whisper-1", "usage": {}}
                                part_meta = {"mode": "en ligne", "model": api_metadata.get("model", "whisper-1")}
                                part_meta.update(api_metadata.get("usage", {}))

                            transcription_texts.append(str(part_text).strip())
                            try:
                                mutp = MutagenFile(str(chunk_path))
                                part_duration = getattr(mutp.info, "length", 0.0) or 0.0
                            except Exception:
                                part_duration = 0.0
                            total_chunk_duration += float(part_duration)

                            # Save partial cumulative transcription after each chunk
                            cumulative_text = "\n\n".join(transcription_texts)
                            save_transcription(
                                transcription=cumulative_text,
                                original_path=original_name,
                                creation_date=creation_date,
                                file_type="enregistrement audio",
                                output_dir=out_dir,
                                metadata={"mode": part_meta.get("mode"), "model": part_meta.get("model"), "duration_seconds": total_chunk_duration},
                            )
                            last_part_meta = part_meta

                        transcription = "\n\n".join(transcription_texts)
                        transcription_metadata = {
                            "mode": last_part_meta.get("mode", "hors-ligne"),
                            "model": last_part_meta.get("model", f"faster-whisper {model_size} int8"),
                            "duration_seconds": total_chunk_duration,
                        }
                        file_type = "enregistrement audio"
                    else:
                        # For images: prefer GPT-4o Vision when key is available,
                        # fallback to local OCR. Honor the per-type handwriting flag.
                        has_api_key = bool(os.environ.get("OPENAI_API_KEY"))
                        if app.config.get("OFFLINE_HANDWRITING", False) or not has_api_key:
                            transcription = transcribe_image_offline(str(tmp_path))
                            transcription_metadata = {
                                "mode": "hors-ligne",
                                "model": "TrOCR + PaddleOCR",
                            }
                        else:
                            image_result = transcribe_image(
                                str(tmp_path),
                                return_metadata=True,
                            )
                            if isinstance(image_result, tuple):
                                transcription, api_metadata = image_result
                            else:
                                transcription = image_result
                                api_metadata = {"model": "gpt-4o-mini", "usage": {}}
                            transcription_metadata = {
                                "mode": "en ligne",
                                "model": api_metadata.get("model", "gpt-4o-mini"),
                            }
                            transcription_metadata.update(api_metadata.get("usage", {}))
                        file_type = "texte manuscrit"

                    transcription_metadata["duration_seconds"] = time.perf_counter() - start_time

                    saved_path = save_transcription(
                        transcription=transcription,
                        original_path=original_name,
                        creation_date=creation_date,
                        file_type=file_type,
                        output_dir=out_dir,
                        metadata=transcription_metadata,
                    )
                    preview_path = _preview_path(Path(saved_path), original_name)
                    preview_path.parent.mkdir(parents=True, exist_ok=True)
                    try:
                        shutil.copyfile(tmp_path, preview_path)
                    except OSError:
                        logger.exception("Failed to store preview for %s", original_name)
                    last_saved = Path(saved_path).name
                    messages.append(
                        {
                            "type": "success",
                            "text": f"✓ {original_name} → {Path(saved_path).name}",
                        }
                    )

                    # Queue smart naming in background if enabled
                    if app.config.get("SMART_NAMING_ENABLED", False):
                        excerpt = extract_excerpt(transcription, max_length=100)
                        model_size = app.config.get("WHISPER_MODEL_SIZE", "base")
                        logger.info(
                            "Queuing smart naming for %s (smart_naming_enabled=%s, model=%s)",
                            saved_path,
                            app.config.get("SMART_NAMING_ENABLED", False),
                            model_size,
                        )
                        app.smart_naming_executor.submit(
                            _rename_with_smart_name,
                            saved_path,
                            excerpt,
                            model_size,
                        )
                        smart_naming_queued = True
                        messages.append(
                            {
                                "type": "info",
                                "text": f"Nommage intelligent lancé pour {Path(saved_path).name}.",
                            }
                        )
                    else:
                        logger.debug("Smart naming disabled or not enabled")
                except AuthenticationError:
                    logger.exception("OpenAI authentication error for %s", original_name)
                    messages.append(
                        {
                            "type": "error",
                            "text": f"Erreur d'authentification OpenAI pour {original_name} : Clé API invalide ou expirée. "
                                    f"Vérifiez votre clé sur https://platform.openai.com/account/api-keys et mettez-la à jour dans la bannière, "
                                    f"ou passez en mode Hors-ligne pour transcrire ce fichier.",
                        }
                    )
                except OSError as exc:
                    logger.exception("OS error during transcription for %s: %s", original_name, exc)
                    # Prefer human-friendly strerror when available but fall back to str(exc).
                    err_msg = getattr(exc, 'strerror', None) or str(exc) or repr(exc)
                    errno_part = f"[Errno {getattr(exc, 'errno', 'n/a')}] "
                    messages.append(
                        {
                            "type": "error",
                            "text": (
                                f"Erreur système pour {original_name} : {errno_part}{err_msg}. "
                                f"Détails: {repr(exc)}. Vérifiez l'espace disque, les permissions et réessayez."
                            ),
                        }
                    )
                except Exception as exc:  # noqa: BLE001
                    logger.exception("Transcription error for %s", original_name)
                    messages.append(
                        {
                            "type": "error",
                            "text": f"Erreur pour {original_name} : {type(exc).__name__} — {str(exc)}",
                        }
                    )

        return jsonify(
            {
                "messages": messages,
                "refresh": last_saved is not None,
                "last_saved": last_saved,
                "smart_naming_queued": smart_naming_queued,
            }
        )

    @app.route("/transcriptions")
    def list_transcriptions():
        out = app.config["OUTPUT_DIR"]
        return jsonify(_list_transcriptions(out))

    def _queue_log_path() -> Path:
        return Path(app.config["OUTPUT_DIR"]).resolve() / ".queue_log.json"

    @app.route("/queue", methods=["GET", "POST"])
    def queue_log():
        """Persist and return a simple queue log stored alongside transcriptions.

        The log is a JSON array of objects with keys: `name`, `status`, `eta_seconds`.
        This allows the client to resume a previously started folder processing
        by re-selecting the same folder and matching filenames.
        """
        path = _queue_log_path()
        if request.method == "GET":
            if not path.exists():
                return jsonify([])
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                return jsonify([])
            return jsonify(data)

        # POST — save/replace the log
        data = request.get_json(force=True, silent=True) or []
        try:
            tmp = path.with_suffix(".queue_log.json.tmp")
            tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            tmp.replace(path)
            return jsonify({"ok": True})
        except Exception:
            logger.exception("Failed to write queue log to %s", path)
            return jsonify({"ok": False}), 500

    @app.route("/transcriptions/<filename>")
    def view_transcription(filename: str):
        out_dir = Path(app.config["OUTPUT_DIR"]).resolve()
        # Validate the requested filename against the actual list of known files.
        # This avoids constructing any filesystem path from raw user input.
        known = {entry["name"] for entry in _list_transcriptions(str(out_dir))}
        safe_name = Path(filename).name
        if safe_name not in known:
            return jsonify({"html": "<p>Fichier introuvable.</p>"}), 404
        path = out_dir / safe_name
        return jsonify({"html": _render_md(path) + _render_preview_html(path)})

    @app.route("/transcriptions/<filename>/rewrite", methods=["POST"])
    def rewrite_transcription_route(filename: str):
        out_dir = Path(app.config["OUTPUT_DIR"]).resolve()
        known = {entry["name"] for entry in _list_transcriptions(str(out_dir))}
        safe_name = Path(filename).name
        if safe_name not in known:
            return jsonify({"ok": False, "error": "Fichier introuvable."}), 404

        if not os.environ.get("OPENAI_API_KEY"):
            return jsonify({"ok": False, "error": "Clé API OpenAI requise pour la réécriture en ligne."}), 403

        data = request.get_json(force=True, silent=True) or {}
        preset_key = (data.get("preset") or "").strip()
        if not preset_key:
            return jsonify({"ok": False, "error": "preset is required"}), 400

        custom_prompt = (data.get("custom_prompt") or "").strip()
        action = (data.get("action") or "save").strip().lower()
        edited_text = (data.get("edited_text") or "").strip()

        config = load_editor_config()
        preset = config.get("presets", {}).get(preset_key)
        if not preset:
            return jsonify({"ok": False, "error": "Preset inconnu."}), 400

        source_path = out_dir / safe_name
        try:
            metadata = {"model": config.get("model", "gpt-4.1-mini"), "usage": {}}
            if action == "preview" or not edited_text:
                source_text = read_transcription_body(source_path)
                edited_text, metadata = rewrite_transcription(source_text, preset_key, custom_prompt=custom_prompt)
        except AuthenticationError:
            return jsonify({"ok": False, "error": "Clé API OpenAI requise pour la réécriture en ligne."}), 403
        except ValueError as exc:
            return jsonify({"ok": False, "error": str(exc)}), 400
        except Exception as exc:  # noqa: BLE001
            logger.exception("Failed to rewrite transcription %s", safe_name)
            return jsonify({"ok": False, "error": f"Réécriture impossible : {exc}"}), 500

        edited_text = edited_text.strip()
        if not edited_text:
            return jsonify({"ok": False, "error": "Réponse vide de l'IA."}), 502

        suggested_name = build_edited_transcription_filename(
            safe_name,
            str(preset.get("slug", preset_key)).strip(),
            custom_prompt=custom_prompt,
        )

        if action == "preview":
            return jsonify(
                {
                    "ok": True,
                    "preview": edited_text,
                    "suggested_name": suggested_name,
                    "preset": preset_key,
                    "label": preset.get("label", preset_key),
                    "metadata": metadata,
                }
            )

        output_name = suggested_name
        output_path = out_dir / output_name
        if output_path.exists():
            counter = 2
            stem = output_path.stem
            suffix = output_path.suffix
            while True:
                candidate = out_dir / f"{stem}__{counter}{suffix}"
                if not candidate.exists():
                    output_path = candidate
                    break
                counter += 1

        output_path.write_text(edited_text + "\n", encoding="utf-8")

        return jsonify(
            {
                "ok": True,
                "saved": output_path.name,
                "preset": preset_key,
                "label": preset.get("label", preset_key),
                "metadata": metadata,
            }
        )

    @app.route("/transcriptions/<filename>/preview")
    def transcription_preview(filename: str):
        out_dir = Path(app.config["OUTPUT_DIR"]).resolve()
        known = {entry["name"] for entry in _list_transcriptions(str(out_dir))}
        safe_name = Path(filename).name
        if safe_name not in known:
            return jsonify({"error": "Fichier introuvable."}), 404

        path = out_dir / safe_name
        original_filename = _extract_frontmatter_value(path, "fichier_original")
        if not original_filename:
            return jsonify({"error": "Aperçu indisponible."}), 404

        preview_path = _preview_path(path, original_filename)
        if not preview_path.exists():
            return jsonify({"error": "Aperçu indisponible."}), 404

        return send_file(preview_path, conditional=True)

    @app.route("/transcriptions/<filename>", methods=["DELETE"])
    def delete_transcription(filename: str):
        out_dir = Path(app.config["OUTPUT_DIR"]).resolve()
        known = {entry["name"] for entry in _list_transcriptions(str(out_dir))}
        safe_name = Path(filename).name
        if safe_name not in known:
            return jsonify({"ok": False, "error": "Fichier introuvable."}), 404

        transcription_path = out_dir / safe_name
        try:
            _trash_transcription_files(transcription_path)
            return jsonify({"ok": True, "deleted": safe_name})
        except Exception:
            logger.exception("Failed to move transcription %s to trash", safe_name)
            return jsonify({"ok": False, "error": "Impossible de déplacer la transcription à la corbeille."}), 500

    @app.route("/transcriptions", methods=["DELETE"])
    def delete_all_transcriptions():
        out_dir = Path(app.config["OUTPUT_DIR"]).resolve()
        entries = _list_transcriptions(str(out_dir))
        deleted = []

        try:
            for entry in entries:
                transcription_path = out_dir / entry["name"]
                _trash_transcription_files(transcription_path)
                deleted.append(entry["name"])
            return jsonify({"ok": True, "deleted": deleted, "count": len(deleted)})
        except Exception:
            logger.exception("Failed to move all transcriptions to trash")
            return jsonify({"ok": False, "error": "Impossible de déplacer toutes les transcriptions à la corbeille."}), 500

    @app.route("/archive-transcriptions", methods=["POST"])
    def archive_transcriptions():
        out_dir = Path(app.config["OUTPUT_DIR"]).resolve()
        entries = _list_transcriptions(str(out_dir))
        archive_root = out_dir.parent / "archives"
        copied = []
        skipped = []

        try:
            for entry in entries:
                transcription_path = out_dir / entry["name"]
                original_filename = _extract_frontmatter_value(transcription_path, "fichier_original") or ""
                model_name = _extract_frontmatter_value(transcription_path, "modele_utilise") or "unknown"
                archive_dir = _archive_folder_for_transcription(out_dir, transcription_path)
                archive_dir.mkdir(parents=True, exist_ok=True)

                already_archived = any(
                    _transcription_matches_metadata(existing, original_filename, model_name)
                    for existing in archive_dir.glob("*.md")
                )
                if already_archived:
                    skipped.append(entry["name"])
                    continue

                destination = _unique_archive_path(archive_dir, entry["name"])
                shutil.copy2(transcription_path, destination)
                copied.append(destination.name)

            _empty_transcription_output_dir(out_dir)
            return jsonify({
                "ok": True,
                "archive_root": str(archive_root),
                "copied": copied,
                "skipped": skipped,
                "count": len(copied),
            })
        except Exception:
            logger.exception("Failed to archive transcriptions")
            return jsonify({"ok": False, "error": "Impossible d'archiver les transcriptions."}), 500

    @app.route("/shutdown", methods=["POST"])
    def shutdown():
        """Gracefully shut down the server."""
        # Capture the shutdown function while still in request context
        func = request.environ.get("werkzeug.server.shutdown")
        
        def do_shutdown():
            import time
            time.sleep(0.5)  # Give time for response to be sent
            if func is None:
                # If running without werkzeug, just exit
                import sys
                sys.exit(0)
            else:
                func()
        
        import threading
        threading.Thread(target=do_shutdown, daemon=True).start()
        return jsonify({"ok": True, "message": "Arrêt en cours..."})

    @app.route("/quit", methods=["POST"])
    def quit_app():
        """Terminate the process after the response is sent."""
        import threading
        import os

        def do_quit():
            time.sleep(0.5)
            os._exit(0)

        threading.Thread(target=do_quit, daemon=True).start()
        return jsonify({"ok": True, "message": "Fermeture en cours..."})

    return app


def run_gui(output_dir: str = "transcriptions", host: str = "127.0.0.1", port: int = 5000, offline: bool = False) -> None:
    """Start the web UI and open a browser tab."""
    import threading
    import webbrowser
    from werkzeug.serving import make_server
    import tempfile
    from pathlib import Path
    import getpass
    import errno

    url = f"http://{host}:{port}"

    # Single-instance guard: create a PID file in the system temp dir
    def _pid_file() -> Path:
        user = getpass.getuser() or "goblin"
        return Path(tempfile.gettempdir()) / f"goblin_{user}.pid"

    def _looks_like_goblin_process(pid: int) -> bool:
        """Return True when *pid* appears to be a Goblin process.

        This avoids false positives when a stale PID file points to a
        recycled PID that now belongs to an unrelated process.
        """
        try:
            result = subprocess.run(
                ["ps", "-p", str(pid), "-o", "command="],
                capture_output=True,
                text=True,
                check=False,
            )
            cmdline = (result.stdout or "").strip().lower()
            return "goblin" in cmdline
        except Exception:
            return False

    pidf = _pid_file()
    if pidf.exists():
        try:
            existing = int(pidf.read_text())
            # Check if process exists
            try:
                os.kill(existing, 0)
            except OSError as e:
                if e.errno in (errno.ESRCH, errno.EINVAL):
                    # Stale PID file
                    pidf.unlink(missing_ok=True)
                else:
                    print(f"Existing Goblin instance seems to be running (PID {existing}). Exiting.")
                    return
            else:
                if _looks_like_goblin_process(existing):
                    print(f"Goblin already running (PID {existing}). Opening browser.")
                    try:
                        webbrowser.open(url)
                    except Exception:
                        pass
                    return
                # PID exists but does not belong to Goblin: treat as stale lock.
                pidf.unlink(missing_ok=True)
        except Exception:
            # Can't parse file — remove and continue
            try:
                pidf.unlink(missing_ok=True)
            except Exception:
                pass

    # Reserve our PID file
    try:
        pidf.write_text(str(os.getpid()), encoding="utf-8")
    except Exception:
        # If we can't write the PID file, warn but continue
        print("Warning: cannot write PID file; single-instance guard disabled.")

    app = create_app(output_dir=output_dir, offline=offline)

    # Create a werkzeug server that can be shut down via the /shutdown endpoint
    server = make_server(host, port, app, threaded=True)
    
    # Run server in a background thread so we can wait for it to shut down
    server_thread = threading.Thread(target=server.serve_forever, daemon=False)
    server_thread.start()

    # Open browser slightly after server starts
    threading.Timer(1.0, lambda: webbrowser.open(url)).start()
    mode_label = "hors-ligne" if offline else "en ligne"
    print(f"Goblin – interface web disponible sur {url}  [{mode_label}]  (Ctrl+C pour quitter)")
    
    # Wait for the server thread to finish (either via /shutdown or Ctrl+C)
    try:
        server_thread.join()
    except KeyboardInterrupt:
        print("\nArrêt du serveur...")
        server.shutdown()
    finally:
        # Remove PID file on clean exit
        try:
            pidf.unlink(missing_ok=True)
        except Exception:
            pass
