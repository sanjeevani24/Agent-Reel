import json
from pathlib import Path

import pytest

from core import orchestrator as orch_mod
from core.brief import load_brief
from core.config import load_settings
from core.llm import LLMClient, LLMError
from core.orchestrator import Orchestrator
from core.runlog import RunLogger
from core.schemas import STAGES
from tests.helpers import (FakeLLM, FakeSDK, critic_out, default_responses, script_out, storyboard_out)

ROOT = Path(__file__).resolve().parent.parent
BRIEF = load_brief(ROOT / "briefs" / "practice.yaml")


def make(tmp_path, responses=None, llm=None, brief=BRIEF):
    llm = llm or FakeLLM(responses or default_responses())
    log = RunLogger(tmp_path / "logs", run_id="t", secrets=["gsk_topsecret"])
    return Orchestrator(brief, llm, log, root=tmp_path, seed=42), llm, log


def events(log):
    return [json.loads(x) for x in log.jsonl.read_text().splitlines()]


def test_stage_order_and_artifacts(tmp_path):
    o, llm, log = make(tmp_path)
    r = o.run()
    assert r.trace == STAGES                                    # exact required order, each once
    assert r.status == "PASS_WITH_WARNINGS" and r.exit_code == 0 and r.repairs_used == 0
    assert llm.agents_called() == ["planner", "scriptwriter", "storyboarder", "critic"]  # researcher: no docs -> no call
    for name in ["plan", "facts", "script", "storyboard", "asset_manifest", "edit_plan", "qa_report"]:
        assert (tmp_path / "outputs" / f"{name}.json").is_file(), name
    assert (tmp_path / "outputs" / "script.md").is_file()
    assert not list((tmp_path / "outputs").glob("*.mp4"))        # no fabricated video
    qa = json.loads((tmp_path / "outputs/qa_report.json").read_text())
    assert qa["final"] is True and qa["status"] == "PASS_WITH_WARNINGS"
    ev = events(log)
    starts = [e["agent"] for e in ev if e["status"] == "start" and e["agent"] in STAGES]
    ends = [e for e in ev if e["status"] == "end"]
    assert starts == STAGES and all("elapsed_s" in e and "output_path" in e for e in ends)


def test_unsupported_claim_triggers_targeted_repair_of_script_and_downstream_only(tmp_path):
    resp = default_responses()
    resp["scriptwriter"] = [script_out(ungrounded=True), script_out()]
    o, llm, log = make(tmp_path, resp)
    r = o.run()
    assert r.status == "PASS_WITH_WARNINGS" and r.repairs_used == 1
    assert r.trace == STAGES + STAGES[2:]                        # planner/researcher NOT re-run
    assert llm.agents_called().count("planner") == 1 and llm.agents_called().count("scriptwriter") == 2
    assert llm.agents_called().count("storyboarder") == 2 and llm.agents_called().count("critic") == 2
    sent = json.loads([u for a, u in llm.history if a == "scriptwriter"][1])
    assert sent["critic_feedback"][0]["code"] == "UNGROUNDED_SEGMENT" and "previous_script" in sent
    hist = r.qa.repair_history
    assert hist[0]["restart_from"] == "scriptwriter" and hist[0]["rerun_stages"] == STAGES[2:]
    assert (tmp_path / "outputs/qa_history/qa_iter_0.json").is_file() and (tmp_path / "outputs/qa_history/qa_iter_1.json").is_file()


def test_critic_feedback_for_storyboard_does_not_rerun_script(tmp_path):
    resp = default_responses()
    bad = critic_out(unsupported=[{"location": "S02", "text": "award-winning", "reason": "no source"}])
    resp["critic"] = [bad, critic_out()]
    o, llm, _ = make(tmp_path, resp)
    r = o.run()
    assert r.trace == STAGES + STAGES[3:] and r.repairs_used == 1
    assert llm.agents_called().count("scriptwriter") == 1
    sent = json.loads([u for a, u in llm.history if a == "storyboarder"][1])
    assert sent["critic_feedback"][0]["code"] == "LLM_UNSUPPORTED_CLAIM"


