"""Compatibility wrapper for the Goblin version constants.

This module prefers importing the top-level ``version`` module (used
when running from the repository root). During isolated build
environments (pip/setuptools), that import may fail; in that case we
fall back to reading the repository root ``version.py`` file directly
so dynamic version resolution still works.
"""

from pathlib import Path
import sys

try:
	# Normal case when the repo root is on sys.path
	from version import APP_BASENAME, VERSION  # type: ignore
except Exception:
	# Fallback: locate a top-level version.py relative to this file
	repo_root = Path(__file__).resolve().parents[2]
	candidate = repo_root / "version.py"
	APP_BASENAME = "Goblin_0.0.0"
	VERSION = "0.0.0"
	if candidate.exists():
		try:
			ns: dict = {}
			code = candidate.read_text(encoding="utf-8")
			exec(compile(code, str(candidate), "exec"), ns)
			VERSION = ns.get("VERSION", VERSION)
			APP_BASENAME = ns.get("APP_BASENAME", f"Goblin_{VERSION}")
		except Exception:
			# Best-effort fallback; keep defaults.
			pass