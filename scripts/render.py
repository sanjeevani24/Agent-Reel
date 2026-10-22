#!/usr/bin/env python3
"""Standalone renderer for AgentReel (Milestone C).
Renders vertical 9:16 MP4 video, SRT subtitles, and preview screenshots
from existing intermediate outputs without making any LLM or external API calls.

Usage:
    python scripts/render.py --brief briefs/practice.yaml
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from agents.editor import render_pipeline
from core.brief import BriefError, load_brief
from core.runlog import RunLogger


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Render AgentReel video from existing outputs")
    ap.add_argument("--brief", default="briefs/practice.yaml", help="Path to YAML brief (default: briefs/practice.yaml)")
    args = ap.parse_args(argv)

    brief_path = Path(args.brief)
    if not brief_path.is_file():
        brief_path = ROOT / args.brief
    if not brief_path.is_file():
        print(f"ERROR: Brief file not found: {args.brief}", file=sys.stderr)
        return 2

    try:
        brief = load_brief(brief_path)
    except BriefError as e:
        print(f"ERROR loading brief: {e}", file=sys.stderr)
        return 2

    log = RunLogger(str(ROOT / "logs"))
    print(f"=== AgentReel Renderer (Milestone C) ===")
    print(f"Brief: {brief.brief_id} - {brief.title}")
    print(f"Target duration: {brief.duration_target_s}s (9:16 vertical 1080x1920)")

    try:
        report = render_pipeline(ROOT, brief, log=log)
    except Exception as e:
        print(f"RENDER FAILED: {e}", file=sys.stderr)
        return 1

    vm = report["video_metrics"]
    print("")
    print(f"SUCCESS: Rendered video created!")
    print(f"  MP4 Video   : {report['final_video_path']} ({vm['duration_s']}s, {vm['width']}x{vm['height']}, {vm['video_codec']}/{vm['audio_codec']}, {vm['file_size_mb']} MB)")
    print(f"  Subtitles   : {report['subtitles_path']}")
    print(f"  Voiceover   : {report['voiceover_path']}")
    print(f"  Screenshots : {', '.join(report['preview_images'])}")
    print(f"  Report JSON : outputs/render_report.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
