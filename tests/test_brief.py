from pathlib import Path

import pytest
from core.brief import BriefError, DISCLOSURE_LINE, load_brief

ROOT = Path(__file__).resolve().parent.parent
BASE = dict(brief_id="T1", title="t", topic="x", objective="o", audience="a")


def _write(tmp_path, text):
    p = tmp_path / "b.yaml"
    p.write_text(text, encoding="utf-8")
    return p


def test_practice_brief_loads():
    b = load_brief(ROOT / "briefs" / "practice.yaml")
    assert b.brief_id == "P00" and 30 <= b.duration_target_s <= 60
    assert b.disclosure_line == DISCLOSURE_LINE
    assert b.requires_human_review is False


def test_duration_out_of_range(tmp_path):
    p = _write(tmp_path, "brief_id: A\ntitle: t\ntopic: x\nobjective: o\naudience: a\nduration_target_s: 90\n")
    with pytest.raises(BriefError):
        load_brief(p)


def test_sensitive_topic_forces_review(tmp_path):
    p = _write(tmp_path, "brief_id: A\ntitle: Anti-ragging awareness\ntopic: x\nobjective: o\naudience: a\n")
    assert load_brief(p).requires_human_review is True


def test_bad_disclosure_rejected(tmp_path):
    p = _write(tmp_path, "brief_id: A\ntitle: t\ntopic: x\nobjective: o\naudience: a\ndisclosure_line: nope\n")
    with pytest.raises(BriefError):
        load_brief(p)


def test_missing_file_and_bad_id(tmp_path):
    with pytest.raises(BriefError):
        load_brief(tmp_path / "nope.yaml")
    p = _write(tmp_path, "brief_id: 'a/b'\ntitle: t\ntopic: x\nobjective: o\naudience: a\n")
    with pytest.raises(BriefError):
        load_brief(p)
