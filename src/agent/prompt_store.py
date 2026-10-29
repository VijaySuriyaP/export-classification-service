"""Versioned prompt artifact loader."""
from __future__ import annotations

from pathlib import Path

PROMPT_ROOT = Path(__file__).resolve().parents[2] / "prompts"


def load_prompt(name: str, version: str = "v1") -> str:
    """Load a named prompt only from a known version directory."""
    if version not in {"v1", "v2"} or "/" in name or ".." in name:
        raise ValueError("unknown prompt version or unsafe prompt name")
    path = PROMPT_ROOT / version / f"{name}.md"
    if not path.is_file():
        raise FileNotFoundError(f"prompt artifact not found: {version}/{name}")
    return path.read_text(encoding="utf-8")
