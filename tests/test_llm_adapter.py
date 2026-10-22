import csv
import json
from types import SimpleNamespace as NS

import pytest
from pydantic import BaseModel

from core.config import load_settings
from core.llm import LLMClient, LLMError
from core.runlog import RunLogger


class Out(BaseModel):
    a: int


class FakeSDK:
    """Mimics openai client: chat.completions.create(**kw) returning queued replies."""
    def __init__(self, replies, usage=(10, 5)):
        self.replies, self.calls, self.usage = list(replies), [], usage
        self.chat = NS(completions=NS(create=self._create))

    def _create(self, **kw):
        self.calls.append(kw)
        r = self.replies.pop(0)
        if isinstance(r, Exception):
            raise r
        u = NS(prompt_tokens=self.usage[0], completion_tokens=self.usage[1]) if self.usage else None
        return NS(choices=[NS(message=NS(content=r))], usage=u)


def _client(tmp_path, replies, env=None, usage=(10, 5)):
    s = load_settings(env={"GROQ_API_KEY": "gsk_topsecret", **(env or {})})
    log = RunLogger(tmp_path, run_id="t", secrets=[s.api_key])
    return LLMClient(s, log, FakeSDK(replies, usage)), log


def test_valid_json_and_unknown_cost(tmp_path):
    c, log = _client(tmp_path, ['{"a": 1}'])
    assert c.chat_json("x", "sys", "usr", Out, seed=42).a == 1
    rows = list(csv.DictReader(open(log.cost_csv)))
    assert rows[0]["cost_usd"] == "unknown" and rows[0]["prompt_tokens"] == "10"
    assert c.sdk.calls[0]["seed"] == 42


def test_cost_computed_only_with_prices(tmp_path):
    c, log = _client(tmp_path, ['{"a": 1}'], env={"LLM_PRICE_IN_PER_M": "1", "LLM_PRICE_OUT_PER_M": "2"},
                     usage=(1_000_000, 1_000_000))
    c.chat_json("x", "s", "u", Out)
    assert list(csv.DictReader(open(log.cost_csv)))[0]["cost_usd"] == "3.000000"


def test_missing_usage_is_unknown(tmp_path):
    c, log = _client(tmp_path, ['{"a": 1}'], usage=None)
    c.chat_json("x", "s", "u", Out)
    assert list(csv.DictReader(open(log.cost_csv)))[0]["prompt_tokens"] == "unknown"


def test_fenced_json_and_one_repair(tmp_path):
    c, log = _client(tmp_path, ["not json", '```json\n{"a": 7}\n```'])
    assert c.chat_json("x", "s", "u", Out).a == 7
    assert len(c.sdk.calls) == 2


def test_repair_limit_enforced(tmp_path):
    c, _ = _client(tmp_path, ["bad", "still bad", '{"a": 1}'])
    with pytest.raises(LLMError):
        c.chat_json("x", "s", "u", Out, max_repairs=1)
    assert len(c.sdk.calls) == 2  # never a third call


def test_schema_mode_fallback(tmp_path):
    c, _ = _client(tmp_path, [Exception("400 response_format json_schema unsupported"), '{"a": 2}'])
    assert c.chat_json("x", "s", "u", Out).a == 2
    assert c.sdk.calls[-1]["response_format"] == {"type": "json_object"}


def test_secret_never_logged(tmp_path):
    c, log = _client(tmp_path, [Exception("auth failed for gsk_topsecret")])
    with pytest.raises(LLMError):
        c.chat_json("x", "s", "u", Out)
    assert "gsk_topsecret" not in log.jsonl.read_text()
    assert "***" in log.jsonl.read_text()
    json.loads(log.jsonl.read_text().splitlines()[0])  # valid JSONL
