"""Tests for AgentReel Motion Graphics Upgrade V3 (Final Submission Polish)."""
from pathlib import Path
import pytest
from PIL import Image

import agents.motion_graphics as mg
from agents.renderer_v3 import (
    SCENES_V3,
    format_srt_time,
    generate_subtitles_v3,
    synthesize_audio_track_v3,
)

ROOT = Path(__file__).resolve().parent.parent


def test_v3_scenes_frame_render():
    """Verify all 5 scene procedural frame renderers output 1080x1920 images at multiple timeline points."""
    renderers = [
        mg.render_scene1_frame,
        mg.render_scene2_frame,
        mg.render_scene3_frame,
        mg.render_scene4_frame,
        mg.render_scene5_frame,
    ]

    for s_idx, fn in enumerate(renderers, 1):
        for frame_idx, total_frames in [(0, 100), (30, 100), (60, 100), (99, 100)]:
            img = fn(frame_idx, total_frames, f"Scene {s_idx} Caption at frame {frame_idx}")
            assert isinstance(img, Image.Image), f"Scene {s_idx} did not return a PIL Image"
            assert img.size == (1080, 1920), f"Scene {s_idx} frame size {img.size} != (1080, 1920)"


def test_v3_subtitles_generation(tmp_path):
    """Verify SRT file generation, timestamp continuity, and SubRip format."""
    srt_file = tmp_path / "subtitles_v3.srt"
    content = generate_subtitles_v3(SCENES_V3, srt_file)

    assert srt_file.is_file()
    assert "1\n00:00:00,000 --> 00:00:05,500" in content
    assert "2\n00:00:05,500 --> 00:00:22,000" in content
    assert "3\n00:00:22,000 --> 00:00:30,000" in content
    assert "4\n00:00:30,000 --> 00:00:38,000" in content
    assert "5\n00:00:38,000 --> 00:00:44,000" in content
    assert "Come and build with us." in content


def test_v3_durations_and_cta():
    """Verify duration specification (43-45s) and required CTA/disclosure lines."""
    total_dur = sum(s["duration_s"] for s in SCENES_V3)
    assert 43.0 <= total_dur <= 45.0, f"Total duration {total_dur}s out of range [43, 45]"
    assert total_dur == 44.0

    scene5 = SCENES_V3[4]
    assert "Come and build with us." in scene5["narration"]
    assert "Come and build with us." in scene5["caption"]


def test_v3_scene2_narration_preserves_all_seven_agents():
    """Verify Scene 2 explicitly names all 7 specialized agents."""
    s2 = SCENES_V3[1]
    text = s2["narration"].lower()
    for agent in ["planner", "researcher", "scriptwriter", "storyboarder", "asset generator", "editor", "critic"]:
        assert agent in text, f"Missing agent '{agent}' in Scene 2 narration"


def test_v3_backup_preservation():
    """Verify both milestone_c_backup and v2_backup exist and preserve earlier outputs."""
    milestone_c = ROOT / "outputs" / "milestone_c_backup"
    v2_backup = ROOT / "outputs" / "v2_backup"

    assert milestone_c.is_dir(), "outputs/milestone_c_backup/ does not exist"
    assert (milestone_c / "final_video.mp4").is_file()

    assert v2_backup.is_dir(), "outputs/v2_backup/ does not exist"
    assert (v2_backup / "final_video_v2.mp4").is_file()
    assert (v2_backup / "subtitles_v2.srt").is_file()
    assert (v2_backup / "render_report_v2.json").is_file()
