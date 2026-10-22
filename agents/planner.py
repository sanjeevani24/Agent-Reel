"""Planner: brief -> structured plan (stages, limits, criteria, budget).

The LLM proposes success criteria and creative direction; the code fixes the video spec,
stage table and budget so they can never be talked out of the requirements.
"""
from __future__ import annotations

import json

from pydantic import BaseModel

from core.brief import Brief
from core.prompts import load_prompt
from core.schemas import CostBudget, Plan, PlannerDraft, StagePlan, VideoSpec

PROMPT_VERSION = "v1"

STAGE_TABLE = [  # name, max_seconds, depends_on, purpose
    ("planner", 60, [], "Turn the brief into a plan, budget and success criteria"),
    ("researcher", 120, ["planner"], "Extract source-grounded facts from data/"),
    ("scriptwriter", 90, ["researcher"], "Write the timed script using only supported facts"),
    ("storyboarder", 90, ["scriptwriter"], "Turn the script into 6-10 shots"),
    ("asset_generator", 120, ["storyboarder"], "Create assets and the asset manifest"),
    ("editor", 60, ["storyboarder", "asset_generator"], "Validate inputs and prepare the edit plan"),
    ("critic", 90, ["scriptwriter", "storyboarder", "asset_generator", "editor"],
     "QA checks and targeted repair feedback"),
]


class PlannerInput(BaseModel):
    brief: Brief
    seed: int = 42


def run(inp: PlannerInput, llm, log=None) -> Plan:
    brief = inp.brief
    spec = VideoSpec.for_target(brief.duration_target_s)
    system, _ = load_prompt("planner", PROMPT_VERSION)
    user = json.dumps({"brief": brief.model_dump(), "video_spec": spec.model_dump()}, ensure_ascii=False)
    draft = llm.chat_json("planner", system, user, PlannerDraft, seed=inp.seed)
    return Plan(
        brief_id=brief.brief_id, title=brief.title, seed=inp.seed, video=spec,
        stages=[StagePlan(name=n, max_seconds=s, depends_on=d, purpose=p) for n, s, d, p in STAGE_TABLE],
        success_criteria=draft.success_criteria, creative_direction=draft.creative_direction,
        risk_notes=draft.risk_notes, cost_budget=CostBudget(),
        human_review_required=brief.requires_human_review)
