"""Versioned prompt loader: prompts/<agent>.<version>.md"""
from __future__ import annotations

from pathlib import Path

PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"


def load_prompt(agent: str, version: str = "v1", prompts_dir: Path | None = None) -> tuple[str, str]:
    """Return (prompt_text, prompt_id) e.g. ('...', 'scriptwriter.v1')."""
    path = (prompts_dir or PROMPTS_DIR) / f"{agent}.{version}.md"
    if not path.is_file():
        raise FileNotFoundError(f"Prompt file missing: {path}")
    return path.read_text(encoding="utf-8").strip(), f"{agent}.{version}"
