Built with ❤️ for *Les Feuillets* by Lucas


# 🧙 Goblin 1.2_WIP – Getting Started

Goblin transcribes audio and converts handwritten images to editable Markdown files.

## ⚡ Quick Start

### Already Have the Executable? (see dist folder if existing) 

**Windows:** Double-click `dist/Goblin_1.2_WIP_WIP_WIP_WIP_WIP_WIP_WIP.exe`  
**macOS:** Open `dist/Goblin_1.2_WIP_WIP_WIP_WIP_WIP_WIP_WIP.app`  
**Linux:** Run `chmod +x dist/Goblin_1.2_WIP_WIP_WIP_WIP_WIP_WIP_WIP && ./dist/Goblin_1.2_WIP_WIP_WIP_WIP_WIP_WIP_WIP`

### No Executable? Build from Source

**Windows:**
```powershell
py -3.12 -m pip install --upgrade pip
py -3.12 -m pip install -r build/REQUIREMENTS.txt
py -3.12 build/installers/build.py
py -3.12 build/installers/install_desktop.py
```

**macOS/Linux:**
```bash
python3.12 -m pip install --upgrade pip
python3.12 -m pip install -r build/REQUIREMENTS.txt
python3.12 build/installers/build.py
python3.12 build/installers/install_desktop.py
```

Can take up to 10-15 minutes.

---

## 🚀 Launching Goblin (from terminal)

You can run the web UI directly from source or after installing the package.

- Run the installed console script (after `pip install -e build`):
```bash
goblin --web
```
- Run from the repository without installing (requires Python to find `src`):
```bash
PYTHONPATH=src python -m goblin.main --web
# or
PYTHONPATH=src python src/goblin/main.py --web
```
- Desktop launcher (finds a free port automatically):
```bash
python src/goblin_desktop.py
```

Specify a custom port if 5000 is in use:
```bash
goblin --web -p 5001
PYTHONPATH=src python -m goblin.main --web -p 5001
```

If you changed code and want the installed `goblin` script to reflect it, rebuild the editable install:
```bash
pip install -e build
```

---

---

## 🔁 Update Version

When you want to bump the release name shown in the README, installer output, and generated filenames:

1. Update the version constant in [version.py](version.py).
2. Run `python build/sync_version.py` to refresh the README and docs.
3. Rebuild with `python build/installers/build.py` if you want fresh release artifacts.

The package shim in [src/goblin/version.py](src/goblin/version.py) keeps existing imports working.

---

## 📊 What Goblin Does

- **Audio** → **Text** : MP3, WAV, M4A, FLAC, OGG, WEBM, MP4
- **Images** → **Text** : JPG, PNG, BMP, GIF, TIFF, WEBP
- **Works Offline** or with OpenAI APIs
- **Smart Naming** (optional, with OpenAI API): AI auto-renames files by content

---

## 📚 Documentation


---

## ✅ System Requirements

- **OS:** Windows 10+, macOS 11+, Ubuntu 20.04+
- **RAM:** 4 GB minimum (8+ GB recommended)
- **Disk:** 2 GB free space for full online, up to 8 GB for offline
- **Python:** 3.11 or 3.12 (only needed if building from source)

## Features

- **🔌 Offline Mode** — Uses local faster-whisper + TrOCR/PaddleOCR
- **🌐 Online Mode** — Uses OpenAI Whisper API + GPT-4o-mini (requires API key)
- **🪄 Smart Naming** — Optionally renames saved transcriptions with GPT-3.5-turbo (requieres API key)
- **📝 Markdown Output** — Editable, searchable text files
- **📁 Batch Processing** — Queue multiple files for processing
- **✍️ Review Assistant** — Rewrites a selected transcription into a cleaned `.md` version with a local Qwen model by default, while keeping the original file untouched

The review assistant also supports a **custom format** option: write your own formatting request in the dialog, and Goblin will apply it with the same anti-hallucination rules, the same language as the transcription, and Markdown-only output.

By default Goblin uses **Qwen 7B Instruct** locally through Ollama for the review assistant. If you want a larger local model, choose **Qwen 14B Instruct** in the dialog. If you prefer the old online workflow, switch the mode to **En ligne (OpenAI)** and provide an API key.

## Reviewing a transcription

When a transcription is open in the viewer, click **Du nerf, insecte !** to open the rewrite dialog.

- The dialog defaults to the local Qwen mode; install Ollama and pull `qwen2.5:7b-instruct` to use it right away.
- Choose **Qwen 14B Instruct** if you want the larger local model.
- Switch to **En ligne (OpenAI)** if you want the API-backed workflow instead.
- Choose one of the config-driven presets: Interview, Résumé, or Documentation.
- Or choose **Personnalisé** and type your own formatting request.
- Click **Aperçu** first to generate a draft, then **Enregistrer** to save the exact markdown result as a new file.
- Goblin saves the rewritten result as a new Markdown file and keeps the original transcription as-is.

### Status & background downloads

- If a local model is missing, the editor warns before a large download and
  pulls the model in the background.
- A status indicator near the editor shows when a model is available,
  downloading, or not installed.
- Use **Aperçu** to trigger a background download; the preview resumes
  automatically once the model is ready.

### New presets

- **Conversation (expérimental)** formats multi-speaker transcripts
  conservatively with neutral labels when attribution is unclear.
- **Traduire en anglais** translates non-English input into English, while
  leaving English input unchanged apart from minor formatting cleanup.

### Release QA

- A one-shot release QA script and manual checklist are included at
  `scripts/e2e_ollama_release_check.sh` and `scripts/E2E_OLLAMA_CHECKLIST.md`.
- Run the script on a machine with Ollama, or where it can be installed, to
  validate server readiness, model presence, Flask endpoints, and the local
  rewrite smoke test.

## Uninstall

Remove the installed browser app and purge generated build/model data with:

```bash
python build/installers/uninstall.py --uninstall
```

This leaves your transcriptions untouched and empty the models cached in Hugging Face.

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| **Python not found** | Install Python 3.11 or 3.12 from python.org and use `py -3.11` or `py -3.12` |
| **Permission denied** | Run: `chmod +x Goblin_1.2_WIP_WIP_WIP_WIP_WIP_WIP_WIP` (Linux/macOS) |
| **"Executable not found"** | Run `python build/installers/build.py` first |
| **macOS "App is damaged"** | Run: `xattr -d com.apple.quarantine /Applications/Goblin_1.2_WIP_WIP_WIP_WIP_WIP_WIP_WIP.app` |
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




## License

See [LICENSE.txt](LICENSE.txt)
