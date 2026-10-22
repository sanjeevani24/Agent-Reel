import pymupdf
from pathlib import Path

from agents import researcher
from core.brief import Brief
from tests.helpers import FakeLLM

BRIEF = Brief(brief_id="T1", title="Lab day", topic="robotics lab", objective="promote the robotics lab",
              audience="students", key_messages=["Students build agents."])
DOC = ("# Robotics Lab\n\nThe robotics lab is open to all engineering students every weekday.\n\n"
       "# Contact\n\nEmail the coordinator for details.\n")


def _run(tmp_path, llm):
    return researcher.run(researcher.ResearcherInput(brief=BRIEF, data_dir=str(tmp_path / "data")), llm)


def test_no_documents_means_no_llm_call_and_clear_flag(tmp_path):
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "README.md").write_text("instructions only")   # must be ignored
    llm = FakeLLM({"researcher": [{"facts": []}]})
    out = _run(tmp_path, llm)
    assert llm.calls == 0
    assert out.official_sources_present is False
    assert any("No official source documents" in m for m in out.missing_info)
    assert [f.origin for f in out.facts] == ["brief"] and out.facts[0].id == "B1"


def test_verified_fact_keeps_source_and_section(tmp_path):
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "fact_sheet.md").write_text(DOC)
    llm = FakeLLM({"researcher": [{"facts": [{
        "passage_id": "P1", "claim": "The lab is open to all engineering students on weekdays.",
        "quote": "open to all engineering students every weekday"}]}]})
    out = _run(tmp_path, llm)
    doc_facts = [f for f in out.facts if f.origin == "document"]
    assert len(doc_facts) == 1
    assert doc_facts[0].source_file == "fact_sheet.md" and doc_facts[0].locator == "section: Robotics Lab"
    assert out.official_sources_present and out.rejected_claims == []


def test_fabricated_and_unquoted_claims_are_rejected(tmp_path):
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "fact_sheet.md").write_text(DOC)
    llm = FakeLLM({"researcher": [{"facts": [
        {"passage_id": "P1", "claim": "The lab was founded in the year 1999.",
         "quote": "founded in the year 1999"},                                   # quote not in source
        {"passage_id": "P1", "claim": "Open to students, with 40 machines.",
         "quote": "open to all engineering students"},                            # number not in quote
        {"passage_id": "P9", "claim": "Ghost passage.", "quote": "a b c d"},       # unknown passage
        {"passage_id": "P1", "claim": "Too short quote.", "quote": "open to"}]}]})
    out = _run(tmp_path, llm)
    assert [f for f in out.facts if f.origin == "document"] == []
    reasons = " | ".join(r.reason for r in out.rejected_claims)
    assert "not found verbatim" in reasons and "not in the quote" in reasons
    assert "unknown passage" in reasons and "shorter than 3 words" in reasons
    assert any("No verifiable claims" in m for m in out.missing_info)


def test_pdf_page_reference(tmp_path):
    (tmp_path / "data").mkdir()
    doc = pymupdf.open()
    doc.new_page().insert_text((72, 72), "Cover page")
    doc.new_page().insert_text((72, 72), "Robotics lab opens at the engineering block for all students.")
    doc.save(tmp_path / "data" / "brochure.pdf")
    llm = FakeLLM({"researcher": [{"facts": [{
        "passage_id": "P2", "claim": "The robotics lab is open to all students.",
        "quote": "lab opens at the engineering block"}]}]})
    out = _run(tmp_path, llm)
    fact = [f for f in out.facts if f.origin == "document"][0]
    assert (fact.source_file, fact.locator) == ("brochure.pdf", "p.2")
