"""Provider adapter: OpenAI-compatible chat completions (Groq by default).

Agents call `LLMClient.chat_json(...)` and get a validated pydantic object back.
Swapping provider = changing .env (base URL / model), not agent code.
"""
from __future__ import annotations

import json
import re
import time
from typing import Type, TypeVar

from pydantic import BaseModel, ValidationError

from core.config import Settings
from core.runlog import RunLogger

T = TypeVar("T", bound=BaseModel)


class LLMError(RuntimeError):
    pass


def _extract_json(text: str) -> dict:
    text = (text or "").strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.S).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        if start != -1 and end > start:
            return json.loads(text[start:end + 1])
        raise


class LLMClient:
    def __init__(self, settings: Settings, logger: RunLogger | None = None, sdk_client=None):
        self.s = settings
        self.log = logger
        self.calls = 0              # running totals, used by the orchestrator's budget guard
        self.prompt_tokens = 0
        self.completion_tokens = 0
        if sdk_client is not None:  # injected (tests)
            self.sdk = sdk_client
        else:
            from openai import OpenAI
            self.sdk = OpenAI(api_key=settings.api_key, base_url=settings.base_url,
                              timeout=settings.timeout_s, max_retries=0)

    # -- cost -------------------------------------------------------------
    def _cost(self, pt, ct):
        if None in (pt, ct, self.s.price_in_per_m, self.s.price_out_per_m):
            return None
        return pt / 1e6 * self.s.price_in_per_m + ct / 1e6 * self.s.price_out_per_m

    # -- one raw call -----------------------------------------------------
    def _call(self, messages, schema_model: Type[BaseModel], seed: int | None, use_schema: bool):
        kw = dict(model=self.s.model, messages=messages, temperature=self.s.temperature,
                  max_tokens=self.s.max_tokens)
        if seed is not None:
            kw["seed"] = seed
        if self.s.reasoning_effort:
            kw["reasoning_effort"] = self.s.reasoning_effort
        if use_schema:
            kw["response_format"] = {"type": "json_schema", "json_schema": {
                "name": schema_model.__name__, "schema": schema_model.model_json_schema()}}
        else:
            kw["response_format"] = {"type": "json_object"}
        return self.sdk.chat.completions.create(**kw)

    # -- public -----------------------------------------------------------
    def chat_json(self, agent: str, system: str, user: str, schema_model: Type[T],
                  seed: int | None = None, max_repairs: int = 1) -> T:
        """Return a validated `schema_model`. Retries once on malformed/invalid JSON."""
        sys_msg = (system.rstrip() + "\n\nRespond with a single JSON object only (JSON, no prose, "
                   "no markdown fences) matching this schema:\n"
                   + json.dumps(schema_model.model_json_schema()))
        messages = [{"role": "system", "content": sys_msg}, {"role": "user", "content": user}]
        use_schema, last_err = True, None
        for attempt in range(max_repairs + 1):
            t0 = time.perf_counter()
            try:
                resp = self._call(messages, schema_model, seed, use_schema)
            except Exception as e:  # provider rejected response_format -> fall back once
                msg = str(e).lower()
                if use_schema and ("response_format" in msg or "json_schema" in msg or "schema" in msg):
                    use_schema = False
                    self._event(agent, "schema_mode_unsupported_fallback", error=str(e)[:300])
                    continue
                self._event(agent, "error", error=str(e)[:500], attempt=attempt)
                raise LLMError(f"{agent}: LLM call failed: {e}") from e
            latency = round(time.perf_counter() - t0, 3)
            usage = getattr(resp, "usage", None)
            pt = getattr(usage, "prompt_tokens", None)
            ct = getattr(usage, "completion_tokens", None)
            cost = self._cost(pt, ct)
            self.calls += 1
            self.prompt_tokens += pt or 0
            self.completion_tokens += ct or 0
            if self.log:
                self.log.cost(agent, self.s.provider, self.s.model, pt, ct, cost)
            content = resp.choices[0].message.content or ""
            try:
                obj = schema_model.model_validate(_extract_json(content))
                self._event(agent, "ok", latency_s=latency, prompt_tokens=pt,
                            completion_tokens=ct, attempt=attempt, model=self.s.model)
                return obj
            except (json.JSONDecodeError, ValidationError) as e:
                last_err = e
                self._event(agent, "invalid_output", latency_s=latency, attempt=attempt,
                            error=str(e)[:500], model=self.s.model)
                messages = messages + [
                    {"role": "assistant", "content": content[:4000]},
                    {"role": "user", "content": "That output was invalid: "
                     f"{str(e)[:800]}\nReturn corrected JSON only."}]
        raise LLMError(f"{agent}: output failed validation after {max_repairs + 1} attempts: {last_err}")

    def _event(self, agent, status, **f):
        if self.log:
            self.log.event(agent, status, **f)