def test_missing_asset_reruns_only_asset_generator_onward(tmp_path, monkeypatch):
    real = orch_mod.asset_generator.run
    calls = {"n": 0}

    def flaky(inp, llm=None, log=None):
        m = real(inp, llm, log)
        calls["n"] += 1
        if calls["n"] == 1:                                       # first attempt loses a file
            (Path(inp.root) / m.assets[0].path).unlink()
        return m
    monkeypatch.setattr(orch_mod.asset_generator, "run", flaky)
    o, llm, _ = make(tmp_path)
    r = o.run()
    assert r.trace == STAGES + ["asset_generator", "editor", "critic"] and r.repairs_used == 1
    assert llm.agents_called().count("scriptwriter") == 1 and llm.agents_called().count("storyboarder") == 1
    assert r.status == "PASS_WITH_WARNINGS"


def test_repair_loop_is_capped_at_three_and_fails_safely(tmp_path):
    resp = default_responses()
    resp["scriptwriter"] = [script_out(ungrounded=True)]          # never gets better
    o, llm, log = make(tmp_path, resp)
    r = o.run()
    assert r.repairs_used == 3 and r.status == "FAIL" and r.exit_code == 1
    assert llm.agents_called().count("scriptwriter") == 4           # 1 initial + 3 repairs, never a 5th
    qa = json.loads((tmp_path / "outputs/qa_report.json").read_text())
    assert qa["status"] == "FAIL" and "stopped safely" in qa["summary"] and len(qa["repair_history"]) == 3
    assert [e for e in events(log) if e["status"] == "failed"] == []   # a QA fail is a result, not a crash


def test_sensitive_brief_ends_in_pending_human_review(tmp_path):
    sensitive = BRIEF.model_copy(update={"title": "Anti-ragging awareness"})
    o, _, _ = make(tmp_path, brief=sensitive)
    r = o.run()
    assert r.status == "PENDING_HUMAN_REVIEW" and r.exit_code == 3


def test_api_error_gives_diagnostic_nonzero_exit_and_scrubbed_logs(tmp_path):
    s = load_settings(env={"GROQ_API_KEY": "gsk_topsecret"})
    log = RunLogger(tmp_path / "logs", run_id="t", secrets=[s.api_key])
    llm = LLMClient(s, log, FakeSDK([Exception("401 invalid key gsk_topsecret")]))
    (tmp_path / "outputs").mkdir()
    (tmp_path / "outputs/plan.json").write_text("{stale}")          # leftovers from an old run
    r = Orchestrator(BRIEF, llm, log, root=tmp_path).run()
    assert r.status == "LLM_ERROR" and r.exit_code == 4 and "gsk_topsecret" not in r.error
    assert not (tmp_path / "outputs/plan.json").exists()             # stale artifact removed
    report = json.loads((tmp_path / "outputs/error_report.json").read_text())
    assert report["last_stage"] == "planner" and "gsk_topsecret" not in json.dumps(report)
    text = log.jsonl.read_text()
    assert "gsk_topsecret" not in text
    kinds = {(e["agent"], e["status"]) for e in events(log)}
    assert ("planner", "error") in kinds and ("run", "failed") in kinds
    assert r.trace == ["planner"]                                    # nothing after the failure ran


def test_unexpected_stage_crash_is_logged_and_nonzero(tmp_path):
    o, _, log = make(tmp_path)
    o.runners["storyboarder"] = lambda fb: (_ for _ in ()).throw(RuntimeError("kaboom"))
    r = o.run()
    assert r.status == "ERROR" and r.exit_code == 5 and "storyboarder failed" in r.error
    assert r.trace[-1] == "storyboarder"
    assert any(e["agent"] == "storyboarder" and e["status"] == "error" for e in events(log))


def test_budget_guard_stops_runaway_usage(tmp_path):
    llm = FakeLLM(default_responses())
    llm.completion_tokens = 1_000_000
    o, _, _ = make(tmp_path, llm=llm)
    r = o.run()
    assert r.status == "ERROR" and "Budget exceeded" in r.error and r.trace == ["planner"]


def test_invalid_llm_output_is_not_silently_replaced(tmp_path):
    resp = default_responses()
    resp["planner"] = [LLMError("planner: output failed validation after 2 attempts")]
    o, _, _ = make(tmp_path, resp)
    r = o.run()
    assert r.exit_code == 4 and r.qa is None
