from pathlib import Path

from agents import asset_generator, critic, editor
from tests.helpers import FakeLLM, critic_out, script_out, storyboard_out
from tests.test_agents import BRIEF, FACTS, make_plan, make_script, make_storyboard

ROOT = Path(__file__).resolve().parent.parent


def build(tmp_path, script_kw=None, sb_raw=None, brief=BRIEF):
    plan, _ = make_plan()
    script, _ = make_script(plan, **(script_kw or {}))
    sb = make_storyboard(plan, script, sb_raw)
    m = asset_generator.run(asset_generator.AssetGenInput(brief=BRIEF, storyboard=sb, spec=plan.video, root=str(tmp_path)))
    e = editor.run(editor.EditorInput(brief=BRIEF, storyboard=sb, manifest=m, spec=plan.video, root=str(tmp_path)))
    return dict(brief=brief, plan=plan, facts=FACTS, script=script, storyboard=sb, manifest=m, edit_plan=e,
                root=str(tmp_path))


def review(tmp_path, llm_out=None, **kw):
    llm = FakeLLM({"critic": [llm_out or critic_out()]})
    return critic.run(critic.CriticInput(**build(tmp_path, **kw)), llm), llm


def codes(qa):
    return {i.code for i in qa.issues}


def test_clean_run_is_pass_with_warning_only_for_absent_sources(tmp_path):
    qa, llm = review(tmp_path)
    assert llm.agents_called() == ["critic"]
    assert qa.status == "PASS_WITH_WARNINGS" and codes(qa) == {"SOURCES_ABSENT"}
    src = qa.issues[0]
    assert src.severity == "soft" and src.repairable is False


def test_unsupported_claim_is_factual_failure_routed_to_scriptwriter(tmp_path):
    qa, _ = review(tmp_path, script_kw={"ungrounded": True})
    assert qa.status == "FAIL"
    i = next(i for i in qa.issues if i.code == "UNGROUNDED_SEGMENT")
    assert (i.severity, i.stage, i.repairable) == ("factual", "scriptwriter", True)


def test_invented_number_in_script_fails(tmp_path):
    qa, _ = review(tmp_path, script_kw={"bad_number": True})
    assert qa.status == "FAIL" and "INVENTED_SPECIFICS" in codes(qa)


def test_llm_review_claims_become_factual_issues_and_route_by_location(tmp_path):
    out = critic_out(unsupported=[{"location": "seg3", "text": "best lab in India", "reason": "no source"},
                                  {"location": "S02", "text": "award-winning", "reason": "no source"}],
                     safety=[{"location": "seg2", "text": "call us", "reason": "contact implied"}])
    qa, _ = review(tmp_path, llm_out=out)
    by = {(i.code, i.location): i.stage for i in qa.issues}
    assert by[("LLM_UNSUPPORTED_CLAIM", "seg3")] == "scriptwriter"
    assert by[("LLM_UNSUPPORTED_CLAIM", "S02")] == "storyboarder"
    assert qa.status == "FAIL" and all(i.severity == "factual" for i in qa.issues if i.code.startswith("LLM_"))


def test_duration_mismatch_is_hard(tmp_path):
    qa, _ = review(tmp_path, script_kw={"words_each": 8})
    assert qa.status == "FAIL" and "SCRIPT_DURATION" in codes(qa)
    assert next(i for i in qa.issues if i.code == "SCRIPT_DURATION").severity == "hard"


def test_missing_asset_routes_to_asset_generator(tmp_path):
    kw = build(tmp_path)
    (tmp_path / kw["manifest"].assets[1].path).unlink()
    qa = critic.run(critic.CriticInput(**kw), FakeLLM({"critic": [critic_out()]}))
    miss = next(i for i in qa.issues if i.code == "ASSET_MISSING")
    assert miss.stage == "asset_generator" and miss.severity == "hard" and qa.status == "FAIL"


def test_missing_disclosure_is_flagged(tmp_path):
    kw = build(tmp_path)
    kw["storyboard"].shots[-1].disclosure_text = ""
    qa = critic.run(critic.CriticInput(**kw), FakeLLM({"critic": [critic_out()]}))
    assert "DISCLOSURE" in codes(qa) and qa.status == "FAIL"


def test_sensitive_brief_stops_at_human_review(tmp_path):
    sensitive = BRIEF.model_copy(update={"title": "Anti-ragging awareness"})
    kw = build(tmp_path, brief=sensitive)
    qa = critic.run(critic.CriticInput(**kw), FakeLLM({"critic": [critic_out()]}))
    assert qa.status == "PENDING_HUMAN_REVIEW" and qa.human_review_required


def test_long_on_screen_text_is_soft_only(tmp_path):
    raw = storyboard_out()
    raw["shots"][0]["on_screen_text"] = "x " * 60
    qa, _ = review(tmp_path, sb_raw=raw)
    i = next(i for i in qa.issues if i.code == "ON_SCREEN_TEXT")
    assert i.severity == "soft" and qa.status == "PASS_WITH_WARNINGS"
