# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for the Goblin desktop executable.

Build with:
    python build/installers/build.py
or directly:
    pyinstaller build/goblin.spec

Platform notes
--------------
macOS  – onedir mode + COLLECT + BUNDLE produces ``dist/Goblin.app``.
         onefile mode cannot be combined with a .app bundle (deprecated in
         PyInstaller ≥6, error in v7).

Windows / Linux – onefile mode produces a single ``dist/Goblin[.exe]``.
"""

import sys
from pathlib import Path

block_cipher = None

a = Analysis(
    ["../src/goblin_desktop.py"],
    pathex=[str(Path("../src").resolve())],
    binaries=[],
    datas=[
        # Include the Jinja2 templates inside the bundle
        ("../src/goblin/templates", "goblin/templates"),
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
        name="Goblin",
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
        name="Goblin",
    )
    app = BUNDLE(  # noqa: F821
        coll,
        name="Goblin.app",
        icon=None,
        bundle_identifier="com.lesfeuillets.goblin",
        info_plist={
            "NSHighResolutionCapable": True,
            "CFBundleShortVersionString": "0.1.0",
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
        name="Goblin",
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
