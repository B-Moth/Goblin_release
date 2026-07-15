#!/bin/bash
# Goblin rebuild script: clean, kill processes, and rebuild executable
# Usage: ./build/rebuild.sh              (preserves downloaded models)
#        ./build/rebuild.sh --full       (deletes and reinstalls everything)
# Does NOT install desktop shortcuts — run build/installers/install_desktop.py separately

set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD_DIR="$REPO_ROOT/build"
DIST_DIR="$REPO_ROOT/dist"
FULL_REBUILD="${1:-}"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ "$FULL_REBUILD" = "--full" ]; then
    echo "Goblin Clean Rebuild (FULL — all models will be re-downloaded)"
else
    echo "Goblin Clean Rebuild (standard — preserves models)"
fi
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Step 1: Kill any running Goblin processes
echo "▸ Killing any running Goblin processes..."
pkill -f "goblin --web" || true
pkill -f "goblin_desktop" || true
sleep 1
echo "  ✓ Processes terminated"
echo ""

# Step 2: Clean build artifacts
echo "▸ Cleaning build artifacts..."
rm -rf "$DIST_DIR" || true
rm -rf "$BUILD_DIR/goblin" || true
rm -rf "$BUILD_DIR/build" || true
find "$REPO_ROOT" -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
find "$REPO_ROOT" -type f -name "*.pyc" -delete 2>/dev/null || true
echo "  ✓ Artifacts cleaned"
echo ""

# Step 3: Optional full clean (delete models)
if [ "$FULL_REBUILD" = "--full" ]; then
    echo "▸ Cleaning downloaded models (full rebuild requested)..."
    # Remove Ollama models
    if command -v ollama &> /dev/null; then
        echo "  Removing Qwen models..."
        ollama rm qwen2.5:7b-instruct 2>/dev/null || true
        ollama rm qwen2.5:14b-instruct 2>/dev/null || true
    fi
    # Remove Whisper cache (stored in ~/.cache/huggingface or similar)
    echo "  Removing Whisper model cache..."
    rm -rf ~/.cache/huggingface/hub/whisper* 2>/dev/null || true
    rm -rf ~/.cache/torch/whisper* 2>/dev/null || true
    echo "  ✓ Models cleaned"
    echo ""
fi

# Step 4: Reinstall dependencies
echo "▸ Reinstalling Python dependencies..."
python -m pip install -r "$BUILD_DIR/REQUIREMENTS.txt" --quiet 2>/dev/null || {
    echo "  ✗ Failed to install requirements"
    exit 1
}
python -m pip install -e "$BUILD_DIR" --no-deps --quiet 2>/dev/null || {
    echo "  ✗ Failed to install goblin package"
    exit 1
}
echo "  ✓ Dependencies installed"
echo ""

# Step 5: Run the build
echo "▸ Building executable (this may take 1-2 minutes)..."
cd "$REPO_ROOT"
python "$BUILD_DIR/installers/build.py" || {
    echo "  ✗ Build failed"
    exit 1
}
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✓ Rebuild complete!"
if [ "$FULL_REBUILD" = "--full" ]; then
    echo "  (Full rebuild with model reinstallation)"
else
    echo "  (Models preserved for faster rebuild)"
fi
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Next steps:"
echo "  1. Test the executable:"
echo "     ./dist/Goblin --web"
echo ""
echo "  2. (Optional) Install desktop shortcuts:"
echo "     python build/installers/install_desktop.py"
echo ""
if [ "$FULL_REBUILD" != "--full" ]; then
    echo "Tip: For a complete rebuild including model reinstallation:"
    echo "  ./build/rebuild.sh --full"
fi
echo ""
