"""Tests for AgentReel Motion Graphics Upgrade V2."""
from pathlib import Path
import pytest
from PIL import Image

import agents.motion_graphics as mg
from agents.renderer_v2 import SCENES_V2, format_srt_time, generate_subtitles_v2, synthesize_audio_track

ROOT = Path(__file__).resolve().parent.parent


def test_motion_scenes_frame_render():
    """Verify all 5 scene procedural frame renderers output 1080x1920 images at various intervals."""
    renderers = [
        mg.render_scene1_frame,
        mg.render_scene2_frame,
        mg.render_scene3_frame,
        mg.render_scene4_frame,
        mg.render_scene5_frame,
    ]

    for s_idx, fn in enumerate(renderers, 1):
        for frame_idx, total_frames in [(0, 100), (50, 100), (99, 100)]:
            img = fn(frame_idx, total_frames, f"Scene {s_idx} Caption at frame {frame_idx}")
            assert isinstance(img, Image.Image), f"Scene {s_idx} did not return a PIL Image"
            assert img.size == (1080, 1920), f"Scene {s_idx} frame size {img.size} != (1080, 1920)"


def test_subtitles_v2_generation(tmp_path):
    """Verify SRT file generation, timestamp continuity, and SubRip format."""
    srt_file = tmp_path / "subtitles_v2.srt"
    content = generate_subtitles_v2(SCENES_V2, srt_file)

    assert srt_file.is_file()
    assert "1\n00:00:00,000 --> 00:00:04,500" in content
    assert "2\n00:00:04,500 --> 00:00:20,000" in content
    assert "3\n00:00:20,000 --> 00:00:28,500" in content
    assert "4\n00:00:28,500 --> 00:00:37,000" in content
    assert "5\n00:00:37,000 --> 00:00:43,000" in content
    assert "Come and build with us." in content


def test_scene_durations_and_cta():
    """Verify duration specification (40-45s) and required CTA/disclosure lines."""
    total_dur = sum(s["duration_s"] for s in SCENES_V2)
    assert 40.0 <= total_dur <= 45.0, f"Total duration {total_dur}s out of range [40, 45]"
    assert total_dur == 43.0

    scene5 = SCENES_V2[4]
    assert "Come and build with us." in scene5["narration"]
    assert "Come and build with us." in scene5["caption"]


def test_srt_time_formatting():
    """Verify accurate time formatting to SubRip standard."""
    assert format_srt_time(0.0) == "00:00:00,000"
    assert format_srt_time(4.5) == "00:00:04,500"
    assert format_srt_time(65.25) == "00:01:05,250"
    assert format_srt_time(3600.0) == "01:00:00,000"


def test_milestone_c_backup_integrity():
    """Verify that earlier Milestone B & C outputs were safely preserved in outputs/milestone_c_backup/."""
    backup_dir = ROOT / "outputs" / "milestone_c_backup"
    assert backup_dir.is_dir(), "Backup directory outputs/milestone_c_backup/ does not exist"

    expected_files = [
        "final_video.mp4",
        "subtitles.srt",
        "script.json",
        "storyboard.json",
        "edit_plan.json",
        "qa_report.json",
        "render_report.json",
    ]
    for fname in expected_files:
        assert (backup_dir / fname).is_file(), f"Preserved file {fname} missing from backup"


def test_audio_synthesis_track(tmp_path):
    """Verify audio track synthesis and padding generates a valid WAV file."""
    out_wav = tmp_path / "test_audio.wav"
    synthesize_audio_track("Short test voice line.", duration_s=2.0, out_wav=out_wav)
    assert out_wav.is_file()
    assert out_wav.stat().st_size > 1000
