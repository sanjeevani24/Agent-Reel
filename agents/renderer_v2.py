"""Renderer V2: Motion Graphics Engine for AgentReel (Milestone C Upgrade).

Generates high-production-value 1080x1920 30fps vertical video:
- Topic: "From Prompt to Product: How 7 AI Agents Build a Video"
- 5 Scenes rendered procedurally with Pillow
- Spoken voiceover synthesized via macOS say with silent fallback
- Synchronized SubRip (.srt) subtitles
- 5 Preview screenshots and comprehensive render_report_v2.json
"""
from __future__ import annotations

import json
import logging
import os
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any, Callable

import agents.motion_graphics as mg

logger = logging.getLogger("agentreel.renderer_v2")

W, H = 1080, 1920
FPS = 30

SCENES_V2: list[dict[str, Any]] = [
    {
        "scene_id": 1,
        "title": "Scene 1: The Prompt",
        "duration_s": 4.5,
        "narration": "Every AgentReel video begins with a single prompt: your vision, your topic, and your target audience.",
        "caption": "Every AgentReel video begins with a single prompt: your vision, your topic, and your target audience.",
        "renderer": mg.render_scene1_frame,
        "preview_offset_s": 3.6,
    },
    {
        "scene_id": 2,
        "title": "Scene 2: The 7 AI Agents Workflow",
        "duration_s": 15.5,
        "narration": (
            "Seven autonomous agents take the stage: the Planner structures the workflow, "
            "the Researcher retrieves verified facts, the Scriptwriter crafts timed spoken narrative, "
            "the Storyboarder maps scenes, the Asset Generator creates Pillow visuals, "
            "the Editor cuts the timeline, and the Critic enforces eighteen rigorous QA checks."
        ),
        "caption": "Seven autonomous agents: Planner, Researcher, Scriptwriter, Storyboarder, Asset Generator, Editor, and Critic.",
        "renderer": mg.render_scene2_frame,
        "preview_offset_s": 12.0,
    },
    {
        "scene_id": 3,
        "title": "Scene 3: Multi-Track Timeline Assembly",
        "duration_s": 8.5,
        "narration": (
            "Next, the Asset Generator and Editor assemble multiple media tracks into lockstep: "
            "visual layers, crisp voiceover audio, and burned SubRip captions."
        ),
        "caption": "Visual cards, spoken audio, and SubRip captions assembled in lockstep.",
        "renderer": mg.render_scene3_frame,
        "preview_offset_s": 24.0,
    },
    {
        "scene_id": 4,
        "title": "Scene 4: Critic QA HUD & Repair Loop",
        "duration_s": 8.5,
        "narration": (
            "Before final delivery, the Critic inspects eighteen quality rules. "
            "If any caption exceeds forty characters, a repair loop triggers automatically until every check passes."
        ),
        "caption": "Critic inspects 18 rules. Any violation triggers an automated repair loop.",
        "renderer": mg.render_scene4_frame,
        "preview_offset_s": 33.0,
    },
    {
        "scene_id": 5,
        "title": "Scene 5: Final Video Reveal & Call to Action",
        "duration_s": 6.0,
        "narration": (
            "The result is a broadcast-ready vertical video built entirely by autonomous AI agents. "
            "Come and build with us."
        ),
        "caption": "The result is a broadcast-ready vertical video built by AI agents. Come and build with us.",
        "renderer": mg.render_scene5_frame,
        "preview_offset_s": 40.0,
    },
]


def format_srt_time(seconds: float) -> str:
    """Format seconds into SubRip SRT timestamp: HH:MM:SS,mmm"""
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int(round((seconds - int(seconds)) * 1000))
    if millis >= 1000:
        secs += 1
        millis -= 1000
    return f"{hrs:02d}:{mins:02d}:{secs:02d},{millis:03d}"


