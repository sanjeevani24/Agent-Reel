import csv
import json
from pathlib import Path

from PIL import Image

from agents import asset_generator, editor, planner, scriptwriter, storyboarder
from core.brief import DISCLOSURE_LINE, load_brief
from core.schemas import FactsOutput, Fact, Plan
from tests.helpers import FakeLLM, default_responses, planner_out, script_out, storyboard_out

ROOT = Path(__file__).resolve().parent.parent
BRIEF = load_brief(ROOT / "briefs" / "practice.yaml")
FACTS = FactsOutput(official_sources_present=False, facts=[
    Fact(id="B1", claim="Students build working multi-agent AI systems.", origin="brief", source_file="brief:P00")])


def make_plan():
    llm = FakeLLM({"planner": [planner_out()]})
    return planner.run(planner.PlannerInput(brief=BRIEF, seed=42), llm), llm


def make_script(plan, **kw):
    llm = FakeLLM({"scriptwriter": [script_out(**kw)]})
    return scriptwriter.run(scriptwriter.ScriptwriterInput(brief=BRIEF, plan=plan, facts=FACTS), llm), llm


def make_storyboard(plan, script, raw=None):
    llm = FakeLLM({"storyboarder": [raw or storyboard_out()]})
    return storyboarder.run(storyboarder.StoryboarderInput(
        brief=BRIEF, plan=plan, script=script, allowed_text=scriptwriter.allowed_text(BRIEF, FACTS)), llm)


def test_planner_code_enforces_video_spec_and_budget():
    plan, llm = make_plan()
    assert isinstance(plan, Plan) and llm.agents_called() == ["planner"]
    assert (plan.video.width, plan.video.height, plan.video.fps) == (1080, 1920, 30)
    assert [s.name for s in plan.stages][0] == "planner" and len(plan.stages) == 7
    assert plan.cost_budget.max_repair_loops == 3 and plan.human_review_required is False


def test_scriptwriter_assigns_ids_metrics_and_no_issues():
    plan, _ = make_plan()
    script, _ = make_script(plan)
    assert [s.id for s in script.segments] == [f"seg{i}" for i in range(1, 7)]
    assert script.word_count == 96 and script.estimated_narration_s == 38.4
    assert script.hook == script.segments[0].narration and script.issues == []
    assert "seg1 (hook)" in scriptwriter.to_markdown(script)


def test_scriptwriter_validates_duration():
    plan, _ = make_plan()
    script, _ = make_script(plan, words_each=6)
    assert "SCRIPT_DURATION" in {i.code for i in script.issues}


def test_scriptwriter_feedback_reaches_the_prompt():
    plan, _ = make_plan()
    script, _ = make_script(plan)
    from core.schemas import Issue
    fb = [Issue(code="INVENTED_SPECIFICS", severity="factual", stage="scriptwriter", message="remove 500")]
    llm = FakeLLM({"scriptwriter": [script_out()]})
    scriptwriter.run(scriptwriter.ScriptwriterInput(brief=BRIEF, plan=plan, facts=FACTS, feedback=fb,
                                                    previous=script), llm)
    sent = json.loads(llm.history[0][1])
    assert sent["critic_feedback"][0]["code"] == "INVENTED_SPECIFICS" and "previous_script" in sent


def test_storyboard_derives_timing_narration_and_disclosure():
    plan, _ = make_plan()
    script, _ = make_script(plan)
    sb = make_storyboard(plan, script)
    assert len(sb.shots) == 6 and sb.total_duration_s == 42.0
    assert sb.shots[0].narration == script.segments[0].narration and sb.shots[1].start_s == 7.0
    assert sb.shots[-1].disclosure_text == DISCLOSURE_LINE and sb.shots[0].disclosure_text == ""
    assert sb.issues == []


def test_storyboard_flags_missing_segment_coverage():
    plan, _ = make_plan()
    script, _ = make_script(plan)
    ids = [[f"seg{i}"] for i in (1, 2, 3, 4, 5, 5)]        # seg6 never used, seg5 twice
    sb = make_storyboard(plan, script, storyboard_out(ids=ids))
    assert "SEGMENT_COVERAGE" in {i.code for i in sb.issues}


def test_asset_generator_creates_real_pngs_and_honest_manifest(tmp_path):
    plan, _ = make_plan()
    script, _ = make_script(plan)
    sb = make_storyboard(plan, script)
    m = asset_generator.run(asset_generator.AssetGenInput(brief=BRIEF, storyboard=sb, spec=plan.video, root=str(tmp_path)))
    images = [a for a in m.assets if a.kind == "image"]
    assert len(images) == 6 and all(a.status == "generated" for a in images)
    for a in images:
        with Image.open(tmp_path / a.path) as im:
            assert im.size == (1080, 1920)
    status = {a.kind: a.status for a in m.assets if a.kind != "image"}
    assert status == {"voiceover": "planned", "subtitles": "planned", "music": "omitted"}
    assert not (tmp_path / "assets/generated/P00/voiceover.mp3").exists()
    rows = list(csv.DictReader(open(tmp_path / "assets" / "manifest.csv")))
    assert len(rows) == 9 and {"asset_path", "source", "licence_status", "intended_use"} <= set(rows[0])


def test_editor_never_claims_a_rendered_video(tmp_path):
    plan, _ = make_plan()
    script, _ = make_script(plan)
    sb = make_storyboard(plan, script)
    m = asset_generator.run(asset_generator.AssetGenInput(brief=BRIEF, storyboard=sb, spec=plan.video, root=str(tmp_path)))
    e = editor.run(editor.EditorInput(brief=BRIEF, storyboard=sb, manifest=m, spec=plan.video, root=str(tmp_path)))
    assert e.render_status == "not_rendered" and e.final_video_path is None and e.ready_for_render
    assert e.pending_assets == ["voiceover", "subtitles"] and e.end_card["disclosure_text"] == DISCLOSURE_LINE
    assert e.clips[-1].end_s == 42.0 and e.output_spec.fps == 30
    (tmp_path / m.assets[2].path).unlink()                    # remove an asset -> blocker reported
    e2 = editor.run(editor.EditorInput(brief=BRIEF, storyboard=sb, manifest=m, spec=plan.video, root=str(tmp_path)))
    assert not e2.ready_for_render and "S03" in e2.blockers[0]
