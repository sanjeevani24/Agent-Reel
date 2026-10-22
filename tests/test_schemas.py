import pytest
from pydantic import ValidationError

from core.schemas import (Issue, PlannerDraft, ScriptDraft, StoryboardDraft, VideoSpec)
from tests.helpers import planner_out, script_out, storyboard_out


def test_video_spec_window_is_clamped():
    s = VideoSpec.for_target(40)
    assert (s.min_duration_s, s.max_duration_s) == (35, 45)
    s = VideoSpec.for_target(58)
    assert s.max_duration_s == 60
    assert (s.width, s.height, s.fps) == (1080, 1920, 30)


def test_planner_draft_needs_3_to_8_criteria():
    PlannerDraft.model_validate(planner_out())
    bad = planner_out()
    bad["success_criteria"] = ["one"]
    with pytest.raises(ValidationError):
        PlannerDraft.model_validate(bad)


def test_script_shape_rules():
    ScriptDraft.model_validate(script_out())
    with pytest.raises(ValidationError):
        ScriptDraft.model_validate(script_out(n_segments=5))          # too few segments
    bad = script_out()
    bad["segments"][0]["role"] = "body"                               # hook missing
    with pytest.raises(ValidationError):
        ScriptDraft.model_validate(bad)
    bad = script_out()
    bad["segments"][1]["end_s"] = bad["segments"][1]["start_s"]       # zero-length
    with pytest.raises(ValidationError):
        ScriptDraft.model_validate(bad)


def test_storyboard_needs_6_to_10_shots():
    StoryboardDraft.model_validate(storyboard_out(6))
    StoryboardDraft.model_validate(storyboard_out(10, ids=[["seg1"]] * 10))
    with pytest.raises(ValidationError):
        StoryboardDraft.model_validate(storyboard_out(5, ids=[["seg1"]] * 5))
    with pytest.raises(ValidationError):
        StoryboardDraft.model_validate(storyboard_out(11, ids=[["seg1"]] * 11))


def test_issue_stage_must_be_known():
    with pytest.raises(ValidationError):
        Issue(code="X", severity="soft", stage="nonexistent", message="m")
