"""Researcher/RAG: extract claims ONLY from files in data/, with source + page/section.

Pipeline: read files -> split into passages (with page/section locators) -> rank by keyword
overlap -> LLM proposes facts with verbatim quotes -> CODE verifies every quote against the
passage text. Unverifiable claims are rejected and recorded, never silently kept.
"""
from __future__ import annotations

import json
import math
import re
from pathlib import Path

from pydantic import BaseModel

from core.brief import Brief
from core.prompts import load_prompt
from core.schemas import ExtractedFact, Fact, FactsOutput, RejectedClaim, ResearchDraft
from core.validators import invented_specifics, norm

PROMPT_VERSION = "v1"
SUPPORTED = {".txt", ".md", ".pdf"}
MAX_PASSAGES, MAX_PASSAGE_CHARS, MAX_CHUNK_CHARS, MAX_FACTS = 10, 1500, 1200, 12
STOPWORDS = set("the and for with that this from are was were has have had you your our their its into about "
                "what when where which who will can not but all any more most than then them they these those "
                "his her she him out one two over under also just how why a an of in on to is it as at by be or".split())


class Passage(BaseModel):
    id: str
    file: str
    locator: str
    text: str


class ResearcherInput(BaseModel):
    brief: Brief
    data_dir: str
    seed: int = 42


# ------------------------------------------------------------------ reading files
def discover_files(data_dir: Path) -> tuple[list[Path], list[str]]:
    """Supported source files (README/dotfiles ignored) and names of skipped unsupported files."""
    if not data_dir.is_dir():
        return [], []
    files, skipped = [], []
    for p in sorted(data_dir.rglob("*")):
        if not p.is_file() or p.name.startswith(".") or p.name.lower().startswith("readme"):
            continue
        (files if p.suffix.lower() in SUPPORTED else skipped).append(p if p.suffix.lower() in SUPPORTED else p.name)
    return files, skipped


def _paragraph_chunks(text: str, locator_prefix: str) -> list[tuple[str, str]]:
    paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks, buf, start = [], "", 1
    for i, para in enumerate(paras, 1):
        if buf and len(buf) + len(para) > MAX_CHUNK_CHARS:
            chunks.append((f"{locator_prefix} {start}-{i - 1}" if i - 1 > start else f"{locator_prefix} {start}", buf))
            buf, start = "", i
        buf = f"{buf}\n\n{para}".strip()
    if buf:
        end = len(paras)
        chunks.append((f"{locator_prefix} {start}-{end}" if end > start else f"{locator_prefix} {start}", buf))
    return chunks


def _markdown_chunks(text: str) -> list[tuple[str, str]]:
    sections, heading, lines = [], "(top of file)", []
    for line in text.splitlines():
        if line.lstrip().startswith("#"):
            if "".join(lines).strip():
                sections.append((heading, "\n".join(lines)))
            heading, lines = line.lstrip("# ").strip() or heading, []
        else:
            lines.append(line)
    if "".join(lines).strip():
        sections.append((heading, "\n".join(lines)))
    out = []
    for head, body in sections:
        for _, chunk in _paragraph_chunks(body, "para"):
            out.append((f"section: {head}", chunk))
    return out


def _pdf_chunks(path: Path) -> list[tuple[str, str]]:
    try:
        import pymupdf
    except ImportError as e:  # pragma: no cover
        raise RuntimeError("PDF support needs PyMuPDF: pip install -r requirements.txt") from e
    out = []
    with pymupdf.open(path) as doc:
        for page_no, page in enumerate(doc, 1):
            for _, chunk in _paragraph_chunks(page.get_text(), "para"):
                out.append((f"p.{page_no}", chunk))
    return out


def load_passages(files: list[Path], data_dir: Path) -> list[Passage]:
    passages: list[Passage] = []
    for f in files:
        suffix = f.suffix.lower()
        if suffix == ".pdf":
            chunks = _pdf_chunks(f)
        else:
            text = f.read_text(encoding="utf-8", errors="replace")
            chunks = _markdown_chunks(text) if suffix == ".md" else _paragraph_chunks(text, "para")
        name = f.relative_to(data_dir).as_posix()
        for locator, text in chunks:
            passages.append(Passage(id=f"P{len(passages) + 1}", file=name, locator=locator, text=text))
    return passages


# ------------------------------------------------------------------ retrieval
def tokenize(text: str) -> list[str]:
    return [t for t in re.findall(r"[a-z][a-z0-9]{2,}", text.lower()) if t not in STOPWORDS]


