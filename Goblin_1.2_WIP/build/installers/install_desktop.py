"""Create desktop shortcuts / launchers for Goblin browser UI.

Usage (after running  python build/installers/build.py):
    python build/installers/install_desktop.py

The script installs the browser UI only.

Platform installation details:
  - Windows : Creates .lnk shortcuts on the Desktop
    - macOS   : Installs the versioned Goblin app bundle and creates launcher scripts
  - Linux   : Writes .desktop entries to ~/.local/share/applications
"""

import os
import platform
import shutil
import stat
import sys
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SRC_DIR = REPO_ROOT / "src"
DIST_DIR = REPO_ROOT / "dist"
WINDOWS_SHORTCUT_NAME = "Goblin (Browser UI).lnk"
WINDOWS_FALLBACK_NAME = "Goblin (Browser UI).exe"
MACOS_LAUNCHER_NAME = "Goblin (Browser UI).command"
LINUX_DESKTOP_NAME = "goblin-browser.desktop"

sys.path.insert(0, str(SRC_DIR))

sys.path.insert(0, str(REPO_ROOT))

from version import APP_BASENAME


# ── Helpers ────────────────────────────────────────────────────────────

def _find_exe() -> Path:
    system = platform.system()
    if system == "Windows":
        exe = DIST_DIR / f"{APP_BASENAME}.exe"
    elif system == "Darwin":
        exe = DIST_DIR / f"{APP_BASENAME}.app"
    else:
        exe = DIST_DIR / APP_BASENAME

    if not exe.exists():
        print(
            f"✗ Executable not found at {exe}\n"
            "  Run  python build/installers/build.py  first.",
            file=sys.stderr,
        )
        sys.exit(1)

    return exe


# ── Platform installers ────────────────────────────────────────────────

def _install_windows(exe: Path) -> None:
    """Create a desktop shortcut for the browser UI on Windows."""
    try:
        import winreg  # noqa: F401 - confirms we're on Windows
        import comtypes.client as cc  # type: ignore[import]
    except ImportError:
        # Fallback: copy the exe to the Desktop
        desktop = Path(os.path.expandvars("%USERPROFILE%")) / "Desktop"
        dest_browser = desktop / WINDOWS_FALLBACK_NAME
        shutil.copy2(exe, dest_browser)
        print(f"✓ Copied to Desktop: {dest_browser}")
        return

    import pythoncom  # type: ignore[import]

    desktop_path = Path(os.path.expandvars("%USERPROFILE%")) / "Desktop"
    shell = cc.CreateObject("WScript.Shell", interface=pythoncom.IID_IDispatch)
    
    shortcut_browser = shell.CreateShortCut(str(desktop_path / WINDOWS_SHORTCUT_NAME))
    shortcut_browser.TargetPath = str(exe)
    shortcut_browser.WorkingDirectory = str(exe.parent)
    shortcut_browser.Description = "Goblin – Browser UI"
    shortcut_browser.Save()
    print(f"✓ Desktop shortcut created: {WINDOWS_SHORTCUT_NAME}")


def _install_macos(exe: Path) -> None:
    """Copy the .app bundle to ~/Applications and create a browser launcher."""
    apps_dir = Path.home() / "Applications"
    apps_dir.mkdir(parents=True, exist_ok=True)
    dest = apps_dir / f"{APP_BASENAME}.app"

    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(exe, dest)

    # Create launcher scripts for easy access
    launcher_dir = apps_dir / "Goblin Launchers"
    launcher_dir.mkdir(parents=True, exist_ok=True)

    browser_launcher = launcher_dir / MACOS_LAUNCHER_NAME
    browser_launcher.write_text(
        f'#!/bin/bash\n"{dest}/Contents/MacOS/{APP_BASENAME}"\n',
        encoding="utf-8",
    )
    browser_launcher.chmod(browser_launcher.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    print(f"✓ Launcher script created: {MACOS_LAUNCHER_NAME}")

    print(f"✓ {APP_BASENAME}.app installed to {dest}")
    print(f"✓ Launcher scripts in {launcher_dir}")
    print(f"  Double-click the launcher or drag {APP_BASENAME}.app to the Dock.")

    # Try to ensure Ollama is available for local-model editing.
    try:
        from shutil import which
        if which("ollama") is None:
            print("ℹ Ollama not found on PATH — attempting to install via Homebrew...")
            if which("brew"):
                try:
                    subprocess.check_call(["brew", "install", "ollama"])  # may require sudo or user interaction
                    print("✓ Ollama installed via Homebrew.")
                except Exception:
                    print(
                        "✗ Failed to install Ollama via Homebrew. Please install Ollama manually: https://ollama.com"
                    )
            else:
                print(
                    "⚠ Homebrew not found. Install Homebrew (https://brew.sh) and then Ollama (https://ollama.com)."
                )
        else:
            print("✓ Ollama detected on PATH.")
    except Exception:
        print("⚠ Could not check or install Ollama automatically. See https://ollama.com for manual installation.")


def _install_linux(exe: Path) -> None:
    """Install a browser .desktop entry and symlink the binary."""
    # 1. Ensure ~/.local/bin is on PATH and symlink the binary
    bin_dir = Path.home() / ".local" / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    link = bin_dir / "goblin"
    if link.exists() or link.is_symlink():
        link.unlink()
    link.symlink_to(exe)
    # Ensure the binary is executable
    exe.chmod(exe.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    # 2. Write a single .desktop file for the browser app
    apps_dir = Path.home() / ".local" / "share" / "applications"
    apps_dir.mkdir(parents=True, exist_ok=True)

    desktop_file_browser = apps_dir / LINUX_DESKTOP_NAME
    desktop_file_browser.write_text(
        "[Desktop Entry]\n"
        "Version=1.0\n"
        "Type=Application\n"
        "Name=Goblin\n"
        "Comment=Goblin – Browser UI\n"
        f"Exec={link}\n"
        "Icon=\n"
        "Terminal=false\n"
        "Categories=Utility;AudioVideo;\n",
        encoding="utf-8",
    )
    desktop_file_browser.chmod(desktop_file_browser.stat().st_mode | stat.S_IXUSR)
    print(f"✓ Desktop entry created: {LINUX_DESKTOP_NAME}")

    print(f"✓ Binary symlinked at: {link}")
    print("  Log out and back in (or run 'update-desktop-database ~/.local/share/applications')")
    print("  to see the entry in your application launcher.")


# ── Entry point ────────────────────────────────────────────────────────

def main() -> None:
    exe = _find_exe()
    system = platform.system()

    if system == "Windows":
        _install_windows(exe)
    elif system == "Darwin":
        _install_macos(exe)
    else:
        _install_linux(exe)


if __name__ == "__main__":
    main()
