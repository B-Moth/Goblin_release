# Goblin changelog

## 2026-05-17 — Cleanup + local editing overhaul

### UI / editor
- Fixed the web UI startup crash that made buttons appear unresponsive.
- Added transcription editor controls to switch between online (OpenAI) and local (Ollama/Qwen) modes.
- Added local model selection for Qwen 7B / 14B and visible status indicators for model availability and download progress.
- Added on-demand background model pulls with user warning before large downloads.
- Kept the transcription review flow with preview-before-save and safe filename generation.

### Installer / uninstall
- Updated the macOS installer to install Ollama when possible.
- Pre-pulls only the default local model during setup to keep installation lighter.
- Updated uninstall cleanup to remove downloaded Ollama models and cached model data.

### Code quality / structure
- Extracted shared Ollama runtime helpers into `src/goblin/ollama_runtime.py` to reduce duplication.
- Cleaned up the rewrite and model-check routes so the Flask app is easier to read and maintain.
- Added optional local dependency support for Ollama in the build metadata.

### Packaging / dependency handling
- Kept the project runnable from source with the minimum web dependencies installed lazily.
- Preserved the existing offline transcription stack while making local editor dependencies optional where possible.

## 2026-05-18 — Code clarity and documentation

### Internal
- Added explanatory comments and docstrings across the Ollama runtime,
	installer helpers and the web UI code to make background-pull behavior,
	job state, and local vs remote provider logic clearer for future
	contributors.
- Documented concurrency considerations for `app.ollama_jobs` and the
	reasoning behind a conservative single-worker `ThreadPoolExecutor`.

### Developer experience
- Improved `CHANGELOG.md` with the above notes and ensured the new
	static client-side module is tracked in version control.

## 2026-05-18 — Editor prompt improvements

### UI / editor
- Improved the `Conversation` preset prompt to better handle uncertain
	multi-speaker transcriptions without hallucinating speaker identity.
- Marked `Conversation` as experimental in the editor option label.
- Added a new `Traduire en anglais` preset with explicit behavior:
	translate to English only when source is not English, otherwise keep
	the text unchanged (except minimal formatting cleanup).

### Prompting behavior
- Updated system/user language instructions so default presets preserve
	the source language, while translation presets can explicitly opt into
	English output.

## Goblin v1.1 changelog :

## Fixes :
- uninstall.py now correctly import sys
- no more stray goblins : only one instance is authorized now

## Distribution :
- cleaned up and re-writted doc

## Dev :
- simplified version change procedure
- drag and drop one file at a time now put them in a queue
- kill script in case of rebelous goblins
- added Du nerf Insecte ! to force goblins to work on editing the transcription to make them more usefull

## Tests :
- big real condition record (~50min, noisy) : excellent precision on medium Whisper