def rank_passages(passages: list[Passage], query: str, k: int = MAX_PASSAGES) -> list[Passage]:
    """Tiny TF-IDF-style keyword ranking. Returns [] when nothing overlaps."""
    q = set(tokenize(query))
    sets = [set(tokenize(p.text)) for p in passages]
    n = len(passages)
    idf = {t: math.log(1 + n / (1 + sum(t in s for s in sets))) for t in q}
    scored = [(sum(idf[t] for t in q & s), i) for i, s in enumerate(sets)]
    scored = [x for x in scored if x[0] > 0]
    scored.sort(key=lambda x: (-x[0], x[1]))
    return [passages[i] for _, i in scored[:k]]


# ------------------------------------------------------------------ verification
def verify_facts(extracted: list[ExtractedFact], passages: list[Passage]) -> tuple[list[Fact], list[RejectedClaim]]:
    by_id = {p.id: p for p in passages}
    facts: list[Fact] = []
    rejected: list[RejectedClaim] = []
    seen: set[str] = set()
    for ef in extracted:
        p = by_id.get(ef.passage_id)
        reason = None
        if p is None:
            reason = f"unknown passage id {ef.passage_id!r}"
        elif len(norm(ef.quote).split()) < 3:
            reason = "quote shorter than 3 words"
        elif norm(ef.quote) not in norm(p.text):
            reason = "quote not found verbatim in the cited passage"
        elif invented_specifics(ef.claim, ef.quote):
            reason = f"claim contains figures/contacts not in the quote: {invented_specifics(ef.claim, ef.quote)}"
        elif norm(ef.claim) in seen:
            reason = "duplicate claim"
        if reason:
            rejected.append(RejectedClaim(claim=ef.claim, reason=reason))
            continue
        seen.add(norm(ef.claim))
        if len(facts) < MAX_FACTS:
            facts.append(Fact(id=f"F{len(facts) + 1}", claim=ef.claim.strip(), origin="document",
                              source_file=p.file, locator=p.locator, quote=ef.quote.strip()))
    return facts, rejected


def brief_facts(brief: Brief) -> list[Fact]:
    """Statements the brief itself supplies (key messages, must-include items)."""
    out = []
    for i, msg in enumerate(brief.key_messages):
        out.append(Fact(id=f"B{len(out) + 1}", claim=msg, origin="brief",
                        source_file=f"brief:{brief.brief_id}", locator=f"key_messages[{i}]"))
    for i, msg in enumerate(brief.must_include):
        out.append(Fact(id=f"B{len(out) + 1}", claim=msg, origin="brief",
                        source_file=f"brief:{brief.brief_id}", locator=f"must_include[{i}]"))
    return out


# ------------------------------------------------------------------ agent entry
def run(inp: ResearcherInput, llm, log=None) -> FactsOutput:
    brief, data_dir = inp.brief, Path(inp.data_dir)
    b_facts = brief_facts(brief)
    files, skipped = discover_files(data_dir)
    missing = [f"Unsupported file type skipped: {n}" for n in skipped]

    if not files:
        missing.append(f"No official source documents found in {data_dir.name}/. Institutional claims are "
                       "limited to statements supplied by the brief; add the faculty documents and re-run.")
        _log(log, "no_sources", data_dir=str(data_dir))
        return FactsOutput(official_sources_present=False, facts=b_facts, missing_info=missing)

    passages = load_passages(files, data_dir)
    names = sorted({p.file for p in passages}) or [f.name for f in files]
    if not passages:
        missing.append("Source files contain no extractable text (scanned PDF?).")
        return FactsOutput(official_sources_present=True, sources_scanned=names, facts=b_facts, missing_info=missing)

    query = " ".join([brief.title, brief.topic, brief.objective, *brief.key_messages, *brief.must_include])
    selected = rank_passages(passages, query)
    if not selected:
        selected = passages[:MAX_PASSAGES]
        missing.append("No passage matched the brief's keywords; the first passages were used instead.")
    _log(log, "retrieval", passages_total=len(passages), passages_selected=len(selected))

    system, _ = load_prompt("researcher", PROMPT_VERSION)
    user = json.dumps({
        "brief": {"title": brief.title, "topic": brief.topic, "objective": brief.objective,
                  "audience": brief.audience, "key_messages": brief.key_messages},
        "passages": [{"id": p.id, "file": p.file, "locator": p.locator, "text": p.text[:MAX_PASSAGE_CHARS]}
                     for p in selected]}, ensure_ascii=False)
    draft: ResearchDraft = llm.chat_json("researcher", system, user, ResearchDraft, seed=inp.seed)

    facts, rejected = verify_facts(draft.facts, passages)
    for r in rejected:
        _log(log, "claim_rejected", claim=r.claim[:200], reason=r.reason)
    missing += draft.missing_info
    if not facts:
        missing.append("No verifiable claims could be extracted from the source documents.")
    return FactsOutput(official_sources_present=True, sources_scanned=names, passages_considered=len(passages),
                       facts=[*facts, *b_facts], rejected_claims=rejected, missing_info=missing)


def _log(log, status, **fields):
    if log:
        log.event("researcher", status, **fields)
