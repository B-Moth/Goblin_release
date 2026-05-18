#!/usr/bin/env bash
# Kill all Goblin processes (packaged or source) and remove PID file
set -euo pipefail

TEMP_PID="$(python - <<'PY'
import tempfile, getpass, pathlib
print(pathlib.Path(tempfile.gettempdir()) / f"goblin_{getpass.getuser()}.pid")
PY)"

echo "Killing Goblin processes..."
pkill -f Goblin || true
pkill -f Goblin_1.1 || true

if [ -f "$TEMP_PID" ]; then
  echo "Removing PID file $TEMP_PID"
  rm -f "$TEMP_PID" || true
fi

echo "Done."
