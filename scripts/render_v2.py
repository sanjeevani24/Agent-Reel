#!/usr/bin/env python3
"""CLI script to render AgentReel Motion Graphics V2 video."""
import argparse
import logging
import sys
from pathlib import Path

# Add project root to sys.path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agents.renderer_v2 import render_motion_graphics_v2

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")


def main():
    parser = argparse.ArgumentParser(description="Render AgentReel Motion Graphics Upgrade Video (V2)")
    parser.add_argument("--output-dir", default="outputs", help="Directory for output files (default: outputs)")
    parser.add_argument("--voice", default="Samantha", help="Voice name for macOS say (default: Samantha)")
    parser.add_argument("--rate", type=int, default=175, help="Speaking rate for macOS say (default: 175)")
    parser.add_argument("--keep-temp", action="store_true", help="Keep temporary scene video/audio clips")
    args = parser.parse_args()

    print("=" * 60)
    print("AgentReel Motion Graphics Upgrade (V2) — Renderer")
    print("Topic: From Prompt to Product: How 7 AI Agents Build a Video")
    print("=" * 60)

    report = render_motion_graphics_v2(
        output_dir=args.output_dir,
        voice=args.voice,
        rate=args.rate,
        keep_temp=args.keep_temp,
    )

    print("\n" + "=" * 60)
    print("RENDER COMPLETED SUCCESSFULLY!")
    print(f"Video File:      {report['outputs']['video']} ({report['file_size_mb']} MB)")
    print(f"Duration:        {report['duration_seconds']}s (Target: {report['target_duration_seconds']}s)")
    print(f"Resolution:      {report['resolution']} @ {report['fps']} fps")
    print(f"Subtitles:       {report['outputs']['subtitles']}")
    print(f"Previews:        {', '.join(report['outputs']['previews'])}")
    print(f"Render Time:     {report['render_time_seconds']}s")
    print(f"CTA:             {report['cta']}")
    print(f"Disclosure:      {report['disclosure']}")
    print("=" * 60)


if __name__ == "__main__":
    main()
