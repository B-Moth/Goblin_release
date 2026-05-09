"""Extraction des métadonnées (date/heure de création) des fichiers."""

import os
from datetime import datetime
from pathlib import Path

from mutagen import File as MutagenFile
from PIL import Image
from PIL.ExifTags import TAGS


def get_file_creation_date(file_path: str) -> datetime:
    """Return the original creation date/time of a file.

    Priority order:
    1. EXIF DateTimeOriginal (for images taken with a camera/phone)
    2. File modification time (reliable cross-platform fallback)
    """
    # --- EXIF data (images) --------------------------------------------------
    try:
        with Image.open(file_path) as img:
            exif_data = img._getexif()  # type: ignore[attr-defined]
            if exif_data:
                for tag_id, value in exif_data.items():
                    tag = TAGS.get(tag_id, tag_id)
                    if tag == "DateTimeOriginal" and isinstance(value, str):
                        return datetime.strptime(value, "%Y:%m:%d %H:%M:%S")
    except Exception:
        pass

    # --- Audio embedded metadata ---------------------------------------------
    try:
        audio = MutagenFile(file_path)
        if audio is not None and audio.tags:
            for tag_key in ("TDRC", "date", "year"):
                if tag_key in audio.tags:
                    date_str = str(audio.tags[tag_key]).strip()
                    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%Y"):
                        try:
                            return datetime.strptime(date_str, fmt)
                        except ValueError:
                            continue
    except Exception:
        pass

    # --- Fallback: file modification time ------------------------------------
    mtime = os.path.getmtime(file_path)
    return datetime.fromtimestamp(mtime)
