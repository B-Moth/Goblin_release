# Goblin Ollama E2E Release Checklist

Use this checklist after running `scripts/e2e_ollama_release_check.sh`.

## 1) Installer + service startup
- [ ] Run installer on a clean or realistic machine.
- [ ] Confirm Ollama is detected or installed.
- [ ] Confirm Ollama server starts automatically (or clear guidance is shown).
- [ ] Confirm default pre-pull attempts `qwen2.5:7b-instruct`.

Pass criteria:
- Installer never crashes when Ollama is unavailable.
- User gets actionable instructions when server cannot start.

## 2) First local preview (model missing)
- [ ] Open Goblin and load a transcription.
- [ ] Select local provider and default model.
- [ ] Click preview.
- [ ] Confirm download warning is shown before pull starts.
- [ ] Confirm status moves through downloading to available.
- [ ] Confirm preview resumes only after download completes.

Pass criteria:
- No UI freeze.
- No recursive retry loop.
- No silent failure.

## 3) Local rewrite with model already present
- [ ] Run preview again with model already installed.
- [ ] Confirm no pull prompt is shown.
- [ ] Save rewritten file.
- [ ] Confirm filename generation is correct and collision handling works.

Pass criteria:
- Preview/save complete without unexpected delay.
- Saved file is valid and readable.

## 4) Language behavior checks
- [ ] Use a French transcription.
- [ ] Run `Résumé`, `Documentation`, `Conversation (expérimental)`.
- [ ] Confirm outputs stay in French.
- [ ] Run `Traduire en anglais` on French input.
- [ ] Confirm output is English.
- [ ] Run `Traduire en anglais` on English input.
- [ ] Confirm content is not rewritten beyond minimal formatting cleanup.

Pass criteria:
- Language behavior matches preset rules.

## 5) Multi-speaker ambiguity check
- [ ] Use an ambiguous multi-speaker transcription.
- [ ] Run `Conversation (expérimental)`.
- [ ] Confirm the model uses neutral labels (for example `Intervenant 1`, `Intervenant 2`).
- [ ] Confirm no guessed identities or invented speaker details.

Pass criteria:
- Output is conservative and does not hallucinate speaker attribution.

## 6) Runtime failure + recovery
- [ ] Stop Ollama service while Goblin is running.
- [ ] Attempt local preview and confirm clear error message.
- [ ] Start Ollama service again.
- [ ] Retry preview and confirm recovery without app restart.

Pass criteria:
- Graceful failure.
- Successful recovery path.

## 7) Restart persistence
- [ ] Restart Goblin.
- [ ] Confirm model status reflects real machine state.

Pass criteria:
- No stale status from prior app session.

## Suggested commands

```bash
brew services start ollama
ollama list
ollama ps
bash scripts/e2e_ollama_release_check.sh
```
