"""Transcription hors-ligne via des modèles locaux (sans clé API).

Audio : faster-whisper (modèle ``base``, CPU) – bon compromis qualité/vitesse.
Image : PaddleOCR pour la détection des lignes + TrOCR local pour la
    reconnaissance manuscrite.

Les modèles sont téléchargés automatiquement au premier démarrage (connexion
Internet requise une seule fois) puis mis en cache localement.
"""

import logging
from pathlib import Path
from typing import Optional

from PIL import Image

logger = logging.getLogger(__name__)

# ── Whisper local ────────────────────────────────────────────────────────────
#: Modèle par défaut (base → bon équilibre qualité/vitesse).
#: Options: "tiny", "base", "medium"
_WHISPER_MODEL_SIZE = "base"

_whisper_model = None


def set_whisper_model_size(size: str) -> None:
    """Change the whisper model size and clear the cached model.

    Valid sizes: "tiny", "base", "medium"
    """
    global _WHISPER_MODEL_SIZE, _whisper_model
    if size not in {"tiny", "base", "medium"}:
        raise ValueError(f"Invalid whisper model size: {size}")
    _WHISPER_MODEL_SIZE = size
    _whisper_model = None  # Clear cache to reload on next use
    logger.info("Whisper model size changed to: %s", size)


def get_whisper_model_size() -> str:
    """Return the current whisper model size."""
    return _WHISPER_MODEL_SIZE


def _get_whisper_model():
    """Chargement paresseux du modèle faster-whisper (CPU, int8)."""
    global _whisper_model
    if _whisper_model is None:
        try:
            from faster_whisper import WhisperModel  # noqa: PLC0415
        except ImportError as exc:
            raise RuntimeError(
                "faster-whisper n'est pas installé. "
                "Lancez : pip install faster-whisper"
            ) from exc

        logger.info(
            "Chargement du modèle Whisper local « %s » (CPU)…",
            _WHISPER_MODEL_SIZE,
        )
        _whisper_model = WhisperModel(
            _WHISPER_MODEL_SIZE,
            device="cpu",
            compute_type="int8",
        )
        logger.info("Modèle Whisper prêt.")
    return _whisper_model


def transcribe_audio_offline(
    file_path: str,
    language: Optional[str] = None,
) -> str:
    """Transcrit *file_path* localement avec faster-whisper (CPU).
    
    ⚠️  Processing time on CPU:
        - Small files (< 10MB): ~5-15 seconds
        - Medium files (10-50MB): ~1-5 minutes
        - Large files (> 50MB): ~20-60 minutes (depending on content)

    Args:
        file_path: Chemin vers le fichier audio.
        language:  Code ISO-639-1 (ex. ``"fr"``).  ``None`` = détection auto.

    Returns:
        Texte transcrit.
    """
    import os
    
    model = _get_whisper_model()
    
    # Warn about large files
    file_size_mb = os.path.getsize(file_path) / 1e6
    if file_size_mb > 50:
        logger.warning(
            "Fichier audio volumineux (%.1f MB). La transcription peut prendre 20-60 minutes. "
            "C'est normal, c'est juste lent sur CPU. Patientez…",
            file_size_mb,
        )
    elif file_size_mb > 10:
        logger.info(
            "Fichier audio de %.1f MB. La transcription peut prendre 1-5 minutes…",
            file_size_mb,
        )
    
    kwargs: dict = {"beam_size": 5}
    if language:
        kwargs["language"] = language

    segments, _info = model.transcribe(file_path, **kwargs)
    return " ".join(seg.text for seg in segments).strip()


# ── PaddleOCR local ─────────────────────────────────────────────────────────

_ocr_reader = None
_trocr_processor = None
_trocr_model = None

_TROCR_MODEL_NAME = "microsoft/trocr-large-handwritten"


