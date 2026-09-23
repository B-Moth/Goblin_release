
# Goblin

Goblin is a desktop transcription assistant for turning audio recordings and handwritten notes into editable Markdown. It can run with cloud APIs or local models, so the user can choose between convenience, privacy, and hardware requirements.

The interface is currently French-only.

## What it does

- Transcribes supported audio formats such as MP3, WAV, M4A, FLAC, OGG, and WEBM.
- Extracts text from supported image formats such as JPG, PNG, TIFF, and WEBP.
- Processes files individually or in batches through a browser-based desktop interface.
- Saves searchable Markdown files with source metadata and creation dates.
- Keeps the original transcription untouched when the review assistant rewrites it.
- Offers local processing with Faster Whisper, OCR models, and Ollama/Qwen.
- Offers OpenAI Whisper and vision workflows when an API key is configured.
- Provides a CLI, a local Flask UI, and PyInstaller packaging for desktop use.

## Why it exists

Audio notes and photographed handwritten documents are useful before they are organized. Goblin shortens the path from capture to usable text while preserving the original file and transcription metadata. Local mode is intended for sensitive material; online mode is useful when local model installation or hardware is not practical.

## Architecture

```text
CLI / desktop launcher
		  |
		  v
	  Flask UI  --------------------  Markdown output
		  |
		  +-- audio.py  ------------  OpenAI Whisper
		  +-- image.py  ------------  OpenAI vision
		  +-- offline.py -----------  Faster Whisper / OCR
		  +-- transcription_editor -  Ollama/Qwen or OpenAI
		  +-- formatter.py ---------  Metadata and file output
		  +-- credentials.py -------  Local API-key storage
```

The application binds its local web server to `127.0.0.1` by default. The control endpoints are designed for the local desktop workflow and should not be exposed to a network without an authentication layer.

## Run from source

Goblin currently supports Python 3.11 and 3.12. From the repository root:

```bash
cd Goblin_1.2
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r build/REQUIREMENTS.txt
python -m pip install -e build
goblin --web
```

The first offline run may download model files. Online processing requires an OpenAI API key. The CLI can store one in the user's local Goblin configuration:

```bash
goblin --set-api-key
goblin --show-api-key
```

## Build the desktop application

The release package contains a PyInstaller build script for macOS, Windows, and Linux:

```bash
cd Goblin_1.2
python3.12 build/installers/build.py
```

The build checks the Python version, installs runtime dependencies, synchronizes versioned documentation, builds the executable, and prepares the optional Ollama and Whisper models. Generated PyInstaller intermediates are intentionally not tracked in Git.

## Test and validation

The repository includes deterministic tests for filename generation, Markdown output, API-key validation, and local credential storage:

```bash
pytest -q
python -m compileall -q Goblin_1.2/src
```

GitHub Actions runs these checks on Python 3.11 and 3.12. Full ML inference and packaged executable checks remain environment-dependent because they require large models and platform-specific dependencies.

## Project status

Goblin is a functional personal application and an active portfolio project. The core workflow is implemented, but the packaged release is still evolving. The main remaining release work is cross-platform bundle verification, broader integration coverage for model-backed flows, and a signed distribution process.

## License

See [Goblin_1.2/LICENSE.txt](Goblin_1.2/LICENSE.txt).

