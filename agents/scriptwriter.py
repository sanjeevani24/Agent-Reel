"""Scriptwriter: facts + brief -> timed script (hook, narration, CTA). Validates length/duration."""
from __future__ import annotations

import json
from typing import Optional

from pydantic import BaseModel

from core.brief import Brief
from core.prompts import load_prompt
from core.schemas import FactsOutput, Issue, Plan, ScriptDraft, ScriptOutput
from core.validators import WORDS_PER_SECOND, estimate_seconds, script_issues, word_count, word_range

PROMPT_VERSION = "v1"


class ScriptwriterInput(BaseModel):
    brief: Brief
    plan: Plan
    facts: FactsOutput
    seed: int = 42
    feedback: list[Issue] = []
    previous: Optional[ScriptOutput] = None


def allowed_text(brief: Brief, facts: FactsOutput) -> str:
    """Everything that may legitimately contain numbers/contact details."""
    parts = [brief.title, brief.topic, brief.objective, brief.audience, brief.call_to_action,
             *brief.key_messages, *brief.must_include, *(f"{f.claim} {f.quote}" for f in facts.facts)]
    return " ".join(parts)


def build_user_message(inp: ScriptwriterInput) -> str:
    b, spec = inp.brief, inp.plan.video
    lo, hi = word_range(spec)
    payload = {
        "brief": {"title": b.title, "topic": b.topic, "objective": b.objective, "audience": b.audience,
                  "tone": b.tone, "language": b.language, "key_messages": b.key_messages,
                  "call_to_action": b.call_to_action, "must_include": b.must_include, "must_avoid": b.must_avoid},
        "creative_direction": inp.plan.creative_direction,
        "official_sources_present": inp.facts.official_sources_present,
        "facts": [{"id": f.id, "claim": f.claim} for f in inp.facts.facts],
        "missing_info": inp.facts.missing_info,
        "constraints": {"target_duration_s": spec.duration_target_s,
                        "last_segment_end_s_window": [spec.min_duration_s, spec.max_duration_s],
                        "total_narration_words_range": [lo, hi], "words_per_second": WORDS_PER_SECOND,
                        "segments": "6 to 9"},
    }
    if inp.feedback:
        payload["critic_feedback"] = [i.model_dump(include={"code", "message", "fix_hint", "location"})
                                      for i in inp.feedback]
        if inp.previous:
            payload["previous_script"] = inp.previous.model_dump(exclude={"issues"})
    return json.dumps(payload, ensure_ascii=False)


def run(inp: ScriptwriterInput, llm, log=None) -> ScriptOutput:
    system, _ = load_prompt("scriptwriter", PROMPT_VERSION)
    draft: ScriptDraft = llm.chat_json("scriptwriter", system, build_user_message(inp), ScriptDraft, seed=inp.seed)
    for i, seg in enumerate(draft.segments, 1):   # deterministic ids: seg1..segN
        seg.id = f"seg{i}"
    words = sum(word_count(s.narration) for s in draft.segments)
    out = ScriptOutput(
        title=draft.title, segments=draft.segments, hook=draft.segments[0].narration,
        call_to_action=draft.segments[-1].narration, word_count=words,
        estimated_narration_s=estimate_seconds(words), timeline_end_s=draft.segments[-1].end_s,
        target_duration_s=inp.plan.video.duration_target_s)
    out.issues = script_issues(out, inp.plan.video, {f.id for f in inp.facts.facts},
                               allowed_text(inp.brief, inp.facts))
    return out


def to_markdown(script: ScriptOutput) -> str:
    lines = [f"# {script.title}", "",
             f"*{script.word_count} words, ~{script.estimated_narration_s}s narration, "
             f"timeline ends at {script.timeline_end_s}s (target {script.target_duration_s}s)*", ""]
    for s in script.segments:
        cite = f" _(facts: {', '.join(s.fact_ids)})_" if s.fact_ids else ""
        lines += [f"**[{s.start_s:g}s - {s.end_s:g}s] {s.id} ({s.role})**{cite}", s.narration, ""]
    return "\n".join(lines)
