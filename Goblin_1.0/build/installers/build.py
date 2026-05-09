"""Cross-platform build script for the Goblin desktop executable.

Usage:
    python build/installers/build.py

What it does:
  1. Ensures PyInstaller is installed (pip install if missing).
  2. Installs / updates all project dependencies so PyInstaller can analyse them.
  3. Runs ``pyinstaller build/goblin.spec --clean`` from the project root.
  4. Reports the location of the produced executable.

The output lands in ``dist/``:
  - Windows : ``dist/Goblin.exe``  (single file)
  - macOS   : ``dist/Goblin.app``  (app bundle – appears as one icon in Finder)
  - Linux   : ``dist/Goblin``      (single file)
"""

import importlib.util
import platform
import shutil
import subprocess
import sys
from pathlib import Path

# ── Paths ─────────────────────────────────────────────────────────────
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SPEC_FILE = REPO_ROOT / "build" / "goblin.spec"
DIST_DIR = REPO_ROOT / "dist"


def _ensure_supported_python() -> None:
    """Fail fast on Python versions that cannot install all build dependencies."""
    if sys.version_info >= (3, 13):
        raise SystemExit(
            "Goblin's build currently requires Python 3.9-3.12 on Windows. "
            "Python 3.13+ is not supported because paddlepaddle wheels are not available. "
            "Install Python 3.11 or 3.12 and rerun the build with `py -3.11` or `py -3.12`."
        )


def _ensure_pyinstaller() -> None:
    """Install PyInstaller if it is not already available."""
    if importlib.util.find_spec("PyInstaller") is None:
        print("PyInstaller not found – installing…")
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "pyinstaller"],
            cwd=REPO_ROOT,
        )
    else:
        print("PyInstaller is available.")


def _install_dependencies() -> None:
    """Install the project and its dependencies into the active environment.

    PyInstaller analyses packages that are importable at *build time*.  If a
    dependency is missing from the venv, its modules are reported as
    "hidden import not found" and silently omitted from the bundle, causing
    ImportError at runtime.  Running ``pip install -e .`` before the build
    ensures every dependency is present for analysis.
    """
    print("Installing / verifying project dependencies…")
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", "-r", str(REPO_ROOT / "build" / "REQUIREMENTS.txt"), "--quiet"],
        cwd=REPO_ROOT,
    )


def _build() -> Path:
    """Run pyinstaller and return the path of the produced executable."""
    print(f"\nBuilding Goblin executable from {SPEC_FILE} …\n")
    subprocess.check_call(
        [
            sys.executable,
            "-m",
            "PyInstaller",
            str(SPEC_FILE),
            "--clean",
            "--noconfirm",
        ],
        cwd=REPO_ROOT,
    )

    system = platform.system()
    if system == "Windows":
        exe = DIST_DIR / "Goblin.exe"
    elif system == "Darwin":
        exe = DIST_DIR / "Goblin.app"
    else:
        exe = DIST_DIR / "Goblin"

    return exe


def main() -> None:
    _ensure_supported_python()
    _ensure_pyinstaller()
    _install_dependencies()
    exe = _build()

    if exe.exists():
        print(f"\n✓ Build successful!\n  Executable : {exe}")
        print("\nNext step: run  python build/installers/install_desktop.py  to create a desktop shortcut.")
    else:
        print(f"\n✗ Build finished but expected executable not found at {exe}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
