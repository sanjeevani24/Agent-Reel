"""Storyboarder: script -> 6-10 shots. Narration and timing are copied from the script by code;
the LLM only designs visuals, captions and asset prompts."""
from __future__ import annotations

import json
from typing import Optional

from pydantic import BaseModel

from core.brief import Brief
from core.prompts import load_prompt
from core.schemas import Issue, Plan, ScriptOutput, Shot, StoryboardDraft, StoryboardOutput
from core.validators import limit_caption, storyboard_issues

PROMPT_VERSION = "v1"


class StoryboarderInput(BaseModel):
    brief: Brief
    plan: Plan
    script: ScriptOutput
    allowed_text: str = ""
    seed: int = 42
    feedback: list[Issue] = []
    previous: Optional[StoryboardOutput] = None


def build_user_message(inp: StoryboarderInput) -> str:
    payload = {
        "tone": inp.brief.tone, "creative_direction": inp.plan.creative_direction,
        "segments": [{"id": s.id, "role": s.role, "start_s": s.start_s, "end_s": s.end_s,
                      "narration": s.narration} for s in inp.script.segments],
    }
    if inp.feedback:
        payload["critic_feedback"] = [i.model_dump(include={"code", "message", "fix_hint", "location"})
                                      for i in inp.feedback]
        if inp.previous:
            payload["previous_storyboard"] = [
                {"segment_ids": s.segment_ids, "visual_description": s.visual_description,
                 "on_screen_text": s.on_screen_text, "asset_prompt": s.asset_prompt} for s in inp.previous.shots]
    return json.dumps(payload, ensure_ascii=False)


def build_shots(draft: StoryboardDraft, script: ScriptOutput) -> list[Shot]:
    segs = {s.id: s for s in script.segments}
    shots = []
    for i, d in enumerate(draft.shots, 1):
        known = [segs[x] for x in d.segment_ids if x in segs]
        start = min((s.start_s for s in known), default=0.0)
        end = max((s.end_s for s in known), default=0.0)
        shots.append(Shot(
            shot_id=f"S{i:02d}", start_s=start, duration_s=round(max(end - start, 0.0), 2),
            segment_ids=d.segment_ids, visual_description=d.visual_description,
            on_screen_text=d.on_screen_text,
            narration=" ".join(s.narration for s in known),            
            asset_prompt=d.asset_prompt))
    return shots


def run(inp: StoryboarderInput, llm, log=None) -> StoryboardOutput:
    system, _ = load_prompt("storyboarder", PROMPT_VERSION)
    draft: StoryboardDraft = llm.chat_json("storyboarder", system, build_user_message(inp),
                                           StoryboardDraft, seed=inp.seed)
    shots = build_shots(draft, inp.script)
    shots[-1].disclosure_text = inp.brief.disclosure_line      # fixed legal/AI-disclosure footer
    out = StoryboardOutput(shots=shots, total_duration_s=round(sum(s.duration_s for s in shots), 2),
                           target_duration_s=inp.plan.video.duration_target_s)
    out.issues = storyboard_issues(out, inp.script, inp.plan.video, inp.brief.disclosure_line, inp.allowed_text)
    return out
