Built with ❤️ for *Les Feuillets* by Lucas


# 🧙 Goblin 1.1 – Getting Started

Goblin transcribes audio and converts handwritten images to editable Markdown files.

## ⚡ Quick Start

### Already Have the Executable? (see dist folder if existing) 

**Windows:** Double-click `dist/Goblin_1.1.exe`  
**macOS:** Open `dist/Goblin_1.1.app`  
**Linux:** Run `chmod +x dist/Goblin_1.1 && ./dist/Goblin_1.1`

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
| **Permission denied** | Run: `chmod +x Goblin_1.1` (Linux/macOS) |
| **"Executable not found"** | Run `python build/installers/build.py` first |
| **macOS "App is damaged"** | Run: `xattr -d com.apple.quarantine /Applications/Goblin_1.1.app` |
| **Missing dependencies** | Run: `pip install -r build/REQUIREMENTS.txt` |
| **Slow first run** | Normal – offline mode downloads models (~2 GB) on first use |

---


## License

See [LICENSE.txt](LICENSE.txt)
