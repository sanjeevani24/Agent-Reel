#!/usr/bin/env python3
"""Live smoke test of your Groq key + model. Run from the repo root:  python scripts/check_llm.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pydantic import BaseModel

from core.config import ConfigError, load_settings
from core.llm import LLMClient, LLMError
from core.runlog import RunLogger


class Ping(BaseModel):
    ok: bool
    message: str


def main() -> int:
    try:
        s = load_settings()
    except ConfigError as e:
        print(f"CONFIG ERROR: {e}")
        return 2
    print(f"Testing {s}")
    client = LLMClient(s, RunLogger("logs", secrets=[s.api_key]))
    try:
        out = client.chat_json("smoke_test", "You are a test endpoint.",
                               'Return {"ok": true, "message": "hello"}.', Ping, seed=42)
    except LLMError as e:
        print(f"LLM CHECK FAILED: {e}")
        return 1
    print("LLM CHECK PASSED:", out.model_dump())
    print("Usage logged to logs/cost_report.csv")
    return 0


if __name__ == "__main__":
    sys.exit(main())
