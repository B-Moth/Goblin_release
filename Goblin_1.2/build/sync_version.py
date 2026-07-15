"""Backward-compatible wrapper for the Goblin version sync command."""

from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "src"))

from goblin.version_sync import main


if __name__ == "__main__":
    main()