def generate_subtitles_v2(scenes: list[dict[str, Any]], out_path: Path) -> str:
    """Write standard SRT file for the 5 scenes."""
    lines: list[str] = []
    current_time = 0.0

    for idx, sc in enumerate(scenes, 1):
        start_s = current_time
        end_s = current_time + sc["duration_s"]
        current_time = end_s

        lines.append(str(idx))
        lines.append(f"{format_srt_time(start_s)} --> {format_srt_time(end_s)}")
        lines.append(sc["caption"])
        lines.append("")

    srt_content = "\n".join(lines)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(srt_content, encoding="utf-8")
    return srt_content


def synthesize_audio_track(text: str, duration_s: float, out_wav: Path, voice: str = "Samantha", rate: int = 175) -> Path:
    """Synthesize voice narration with macOS `say` and pad to exact duration with FFmpeg."""
    out_wav.parent.mkdir(parents=True, exist_ok=True)
    temp_aiff = out_wav.with_suffix(".aiff")

    say_cmd = shutil.which("say")
    tts_success = False

    if say_cmd:
        try:
            cmd = [say_cmd, "-v", voice, "-r", str(rate), "-o", str(temp_aiff), text]
            subprocess.run(cmd, check=True, capture_output=True, timeout=15)
            if temp_aiff.is_file() and temp_aiff.stat().st_size > 0:
                tts_success = True
        except Exception as e:
            logger.warning(f"say command failed: {e}. Falling back to silent audio track.")

    if tts_success:
        # Convert AIFF and pad with silence up to exact scene duration (or trim if longer)
        cmd = [
            "ffmpeg", "-y",
            "-i", str(temp_aiff),
            "-af", f"apad=whole_dur={duration_s}",
            "-t", str(duration_s),
            "-ar", "48000",
            "-ac", "2",
            str(out_wav)
        ]
        subprocess.run(cmd, check=True, capture_output=True)
        try:
            temp_aiff.unlink(missing_ok=True)
        except Exception:
            pass
    else:
        # Generate silence of exact duration
        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi",
            "-i", "anullsrc=r=48000:cl=stereo",
            "-t", str(duration_s),
            "-ar", "48000",
            "-ac", "2",
            str(out_wav)
        ]
        subprocess.run(cmd, check=True, capture_output=True)

    return out_wav


def render_scene_clip(scene: dict[str, Any], temp_dir: Path, voice: str = "Samantha", rate: int = 175) -> Path:
    """Render a single scene clip with video frames streamed into FFmpeg muxed with audio."""
    scene_id = scene["scene_id"]
    dur = scene["duration_s"]
    num_frames = int(round(dur * FPS))
    renderer_fn: Callable = scene["renderer"]
    caption = scene["caption"]

    audio_path = temp_dir / f"scene_{scene_id}_audio.wav"
    synthesize_audio_track(scene["narration"], dur, audio_path, voice=voice, rate=rate)

    clip_path = temp_dir / f"scene_{scene_id}.mp4"

    cmd = [
        "ffmpeg", "-y",
        "-f", "rawvideo",
        "-vcodec", "rawvideo",
        "-s", f"{W}x{H}",
        "-pix_fmt", "rgb24",
        "-r", str(FPS),
        "-i", "-",
        "-i", str(audio_path),
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-preset", "fast",
        "-crf", "22",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        str(clip_path)
    ]

    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        for f in range(num_frames):
            img = renderer_fn(f, num_frames, caption)
            proc.stdin.write(img.tobytes())
        proc.stdin.close()
        stderr = proc.stderr.read()
        proc.wait()
        if proc.returncode != 0:
            raise RuntimeError(f"FFmpeg render failed for scene {scene_id}: {stderr.decode(errors='ignore')}")
    except Exception:
        proc.kill()
        raise

    return clip_path


