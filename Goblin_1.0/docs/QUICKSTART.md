# Quick Start Guide

## 1. Launch Goblin

Double-click the executable or launcher created during installation.

---

## 2. What You'll See

The main window has:
- **Left sidebar** – List of past transcriptions
- **Drop zone** – Area to drag files or click "Select files"
- **Options panel** – Language, model, output folder
- **Preview area** – View results here

---

## 3. Transcribe Your First File

### Step 1: Add a File
- **Drag & drop** audio or image onto the drop zone, OR
- Click **"Select files"** button

### Step 2: Choose Mode
- **Offline** (default) – Free, no API key needed, ~1-5 min per file
- **Online** – Faster (~10-30 sec), more accurate, costs ~$0.01-0.05/file

To use online mode:
1. Click **🔑 API Key** button
2. Paste your OpenAI API key
3. Toggle to **"En ligne"** (Online)

### Step 3: Wait & Review
- File queues for processing
- Results appear in left sidebar when done
- Click any result to view it
- Edit directly in the preview area if needed

---

## 4. Options Explained

| Option | What It Does |
|--------|-------------|
| **Langue** | Language of audio/text (auto-detect recommended) |
| **Modèle** | Whisper model: tiny (fast), base (good), medium (best) |
| **Dossier** | Where to save `.md` files |
| **Nommage intelligent** | AI auto-renames files by content (needs API key) |

---

## 5. Manage Files

- **Archive** – Move file to archive folder (keeps it safe)
- **Delete** – Remove from list
- **Edit** – Click any result to edit text directly

---

## 6. Tips & Tricks

✅ **Batch process** – Add multiple files, they queue automatically  
✅ **First run** – Offline mode downloads models (~2 GB), only happens once  
✅ **Best quality** – Use online mode or medium Whisper model  
✅ **Smart naming** – Enable to get AI-generated filenames  
✅ **Interrupts** – File saves every 30 seconds automatically

---

## Need Help?

- **How to install?** → [INSTALL.md](INSTALL.md)
- **How do modes work?** → [guides/MODES.md](guides/MODES.md)
- **All features?** → [guides/FEATURES.md](guides/FEATURES.md)
- **Full manual?** → [guides/USER_GUIDE.md](guides/USER_GUIDE.md)
|------|---------|
| **Audio** | MP3, WAV, M4A, FLAC, OGG, WEBM, MP4 |
| **Image** | JPG, PNG, BMP, GIF, TIFF, WEBP |

## Tips & Tricks

- **Batch processing:** Add multiple files to the queue, they'll process sequentially
- **Offline first:** Offline mode is fast and free — use it for most tasks
- **Language detection:** Leave "Détection automatique" for auto-detection, or choose a language code (fr, en, es, de, it)
- **Model size:** For offline audio, choose "base" for speed or "medium" for accuracy
- **Output folder:** Change the output folder path to organize your transcriptions

## Next Steps

- Read the full **[docs/USER_GUIDE.md](docs/USER_GUIDE.md)** for advanced features
- Learn about **[docs/MODES.md](docs/MODES.md)** for detailed mode information
- Check **[docs/FEATURES.md](docs/FEATURES.md)** for all capabilities

## Troubleshooting

**No sound detected?**
- Ensure the file format is supported
- Try reducing file size or re-encoding the audio

**Handwriting recognition not accurate?**
- Use high-contrast images
- Ensure text is clearly legible
- Try online mode (GPT-4o-mini) for better results

**App crashes?**
- Update to the latest Python version
- Reinstall using `pip install -r REQUIREMENTS.txt`
- Check `/tmp/goblin-main.log` for error details (macOS/Linux)

Need more help? See [docs/USER_GUIDE.md](docs/USER_GUIDE.md).
