# Full User Guide

Complete reference for Goblin features, UI navigation, and workflows.

## Table of Contents
1. [Getting Started](#getting-started)
2. [UI Overview](#ui-overview)
3. [Basic Workflow](#basic-workflow)
4. [Advanced Features](#advanced-features)
5. [Tips & Tricks](#tips--tricks)
6. [Troubleshooting](#troubleshooting)

---

## Getting Started

### First Launch
1. Install Goblin (see [INSTALL.md](../INSTALL.md))
2. Launch via:
   - Windows: Double-click shortcut or `Goblin.exe`
   - macOS: Double-click `Goblin.app` or `.command` launcher
   - Linux: Click app launcher or run `goblin` command

3. Open the browser app:
   - Goblin launches in your browser

### Initial Configuration
1. Choose processing mode:
   - **Offline** (default) — Free, no setup required
   - **Online** — Requires OpenAI API key
2. Set output folder (defaults to `transcriptions/`)
3. Select Whisper model size for offline audio (defaults to `base`; available models are `tiny`, `base`, and `medium`)

---

## UI Overview

### Header (Dark Bar)
```
🧙 Goblin | Audio: Hors-ligne | Manuscrit: En ligne | 🔑 Clé API | Quitter
```

**Controls:**
- **🧙 Goblin** — Title and logo
- **Audio toggle** — Switch between offline/online audio processing
- **Manuscrit toggle** — Switch between offline/online handwriting
- **🔑 Clé API** — Manage OpenAI API key
- **Quitter** — Exit application

### Left Sidebar (Transcriptions)
Lists all completed transcriptions in your output folder.

**Features:**
- **Search/Filter** — Find transcriptions by name
- **Archiver** — Move selected file to archive folder
- **Tout supprimer** — Clear all transcriptions (with confirmation)
- **Click to view** — Select any file to preview in main panel
- **Double-click** — Open original file (if available)

### Main Content Area (Drop Zone & Settings)

#### Drop Zone
```
Glissez vos fichiers ici
Audio (mp3, wav, m4a...) ou images de texte manuscrit (jpg, png...)
[Sélectionner des fichiers]
```

**Actions:**
- Drag & drop files
- Click button to browse files
- Supports multiple file selection

#### Settings Row
- **Langue** — Language selection (auto-detect or specific code: fr, en, es, etc.)
- **Dossier de sortie** — Change output folder path
- **Modèle Whisper** — Select offline model size (tiny, base, medium)

### Main Viewer (Text Area)
Displays selected transcription text.

**Features:**
- Read-only by default (protected from accidental edits)
- Full text search (Ctrl+F / Cmd+F in browser)
- Copy text (Ctrl+C / Cmd+C)
- Shows file metadata in status bar

---

## Basic Workflow

### Transcribe Audio

1. **Prepare file:**
   - Supported: MP3, WAV, M4A, FLAC, OGG, WEBM, MP4
   - File size: No limit (but large files take longer)
   - Quality: Best with clear, professional audio

2. **Select file:**
   - Click "Sélectionner des fichiers" or drag & drop
   - Select one or more audio files

3. **Configure:**
   - **Audio mode:** Toggle to your preference (offline/online)
   - **Language:** Auto-detect or specify (fr, en, es, etc.)

4. **Process:**
   - Files are queued and processed sequentially
   - ETA displayed at top
   - Status updates in real-time

5. **Review:**
   - Click file in sidebar to view
   - Edit text if needed
   - Save location shown in status bar

### Transcribe Handwriting (OCR)

1. **Prepare file:**
   - Supported: JPG, PNG, BMP, GIF, TIFF, WEBP
   - Recommended: High-contrast, clear handwriting
   - Tips: Straighten pages, even lighting, remove shadows

2. **Select file:**
   - Click "Sélectionner des fichiers" or drag & drop
   - Select one or more image files

3. **Configure:**
   - **Manuscrit mode:** Toggle to your preference (offline/online)
   - **Language:** Auto-detect or specify
   - **Output folder:** Ensure writable location

4. **Process:**
   - Files are queued and processed sequentially
   - Higher accuracy with online mode (GPT-4o-mini)
   - Offline mode faster but less accurate

5. **Review:**
   - Click file in sidebar
   - Online results typically more accurate
   - Edit manually if needed

---

## Advanced Features

### Batch Processing

Queue multiple files at once:

1. Click "Sélectionner des fichiers"
2. Select 5, 10, or 100+ files
3. All are queued with:
   - Individual ETA per file
   - Total queue ETA
   - Current processing status

**Queue Management:**
- Files process one-at-a-time in order
- ETA updates as processing completes
- Can close app; queue resumes on restart (offline mode only)

### API Key Management

#### Add API Key
1. Click **🔑 Clé API** button
2. Paste your OpenAI API key
3. Key is securely stored locally

#### Remove API Key
1. Click **🔑 Clé API** button
2. Select "Supprimer la clé" (Delete Key)
3. Confirm deletion
4. Online mode becomes unavailable

#### Find Your Key
1. Visit https://platform.openai.com/api-keys
2. Create or copy existing key
3. Paste into Goblin

### File Organization

#### Output Folder
- Default: `transcriptions/` in app directory
- Change via settings input field
- New folders created automatically

#### Archive Folder
- Transcriptions archived to: `transcriptions/archive/`
- Organized by date (YYYY/MM/DD/filename.md)
- Safely stored, can be restored

#### Prevent Accidental Deletion
- Deletion requires confirmation
- Deleted files moved to trash (recoverable)
- Archive before final cleanup

### Language Support

#### Automatic Detection
- Leave "Détection automatique" selected
- Works for ~99 languages
- Best accuracy with clear audio

#### Specific Languages
Select language code:
- **fr** — Français (French)
- **en** — English
- **es** — Español (Spanish)
- **de** — Deutsch (German)
- **it** — Italiano (Italian)
- **pt** — Português (Portuguese)
- **ru** — Русский (Russian)
- **ja** — 日本語 (Japanese)
- And 90+ others...

**Tip:** Specifying language improves accuracy for audio.

### Offline Model Selection

For offline audio processing, choose:

- **tiny** — Fastest (10-20x real-time), lowest accuracy
- **base** — **Recommended** (2-5x real-time), good accuracy
- **medium** — Very good accuracy (0.5-1x real-time)

**First download:** Models download on first use (~30 min to 2 hours).

---

## Tips & Tricks

### Performance Optimization

**For speed:**
- Use **offline tiny** model for quick drafts
- Use **online** mode for final transcriptions
- Reduce image size for OCR
- Use **base** model for audio (good balance)

**For accuracy:**
- Use **online** mode (Whisper API + GPT-4o-mini)
- Use **medium** offline models for audio
- Improve image quality for OCR
- Specify language if known

**For offline mode:**
- Use GPU if available (much faster)
- Close other apps to free RAM
- Consider the medium model only with 8+ GB RAM

### Smart Naming

When you enable smart naming, Goblin sends a short excerpt of the saved transcription to GPT-3.5-turbo and renames the Markdown file with the returned slug.

- It only runs after the file is saved.
- The browser sidebar updates automatically after the rename.
- If no usable name is returned, Goblin keeps the original filename.

### Workflow Tips

1. **Quick drafts:** Use offline tiny model, review, re-run online for final
2. **Batch processing:** Queue 10+ files overnight, review in morning
3. **Multiple folders:** Create separate output folders for projects
4. **Language specific:** Set language before processing for better accuracy
5. **Hybrid mode:** Audio offline, handwriting online (best value)

### Keyboard Shortcuts

| Action | Windows/Linux | macOS |
|--------|---------------|-------|
| Open files | Ctrl+O | Cmd+O |
| Quit app | Ctrl+Q | Cmd+Q |
| Focus search | Ctrl+F | Cmd+F |
| Copy text | Ctrl+C | Cmd+C |

### Accessibility

- **Keyboard navigation:** Tab through all controls
- **High contrast:** Works with system dark/light modes
- **Text size:** Adjust browser zoom (Ctrl/Cmd + +/-)
- **Screen readers:** Supported in web UI

---

## Troubleshooting

### Common Issues

#### "Executable not found"
**Error:** Appears during installation
**Solution:** Run `python scripts/build.py` to build executable

#### "No module named goblin"
**Error:** Command line error
**Solution:** 
- Reinstall: `pip install -e .`
- Check Python path: `which python`

#### App crashes on startup
**Solution:**
- Check logs: `/tmp/goblin-main.log` (macOS/Linux)
- Reinstall dependencies: `pip install -r REQUIREMENTS.txt --force-reinstall`
- Clear cache: `rm -rf ~/.cache/huggingface`

#### Models not downloading
**Error:** "Could not download model"
**Solution:**
- Check internet connection
- Increase timeout: Run again (retry automatic)
- Manual download: See [MODES.md](MODES.md)

#### API key not working
**Error:** "Invalid API key" or "Authentication error"
**Solution:**
- Verify key at https://platform.openai.com/api-keys
- Check for trailing spaces in key
- Ensure account has credit
- Try removing and re-adding key

#### Files not processed
**Error:** Files stay in queue indefinitely
**Solution:**
- Check output folder is writable: `ls -la transcriptions/`
- Free up disk space (models + output)
- Check logs for errors
- Restart app

#### Handwriting recognition failing
**Error:** Results are garbled or blank
**Solution:**
- Improve image quality (high contrast)
- Straighten tilted pages
- Try **online mode** (much better accuracy)
- Reduce image size if very large

#### Slow performance
**Causes & Solutions:**
- **Offline mode slow?** Upgrade to GPU, or use online mode
- **Large files slow?** Normal; large audio/images take time
- **Many models?** Delete unused models: `rm -rf ~/.cache/huggingface`
- **RAM limited?** Use **tiny** model, reduce file size

#### Permission denied (Linux/macOS)
**Error:** "Permission denied"
**Solution:**
```bash
chmod +x Goblin
sudo chown $USER Goblin  # If needed
```

#### macOS "App is damaged"
**Error:** "The app is damaged and can't be opened"
**Solution:**
```bash
xattr -d com.apple.quarantine /Applications/Goblin.app
```

### Getting Help

1. **Check logs:**
   - Windows: `%USERPROFILE%\AppData\Local\Temp\goblin-main.log`
   - macOS/Linux: `/tmp/goblin-main.log`

2. **Search documentation:**
   - [FEATURES.md](FEATURES.md) — All capabilities
   - [MODES.md](MODES.md) — Offline vs online
   - [QUICKSTART.md](../QUICKSTART.md) — Quick reference

3. **Report issues:**
   - Include logs and error messages
   - Describe steps to reproduce
   - Specify OS, Python version, file format

---

## Keyboard Shortcut Reference

### Application
| Action | Shortcut |
|--------|----------|
| Quit | Ctrl/Cmd + Q |
| Open files | Ctrl/Cmd + O |

### Text Viewer
| Action | Shortcut |
|--------|----------|
| Select all | Ctrl/Cmd + A |
| Copy | Ctrl/Cmd + C |
| Find | Ctrl/Cmd + F |

### Navigation (Web UI)
| Action | Shortcut |
|--------|----------|
| Tab forward | Tab |
| Tab backward | Shift + Tab |
| Focus dropdown | Space/Enter |

---

Last updated: May 7, 2026  
For updates and community support, visit the GitHub repository.
