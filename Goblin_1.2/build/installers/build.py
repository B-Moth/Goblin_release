"""Cross-platform build script for the Goblin desktop executable.

Usage:
    python build/installers/build.py

What it does:
  1. Ensures PyInstaller is installed (pip install if missing).
  2. Installs / updates all project dependencies so PyInstaller can analyse them.
  3. Runs ``pyinstaller build/goblin.spec --clean`` from the project root.
  4. Reports the location of the produced executable.

The output lands in ``dist/`` as a versioned artifact derived from ``version.py``.
"""

import importlib.util
import platform
import subprocess
import sys
from pathlib import Path

# ── Paths ─────────────────────────────────────────────────────────────
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SRC_DIR = REPO_ROOT / "src"
BUILD_DIR = REPO_ROOT / "build"
SPEC_FILE = REPO_ROOT / "build" / "goblin.spec"
DIST_DIR = REPO_ROOT / "dist"

sys.path.insert(0, str(BUILD_DIR))
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(SRC_DIR))

from version import APP_BASENAME
from goblin.version_sync import sync_versioned_files


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
    ImportError at runtime.  Running ``pip install -e build`` before the build
    also restores the ``goblin`` console script in the active environment.
    """
    print("Installing / verifying project dependencies…")
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", "-r", str(REPO_ROOT / "build" / "REQUIREMENTS.txt"), "--quiet"],
        cwd=REPO_ROOT,
    )
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", "-e", str(BUILD_DIR), "--no-deps", "--quiet"],
        cwd=REPO_ROOT,
    )


def _sync_docs() -> None:
    changed_files = sync_versioned_files()
    if changed_files:
        print("Synced versioned docs:")
        for path in changed_files:
            print(f"- {path.relative_to(REPO_ROOT)}")
    else:
        print("Versioned docs already match the current version.")


def _build() -> Path:
    """Run pyinstaller and return the path of the produced executable."""
    print(f"\nBuilding versioned Goblin executable from {SPEC_FILE} …\n")
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
        exe = DIST_DIR / f"{APP_BASENAME}.exe"
    elif system == "Darwin":
        exe = DIST_DIR / f"{APP_BASENAME}.app"
    else:
        exe = DIST_DIR / APP_BASENAME

    return exe


def main() -> None:
    _ensure_supported_python()
    _ensure_pyinstaller()
    _install_dependencies()
    _sync_docs()
    exe = _build()

    if exe.exists():
        print(f"\n✓ Build successful!\n  Executable : {exe}")
        
        # Setup shell alias for kill-goblin command (Unix-like systems)
        system = platform.system()
        if system in ("Darwin", "Linux"):
            try:
                print("\n▸ Setting up shell alias for 'kill-goblin'...")
                sys.path.insert(0, str(REPO_ROOT / "build" / "installers"))
                from setup_shell_alias import setup_alias
                setup_alias()
            except Exception as e:
                print(f"⚠ Could not setup shell alias: {e}")
                print("  You can setup manually by running:")
                print(f"  python build/installers/setup_shell_alias.py")
        
        # Setup Ollama and pre-pull Qwen model for offline mode
        print("\n▸ Setting up Ollama and pre-pulling Qwen model...")
        try:
            sys.path.insert(0, str(REPO_ROOT / "build" / "installers"))
            from ollama_support import ensure_ollama_available, preload_default_models
            ensure_ollama_available()
            preload_default_models(REPO_ROOT / "src", ["qwen2.5:7b-instruct"])
            print("✓ Ollama setup complete. Goblin is ready for offline mode.")
        except Exception as e:
            print(f"⚠ Ollama setup encountered issues: {e}")
            print("  You can setup manually later or use online mode with an OpenAI API key.")
        
        # Pre-download Whisper base model for offline transcription
        print("\n▸ Pre-downloading Whisper base model for offline transcription...")
        try:
            sys.path.insert(0, str(REPO_ROOT / "src"))
            from goblin.offline import preload_whisper_model
            preload_whisper_model("base")
            print("✓ Whisper model ready.")
        except Exception as e:
            print(f"⚠ Whisper model download encountered issues: {e}")
            print("  It will be downloaded automatically on first use.")
        
        print("\nNext step: run  python build/installers/install_desktop.py  to create a desktop shortcut.")
    else:
        print(f"\n✗ Build finished but expected executable not found at {exe}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
