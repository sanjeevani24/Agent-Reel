"""Brief schema. A new faculty brief is just a new YAML file - no code changes."""
from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, Field, field_validator, model_validator

DISCLOSURE_LINE = "Created with AI agents \u2014 LY Agentic AI Lab"

# Topics that force a human review checkpoint before export (spec section 5).
SENSITIVE_KEYWORDS = (
    "ragging", "anti-ragging", "icc", "posh", "harassment", "mental health",
    "counselling", "counseling", "suicide", "helpline", "legal", "policy",
    "grievance", "safety", "emergency", "abuse",
)


class Brief(BaseModel):
    brief_id: str = Field(min_length=1, max_length=40)
    title: str
    topic: str
    objective: str
    audience: str
    tone: str = "energetic, friendly, clear"
    language: str = "en"
    duration_target_s: int = Field(default=40, ge=30, le=60)
    key_messages: list[str] = Field(default_factory=list)
    call_to_action: str = ""
    must_include: list[str] = Field(default_factory=list)
    must_avoid: list[str] = Field(default_factory=list)
    data_dir: str = "data"
    sensitive_topic: bool = False  # set true to force human review manually
    disclosure_line: str = DISCLOSURE_LINE

    @field_validator("brief_id")
    @classmethod
    def _safe_id(cls, v: str) -> str:
        if not all(c.isalnum() or c in "-_" for c in v):
            raise ValueError("brief_id may only contain letters, digits, '-' and '_'")
        return v

    @field_validator("disclosure_line")
    @classmethod
    def _exact_disclosure(cls, v: str) -> str:
        if v != DISCLOSURE_LINE:
            raise ValueError(f"disclosure_line must be exactly: {DISCLOSURE_LINE!r}")
        return v

    @model_validator(mode="after")
    def _non_empty(self) -> "Brief":
        for name in ("title", "topic", "objective", "audience"):
            if not getattr(self, name).strip():
                raise ValueError(f"{name} must not be empty")
        return self

    @property
    def requires_human_review(self) -> bool:
        if self.sensitive_topic:
            return True
        text = " ".join([self.title, self.topic, self.objective, *self.key_messages]).lower()
        return any(k in text for k in SENSITIVE_KEYWORDS)


class BriefError(ValueError):
    pass


def load_brief(path: str | Path) -> Brief:
    p = Path(path)
    if not p.is_file():
        raise BriefError(f"Brief file not found: {p}")
    try:
        raw = yaml.safe_load(p.read_text(encoding="utf-8"))
    except yaml.YAMLError as e:
        raise BriefError(f"Invalid YAML in {p}: {e}") from e
    if not isinstance(raw, dict):
        raise BriefError(f"{p} must contain a YAML mapping at the top level")
    try:
        return Brief(**raw)
    except Exception as e:  # pydantic ValidationError -> readable message
        raise BriefError(f"Brief validation failed for {p}:\n{e}") from e