def _get_paddle_ocr():
    """Chargement paresseux du lecteur PaddleOCR optimisé pour les manuscrits."""
    global _ocr_reader
    if _ocr_reader is None:
        try:
            from paddleocr import PaddleOCR  # noqa: PLC0415
        except ImportError as exc:
            raise RuntimeError(
                "paddleocr n'est pas installé. "
                "Lancez : pip install paddleocr paddlepaddle"
            ) from exc

        logger.info("Chargement du lecteur PaddleOCR (optimisé manuscrits)…")
        _ocr_reader = PaddleOCR(use_textline_orientation=True, lang="fr")
        logger.info("Lecteur PaddleOCR prêt.")
    return _ocr_reader


def _get_trocr_components():
    """Chargement paresseux du modèle TrOCR local."""
    global _trocr_processor, _trocr_model
    if _trocr_processor is None or _trocr_model is None:
        try:
            import torch  # noqa: PLC0415
            from transformers import (  # noqa: PLC0415
                TrOCRProcessor,
                VisionEncoderDecoderModel,
            )
        except ImportError as exc:
            raise RuntimeError(
                "transformers et torch sont requis pour l'OCR manuscrit local. "
                "Lancez : pip install transformers torch"
            ) from exc

        logger.info("Chargement du modèle TrOCR local « %s »…", _TROCR_MODEL_NAME)
        _trocr_processor = TrOCRProcessor.from_pretrained(_TROCR_MODEL_NAME)
        _trocr_model = VisionEncoderDecoderModel.from_pretrained(_TROCR_MODEL_NAME)
        _trocr_model.to("cpu")
        _trocr_model.eval()
        logger.info("Modèle TrOCR prêt.")

    return _trocr_processor, _trocr_model


def _box_bounds(box) -> tuple[int, int, int, int]:
    """Return left, top, right, bottom coordinates for a box or polygon."""
    if isinstance(box, (list, tuple)) or hasattr(box, "__len__"):
        try:
            values = [float(value) for value in box]
        except (TypeError, ValueError):
            values = []

        if len(values) == 4:
            left, top, right, bottom = values
            return int(left), int(top), int(right), int(bottom)

    xs = [point[0] for point in box]
    ys = [point[1] for point in box]
    return int(min(xs)), int(min(ys)), int(max(xs)), int(max(ys))


def _extract_boxes(page_result) -> list:
    """Extract line boxes from a PaddleOCR page result."""
    boxes = None
    if hasattr(page_result, "get"):
        boxes = page_result.get("rec_boxes")
        if boxes is None:
            boxes = page_result.get("dt_polys")

    if boxes is None and hasattr(page_result, "json"):
        data = page_result.json
        if isinstance(data, dict):
            res = data.get("res", {})
            boxes = res.get("rec_boxes")
            if boxes is None:
                boxes = res.get("dt_polys")

    return list(boxes) if boxes is not None else []


def _crop_box(image: Image.Image, box) -> Image.Image:
    """Crop a text line from an image with a small padding."""
    left, top, right, bottom = _box_bounds(box)
    padding = 8
    left = max(0, left - padding)
    top = max(0, top - padding)
    right = min(image.width, right + padding)
    bottom = min(image.height, bottom + padding)
    return image.crop((left, top, right, bottom))


def _recognize_handwritten_line(line_image: Image.Image) -> str:
    """Recognize a single handwritten line with TrOCR."""
    import torch  # noqa: PLC0415

    processor, model = _get_trocr_components()
    pixel_values = processor(images=line_image, return_tensors="pt").pixel_values
    with torch.inference_mode():
        generated_ids = model.generate(
            pixel_values,
            num_beams=4,
            max_new_tokens=128,
        )
    text = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
    return " ".join(text.split()).strip()


def _should_skip_ocr_line(text: str, poly) -> bool:
    """Filtre quelques faux positifs évidents issus des estampilles et en-têtes."""
    normalized = " ".join(text.split())
    if not normalized:
        return True

    compact = normalized.replace(" ", "")
    if normalized.upper() in {"ARCHIVES", "NATIONALES", "ARCHIVES NATIONALES"}:
        return True

    if len(compact) >= 6 and compact.isalpha() and compact.isupper():
        if poly is not None:
            xs = [point[0] for point in poly]
            avg_x = sum(xs) / len(xs)
            if avg_x > 450:
                return True
        return normalized in {"ARCHIVES", "NATIONALES"}

    return False


