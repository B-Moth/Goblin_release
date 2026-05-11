"""Sync the README and docs to the current Goblin version."""

from __future__ import annotations

import re
from pathlib import Path

from goblin.version import APP_BASENAME, VERSION

REPO_ROOT = Path(__file__).resolve().parents[2]

VERSIONED_NAME_RE = re.compile(r"Goblin_[0-9]+(?:\.[0-9]+)*")
README_HEADING_RE = re.compile(r"^(# 🧙 Goblin )([0-9]+(?:\.[0-9]+)*) (– Getting Started)$", re.M)

SYNC_FILES = [
    REPO_ROOT / "README.md",
    REPO_ROOT / "docs" / "INSTALL.md",
    REPO_ROOT / "docs" / "QUICK_REFERENCE.txt",
    REPO_ROOT / "docs" / "guides" / "USER_GUIDE.md",
    REPO_ROOT / "build" / "installers" / "README.md",
]


def _sync_text(text: str) -> str:
    updated = VERSIONED_NAME_RE.sub(APP_BASENAME, text)
    updated = README_HEADING_RE.sub(rf"\g<1>{VERSION} \g<3>", updated)
    return updated


def sync_versioned_files() -> list[Path]:
    changed_files: list[Path] = []
    for path in SYNC_FILES:
        original = path.read_text(encoding="utf-8")
        updated = _sync_text(original)
        if updated != original:
            path.write_text(updated, encoding="utf-8")
            changed_files.append(path)
    return changed_files


def main() -> None:
    changed = sync_versioned_files()
    if changed:
        print("Updated:")
        for path in changed:
            print(f"- {path.relative_to(REPO_ROOT)}")
    else:
        print("No versioned docs needed updates.")


if __name__ == "__main__":
    main()