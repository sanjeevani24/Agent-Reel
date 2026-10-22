"""Deterministic checks shared by the agents and the Critic (no LLM involved)."""
from __future__ import annotations

import math
import re

from core.schemas import Issue, ScriptDraft, StoryboardOutput, VideoSpec

WORDS_PER_SECOND = 2.5          # ~150 wpm narration pace
MAX_ON_SCREEN_CHARS = 80
_NUMBER = re.compile(r"\d+(?:[.,]\d+)*")
_EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
_URL = re.compile(r"(?:https?://|www\.)\S+", re.I)


def norm(text: str) -> str:
    """Lower-case, strip punctuation, collapse spaces (for tolerant text matching)."""
    return " ".join(re.sub(r"[^\w]+", " ", text.lower()).split())


def word_count(text: str) -> int:
    return len(re.findall(r"[\w']+", text))


def estimate_seconds(words: int) -> float:
    return round(words / WORDS_PER_SECOND, 2)


def word_range(spec: VideoSpec) -> tuple[int, int]:
    return math.ceil(spec.min_duration_s * WORDS_PER_SECOND), math.floor(spec.max_duration_s * WORDS_PER_SECOND)


def specifics(text: str) -> set[str]:
    """Numbers, e-mails and URLs: the things that must never be invented."""
    found = {m.rstrip(".,") for m in _NUMBER.findall(text)}
    found |= {m.lower() for m in _EMAIL.findall(text)} | {m.lower() for m in _URL.findall(text)}
    return found


def invented_specifics(text: str, allowed_text: str) -> list[str]:
    allowed = specifics(allowed_text)
    return sorted(s for s in specifics(text) if s not in allowed)


def limit_caption(text: str, max_chars: int = 80) -> str:
    """Keep rendered on-screen captions readable and within the character limit."""
    text = " ".join((text or "").split())
    if len(text) <= max_chars:
        return text
    shortened = text[:max_chars - 1].rsplit(" ", 1)[0].rstrip()
    if not shortened:
        shortened = text[:max_chars - 1]
    return shortened + "…"


# ------------------------------------------------------------------ script checks
def script_issues(script: ScriptDraft, spec: VideoSpec, known_fact_ids: set[str],
                  allowed_text: str) -> list[Issue]:
    issues: list[Issue] = []
    segs = script.segments
    words = sum(word_count(s.narration) for s in segs)
    est = estimate_seconds(words)
    lo, hi = word_range(spec)
    if not spec.min_duration_s <= est <= spec.max_duration_s:
        issues.append(Issue(
            code="SCRIPT_DURATION", severity="hard", stage="scriptwriter",
            message=f"Narration is {words} words (~{est}s); allowed window is "
                    f"{spec.min_duration_s}-{spec.max_duration_s}s.",
            fix_hint=f"Rewrite so total narration is between {lo} and {hi} words."))

    problems = []
    if abs(segs[0].start_s) > 0.5:
        problems.append("first segment must start at 0s")
    for a, b in zip(segs, segs[1:]):
        if abs(b.start_s - a.end_s) > 0.5:
            problems.append(f"gap/overlap between {a.id or 'segment'} and {b.id or 'next segment'}")
    end = segs[-1].end_s
    if not spec.min_duration_s <= end <= spec.max_duration_s:
        problems.append(f"timeline ends at {end}s, outside {spec.min_duration_s}-{spec.max_duration_s}s")
    if problems:
        issues.append(Issue(code="SCRIPT_TIMELINE", severity="hard", stage="scriptwriter",
                            message="; ".join(problems),
                            fix_hint="Use contiguous timestamps starting at 0 and ending near the target duration."))

    for s in segs:
        loc = s.id or "segment"
        seg_s = estimate_seconds(word_count(s.narration))
        if seg_s > (s.end_s - s.start_s) * 1.35 + 0.5:
            issues.append(Issue(code="SEGMENT_FIT", severity="soft", stage="scriptwriter", location=loc,
                                message=f"{loc}: narration needs ~{seg_s}s but slot is {round(s.end_s - s.start_s, 2)}s.",
                                fix_hint="Shorten this segment or widen its time slot."))
        bad_ids = [f for f in s.fact_ids if f not in known_fact_ids]
        if bad_ids:
            issues.append(Issue(code="UNKNOWN_FACT_ID", severity="factual", stage="scriptwriter", location=loc,
                                message=f"{loc} cites fact ids that do not exist: {bad_ids}.",
                                fix_hint="Cite only ids from the provided facts list."))
        if s.makes_factual_claim and not [f for f in s.fact_ids if f in known_fact_ids]:
            issues.append(Issue(code="UNGROUNDED_SEGMENT", severity="factual", stage="scriptwriter", location=loc,
                                message=f"{loc} makes a factual claim without a supporting fact id.",
                                fix_hint="Remove the claim or rewrite it using a provided fact and cite its id."))
        inv = invented_specifics(s.narration, allowed_text)
        if inv:
            issues.append(Issue(code="INVENTED_SPECIFICS", severity="factual", stage="scriptwriter", location=loc,
                                message=f"{loc} contains numbers/contact details not present in any fact: {inv}.",
                                fix_hint="Remove these figures or contact details; never invent them."))
    return issues