def render_motion_graphics_v2(
    output_dir: Path | str = "outputs",
    voice: str = "Samantha",
    rate: int = 175,
    keep_temp: bool = False
) -> dict[str, Any]:
    """Execute complete Milestone C Upgrade pipeline:

    1. Renders 5 procedural motion graphics scenes.
    2. Generates voiceover and muxes each scene to MP4.
    3. Concatenates all scenes into outputs/final_video_v2.mp4.
    4. Generates outputs/subtitles_v2.srt.
    5. Extracts 5 preview screenshots (preview_v2_1.png to preview_v2_5.png).
    6. Produces outputs/render_report_v2.json.
    """
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    temp_dir = out_dir / "temp_v2"
    temp_dir.mkdir(parents=True, exist_ok=True)

    start_time = time.time()
    total_expected_dur = sum(s["duration_s"] for s in SCENES_V2)

    # 1. Generate subtitles
    srt_path = out_dir / "subtitles_v2.srt"
    generate_subtitles_v2(SCENES_V2, srt_path)

    # 2. Render each scene clip
    clip_paths: list[Path] = []
    for sc in SCENES_V2:
        logger.info(f"Rendering {sc['title']} ({sc['duration_s']}s)...")
        clip = render_scene_clip(sc, temp_dir, voice=voice, rate=rate)
        clip_paths.append(clip)

    # 3. Concatenate scene clips
    concat_list_file = temp_dir / "concat_list.txt"
    concat_content = "\n".join(f"file '{p.resolve()}'" for p in clip_paths)
    concat_list_file.write_text(concat_content, encoding="utf-8")

    final_video_path = out_dir / "final_video_v2.mp4"
    concat_cmd = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(concat_list_file),
        "-c", "copy",
        str(final_video_path)
    ]
    res = subprocess.run(concat_cmd, capture_output=True)
    if res.returncode != 0:
        raise RuntimeError(f"FFmpeg concat failed: {res.stderr.decode(errors='ignore')}")

    # 4. Extract 5 preview screenshots
    preview_paths: list[str] = []
    for sc in SCENES_V2:
        prev_idx = sc["scene_id"]
        prev_time = sc["preview_offset_s"]
        prev_file = out_dir / f"preview_v2_{prev_idx}.png"
        extract_cmd = [
            "ffmpeg", "-y",
            "-ss", str(prev_time),
            "-i", str(final_video_path),
            "-vframes", "1",
            str(prev_file)
        ]
        subprocess.run(extract_cmd, check=True, capture_output=True)
        preview_paths.append(str(prev_file.name))

    # 5. Measure final file stats
    file_size_bytes = final_video_path.stat().st_size
    file_size_mb = round(file_size_bytes / (1024 * 1024), 2)
    elapsed_s = round(time.time() - start_time, 2)

    # Probe actual duration
    probe_cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(final_video_path)
    ]
    probe_res = subprocess.run(probe_cmd, capture_output=True, text=True)
    actual_duration = float(probe_res.stdout.strip()) if probe_res.stdout.strip() else total_expected_dur

    # 6. Build and write render_report_v2.json
    report_data = {
        "topic": "From Prompt to Product: How 7 AI Agents Build a Video",
        "status": "SUCCESS",
        "duration_seconds": round(actual_duration, 2),
        "target_duration_seconds": total_expected_dur,
        "resolution": f"{W}x{H}",
        "aspect_ratio": "9:16",
        "fps": FPS,
        "video_codec": "h264",
        "audio_codec": "aac",
        "audio_sample_rate": 48000,
        "audio_channels": 2,
        "file_size_bytes": file_size_bytes,
        "file_size_mb": file_size_mb,
        "render_time_seconds": elapsed_s,
        "scenes_count": len(SCENES_V2),
        "scenes": [
            {
                "scene_id": s["scene_id"],
                "title": s["title"],
                "duration_seconds": s["duration_s"],
                "narration": s["narration"],
                "caption": s["caption"],
            }
            for s in SCENES_V2
        ],
        "outputs": {
            "video": str(final_video_path.name),
            "subtitles": str(srt_path.name),
            "previews": preview_paths,
        },
        "cta": "Come and build with us.",
        "disclosure": "Created with AI agents — LY Agentic AI Lab"
    }

    report_path = out_dir / "render_report_v2.json"
    report_path.write_text(json.dumps(report_data, indent=2), encoding="utf-8")

    # Clean up temp clips if requested
    if not keep_temp:
        try:
            shutil.rmtree(temp_dir)
        except Exception:
            pass

    return report_data
