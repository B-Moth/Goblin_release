Built with ❤️ for *Les Feuillets* by Lucas


# 🧙 Goblin 1.2 – Getting Started

Goblin transcribes audio and converts handwritten images to editable Markdown files.
For now the UI is french-only.

## Getting started

### Already Have the Executable? (see dist/ folder) 

**Windows:** Double-click `dist/Goblin_1.2.exe`  
**macOS:** Open `dist/Goblin_1.2.app`  
**Linux:** Run `chmod +x dist/Goblin_1.2 && ./dist/Goblin_1.2`

---

### Run from source WITHOUT building the executable (usefull for testing changes, no need to build)

```bash
goblin --web
```

Specify a custom port if you need:
```bash
goblin --web -p 5001
```

---

### Build the self-contained, fully-configured executable

This creates a complete, ready-to-use Goblin installation with everything included:

**Windows:**
```powershell
py -3.12 build/installers/build.py
```

**macOS/Linux:**
```bash
python3.12 build/installers/build.py
```

What this does:
- ✅ Builds the executable
- ✅ Sets up `kill-goblin` shell alias
- ✅ Installs Ollama (if not already present)
- ✅ Pre-pulls Qwen 7B model for offline transcription
- ✅ Goblin is ready to use immediately after

**Optional: Create desktop shortcuts**

If you want desktop shortcuts and system launcher integration:

**Windows:**
```powershell
py -3.12 build/installers/install_desktop.py
```

**macOS/Linux:**
```bash
python3.12 build/installers/install_desktop.py
```

This adds:
- Desktop shortcuts / application launcher entries
- macOS: App bundle in `~/Applications` + Dock-friendly launcher scripts
- Linux: `.desktop` entry in application menu

### Clean Rebuild

**macOS/Linux (standard rebuild — preserves downloaded models):**
```bash
./build/rebuild.sh
```

What this does:
- ✅ Kills any running Goblin processes
- ✅ Cleans build artifacts (executable, __pycache__, etc)
- ✅ Reinstalls Python dependencies
- ✅ Rebuilds the executable
- ⏭️ **Preserves models** (Whisper + Qwen) for faster rebuild

**Full rebuild (deletes and reinstalls everything including models):**
```bash
./build/rebuild.sh --full
```

What this does:
- ✅ Everything from standard rebuild, plus:
- ✅ Removes all cached Whisper models
- ✅ Removes Ollama models (qwen2.5:7b-instruct, qwen2.5:14b-instruct)
- ✅ Re-downloads and caches models during build

**Use `--full` when:**
- Updating to a new model version
- Troubleshooting model-related issues
- Starting from a completely clean state

---

### Shell Alias Setup (automatic during build)

The `build.py` script automatically sets up the `kill-goblin` alias to your shell profile.

After building, restart your terminal and use:
```bash
kill-goblin
```

To manually setup later, run:
```bash
python3.12 build/installers/setup_shell_alias.py
```

## 📊 What Goblin Does

- **Audio** → **Text** : MP3, WAV, M4A, FLAC, OGG, WEBM, MP4
- **Images** → **Text** : JPG, PNG, BMP, GIF, TIFF, WEBP
- **Works Offline** or with OpenAI APIs
- **Smart Naming** (optional, with OpenAI API): AI auto-renames files by content

---

## ✅ System Requirements

- **OS:** Windows 10+, macOS 11+, Ubuntu 20.04+
- **RAM:** 4 GB minimum (8+ GB recommended)
- **Disk:** 2 GB free space for full online, up to 8 GB for offline
- **Python:** 3.11 or 3.12 (only needed if building from source)

## Features

- **🔌 Offline transcription Mode** — Uses local faster-whisper + TrOCR/PaddleOCR
- **🌐 Online Mode** — Uses OpenAI Whisper API + GPT-4o-mini (requires API key)
- **🪄 Smart Naming** — Optionally renames saved transcriptions with GPT-3.5-turbo (requieres API key for now)
- **📝 Markdown Output** — Editable, searchable text files
- **📁 Batch Processing** — Queue multiple files for processing
- **✍️ Review Assistant** — Rewrites a selected transcription into a cleaned `.md` version with a local Qwen model by default, while keeping the original file untouched.