def _extract_paddle_text(page_result) -> str:
    """Extrait le texte d'une page OCR PaddleOCR."""
    texts = None
    polys = None

    if hasattr(page_result, "get"):
        texts = page_result.get("rec_texts")
        polys = page_result.get("rec_polys")

    if texts is None and hasattr(page_result, "json"):
        data = page_result.json
        if isinstance(data, dict):
            res = data.get("res", {})
            texts = res.get("rec_texts")
            polys = res.get("rec_polys")

    lines = []
    if texts:
        for index, text in enumerate(texts):
            if not isinstance(text, str):
                continue
            poly = polys[index] if polys and index < len(polys) else None
            if _should_skip_ocr_line(text, poly):
                continue
            cleaned = " ".join(text.split())
            if cleaned:
                lines.append(cleaned)
        return "\n".join(lines).strip()

    # Fallback for older PaddleOCR output structures.
    try:
        for item in page_result:
            if isinstance(item, (list, tuple)) and len(item) >= 2:
                text_data = item[1]
                if isinstance(text_data, (list, tuple)) and text_data:
                    text = text_data[0]
                else:
                    text = text_data
                if isinstance(text, str) and text.strip():
                    lines.append(text.strip())
    except TypeError:
        return ""

    return "\n".join(lines).strip()


def _resize_image_for_ocr(image: Image.Image) -> Image.Image:
    """Redimensionne l'image si elle est trop grande pour PaddleOCR.
    
    PaddleOCR peut se bloquer sur les très grandes images. 
    Limite la largeur à 1600 pixels tout en préservant le ratio d'aspect.
    
    Args:
        image: Image PIL à redimensionner.
        
    Returns:
        Image redimensionnée ou originale si déjà assez petite.
    """
    max_width = 1600
    if image.width > max_width:
        ratio = max_width / image.width
        new_height = int(image.height * ratio)
        logger.info(
            "Image trop grande (%dx%d). Redimensionnement à %dx%d…",
            image.width,
            image.height,
            max_width,
            new_height,
        )
        return image.resize((max_width, new_height), Image.Resampling.LANCZOS)
    return image


def transcribe_image_offline(file_path: str) -> str:
    """Extrait le texte manuscrit de *file_path* via PaddleOCR + TrOCR.

    Args:
        file_path: Chemin vers le fichier image.

    Returns:
        Texte extrait, lignes séparées par des sauts de ligne.
    """
    ocr = _get_paddle_ocr()
    
    # Load and potentially resize image before OCR
    source_image = Image.open(file_path).convert("RGB")
    processed_image = _resize_image_for_ocr(source_image)
    
    # Save resized image temporarily if it was resized
    import tempfile
    if processed_image is not source_image:
        # Use temp file for resized image
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            processed_image.save(tmp.name)
            temp_file_path = tmp.name
    else:
        temp_file_path = file_path
    
    try:
        results = ocr.ocr(temp_file_path)
    finally:
        # Clean up temp file if created
        if processed_image is not source_image:
            import os
            try:
                os.unlink(temp_file_path)
            except OSError:
                pass

    lines = []
    # Use the processed (potentially resized) image for cropping OCR boxes
    ocr_image = processed_image
    
    for page_result in results:
        boxes = _extract_boxes(page_result)
        if boxes:
            for box in sorted(boxes, key=lambda item: (_box_bounds(item)[1], _box_bounds(item)[0])):
                line_image = _crop_box(ocr_image, box)
                line_text = _recognize_handwritten_line(line_image)
                if line_text and not _should_skip_ocr_line(line_text, box):
                    lines.append(line_text)
        else:
            page_text = _extract_paddle_text(page_result)
            if page_text:
                lines.extend(page_text.splitlines())

    return "\n".join(lines).strip()

