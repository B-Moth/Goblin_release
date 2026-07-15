"""Setup shell alias for kill-goblin command.

This script adds the `kill-goblin` alias to the user's shell profile
for easy process management.

Usage:
    python build/installers/setup_shell_alias.py
"""

import os
import sys
from pathlib import Path


def get_shell_profile() -> Path:
    """Detect and return the appropriate shell profile path."""
    home = Path.home()
    
    # Check which shell is being used
    shell = os.environ.get("SHELL", "").lower()
    
    if "zsh" in shell:
        return home / ".zshrc"
    elif "bash" in shell:
        # Prefer .bash_profile on macOS, .bashrc on Linux
        if sys.platform == "darwin":
            return home / ".bash_profile"
        return home / ".bashrc"
    else:
        # Default to .zshrc (common on modern macOS)
        return home / ".zshrc"


def setup_alias() -> None:
    """Add kill-goblin alias to shell profile."""
    profile_path = get_shell_profile()
    repo_root = Path(__file__).resolve().parent.parent.parent
    
    # The alias command
    alias_line = f"alias kill-goblin='{repo_root}/scripts/kill_goblin.sh'\n"
    alias_comment = "# Goblin process management\n"
    
    # Read existing profile
    profile_content = ""
    if profile_path.exists():
        profile_content = profile_path.read_text(encoding="utf-8")
    
    # Check if alias already exists
    if "kill-goblin" in profile_content:
        print(f"✓ Alias 'kill-goblin' already exists in {profile_path}")
        return
    
    # Append alias to profile
    try:
        with open(profile_path, "a", encoding="utf-8") as f:
            f.write("\n")
            f.write(alias_comment)
            f.write(alias_line)
        print(f"✓ Added 'kill-goblin' alias to {profile_path}")
        print(f"\nTo use it immediately, run:")
        print(f"  source {profile_path}")
        print(f"\nOr restart your terminal and use:")
        print(f"  kill-goblin")
    except Exception as e:
        print(f"✗ Failed to add alias: {e}", file=sys.stderr)
        print(f"  You can add it manually to {profile_path}:", file=sys.stderr)
        print(f"  {alias_comment.strip()}", file=sys.stderr)
        print(f"  {alias_line.strip()}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    setup_alias()
