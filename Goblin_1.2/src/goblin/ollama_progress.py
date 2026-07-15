"""Parse and track Ollama model download progress.

This module extracts download progress information from Ollama's verbose output
to provide real-time updates to the frontend (percentage, speed, ETA, etc).
"""

import re
from typing import Optional


class OllamaProgressTracker:
    """Track download progress from Ollama pull output."""

    def __init__(self):
        self.current_file = ""
        self.total_size = 0
        self.downloaded = 0
        self.percentage = 0
        self.speed = ""
        self.status = "starting"

    def parse_line(self, line: str) -> None:
        """Parse a single line of Ollama output and update progress."""
        if not line or not line.strip():
            return

        # Example output from "ollama pull qwen2.5:14b":
        # downloading abc123de... 45%  4.2 GB / 14.8 GB  2.1 MB/s
        # pulling abc123de... 100% 1.2 kB / 1.2 kB
        # verifying digest
        # writing manifest
        # success

        line = line.strip()

        # Check for status keywords
        if line.startswith("downloading"):
            self.status = "downloading"
            self._parse_progress_line(line)
        elif line.startswith("pulling"):
            self.status = "downloading"
            self._parse_progress_line(line)
        elif line.startswith("verifying"):
            self.status = "verifying"
        elif line.startswith("writing"):
            self.status = "writing"
        elif line.lower() in ("success", "done"):
            self.status = "success"
            self.percentage = 100
        elif line.startswith("error") or line.startswith("failed"):
            self.status = "error"

    def _parse_progress_line(self, line: str) -> None:
        """Parse a progress line like: 'downloading abc123de... 45%  4.2 GB / 14.8 GB  2.1 MB/s'"""
        # Extract percentage
        pct_match = re.search(r"(\d+)%", line)
        if pct_match:
            self.percentage = int(pct_match.group(1))

        # Extract current/total size (e.g., "4.2 GB / 14.8 GB")
        size_match = re.search(r"([\d.]+\s*(?:B|KB|MB|GB))\s*/\s*([\d.]+\s*(?:B|KB|MB|GB))", line)
        if size_match:
            self.downloaded = self._parse_size(size_match.group(1))
            self.total_size = self._parse_size(size_match.group(2))

        # Extract speed (e.g., "2.1 MB/s")
        speed_match = re.search(r"([\d.]+\s*(?:B|KB|MB|GB)/s)", line)
        if speed_match:
            self.speed = speed_match.group(1)

        # Extract file hash/name
        file_match = re.search(r"(?:downloading|pulling)\s+(\w+)", line)
        if file_match:
            self.current_file = file_match.group(1)[:12]  # Keep first 12 chars

    @staticmethod
    def _parse_size(size_str: str) -> int:
        """Convert size string like '4.2 GB' to bytes."""
        size_str = size_str.strip().upper()
        multipliers = {
            "B": 1,
            "KB": 1024,
            "MB": 1024**2,
            "GB": 1024**3,
        }

        for unit, multiplier in multipliers.items():
            if unit in size_str:
                num = float(size_str.replace(unit, "").strip())
                return int(num * multiplier)

        return 0

    def to_dict(self) -> dict:
        """Return current progress as a dictionary for JSON response."""
        return {
            "percentage": self.percentage,
            "status": self.status,
            "downloaded": self._format_bytes(self.downloaded),
            "total": self._format_bytes(self.total_size),
            "speed": self.speed,
            "current_file": self.current_file,
        }

    @staticmethod
    def _format_bytes(num_bytes: int) -> str:
        """Format bytes as human-readable string."""
        for unit in ("B", "KB", "MB", "GB"):
            if num_bytes < 1024:
                return f"{num_bytes:.1f} {unit}" if unit != "B" else f"{num_bytes} B"
            num_bytes /= 1024
        return f"{num_bytes:.1f} GB"