# ------------------------------------------------------------------ storyboard checks
def storyboard_issues(sb: StoryboardOutput, script: ScriptDraft, spec: VideoSpec, disclosure: str,
                      allowed_text: str) -> list[Issue]:
    issues: list[Issue] = []
    if not 6 <= len(sb.shots) <= 10:
        issues.append(Issue(code="SHOT_COUNT", severity="hard", stage="storyboarder",
                            message=f"{len(sb.shots)} shots; 6-10 required.", fix_hint="Produce 6-10 shots."))

    seg_ids = [s.id for s in script.segments]
    used = [sid for shot in sb.shots for sid in shot.segment_ids]
    missing = [i for i in seg_ids if i not in used]
    unknown = [i for i in used if i not in seg_ids]
    dupes = sorted({i for i in used if used.count(i) > 1})
    if missing or unknown or dupes:
        issues.append(Issue(code="SEGMENT_COVERAGE", severity="hard", stage="storyboarder",
                            message=f"Shots must cover each script segment exactly once "
                                    f"(missing={missing}, unknown={unknown}, duplicated={dupes}).",
                            fix_hint="Assign every segment id to exactly one shot, in order."))

    script_ok = spec.min_duration_s <= script.segments[-1].end_s <= spec.max_duration_s
    if script_ok and not spec.min_duration_s <= sb.total_duration_s <= spec.max_duration_s:
        issues.append(Issue(code="STORYBOARD_DURATION", severity="hard", stage="storyboarder",
                            message=f"Shot durations sum to {sb.total_duration_s}s; window is "
                                    f"{spec.min_duration_s}-{spec.max_duration_s}s.",
                            fix_hint="Cover all script segments so the shot timeline matches the script."))

    for shot in sb.shots:
        text = shot.on_screen_text.strip()
        if not text or len(text) > MAX_ON_SCREEN_CHARS:
            issues.append(Issue(code="ON_SCREEN_TEXT", severity="soft", stage="storyboarder", location=shot.shot_id,
                                message=f"{shot.shot_id}: on-screen text must be 1-{MAX_ON_SCREEN_CHARS} characters "
                                        f"(is {len(text)}).",
                                fix_hint="Use a short, readable caption."))
        inv = invented_specifics(shot.on_screen_text, allowed_text)
        if inv:
            issues.append(Issue(code="INVENTED_SPECIFICS", severity="factual", stage="storyboarder",
                                location=shot.shot_id,
                                message=f"{shot.shot_id} on-screen text contains unsupported figures/contacts: {inv}.",
                                fix_hint="Remove them; on-screen text must not introduce new facts."))

    if not sb.shots or sb.shots[-1].disclosure_text != disclosure:
        issues.append(Issue(code="DISCLOSURE", severity="hard", stage="storyboarder",
                            message=f"Final shot must carry the exact disclosure line: {disclosure!r}.",
                            fix_hint="Put the exact disclosure line in the final shot's disclosure_text."))
    return issues
