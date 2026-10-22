#!/usr/bin/env python3
"""AgentReel entry point.

    python run.py --brief briefs/practice.yaml --seed 42

Runs: Brief -> Planner -> Researcher -> Scriptwriter -> Storyboarder -> Asset Generator -> Editor -> Critic
(with a bounded repair loop). MILESTONE B: no video is rendered yet (that is Milestone C).

Exit codes: 0 ok | 1 QA failed (unsafe/unsupported) | 2 preflight error | 3 human review pending
            4 LLM/API error | 5 internal/budget error
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from core.brief import BriefError, load_brief
from core.config import ConfigError, load_settings
from core.llm import LLMClient
from core.orchestrator import Orchestrator
from core.runlog import RunLogger


def _print_summary(result, llm) -> None:
    print(f"\nStages run : {' -> '.join(result.trace)}")
    print(f"LLM usage  : {llm.calls} calls, {llm.prompt_tokens} prompt + {llm.completion_tokens} completion tokens "
          "(cost: see logs/cost_report.csv; 'unknown' unless prices are configured)")
    print(f"Repairs    : {result.repairs_used} of 3 used")
    if result.qa:
        print(f"QA status  : {result.status} - {result.qa.summary}")
        for i in result.qa.issues:
            print(f"   [{i.severity:7}] {i.code} ({i.stage}): {i.message}")
    if result.error:
        print(f"ERROR      : {result.error}", file=sys.stderr)
    if result.status in ("PASS", "PASS_WITH_WARNINGS", "PENDING_HUMAN_REVIEW"):
        print("Artifacts  : outputs/plan.json facts.json script.json script.md storyboard.json "
              "asset_manifest.json edit_plan.json qa_report.json")
        print("Note       : Milestone B produces NO video; render_status is 'not_rendered'.")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="AgentReel multi-agent video pipeline")
    ap.add_argument("--brief", required=True, help="Path to YAML brief")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--preflight-only", action="store_true", help="Validate config + brief, then stop")
    ap.add_argument("--no-key", action="store_true", help="Skip API key check (implies --preflight-only)")
    ap.add_argument("--render-only", action="store_true", help="Render video from existing outputs without calling LLMs")
    ap.add_argument("--render-v2", action="store_true", help="Render Upgrade V2 motion-graphics video without calling LLMs")
    ap.add_argument("--render-v3", action="store_true", help="Render Upgrade V3 (Final Submission Polish) video without calling LLMs")
    args = ap.parse_args(argv)
    preflight_only = args.preflight_only or args.no_key
    need_key = not (args.no_key or args.render_only or args.render_v2 or args.render_v3)

    try:
        settings = load_settings(require_key=need_key)
        brief = load_brief(args.brief)
    except (ConfigError, BriefError) as e:
        print(f"PREFLIGHT FAILED: {e}", file=sys.stderr)
        return 2

    log = RunLogger("logs", secrets=[settings.api_key] if settings.api_key else [])
    log.event("run", "preflight_ok", brief_id=brief.brief_id, seed=args.seed,
              model=settings.model, provider=settings.provider,
              requires_human_review=brief.requires_human_review)
    print(f"Settings : {settings}")
    print(f"Brief    : {brief.brief_id} - {brief.title} (target {brief.duration_target_s}s)")
    print(f"Review   : human review checkpoint {'REQUIRED' if brief.requires_human_review else 'not required'}")
    if preflight_only:
        print("Preflight complete (pipeline not run).")
        return 0

    if args.render_only:
        from agents.editor import render_pipeline
        print(f"\nRendering Milestone C video for {brief.brief_id} from existing outputs (no LLM calls)...")
        try:
            report = render_pipeline(Path.cwd(), brief, log=log)
            print(f"\nRender SUCCESS!")
            print(f"Video output : {report['final_video_path']} ({report['video_metrics']['duration_s']}s, "
                  f"{report['video_metrics']['width']}x{report['video_metrics']['height']}, "
                  f"{report['video_metrics']['video_codec']}/{report['video_metrics']['audio_codec']}, "
                  f"{report['video_metrics']['file_size_mb']}MB)")
            print(f"Subtitles    : {report['subtitles_path']}")
            print(f"Voiceover    : {report['voiceover_path']}")
            print(f"Screenshots  : {', '.join(report['preview_images'])}")
            print(f"Report       : outputs/render_report.json")
            return 0
        except Exception as e:
            print(f"RENDER FAILED: {e}", file=sys.stderr)
    if args.render_v2:
        from agents.renderer_v2 import render_motion_graphics_v2
        print(f"\nRendering AgentReel Upgrade V2 motion graphics video (no LLM calls)...")
        try:
            report = render_motion_graphics_v2(output_dir="outputs")
            print(f"\nRender V2 SUCCESS!")
            print(f"Video output : {report['outputs']['video']} ({report['duration_seconds']}s, "
                  f"{report['resolution']}, {report['video_codec']}/{report['audio_codec']}, "
                  f"{report['file_size_mb']}MB)")
            print(f"Subtitles    : {report['outputs']['subtitles']}")
            print(f"Previews     : {', '.join(report['outputs']['previews'])}")
            print(f"Report       : outputs/render_report_v2.json")
            return 0
        except Exception as e:
            print(f"RENDER V2 FAILED: {e}", file=sys.stderr)
            return 1

    if args.render_v3:
        from agents.renderer_v3 import render_motion_graphics_v3
        print(f"\nRendering AgentReel Upgrade V3 (Final Submission Polish) video (no LLM calls)...")
        try:
            report = render_motion_graphics_v3(output_dir="outputs")
            print(f"\nRender V3 SUCCESS!")
            print(f"Video output : {report['outputs']['video']} ({report['duration_seconds']}s, "
                  f"{report['resolution']}, {report['video_codec']}/{report['audio_codec']}, "
                  f"{report['file_size_mb']}MB)")
            print(f"Subtitles    : {report['outputs']['subtitles']}")
            print(f"Previews     : {', '.join(report['outputs']['previews'])}")
            print(f"Report       : outputs/render_report_v3.json")
            return 0
        except Exception as e:
            print(f"RENDER V3 FAILED: {e}", file=sys.stderr)
            return 1

    llm = LLMClient(settings, log)
    result = Orchestrator(brief, llm, log, root=Path.cwd(), seed=args.seed).run()
    _print_summary(result, llm)
    return result.exit_code


if __name__ == "__main__":
    sys.exit(main())
