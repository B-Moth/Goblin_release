#!/usr/bin/env bash
# Kill all Goblin processes (packaged or source) and remove PID file
set -euo pipefail

TEMP_PID="$(python - <<'PY'
import tempfile, getpass, pathlib
print(pathlib.Path(tempfile.gettempdir()) / f"goblin_{getpass.getuser()}.pid")
PY)"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Goblin Process Manager"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Count processes before killing
echo "▸ Scanning for Goblin processes..."
goblin_main=$(pgrep -f "goblin --web" 2>/dev/null | wc -l | tr -d ' \n' || echo 0)
goblin_packed=$(pgrep -f "Goblin" 2>/dev/null | wc -l | tr -d ' \n' || echo 0)
goblin_main=${goblin_main:-0}
goblin_packed=${goblin_packed:-0}
total_processes=$((goblin_main + goblin_packed))

echo "  Found: $goblin_main main process(es)"
echo "  Found: $goblin_packed packaged process(es)"
echo "  Total: $total_processes process(es)"
echo ""

# Kill all matching processes
if [ "$total_processes" -gt 0 ]; then
    echo "▸ Terminating processes..."
    pkill -f "goblin --web" || true
    pkill -f "goblin_desktop" || true
    pkill -f "Goblin" || true
    pkill -f "Goblin_1" || true
    sleep 1
fi

# Verify everything is killed
echo "▸ Verifying termination..."
remaining=$(pgrep -f "goblin|Goblin" 2>/dev/null | wc -l | tr -d ' \n' || echo 0)
remaining=${remaining:-0}
terminated=$((total_processes - remaining))

if [ "$remaining" -eq 0 ]; then
    echo "  ✓ Successfully terminated $total_processes process(es)"
else
    echo "  ⚠ $remaining process(es) still running, attempting force kill..."
    pkill -9 -f "goblin\|Goblin" || true
    sleep 1
    remaining=$(pgrep -f "goblin|Goblin" 2>/dev/null | wc -l | tr -d ' \n' || echo 0)
    remaining=${remaining:-0}
    if [ "$remaining" -eq 0 ]; then
        echo "  ✓ Force kill successful (all $total_processes process(es) terminated)"
    else
        echo "  ✗ Failed to terminate $remaining process(es)"
    fi
fi
echo ""

# Clean up PID file
echo "▸ Cleaning PID file..."
if [ -f "$TEMP_PID" ]; then
    rm -f "$TEMP_PID" || true
    echo "  ✓ Removed: $TEMP_PID"
else
    echo "  ℹ PID file already clean"
fi
echo ""

# Double-check for port 5000 (Flask server)
echo "▸ Checking for orphaned server connections..."
if command -v lsof &> /dev/null; then
    port_5000=$(lsof -i :5000 2>/dev/null | grep -v COMMAND | wc -l | tr -d ' \n' || echo 0)
    port_5000=${port_5000:-0}
    if [ "$port_5000" -gt 0 ]; then
        echo "  ⚠ Port 5000 still in use, cleaning up..."
        lsof -ti :5000 | xargs kill -9 2>/dev/null || true
        sleep 1
        echo "  ✓ Port 5000 released"
    else
        echo "  ✓ Port 5000 is free"
    fi
else
    echo "  ℹ lsof not available, skipping port check"
fi
echo ""

# Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ "$remaining" -eq 0 ]; then
    echo "✓ Cleanup complete. All systems clean."
    echo ""
    echo "Summary:"
    echo "  • Processes terminated: $total_processes"
    echo "  • Successful terminations: $terminated"
    echo "  • PID files cleaned"
    echo ""
    echo "Goblin is now fully shut down and ready to restart."
else
    echo "✗ Cleanup incomplete. Please check manually:"
    echo ""
    pgrep -f "goblin|Goblin" -a || echo "  No Goblin processes found"
fi
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
