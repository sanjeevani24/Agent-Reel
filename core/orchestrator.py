"""Orchestrator: Brief -> Planner -> Researcher -> Scriptwriter -> Storyboarder -> Asset Generator
-> Editor -> Critic, with a bounded, targeted repair loop (max 3).

Repair policy: the Critic names the responsible stage for each issue. We re-run the EARLIEST
responsible stage plus everything downstream of it (their inputs changed), and leave earlier
valid artifacts untouched. Each rerun stage receives only the issues assigned to it.
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path

from agents import (asset_generator, critic, editor, planner, researcher, scriptwriter, storyboarder)
from core.brief import Brief
from core.llm import LLMError
from core.runlog import RunLogger
from core.schemas import BLOCKING, STAGES, CostBudget, Issue, QAReport

ARTIFACT_FILES = {"planner": "plan.json", "researcher": "facts.json", "scriptwriter": "script.json",
                  "storyboarder": "storyboard.json", "asset_generator": "asset_manifest.json",
                  "editor": "edit_plan.json", "critic": "qa_report.json"}
PROMPT_STAGES = {"planner", "researcher", "scriptwriter", "storyboarder", "critic"}
EXIT_CODES = {"PASS": 0, "PASS_WITH_WARNINGS": 0, "FAIL": 1, "PENDING_HUMAN_REVIEW": 3,
              "LLM_ERROR": 4, "ERROR": 5}


class StageError(RuntimeError):
    pass


class BudgetExceeded(RuntimeError):
    pass


@dataclass
class RunResult:
    status: str
    exit_code: int
    qa: QAReport | None = None
    error: str | None = None
    repairs_used: int = 0
    trace: list[str] = field(default_factory=list)


class Orchestrator:
    def __init__(self, brief: Brief, llm, log: RunLogger, root: Path | None = None,
                 seed: int = 42, max_repairs: int = 3):
        self.brief, self.llm, self.log, self.seed = brief, llm, log, seed
        self.root = Path(root or Path.cwd())
        self.out = self.root / "outputs"
        self.max_repairs = max_repairs
        self.art: dict = {}
        self.trace: list[str] = []
        self.loops = 0
        self.runners = {"planner": self._planner, "researcher": self._researcher,
                        "scriptwriter": self._scriptwriter, "storyboarder": self._storyboarder,
                        "asset_generator": self._asset_generator, "editor": self._editor,
                        "critic": self._critic}

    # ------------------------------------------------------------ stage runners
    def _planner(self, fb):
        return planner.run(planner.PlannerInput(brief=self.brief, seed=self.seed), self.llm, self.log)

    def _researcher(self, fb):
        return researcher.run(researcher.ResearcherInput(
            brief=self.brief, data_dir=str(self.root / self.brief.data_dir), seed=self.seed), self.llm, self.log)

    def _scriptwriter(self, fb):
        return scriptwriter.run(scriptwriter.ScriptwriterInput(
            brief=self.brief, plan=self.art["planner"], facts=self.art["researcher"], seed=self.seed,
            feedback=fb, previous=self.art.get("scriptwriter") if fb else None), self.llm, self.log)

    def _storyboarder(self, fb):
        return storyboarder.run(storyboarder.StoryboarderInput(
            brief=self.brief, plan=self.art["planner"], script=self.art["scriptwriter"], seed=self.seed,
            allowed_text=scriptwriter.allowed_text(self.brief, self.art["researcher"]),
            feedback=fb, previous=self.art.get("storyboarder") if fb else None), self.llm, self.log)

    def _asset_generator(self, fb):
        return asset_generator.run(asset_generator.AssetGenInput(
            brief=self.brief, storyboard=self.art["storyboarder"], spec=self.art["planner"].video,
            root=str(self.root), seed=self.seed), None, self.log)

    def _editor(self, fb):
        return editor.run(editor.EditorInput(
            brief=self.brief, storyboard=self.art["storyboarder"], manifest=self.art["asset_generator"],
            spec=self.art["planner"].video, root=str(self.root)), None, self.log)

    def _critic(self, fb):
        return critic.run(critic.CriticInput(
            brief=self.brief, plan=self.art["planner"], facts=self.art["researcher"],
            script=self.art["scriptwriter"], storyboard=self.art["storyboarder"],
            manifest=self.art["asset_generator"], edit_plan=self.art["editor"], root=str(self.root),
            iteration=self.loops, seed=self.seed), self.llm, self.log)

    # ------------------------------------------------------------ helpers
    def _usage(self) -> dict:
        return {"llm_calls": getattr(self.llm, "calls", 0),
                "prompt_tokens": getattr(self.llm, "prompt_tokens", 0),
                "completion_tokens": getattr(self.llm, "completion_tokens", 0)}

    def _write_json(self, name: str, obj) -> Path:
        path = self.out / name
        path.parent.mkdir(parents=True, exist_ok=True)
        data = obj.model_dump(mode="json") if hasattr(obj, "model_dump") else obj
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        return path

    def _save(self, stage: str, art) -> Path:
        path = self._write_json(ARTIFACT_FILES[stage], art)
        if stage == "scriptwriter":
            (self.out / "script.md").write_text(scriptwriter.to_markdown(art), encoding="utf-8")
        if stage == "critic":
            self._write_json(f"qa_history/qa_iter_{art.iteration}.json", art)
        return path

    def _check_budget(self, stage: str) -> None:
        plan = self.art.get("planner")
        budget = plan.cost_budget if plan else CostBudget()
        u = self._usage()
        if u["llm_calls"] > budget.max_llm_calls or u["prompt_tokens"] + u["completion_tokens"] > budget.max_total_tokens:
            raise BudgetExceeded(f"Budget exceeded after '{stage}': {u} vs limits "
                                 f"{budget.max_llm_calls} calls / {budget.max_total_tokens} tokens.")

    def _execute(self, stage: str, feedback: list[Issue]) -> None:
        self.trace.append(stage)
        before = self._usage()["llm_calls"]
        self.log.event(stage, "start", repair_loop=self.loops, feedback_issues=[i.code for i in feedback],
                       uses_prompt=stage in PROMPT_STAGES)
        t0 = time.perf_counter()
        try:
            art = self.runners[stage](feedback)
        except LLMError as e:
            self.log.event(stage, "error", error_type="LLMError", error=str(e)[:500])
            raise
        except Exception as e:
            self.log.event(stage, "error", error_type=type(e).__name__, error=str(e)[:500])
            raise StageError(f"{stage} failed: {type(e).__name__}: {e}") from e
        elapsed = round(time.perf_counter() - t0, 3)
        self.art[stage] = art
        path = self._save(stage, art)
        self.log.event(stage, "end", elapsed_s=elapsed, output_path=path.relative_to(self.root).as_posix(),
                       llm_calls_in_stage=self._usage()["llm_calls"] - before, **self._usage())
        plan = self.art.get("planner")
        limit = next((s.max_seconds for s in plan.stages if s.name == stage), None) if plan else None
        if limit and elapsed > limit:
            self.log.event(stage, "over_time_limit", elapsed_s=elapsed, limit_s=limit)
        self._check_budget(stage)

    def _run_from(self, start: str, feedback_by_stage: dict[str, list[Issue]]) -> None:
        for stage in STAGES[STAGES.index(start):]:
            self._execute(stage, feedback_by_stage.get(stage, []))

    def _reset_outputs(self) -> None:
        for name in [*ARTIFACT_FILES.values(), "script.md", "error_report.json"]:
            (self.out / name).unlink(missing_ok=True)
        hist = self.out / "qa_history"
        if hist.is_dir():
            for f in hist.glob("qa_iter_*.json"):
                f.unlink()

    # ------------------------------------------------------------ main loop
    def run(self) -> RunResult:
        t0 = time.perf_counter()
        self._reset_outputs()
        self.log.event("run", "start", brief_id=self.brief.brief_id, seed=self.seed)
        try:
            self._run_from("planner", {})
            qa = self._repair_loop()
            return self._finish(qa, t0)
        except LLMError as e:
            return self._fail("LLM_ERROR", f"LLM/API error: {e}", t0)
        except (StageError, BudgetExceeded) as e:
            return self._fail("ERROR", str(e), t0)
        except Exception as e:  # unexpected bug: still a clean, logged, non-zero exit
            return self._fail("ERROR", f"Unexpected {type(e).__name__}: {e}", t0)

    def _repair_loop(self) -> QAReport:
        max_loops = min(self.max_repairs, self.art["planner"].cost_budget.max_repair_loops)
        qa: QAReport = self.art["critic"]
        history: list[dict] = []
        while True:
            repairable = [i for i in qa.issues if i.repairable]
            if not repairable or self.loops >= max_loops:
                break
            self.loops += 1
            start = min((i.stage for i in repairable), key=STAGES.index)
            by_stage: dict[str, list[Issue]] = {}
            for i in repairable:
                by_stage.setdefault(i.stage, []).append(i)
            history.append({"loop": self.loops, "triggering_status": qa.status, "restart_from": start,
                            "rerun_stages": STAGES[STAGES.index(start):],
                            "issues": [{"code": i.code, "severity": i.severity, "stage": i.stage,
                                        "message": i.message} for i in repairable]})
            self.log.event("orchestrator", "repair", loop=self.loops, restart_from=start,
                           issues=[i.code for i in repairable])
            self._run_from(start, by_stage)
            qa = self.art["critic"]
        qa.repairs_used, qa.repair_history = self.loops, history
        return qa

    def _finish(self, qa: QAReport, t0: float) -> RunResult:
        blocking = [i for i in qa.issues if i.severity in BLOCKING]
        if blocking:
            qa.status = "FAIL"
            qa.summary = (f"Run stopped safely: {len(blocking)} blocking issue(s) unresolved after "
                          f"{self.loops} repair loop(s). No export was produced. " +
                          " | ".join(f"[{i.code}] {i.message}" for i in blocking))[:1500]
        qa.final = True
        self._write_json("qa_report.json", qa)
        self.log.event("run", "finished", final_status=qa.status, repairs_used=self.loops,
                       elapsed_s=round(time.perf_counter() - t0, 3), **self._usage())
        return RunResult(status=qa.status, exit_code=EXIT_CODES[qa.status], qa=qa,
                         repairs_used=self.loops, trace=list(self.trace))

    def _fail(self, status: str, message: str, t0: float) -> RunResult:
        message = self.log.scrub(message)
        self._write_json("error_report.json", {"status": status, "message": message,
                                               "last_stage": self.trace[-1] if self.trace else None,
                                               "usage": self._usage()})
        self.log.event("run", "failed", final_status=status, error=message[:500],
                       elapsed_s=round(time.perf_counter() - t0, 3), **self._usage())
        return RunResult(status=status, exit_code=EXIT_CODES[status], error=message,
                         repairs_used=self.loops, trace=list(self.trace))
