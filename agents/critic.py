"""Critic/QA: deterministic checks + LLM claim review -> structured issues with a responsible stage.

Severity: hard (spec/structure/files), factual (grounding/safety), soft (quality).
The Critic never approves unsupported claims: any factual issue makes the iteration FAIL.
"""
from __future__ import annotations

import json
from pathlib import Path

from PIL import Image
from pydantic import BaseModel

from agents.scriptwriter import allowed_text
from core.brief import Brief
from core.prompts import load_prompt
from core.schemas import (BLOCKING, AssetManifest, CheckResult, CriticDraft, EditPlan, FactsOutput, Issue,
                          Plan, QAReport, ScriptOutput, StoryboardOutput, VideoSpec)
from core.validators import script_issues, storyboard_issues

PROMPT_VERSION = "v1"
CHECKS = [  # (check name, issue code)
    ("script duration", "SCRIPT_DURATION"), ("script timeline", "SCRIPT_TIMELINE"),
    ("segment timing fit", "SEGMENT_FIT"), ("fact ids exist", "UNKNOWN_FACT_ID"),
    ("claims grounded in facts", "UNGROUNDED_SEGMENT"), ("no invented numbers/contacts", "INVENTED_SPECIFICS"),
    ("LLM claim review", "LLM_UNSUPPORTED_CLAIM"), ("LLM safety review", "LLM_SAFETY_CONCERN"),
    ("shot count 6-10", "SHOT_COUNT"), ("segments covered by shots", "SEGMENT_COVERAGE"),
    ("storyboard duration", "STORYBOARD_DURATION"), ("on-screen text length", "ON_SCREEN_TEXT"),
    ("disclosure line", "DISCLOSURE"), ("assets exist", "ASSET_MISSING"), ("assets valid", "ASSET_INVALID"),
    ("edit plan ready", "EDIT_NOT_READY"), ("no false video claim", "EDIT_CLAIMS_VIDEO"),
    ("video file valid", "VIDEO_INVALID"), ("video duration valid", "VIDEO_DURATION"),
    ("official sources present", "SOURCES_ABSENT"),
]


class CriticInput(BaseModel):
    brief: Brief
    plan: Plan
    facts: FactsOutput
    script: ScriptOutput
    storyboard: StoryboardOutput
    manifest: AssetManifest
    edit_plan: EditPlan
    root: str
    iteration: int = 0
    seed: int = 42


def asset_issues(manifest: AssetManifest, sb: StoryboardOutput, plan: Plan, root: Path) -> list[Issue]:
    issues: list[Issue] = []
    images = {a.shot_id: a for a in manifest.assets if a.kind == "image" and a.status == "generated"}
    for shot in sb.shots:
        a = images.get(shot.shot_id)
        if a is None or not a.path or not (root / a.path).is_file() or (root / a.path).stat().st_size == 0:
            issues.append(Issue(code="ASSET_MISSING", severity="hard", stage="asset_generator", location=shot.shot_id,
                                message=f"{shot.shot_id}: image asset missing or empty.",
                                fix_hint="Regenerate the asset for this shot."))
            continue
        try:
            with Image.open(root / a.path) as im:
                size = im.size
        except Exception as e:  # corrupt file
            size = None
            issues.append(Issue(code="ASSET_INVALID", severity="hard", stage="asset_generator", location=shot.shot_id,
                                message=f"{shot.shot_id}: image unreadable ({e}).", fix_hint="Regenerate the asset."))
        if size and size != (plan.video.width, plan.video.height):
            issues.append(Issue(code="ASSET_INVALID", severity="hard", stage="asset_generator", location=shot.shot_id,
                                message=f"{shot.shot_id}: image is {size}, expected "
                                        f"{(plan.video.width, plan.video.height)}.", fix_hint="Regenerate at 1080x1920."))
    for a in manifest.assets:   # nothing may claim to be generated without existing on disk
        if a.kind != "image" and a.status == "generated" and not (a.path and (root / a.path).is_file()):
            issues.append(Issue(code="ASSET_MISSING", severity="hard", stage="asset_generator", location=a.asset_id,
                                message=f"{a.asset_id} is marked generated but the file does not exist.",
                                fix_hint="Generate it or mark it planned."))
    return issues


def probe_video(path: Path) -> dict | None:
    import subprocess
    try:
        r = subprocess.run(
            ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", "-show_streams", str(path)],
            capture_output=True, text=True, check=True, timeout=10)
        return json.loads(r.stdout)
    except Exception:
        return None


