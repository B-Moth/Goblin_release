#!/usr/bin/env python3
"""Desktop entry point for Goblin application.

This module serves as the entry point for the PyInstaller-bundled desktop application.
It launches the browser-based GUI without requiring CLI arguments.
"""

import socket
import sys
from pathlib import Path

# Add the src directory to the path so we can import goblin modules
sys.path.insert(0, str(Path(__file__).parent))

from goblin.gui import run_gui


def find_available_port(start_port: int = 5000) -> int:
    """Find an available port starting from start_port."""
    port = start_port
    while port < 65535:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('127.0.0.1', port))
                s.close()
                return port
        except OSError:
            port += 1
    raise RuntimeError("No available port found")


def main() -> None:
    """Launch the Goblin desktop application."""
    # Find an available port starting from 5000
    port = find_available_port(5000)
    # Use default parameters for the desktop application
    run_gui(output_dir="transcriptions", port=port, offline=False)


if __name__ == "__main__":
    main()
