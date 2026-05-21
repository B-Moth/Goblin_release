# Goblin changelog v1.1 

- UI & Editor: added automated editor with local/online switch, model selection (Qwen 7B/14B), status indicators, preview-before-save, and improved conversation/translation presets.
- Installers & QA: macOS installer can install/start Ollama, pre-pulls the default edit model, cleans up downloaded models on uninstall, and includes release QA scripts.
- Runtime & Queue: fixed clean shutdown across browsers, added a heartbeat watchdog, and improved queue handling to preserve duplicate entries and resume correctly.
- Packaging & Code: refactored Ollama runtime helpers, simplified Flask routes, and kept source-run with minimal dependencies while making local editor deps optional.
- Tests: large real-world recording shows strong transcription and editing quality.