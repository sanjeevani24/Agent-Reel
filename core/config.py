"""Environment-driven configuration. Secrets are read from .env and never printed."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_BASE_URL = "https://api.groq.com/openai/v1"
DEFAULT_MODEL = "openai/gpt-oss-120b"


class ConfigError(RuntimeError):
    pass


def _opt_float(name: str, env: dict) -> float | None:
    raw = (env.get(name) or "").strip()
    if not raw:
        return None
    try:
        return float(raw)
    except ValueError as e:
        raise ConfigError(f"{name} must be a number, got {raw!r}") from e


@dataclass(frozen=True)
class Settings:
    api_key: str
    model: str = DEFAULT_MODEL
    base_url: str = DEFAULT_BASE_URL
    temperature: float = 0.2
    max_tokens: int = 4000
    timeout_s: float = 60.0
    reasoning_effort: str | None = "low"
    price_in_per_m: float | None = None   # USD per 1M input tokens, None = unknown
    price_out_per_m: float | None = None  # USD per 1M output tokens, None = unknown
    provider: str = "groq"

    def __repr__(self) -> str:  # never leak the key
        return (f"Settings(provider={self.provider!r}, model={self.model!r}, "
                f"base_url={self.base_url!r}, api_key={'<set>' if self.api_key else '<missing>'})")

    __str__ = __repr__


def load_settings(env: dict | None = None, dotenv_path: Path | None = None,
                  require_key: bool = True) -> Settings:
    """Load settings from the process environment (after reading .env if present)."""
    if env is None:
        load_dotenv(dotenv_path or ROOT / ".env", override=False)
        env = dict(os.environ)
    key = (env.get("GROQ_API_KEY") or "").strip()
    if require_key and (not key or key.startswith("your_")):
        raise ConfigError("GROQ_API_KEY is missing. Copy .env.example to .env and add your key.")
    effort = (env.get("LLM_REASONING_EFFORT") or "low").strip().lower() or None
    if effort not in (None, "low", "medium", "high"):
        raise ConfigError("LLM_REASONING_EFFORT must be low, medium or high")
    try:
        return Settings(
            api_key=key,
            model=(env.get("GROQ_MODEL") or DEFAULT_MODEL).strip(),
            base_url=(env.get("LLM_BASE_URL") or DEFAULT_BASE_URL).strip().rstrip("/"),
            temperature=float(env.get("LLM_TEMPERATURE") or 0.2),
            max_tokens=int(env.get("LLM_MAX_TOKENS") or 4000),
            timeout_s=float(env.get("LLM_TIMEOUT_S") or 60),
            reasoning_effort=effort,
            price_in_per_m=_opt_float("LLM_PRICE_IN_PER_M", env),
            price_out_per_m=_opt_float("LLM_PRICE_OUT_PER_M", env),
        )
    except ValueError as e:
        raise ConfigError(f"Invalid numeric value in environment: {e}") from e
