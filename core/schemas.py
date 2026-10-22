"""Pydantic contracts shared by every agent (the explicit input/output contracts)."""
from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

STAGES = ["planner", "researcher", "scriptwriter", "storyboarder",
          "asset_generator", "editor", "critic"]
Severity = Literal["hard", "factual", "soft"]
BLOCKING = ("hard", "factual")


# ---------------------------------------------------------------- critic issues
class Issue(BaseModel):
    code: str
    severity: Severity            # hard = spec/structure, factual = grounding/safety, soft = quality
    stage: str                    # agent responsible for fixing it
    message: str
    fix_hint: str = ""
    repairable: bool = True
    location: str = ""

    @field_validator("stage")
    @classmethod
    def _known_stage(cls, v: str) -> str:
        if v not in STAGES:
            raise ValueError(f"unknown stage {v!r}")
        return v


# ---------------------------------------------------------------- planner
class VideoSpec(BaseModel):
    duration_target_s: int
    min_duration_s: int
    max_duration_s: int
    aspect_ratio: str = "9:16"
    width: int = 1080
    height: int = 1920
    fps: int = 30
    video_codec: str = "h264"
    audio_codec: str = "aac"
    max_file_mb: int = 100
    safe_top_px: int = 250
    safe_bottom_px: int = 350

    @classmethod
    def for_target(cls, target: int) -> "VideoSpec":
        return cls(duration_target_s=target, min_duration_s=max(30, target - 5),
                   max_duration_s=min(60, target + 5))


class StagePlan(BaseModel):
    name: str
    max_seconds: int
    depends_on: list[str] = []
    purpose: str = ""


class CostBudget(BaseModel):
    max_llm_calls: int = 30
    max_total_tokens: int = 250_000
    max_repair_loops: int = 3
    cost_note: str = ("USD cost is 'unknown' unless LLM_PRICE_IN_PER_M / LLM_PRICE_OUT_PER_M "
                      "are set; the budget is therefore enforced on calls and tokens.")


class PlannerDraft(BaseModel):          # what the LLM fills in
    success_criteria: list[str] = Field(min_length=3, max_length=8)
    creative_direction: str
    risk_notes: list[str] = []


class Plan(BaseModel):
    brief_id: str
    title: str
    seed: int
    video: VideoSpec
    stages: list[StagePlan]
    success_criteria: list[str]
    creative_direction: str
    risk_notes: list[str] = []
    cost_budget: CostBudget
    human_review_required: bool


# ---------------------------------------------------------------- researcher
class Fact(BaseModel):
    id: str
    claim: str
    origin: Literal["document", "brief"]
    source_file: str
    locator: str = ""
    quote: str = ""


class RejectedClaim(BaseModel):
    claim: str
    reason: str


class ExtractedFact(BaseModel):         # LLM output, verified in code before it becomes a Fact
    passage_id: str
    claim: str
    quote: str


class ResearchDraft(BaseModel):
    facts: list[ExtractedFact] = []
    missing_info: list[str] = []


class FactsOutput(BaseModel):
    official_sources_present: bool
    sources_scanned: list[str] = []
    passages_considered: int = 0
    facts: list[Fact] = []
    rejected_claims: list[RejectedClaim] = []
    missing_info: list[str] = []


# ---------------------------------------------------------------- scriptwriter
class ScriptSegment(BaseModel):
    id: str = ""
    role: Literal["hook", "body", "cta"]
    start_s: float = Field(ge=0)
    end_s: float
    narration: str
    fact_ids: list[str] = []
    makes_factual_claim: bool = False

    @model_validator(mode="after")
    def _times(self) -> "ScriptSegment":
        if self.end_s <= self.start_s:
            raise ValueError("end_s must be greater than start_s")
        if not self.narration.strip():
            raise ValueError("narration must not be empty")
        return self


class ScriptDraft(BaseModel):
    title: str
    segments: list[ScriptSegment] = Field(min_length=6, max_length=9)

    @model_validator(mode="after")
    def _shape(self) -> "ScriptDraft":
        if self.segments[0].role != "hook":
            raise ValueError("first segment must have role 'hook'")
        if self.segments[-1].role != "cta":
            raise ValueError("last segment must have role 'cta'")
        return self


class ScriptOutput(ScriptDraft):
    hook: str
    call_to_action: str
    word_count: int
    estimated_narration_s: float
    timeline_end_s: float
    target_duration_s: int
    issues: list[Issue] = []


# ---------------------------------------------------------------- storyboarder
class ShotDraft(BaseModel):
    segment_ids: list[str] = Field(min_length=1)
    visual_description: str
    on_screen_text: str
    asset_prompt: str


class StoryboardDraft(BaseModel):
    shots: list[ShotDraft] = Field(min_length=6, max_length=10)


class Shot(BaseModel):
    shot_id: str
    start_s: float
    duration_s: float
    segment_ids: list[str]
    visual_description: str
    on_screen_text: str
    disclosure_text: str = ""
    narration: str
    asset_prompt: str


class StoryboardOutput(BaseModel):
    shots: list[Shot] = Field(min_length=6, max_length=10)
    total_duration_s: float
    target_duration_s: int
    issues: list[Issue] = []


# ---------------------------------------------------------------- assets / editor
class AssetRecord(BaseModel):
    asset_id: str
    kind: Literal["image", "voiceover", "subtitles", "music"]
    shot_id: Optional[str] = None
    path: Optional[str] = None
    status: Literal["generated", "planned", "omitted"]
    source: str
    licence: str
    intended_use: str
    placeholder: bool = False


class AssetManifest(BaseModel):
    brief_id: str
    assets: list[AssetRecord]
    notes: list[str] = []


class OutputSpec(BaseModel):
    container: str = "mp4"
    width: int
    height: int
    fps: int
    video_codec: str
    audio_codec: str
    max_file_mb: int
    target_duration_s: int


class EditClip(BaseModel):
    shot_id: str
    start_s: float
    end_s: float
    duration_s: float
    image_path: Optional[str]
    caption_text: str
    narration: str
    motion: str
    transition_in: str


class EditPlan(BaseModel):
    output_spec: OutputSpec
    safe_zone_px: dict[str, int]
    clips: list[EditClip]
    subtitles: dict[str, object]
    voiceover: dict[str, object]
    background_music: dict[str, object]
    end_card: dict[str, str]
    disclosure_line: str
    render_status: Literal["not_rendered", "rendered", "failed"] = "not_rendered"
    final_video_path: Optional[str] = None
    ready_for_render: bool
    blockers: list[str] = []
    pending_assets: list[str] = []


# ---------------------------------------------------------------- critic / QA
class CriticClaim(BaseModel):
    location: str          # segment id (seg3) or shot id (S02)
    text: str
    reason: str


class CriticDraft(BaseModel):          # LLM review output
    unsupported_claims: list[CriticClaim] = []
    safety_concerns: list[CriticClaim] = []
    notes: str = ""


class CheckResult(BaseModel):
    name: str
    passed: bool
    severity: Optional[Severity] = None
    detail: str = ""


class QAReport(BaseModel):
    brief_id: str
    iteration: int
    status: Literal["PASS", "PASS_WITH_WARNINGS", "PENDING_HUMAN_REVIEW", "FAIL"]
    checks: list[CheckResult]
    issues: list[Issue]
    human_review_required: bool
    llm_review: Optional[CriticDraft] = None
    summary: str = ""
    repairs_used: int = 0
    repair_history: list[dict] = []
    final: bool = False
