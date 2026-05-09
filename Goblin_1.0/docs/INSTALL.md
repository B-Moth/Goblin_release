# Installation Guide

## Quick Install

## Option A: Pre-Built Browser App (Easiest) ⭐

### Windows

1. Open `dist/` folder
2. Double-click **`Goblin.exe`**
3. (Optional) Run to create desktop shortcuts:
   ```cmd
   python build/installers/install_desktop.py
   ```

### macOS

1. Open `dist/` folder
2. Drag **`Goblin.app`** to your Applications folder
3. Double-click `Goblin.app` to launch
4. (Optional) Run to create launcher scripts:
   ```bash
   python build/installers/install_desktop.py
   ```

### Linux

1. Open `dist/` folder
2. Make executable: `chmod +x Goblin`
3. Run: `./Goblin`
4. (Optional) Install desktop entry:
   ```bash
   python build/installers/install_desktop.py
   ```

---

## Option B: Build from Source

You'll need **Python 3.11 or 3.12** installed. Python 3.13+ is not supported for the Windows build because `paddlepaddle` does not provide wheels for those versions.

### All Platforms (Windows, macOS, Linux)

1. **Install dependencies:**
   ```bash
   py -3.11 -m pip install --upgrade pip
   py -3.11 -m pip install -r build/REQUIREMENTS.txt
   ```

2. **Build the browser app** (takes 10-15 minutes):
   ```bash
   py -3.11 build/installers/build.py
   ```
   
   This creates:
   - Windows: `dist/Goblin.exe`
   - macOS: `dist/Goblin.app`
   - Linux: `dist/Goblin`

3. **Create desktop shortcuts** (optional but recommended):
   ```bash
   py -3.11 build/installers/install_desktop.py
   ```
   
   This creates:
   - Windows: Desktop shortcut
   - macOS: Launcher scripts in ~/Applications
   - Linux: Application menu entry

### Uninstall

To remove the installed launchers, build output, and downloaded model cache:

```bash
python build/installers/uninstall.py --uninstall
```

This keeps your transcriptions and source files on disk.

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| **Python not found** | Install Python 3.11 or 3.12 from python.org and use `py -3.11` or `py -3.12` |
| **Permission denied** | Run: `chmod +x Goblin` (Linux/macOS) |
| **"Executable not found"** | Run `python build/installers/build.py` first |
| **macOS "App is damaged"** | Run: `xattr -d com.apple.quarantine /Applications/Goblin.app` |
| **Missing dependencies** | Run: `pip install -r build/REQUIREMENTS.txt` |
| **Slow first run** | Normal – offline mode downloads models (~2 GB) on first use |

---

## System Requirements

- **OS:** Windows 10+, macOS 11+, Ubuntu 20.04+
- **RAM:** 4 GB minimum (8 GB recommended)
- **Disk:** 2 GB free (5 GB if using offline mode)
- **Python:** 3.11 or 3.12 (only needed for Option B: Build from Source)

## Next Steps

After installation, open [QUICKSTART.md](QUICKSTART.md) to learn how to use Goblin.
