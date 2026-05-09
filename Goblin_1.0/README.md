# 🧙 Goblin – Getting Started

Goblin transcribes audio and converts handwritten images to editable Markdown files.

---

## ⚡ Quick Start (2 Minutes)

### Already Have the Executable?

**Windows:** Double-click `dist/Goblin.exe`  
**macOS:** Open `dist/Goblin.app`  
**Linux:** Run `chmod +x dist/Goblin && ./dist/Goblin`

Done! The app launches. 🎉

### No Executable? Build from Source

```powershell
py -3.11 -m pip install --upgrade pip
py -3.11 -m pip install -r build/REQUIREMENTS.txt
py -3.11 build/installers/build.py
py -3.11 build/installers/install_desktop.py
```

Takes 10-15 minutes. See [INSTALL.md](INSTALL.md) for details.

---

## 📊 What Goblin Does

- **Audio** → Text: MP3, WAV, M4A, FLAC, OGG, WEBM, MP4
- **Images** → Text: JPG, PNG, BMP, GIF, TIFF, WEBP
- **Works Offline** or with OpenAI APIs (your choice)
- **Smart Naming** (optional): AI auto-renames files by content

---

## 📚 Documentation


---

## ✅ System Requirements

- **OS:** Windows 10+, macOS 11+, Ubuntu 20.04+
- **RAM:** 4 GB (8 GB recommended)
- **Disk:** 2 GB free
- **Python:** 3.11 or 3.12 (only if building from source)
- **🔌 Offline Mode** (default) — Uses local faster-whisper + TrOCR/PaddleOCR
- **🌐 Online Mode** — Uses OpenAI Whisper API + GPT-4o-mini (requires API key)
- **🪄 Smart Naming** — Optionally renames saved transcriptions with GPT-3.5-turbo based on the transcript content
- **📝 Markdown Output** — Editable, searchable text files
- **📁 Batch Processing** — Queue multiple files for processing

## System Requirements

- **Windows:** Windows 10 or later
- **macOS:** macOS 11 or later
- **Linux:** Ubuntu 20.04+ or equivalent
- **RAM:** 4 GB minimum (8 GB recommended for offline mode)
- **Disk:** 2 GB available (+ model cache if using offline)

## Getting Started

1. **Install:** See [INSTALL.md](INSTALL.md)
2. **Learn:** See [QUICKSTART.md](QUICKSTART.md)
3. **Explore:** See [docs/USER_GUIDE.md](docs/USER_GUIDE.md)

## Support & Documentation

- **User Guide:** [docs/USER_GUIDE.md](docs/USER_GUIDE.md)
- **Features:** [docs/FEATURES.md](docs/FEATURES.md)
- **Modes:** [docs/MODES.md](docs/MODES.md)
- **Issues:** Report bugs or request features via GitHub

## Uninstall

Remove the installed browser app and purge generated build/model data with:

```bash
python build/installers/uninstall.py --uninstall
```

This leaves your transcriptions untouched.

## License

See [LICENSE.txt](LICENSE.txt)

## Credits

Built with ❤️ for *Les Feuillets*
