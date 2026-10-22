"""Shared test doubles: a scripted FakeLLM (no network) and builders of valid agent outputs."""
from __future__ import annotations

from types import SimpleNamespace as NS

WORDS = ["build", "learn", "test", "agents", "think", "plan", "create", "improve", "explore", "share"]


def narration(n: int, tag: str = "") -> str:
    """n letter-only words (no digits, so nothing looks like an invented statistic)."""
    ws = [WORDS[i % len(WORDS)] for i in range(n)]
    if tag:
        ws[0] = tag
    return " ".join(ws)


def planner_out() -> dict:
    return {"success_criteria": ["Fits 35-45 seconds", "Only supported claims", "Clear call to action"],
            "creative_direction": "Bright, fast-paced, abstract visuals with gentle motion.",
            "risk_notes": ["No official source documents supplied"]}


def research_out(facts=None) -> dict:
    return {"facts": facts or [], "missing_info": []}


def script_out(n_segments=6, words_each=16, seg_len=7.0, bad_number=False, ungrounded=False,
               fact_ids=("B1",)) -> dict:
    segs = []
    for i in range(n_segments):
        role = "hook" if i == 0 else ("cta" if i == n_segments - 1 else "body")
        text = narration(words_each, "Imagine" if i == 0 else "")
        if bad_number and i == 2:
            text += " with 500 happy students"
        grounded = i in (1, 2)
        segs.append({"role": role, "start_s": round(i * seg_len, 2), "end_s": round((i + 1) * seg_len, 2),
                     "narration": text, "fact_ids": list(fact_ids) if grounded and not ungrounded else [],
                     "makes_factual_claim": grounded})
    return {"title": "Lab day", "segments": segs}


def storyboard_out(n_shots=6, ids=None) -> dict:
    ids = ids or [[f"seg{i}"] for i in range(1, n_shots + 1)]
    return {"shots": [{"segment_ids": sid, "visual_description": f"Abstract scene {WORDS[i % len(WORDS)]}",
                       "on_screen_text": f"Caption {WORDS[i % len(WORDS)]}", "asset_prompt": f"gradient background {WORDS[i % len(WORDS)]}"}
                      for i, sid in enumerate(ids, 1)]}


def critic_out(unsupported=None, safety=None) -> dict:
    return {"unsupported_claims": unsupported or [], "safety_concerns": safety or [], "notes": "ok"}


def default_responses() -> dict:
    return {"planner": [planner_out()], "researcher": [research_out()], "scriptwriter": [script_out()],
            "storyboarder": [storyboard_out()], "critic": [critic_out()]}


class FakeLLM:
    """Scripted replacement for LLMClient.chat_json. The LAST item of each list repeats."""

    def __init__(self, responses: dict):
        self.responses = {k: list(v) for k, v in responses.items()}
        self.calls = self.prompt_tokens = self.completion_tokens = 0
        self.history: list[tuple[str, str]] = []

    def chat_json(self, agent, system, user, schema_model, seed=None, max_repairs=1):
        self.calls += 1
        self.history.append((agent, user))
        queue = self.responses[agent]
        item = queue.pop(0) if len(queue) > 1 else queue[0]
        if isinstance(item, Exception):
            raise item
        self.prompt_tokens += 100
        self.completion_tokens += 50
        return schema_model.model_validate(item) if isinstance(item, dict) else item

    def agents_called(self) -> list[str]:
        return [a for a, _ in self.history]


class FakeSDK:
    """Mimics openai client for adapter-level tests."""

    def __init__(self, replies):
        self.replies = list(replies)
        self.chat = NS(completions=NS(create=self._create))

    def _create(self, **kw):
        r = self.replies.pop(0) if len(self.replies) > 1 else self.replies[0]
        if isinstance(r, Exception):
            raise r
        return NS(choices=[NS(message=NS(content=r))], usage=NS(prompt_tokens=10, completion_tokens=5))
