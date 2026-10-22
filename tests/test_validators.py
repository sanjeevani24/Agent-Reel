from core.schemas import ScriptDraft, VideoSpec
from core.validators import (estimate_seconds, invented_specifics, norm, script_issues, word_count, word_range)
from tests.helpers import script_out

SPEC = VideoSpec.for_target(40)


def codes(issues):
    return {i.code for i in issues}


def test_word_and_duration_math():
    assert word_count("Hello, it's a test.") == 4
    assert estimate_seconds(100) == 40.0
    assert word_range(SPEC) == (88, 112)


def test_good_script_has_no_issues():
    s = ScriptDraft.model_validate(script_out())
    for i, seg in enumerate(s.segments, 1):
        seg.id = f"seg{i}"
    assert script_issues(s, SPEC, {"B1"}, "") == []


def test_duration_too_short_and_too_long_are_hard_failures():
    for words in (8, 30):  # 6 segs * 8 = 48 words (~19s); 6 * 30 = 180 words (~72s)
        s = ScriptDraft.model_validate(script_out(words_each=words, seg_len=7.0))
        found = [i for i in script_issues(s, SPEC, {"B1"}, "") if i.code == "SCRIPT_DURATION"]
        assert found and found[0].severity == "hard" and found[0].stage == "scriptwriter"


def test_timeline_gap_and_wrong_end():
    raw = script_out()
    raw["segments"][2]["start_s"] += 3          # gap
    s = ScriptDraft.model_validate(raw)
    assert "SCRIPT_TIMELINE" in codes(script_issues(s, SPEC, {"B1"}, ""))
    s = ScriptDraft.model_validate(script_out(seg_len=3.0))   # ends at 18s
    assert "SCRIPT_TIMELINE" in codes(script_issues(s, SPEC, {"B1"}, ""))


def test_unsupported_factual_claim_detection():
    s = ScriptDraft.model_validate(script_out(ungrounded=True))
    found = script_issues(s, SPEC, {"B1"}, "")
    assert "UNGROUNDED_SEGMENT" in codes(found)
    assert all(i.severity == "factual" for i in found if i.code == "UNGROUNDED_SEGMENT")
    s = ScriptDraft.model_validate(script_out(fact_ids=("F99",)))
    assert "UNKNOWN_FACT_ID" in codes(script_issues(s, SPEC, {"B1"}, ""))


def test_invented_numbers_and_contacts_detected_unless_in_facts():
    assert invented_specifics("Call 98765 now or mail a@b.com", "") == ["98765", "a@b.com"]
    assert invented_specifics("We have 500 labs", "Fact: 500 labs exist") == []
    s = ScriptDraft.model_validate(script_out(bad_number=True))
    assert "INVENTED_SPECIFICS" in codes(script_issues(s, SPEC, {"B1"}, "no digits here"))


def test_norm_is_punctuation_and_case_insensitive():
    assert norm("Hello,   WORLD!") == "hello world"
