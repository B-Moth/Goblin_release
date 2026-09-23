# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for the Goblin desktop executable.

Build with:
    python build/installers/build.py
or directly:
    pyinstaller build/goblin.spec

Platform notes
--------------
macOS  – onedir mode + COLLECT + BUNDLE produces a versioned ``dist/Goblin_<version>.app``.
         onefile mode cannot be combined with a .app bundle (deprecated in
         PyInstaller ≥6, error in v7).

Windows / Linux – onefile mode produces a single versioned executable in ``dist/``.
"""

import sys
from pathlib import Path

block_cipher = None
# Handle case where __file__ might not be defined in PyInstaller's exec environment
try:
    REPO_ROOT = Path(__file__).resolve().parent.parent
except NameError:
    # If __file__ is not defined, use the current working directory
    REPO_ROOT = Path.cwd()
SRC_DIR = REPO_ROOT / "src"

sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(SRC_DIR))

from version import APP_BASENAME, VERSION

a = Analysis(
    ["../src/goblin_desktop.py"],
    pathex=[str(REPO_ROOT.resolve()), str(Path("../src").resolve())],
    binaries=[],
    datas=[
        # Include the Jinja2 templates inside the bundle
        ("../src/goblin/templates", "goblin/templates"),
        # Include the transcription editor prompt config
        ("../src/goblin/editor_prompts.json", "goblin"),
    ],
    hiddenimports=[
        # Core goblin modules
        "goblin.gui",
        "goblin.audio",
        "goblin.image",
        "goblin.offline",
        "goblin.formatter",
        "goblin.metadata",
        "goblin.smart_naming",
        "goblin.ollama_runtime",
        "goblin.transcription_editor",
        # Flask / Werkzeug internals often missed by the hook
        "flask",
        "jinja2",
        "jinja2.ext",
        "werkzeug",
        "werkzeug.serving",
        "werkzeug.debug",
        # Click
        "click",
        # Markdown
        "markdown",
        "markdown.extensions.tables",
        "markdown.extensions.fenced_code",
        # Media / ML
        "openai",
        "mutagen",
        "PIL",
        "PIL.Image",
        "faster_whisper",
        "ollama",
        "paddleocr",
        "paddle",
        "torch",
        "transformers",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# ------------------------------------------------------------------
# macOS: onedir mode → COLLECT → BUNDLE (.app)
#
# Combining onefile with BUNDLE is deprecated (PyInstaller ≥6) and
# will become an error in v7.  macOS .app bundles are directories by
# nature; they just appear as a single icon in Finder / Dock.
# ------------------------------------------------------------------
if sys.platform == "darwin":
    exe = EXE(  # noqa: F821
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name=APP_BASENAME,
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        upx_exclude=[],
        runtime_tmpdir=None,
        console=False,  # no terminal window
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
        icon=None,
    )
    coll = COLLECT(  # noqa: F821
        exe,
        a.binaries,
        a.zipfiles,
        a.datas,
        strip=False,
        upx=True,
        upx_exclude=[],
        name=APP_BASENAME,
    )
    app = BUNDLE(  # noqa: F821
        coll,
        name=f"{APP_BASENAME}.app",
        icon=None,
        bundle_identifier="com.lesfeuillets.goblin",
        info_plist={
            "NSHighResolutionCapable": True,
            "CFBundleShortVersionString": VERSION,
        },
    )

# ------------------------------------------------------------------
# Windows / Linux: onefile mode → single executable
# ------------------------------------------------------------------
else:
    exe = EXE(  # noqa: F821
        pyz,
        a.scripts,
        a.binaries,
        a.zipfiles,
        a.datas,
        [],
        name=APP_BASENAME,
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        upx_exclude=[],
        runtime_tmpdir=None,
        # Hide the console on Windows; keep it visible on Linux for debugging
        console=(sys.platform == "linux"),
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
        icon=None,
    )