You can find and change the prompts used for the defaults editing options in src/goblin/editor_prompts.json .
The review assistant also supports a **custom format** option: write your own formatting request in the dialog, and Goblin will apply it with the same anti-hallucination rules, the same language as the transcription, and Markdown-only output.

By default Goblin uses **Qwen 7B Instruct** locally through Ollama for the review assistant. If you want a larger local model, choose **Qwen 14B Instruct** in the dialog. If you prefer a faster and more powerfull online workflow, switch the mode to **En ligne (OpenAI)** and provide an API key.

## Edit a transcription

When a transcription is open in the viewer, click **Mise en forme auto** to open the automated editor.

- Choose **Qwen 14B Instruct** if you want the larger local model.
- Switch to **En ligne (OpenAI)** if you want the API-backed workflow instead.
- Choose one of the config-driven presets: Interview, Résumé, or Documentation.
- Or choose **Personnalisé** and type your own formatting request.
- Click **Aperçu** first to generate a draft, then **Enregistrer** to save the exact markdown result as a new file.
- Goblin saves the rewritten result as a new Markdown file and keeps the original transcription as-is.

## Uninstall

### Standard Uninstall (removes app, keeps models)

```bash
python build/installers/uninstall.py --uninstall
```

What this does:
- ✅ Removes installed launchers/shortcuts
- ✅ Deletes build artifacts (dist/ and build output)
- ✅ Removes metadata files (.DS_Store, Thumbs.db, etc)
- ⏭️ **Preserves downloaded models** (Whisper + Qwen)
- ✅ Keeps all transcriptions untouched

**Use this** when uninstalling temporarily or if you plan to reinstall soon.

### Full Uninstall (removes everything including models)

```bash
python build/installers/uninstall.py --uninstall --full
```

What this does:
- ✅ Everything from standard uninstall, plus:
- ✅ Removes all cached Whisper models (~1.5 GB)
- ✅ Removes all installed Ollama models (Qwen 7B & 14B, ~10+ GB total)
- ✅ Keeps all transcriptions untouched

**Use this** when doing a complete cleanup or freeing up disk space.

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| **Python not found** | Install Python 3.11 or 3.12 from python.org and use `py -3.11` or `py -3.12` |
| **Permission denied** | Run: `chmod +x Goblin_1.2` (Linux/macOS) |
| **"Executable not found"** | Run `python build/installers/build.py` first |
| **macOS "App is damaged"** | Run: `xattr -d com.apple.quarantine /Applications/Goblin_1.2.app` |
| **Missing dependencies** | Run: `pip install -r build/REQUIREMENTS.txt` |
| **Slow first run** | Normal – offline mode downloads models (~2 GB) on first use |

---

### OSError while saving files

If you see messages like "Erreur ... : OSError" in the UI, try:

- Ensure you have write permission to the output folder (default: `transcriptions`).
- Check available disk space.
- Avoid unusual characters in filenames; Goblin sanitises names but some filesystem errors can still occur.
- Rebuild/reinstall if you changed packaging or `version.py`:
```bash
pip install -e build
```

### App opens twice

If a browser window/tab opens twice when launching the UI:

- Make sure you don't start multiple instances (check running `goblin` or Python processes).
- Start with an explicit port to avoid conflicts: `goblin --web -p 5001`.
- Use the desktop launcher (`python src/goblin_desktop.py`) which finds a free port automatically.

### Kill stray Goblin processes

If Goblin appears to be already running or the app opens twice, use the helper script to stop any stray packaged or source instances and remove the PID lock:

```bash
./scripts/kill_goblin.sh
```

This script attempts to stop processes whose command line contains `Goblin` and removes the temporary PID file used by the single-instance guard.

---


## License

See [LICENSE.txt](LICENSE.txt)
