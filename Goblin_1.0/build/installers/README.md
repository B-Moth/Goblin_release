# Installers & Build Scripts

This folder contains the scripts for building, installing, and uninstalling the Goblin browser UI.

## Scripts

### `build.py`
Builds the browser app with PyInstaller.

```bash
python build.py
```

**Output:**
- Windows: `../dist/Goblin.exe`
- macOS: `../dist/Goblin.app`
- Linux: `../dist/Goblin`

**Requirements:**
- PyInstaller installed (`pip install pyinstaller`)
- All dependencies in `REQUIREMENTS.txt`

**Build time:** 5-15 minutes depending on system

### `install_desktop.py`
Creates browser launchers and desktop entries.

```bash
python install_desktop.py
```

**Features:**
- Browser UI only
- Platform-specific installation:
  - Windows: `.lnk` shortcut
  - macOS: `.app` bundle + launcher script
  - Linux: `.desktop` entry + symlink to `~/.local/bin`

**Requirements:**
- Python 3.9+
- Pre-built app from `build.py`

### `uninstall.py`
Removes installed launchers and purges generated build content.

```bash
python uninstall.py --uninstall
```

**What it removes:**
- Desktop shortcuts and launchers
- `dist/` build output
- `build/goblin/` PyInstaller work files
- Downloaded Hugging Face model cache

**What it keeps:**
- Your transcription files
- Your source tree

### `goblin_desktop.py`
Desktop entry point for launching the browser app.

**Purpose:**
- Used by desktop shortcuts/launchers
- Starts the browser UI by default

---

## Build & Install Workflow

### Step 1: Build App
```bash
python build.py
```
This creates the app in `../dist/`

### Step 2: Install Desktop Entry
```bash
python install_desktop.py
```

### Step 3: Launch
- Windows: Click desktop shortcut
- macOS: Open the `.app` or the launcher script
- Linux: Click the app launcher entry

### Step 4: Uninstall / Clean Up
```bash
python uninstall.py --uninstall
```
This removes the browser app launchers plus downloaded build/model content, but preserves transcriptions.

---

## Troubleshooting

### Build Fails
- Ensure all dependencies: `pip install -r REQUIREMENTS.txt`
- Check Python version: `python --version` (need 3.9+)
- Delete `build/` and `dist/` folders, retry

### Installation Fails
- Ensure the app exists: `ls ../dist/Goblin*`
- Check permissions: `chmod +x ../dist/Goblin` (Linux/macOS)
- Try running `python install_desktop.py` again

### App Won't Run
- macOS: `xattr -d com.apple.quarantine /Applications/Goblin.app`
- Windows: Check antivirus software (false positives)
- Linux: `chmod +x Goblin`

---

## Environment Variables

### For build.py
- `TK_SILENCE_DEPRECATION=1` — Suppress Tkinter deprecation warnings (macOS)
- `PYINSTALLER_CUSTOM_ARGS` — Pass additional PyInstaller arguments

### For install_desktop.py
None required, but scripts may use:
- `HOME` — User home directory (Linux/macOS)
- `USERPROFILE` — User home directory (Windows)

---

## File Locations After Installation

### Windows
- App: Desktop shortcut or `C:\Program Files\Goblin\Goblin.exe`
- Config: `%USERPROFILE%\AppData\Local\Goblin\`

### macOS
- App: `~/Applications/Goblin.app`
- Launchers: `~/Applications/Goblin Launchers/`
- Config: `~/.config/goblin/`

### Linux
- App: `~/.local/bin/goblin`
- Desktop entry: `~/.local/share/applications/goblin-*.desktop`
- Config: `~/.config/goblin/`

---

## Development Notes

- PyInstaller specs are generated automatically
- Build includes all Python modules and data files
- Tk included in bundle for cross-platform consistency
- Build output is platform-specific (cannot build Windows app on Mac)

For development modifications, see the main repository README.
