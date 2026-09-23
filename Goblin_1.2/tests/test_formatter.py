from datetime import datetime
from pathlib import Path

from goblin.formatter import build_output_filename, save_transcription, sanitize_filename


def test_sanitize_filename_replaces_unsafe_characters():
    assert sanitize_filename("interview: final / draft?") == "interview__final___draft_"


def test_build_output_filename_includes_date_stem_and_model():
    result = build_output_filename(
        "/tmp/Interview final!.mp3",
        datetime(2026, 9, 23, 14, 5),
        "faster-whisper base",
    )

    assert result == "2026-09-23_14-05_Interview_final__faster-whisper_base.md"


def test_save_transcription_writes_metadata_and_body(tmp_path):
    output_path = save_transcription(
        "  Bonjour le monde.  ",
        "/tmp/notes.mp3",
        datetime(2026, 9, 23, 14, 5),
        "enregistrement audio",
        output_dir=str(tmp_path),
        metadata={
            "mode": "hors-ligne",
            "model": "faster-whisper base",
            "duration_seconds": 12.34,
            "total_tokens": 42,
        },
    )

    content = Path(output_path).read_text(encoding="utf-8")
    assert "fichier_original: notes.mp3" in content
    assert "modele_utilise: faster-whisper base" in content
    assert "| **Durée** | 12.3 s |" in content
    assert content.endswith("\nBonjour le monde.\n")
