import json
import pytest
from pathlib import Path
from PIL import Image

from agents import asset_generator, editor
from agents.critic import video_issues
from core.brief import load_brief
from core.schemas import EditClip, EditPlan, OutputSpec, Shot, StoryboardOutput, VideoSpec
from core.validators import limit_caption

ROOT = Path(__file__).resolve().parent.parent
BRIEF = load_brief(ROOT / "briefs" / "practice.yaml")
SPEC = VideoSpec.for_target(40)


def test_limit_caption_behavior():
    assert limit_caption("") == ""
    assert limit_caption("   hello   world   ") == "hello world"
    short = "Short caption under eighty characters."
    assert limit_caption(short, 80) == short

    # Exactly 80 characters
    eighty = "a" * 80
    assert limit_caption(eighty, 80) == eighty

    # Longer text split at word boundary
    long_text = "This is a deliberately very long caption that extends past eighty characters to test clean truncation at word boundaries properly."
    limited = limit_caption(long_text, 80)
    assert len(limited) <= 80
    assert limited.endswith("…")
    assert not limited.endswith(" …")

    # Very long single word
    one_word = "X" * 100
    limited_word = limit_caption(one_word, 80)
    assert len(limited_word) == 80
    assert limited_word.endswith("…")


def test_generate_subtitles_srt_format(tmp_path):
    clips = [
        EditClip(shot_id="S01", start_s=0.0, end_s=5.0, duration_s=5.0,
                 image_path="assets/S01.png", caption_text="Welcome to the AI lab.",
                 narration="Welcome to the AI lab today.", motion="slow_zoom_in", transition_in="fade_in_0.3s"),
        EditClip(shot_id="S02", start_s=5.0, end_s=10.0, duration_s=5.0,
                 image_path="assets/S02.png", caption_text="Students build multi-agent systems.",
                 narration="Students build multi-agent systems.", motion="slow_zoom_out", transition_in="crossfade_0.4s")
    ]
    srt_p = tmp_path / "test.srt"
    editor.generate_subtitles_srt(clips, end_card_text="Come build with us.", end_card_start=10.0, end_card_dur=4.0, srt_path=srt_p)
    assert srt_p.is_file()
    content = srt_p.read_text(encoding="utf-8")
    assert "00:00:00,000 --> 00:00:05,000" in content
    assert "Welcome to the AI lab." in content
    assert "00:00:05,000 --> 00:00:10,000" in content
    assert "Students build multi-agent systems." in content
    assert "00:00:10,000 --> 00:00:14,000" in content
    assert "Come build with us." in content


def test_editor_assigns_caption_from_on_screen_text(tmp_path):
    shots = [
        Shot(shot_id="S01", start_s=0.0, duration_s=5.0, segment_ids=["seg1"],
             visual_description="desc1", on_screen_text="Short caption",
             narration="Very long spoken narration that is different", asset_prompt="prompt1"),
        Shot(shot_id="S02", start_s=5.0, duration_s=5.0, segment_ids=["seg2"],
             visual_description="desc2", on_screen_text="Another short caption",
             narration="Another different narration", asset_prompt="prompt2"),
        Shot(shot_id="S03", start_s=10.0, duration_s=5.0, segment_ids=["seg3"],
             visual_description="desc3", on_screen_text="Caption 3", narration="Narr 3", asset_prompt="prompt3"),
        Shot(shot_id="S04", start_s=15.0, duration_s=5.0, segment_ids=["seg4"],
             visual_description="desc4", on_screen_text="Caption 4", narration="Narr 4", asset_prompt="prompt4"),
        Shot(shot_id="S05", start_s=20.0, duration_s=5.0, segment_ids=["seg5"],
             visual_description="desc5", on_screen_text="Caption 5", narration="Narr 5", asset_prompt="prompt5"),
        Shot(shot_id="S06", start_s=25.0, duration_s=5.0, segment_ids=["seg6"],
             visual_description="desc6", on_screen_text="Caption 6", narration="Narr 6", asset_prompt="prompt6"),
    ]
    sb = StoryboardOutput(shots=shots, total_duration_s=30.0, target_duration_s=40)
    from core.schemas import AssetManifest, AssetRecord
    manifest = AssetManifest(brief_id="P00", assets=[
        AssetRecord(asset_id=f"img_{s.shot_id}", kind="image", shot_id=s.shot_id, path=None, status="planned", source="s", licence="l", intended_use="u")
        for s in shots
    ])
    edit_plan = editor.run(editor.EditorInput(brief=BRIEF, storyboard=sb, manifest=manifest, spec=SPEC, root=str(tmp_path)))
    assert edit_plan.clips[0].caption_text == "Short caption"
    assert edit_plan.clips[0].caption_text != edit_plan.clips[0].narration
    assert edit_plan.clips[1].caption_text == "Another short caption"


def test_render_end_card_dimensions(tmp_path):
    out = tmp_path / "end_card.png"
    asset_generator.render_end_card(out, "Test Lab", "Build with us", "AI disclosure", 0.5, SPEC)
    assert out.is_file()
    with Image.open(out) as im:
        assert im.size == (1080, 1920)


def test_missing_assets_raises_render_error(tmp_path):
    clips = [
        EditClip(shot_id="S01", start_s=0.0, end_s=5.0, duration_s=5.0,
                 image_path="nonexistent/S01.png", caption_text="Caption",
                 narration="Narration", motion="slow_zoom_in", transition_in="fade")
    ]
    with pytest.raises(editor.RenderError) as exc_info:
        editor.render_shot_clips(clips, None, 0, tmp_path / "work", SPEC, tmp_path)
    assert "Missing image asset" in str(exc_info.value)


def test_video_issues_validator_detects_bad_video(tmp_path):
    missing_video = tmp_path / "no_video.mp4"
    issues = video_issues(missing_video, SPEC)
    assert any(i.code == "VIDEO_INVALID" for i in issues)

    empty_video = tmp_path / "empty.mp4"
    empty_video.write_bytes(b"")
    issues = video_issues(empty_video, SPEC)
    assert any(i.code == "VIDEO_INVALID" for i in issues)