def video_issues(video_path: Path, spec: VideoSpec) -> list[Issue]:
    issues: list[Issue] = []
    if not video_path.is_file() or video_path.stat().st_size == 0:
        issues.append(Issue(code="VIDEO_INVALID", severity="hard", stage="editor",
                            message="Rendered video file is missing or empty.", repairable=False))
        return issues
    info = probe_video(video_path)
    if not info or "format" not in info:
        issues.append(Issue(code="VIDEO_INVALID", severity="hard", stage="editor",
                            message="Rendered video could not be parsed by ffprobe.", repairable=False))
        return issues

    fmt = info.get("format", {})
    dur = float(fmt.get("duration", 0.0))
    if not (spec.min_duration_s <= dur <= spec.max_duration_s):
        issues.append(Issue(code="VIDEO_DURATION", severity="hard", stage="editor",
                            message=f"Video duration is {dur:.2f}s, outside allowed {spec.min_duration_s}-{spec.max_duration_s}s.",
                            repairable=False))

    size_mb = int(fmt.get("size", 0)) / (1024 * 1024)
    if size_mb > spec.max_file_mb:
        issues.append(Issue(code="VIDEO_INVALID", severity="hard", stage="editor",
                            message=f"Video file size {size_mb:.1f}MB exceeds limit of {spec.max_file_mb}MB.",
                            repairable=False))

    streams = info.get("streams", [])
    v_streams = [s for s in streams if s.get("codec_type") == "video"]
    if not v_streams:
        issues.append(Issue(code="VIDEO_INVALID", severity="hard", stage="editor",
                            message="Video file has no video stream.", repairable=False))
    else:
        v = v_streams[0]
        if v.get("width") != spec.width or v.get("height") != spec.height:
            issues.append(Issue(code="VIDEO_INVALID", severity="hard", stage="editor",
                                message=f"Video resolution is {v.get('width')}x{v.get('height')}, expected {spec.width}x{spec.height}.",
                                repairable=False))
        if v.get("codec_name") != spec.video_codec:
            issues.append(Issue(code="VIDEO_INVALID", severity="hard", stage="editor",
                                message=f"Video codec is {v.get('codec_name')}, expected {spec.video_codec}.",
                                repairable=False))

    a_streams = [s for s in streams if s.get("codec_type") == "audio"]
    if a_streams:
        a = a_streams[0]
        if a.get("codec_name") != spec.audio_codec:
            issues.append(Issue(code="VIDEO_INVALID", severity="hard", stage="editor",
                                message=f"Audio codec is {a.get('codec_name')}, expected {spec.audio_codec}.",
                                repairable=False))
    return issues


def edit_issues(edit: EditPlan, root: Path, asset_problem: bool, spec: VideoSpec | None = None) -> list[Issue]:
    issues: list[Issue] = []
    if edit.final_video_path and not (root / edit.final_video_path).is_file():
        issues.append(Issue(code="EDIT_CLAIMS_VIDEO", severity="hard", stage="editor",
                            message="Edit plan names a final video that does not exist.", repairable=False))
    elif edit.render_status == "rendered" and edit.final_video_path and spec:
        issues.extend(video_issues(root / edit.final_video_path, spec))
    if edit.blockers and not asset_problem:
        issues.append(Issue(code="EDIT_NOT_READY", severity="hard", stage="editor", repairable=False,
                            message=f"Edit plan has blockers: {edit.blockers}"))
    return issues


def review_with_llm(inp: CriticInput, llm) -> CriticDraft:
    system, _ = load_prompt("critic", PROMPT_VERSION)
    user = json.dumps({
        "facts": [{"id": f.id, "claim": f.claim} for f in inp.facts.facts],
        "segments": [{"id": s.id, "narration": s.narration, "fact_ids": s.fact_ids} for s in inp.script.segments],
        "shots": [{"id": s.shot_id, "on_screen_text": s.on_screen_text} for s in inp.storyboard.shots]},
        ensure_ascii=False)
    return llm.chat_json("critic", system, user, CriticDraft, seed=inp.seed)


def llm_issues(review: CriticDraft) -> list[Issue]:
    def stage_of(loc: str) -> str:
        return "storyboarder" if loc.upper().startswith("S") and not loc.lower().startswith("seg") else "scriptwriter"
    out = []
    for c in review.unsupported_claims:
        out.append(Issue(code="LLM_UNSUPPORTED_CLAIM", severity="factual", stage=stage_of(c.location),
                         location=c.location, message=f"Unsupported claim in {c.location}: '{c.text}' ({c.reason})",
                         fix_hint="Remove it or rephrase using only the supplied facts."))
    for c in review.safety_concerns:
        out.append(Issue(code="LLM_SAFETY_CONCERN", severity="factual", stage=stage_of(c.location),
                         location=c.location, message=f"Safety concern in {c.location}: '{c.text}' ({c.reason})",
                         fix_hint="Remove the content or use neutral wording."))
    return out


def run(inp: CriticInput, llm, log=None) -> QAReport:
    root = Path(inp.root)
    allowed = allowed_text(inp.brief, inp.facts)
    issues = script_issues(inp.script, inp.plan.video, {f.id for f in inp.facts.facts}, allowed)
    issues += storyboard_issues(inp.storyboard, inp.script, inp.plan.video, inp.brief.disclosure_line, allowed)
    a_issues = asset_issues(inp.manifest, inp.storyboard, inp.plan, root)
    issues += a_issues + edit_issues(inp.edit_plan, root, bool(a_issues), inp.plan.video)
    if not inp.facts.official_sources_present:
        issues.append(Issue(code="SOURCES_ABSENT", severity="soft", stage="researcher", repairable=False,
                            message="No official source documents were supplied; only brief-provided statements "
                                    "could be used as facts.",
                            fix_hint="Add faculty documents to data/ and re-run."))
    review = review_with_llm(inp, llm)
    issues += llm_issues(review)

    checks = []
    for name, code in CHECKS:
        hits = [i for i in issues if i.code == code]
        sev = next((s for s in ("hard", "factual", "soft") if any(i.severity == s for i in hits)), None)
        checks.append(CheckResult(name=name, passed=not hits, severity=sev,
                                  detail="; ".join(i.message for i in hits)[:400]))

    blocking = [i for i in issues if i.severity in BLOCKING]
    if blocking:
        status = "FAIL"
    elif inp.brief.requires_human_review or inp.plan.human_review_required:
        status = "PENDING_HUMAN_REVIEW"
    elif issues:
        status = "PASS_WITH_WARNINGS"
    else:
        status = "PASS"
    summary = (f"{len(blocking)} blocking issue(s), {len(issues) - len(blocking)} warning(s)."
               if issues else "All checks passed.")
    return QAReport(brief_id=inp.brief.brief_id, iteration=inp.iteration, status=status, checks=checks,
                    issues=issues, human_review_required=inp.brief.requires_human_review,
                    llm_review=review, summary=summary)
