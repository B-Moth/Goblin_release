#!/usr/bin/env bash
set -euo pipefail

# One-shot release validation for Goblin + Ollama local editing flow.
#
# This script runs fast automated checks and reports what passed, failed,
# or was skipped. It does not modify production data.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

PYTHON_BIN="${PYTHON_BIN:-python}"
DEFAULT_MODEL="${DEFAULT_MODEL:-qwen2.5:7b-instruct}"
START_SERVICE="${START_SERVICE:-1}"
RUN_REWRITE_SMOKE="${RUN_REWRITE_SMOKE:-1}"

echo "[info] Goblin root: $ROOT_DIR"
echo "[info] Python: $PYTHON_BIN"
echo "[info] Default model: $DEFAULT_MODEL"

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "[fail] Missing required command: $1"
    exit 1
  fi
}

require_cmd "$PYTHON_BIN"
require_cmd ollama

if [[ "$START_SERVICE" == "1" ]] && command -v brew >/dev/null 2>&1; then
  echo "[step] Starting Ollama service (brew services start ollama)"
  brew services start ollama >/dev/null 2>&1 || true
fi

echo "[step] Waiting for Ollama server readiness"
READY=0
for _ in $(seq 1 20); do
  if ollama list >/dev/null 2>&1; then
    READY=1
    break
  fi
  sleep 1
done

if [[ "$READY" != "1" ]]; then
  echo "[fail] Ollama server is not reachable."
  echo "       Try: brew services start ollama"
  echo "       Or:  OLLAMA_FLASH_ATTENTION=\"1\" OLLAMA_KV_CACHE_TYPE=\"q8_0\" ollama serve"
  exit 1
fi

echo "[pass] Ollama server is reachable"

MODEL_PRESENT=0
if ollama list | grep -q "$DEFAULT_MODEL"; then
  MODEL_PRESENT=1
  echo "[pass] Default model already present: $DEFAULT_MODEL"
else
  echo "[warn] Default model not found: $DEFAULT_MODEL"
  echo "       Optional: ollama pull $DEFAULT_MODEL"
fi

echo "[step] Running Flask endpoint smoke checks"
"$PYTHON_BIN" - <<'PY'
import sys
sys.path.insert(0, 'src')
from goblin.gui import create_app

app = create_app(output_dir='transcriptions_e2e_check', offline=True)
client = app.test_client()

r = client.get('/')
assert r.status_code == 200, f"GET / expected 200, got {r.status_code}"
print('[pass] GET / == 200')

r = client.get('/ollama/check-model?model=qwen2.5:7b-instruct')
assert r.status_code == 200, f"check-model expected 200, got {r.status_code}"
body = r.get_json() or {}
assert 'ok' in body and 'present' in body, f"check-model payload incomplete: {body}"
print(f"[pass] /ollama/check-model payload ok: {body}")

r = client.get('/ollama/pull-status?model=qwen2.5:7b-instruct')
assert r.status_code == 200, f"pull-status expected 200, got {r.status_code}"
body = r.get_json() or {}
assert body.get('ok') is True and 'status' in body, f"pull-status payload invalid: {body}"
print(f"[pass] /ollama/pull-status payload ok: {body}")
PY

if [[ "$RUN_REWRITE_SMOKE" == "1" && "$MODEL_PRESENT" == "1" ]]; then
  echo "[step] Running local rewrite smoke test with installed model"
  "$PYTHON_BIN" - <<'PY'
import sys
from pathlib import Path
sys.path.insert(0, 'src')
from goblin.gui import create_app

out_dir = Path('transcriptions_e2e_check')
out_dir.mkdir(parents=True, exist_ok=True)
sample = out_dir / '2026-05-18_00-00_test_qwen_7b.md'
sample.write_text(
    "Bonjour, ceci est un test de transcription avec deux intervenants.\\n"
    "Intervenant A: salut.\\nIntervenant B: bonjour.",
    encoding='utf-8',
)

app = create_app(output_dir=str(out_dir), offline=True)
client = app.test_client()

resp = client.post(
    f"/transcriptions/{sample.name}/rewrite",
    json={
        'preset': 'conversation',
        'provider': 'local',
        'local_model': 'qwen2.5:7b-instruct',
        'action': 'preview',
    },
)
assert resp.status_code == 200, f"rewrite preview failed: {resp.status_code} {resp.get_data(as_text=True)}"
body = resp.get_json() or {}
assert body.get('ok') is True, f"rewrite preview not ok: {body}"
preview = (body.get('preview') or '').strip()
assert preview, f"rewrite preview empty: {body}"
print('[pass] Local rewrite preview returned non-empty output')
PY
else
  if [[ "$RUN_REWRITE_SMOKE" == "1" ]]; then
    echo "[skip] Rewrite smoke skipped because model is not installed."
  else
    echo "[skip] Rewrite smoke skipped by RUN_REWRITE_SMOKE=0"
  fi
fi

echo ""
echo "[done] Automated Ollama E2E checks completed."
echo "       For full release sign-off, run the manual checklist in:"
echo "       scripts/E2E_OLLAMA_CHECKLIST.md"
