"""End-to-end run of `run.py` through the REAL LLMClient + OpenAI SDK against a local fake
OpenAI-compatible server (no internet, no real Groq). Also exercises a genuine repair loop."""
import csv
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import run as run_mod
from tests.helpers import critic_out, planner_out, research_out, script_out, storyboard_out

ROOT = Path(__file__).resolve().parent.parent


def make_handler(script_replies):
    state = {"script": list(script_replies), "schemas": []}

    class H(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            name = body["response_format"]["json_schema"]["name"]
            state["schemas"].append(name)
            if name == "ScriptDraft":
                payload = state["script"].pop(0) if len(state["script"]) > 1 else state["script"][0]
            else:
                payload = {"PlannerDraft": planner_out(), "ResearchDraft": research_out(),
                           "StoryboardDraft": storyboard_out(), "CriticDraft": critic_out()}[name]
            reply = {"id": "x", "object": "chat.completion", "created": 0, "model": body["model"],
                     "choices": [{"index": 0, "finish_reason": "stop",
                                  "message": {"role": "assistant", "content": json.dumps(payload)}}],
                     "usage": {"prompt_tokens": 120, "completion_tokens": 60, "total_tokens": 180}}
            data = json.dumps(reply).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
    return H, state


def test_full_pipeline_with_real_adapter_and_repair(tmp_path, monkeypatch):
    handler, state = make_handler([script_out(bad_number=True), script_out()])
    server = HTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("GROQ_API_KEY", "gsk_e2e_secret")
        monkeypatch.setenv("LLM_BASE_URL", f"http://127.0.0.1:{server.server_port}/v1")
        monkeypatch.setenv("NO_PROXY", "127.0.0.1")
        code = run_mod.main(["--brief", str(ROOT / "briefs/practice.yaml"), "--seed", "42"])
    finally:
        server.shutdown()
    assert code == 0
    qa = json.loads((tmp_path / "outputs/qa_report.json").read_text())
    assert qa["status"] == "PASS_WITH_WARNINGS" and qa["repairs_used"] == 1
    assert qa["repair_history"][0]["restart_from"] == "scriptwriter"
    assert state["schemas"].count("ScriptDraft") == 2 and state["schemas"].count("PlannerDraft") == 1
    for f in ["plan", "facts", "script", "storyboard", "asset_manifest", "edit_plan"]:
        assert (tmp_path / "outputs" / f"{f}.json").is_file()
    rows = list(csv.DictReader(open(tmp_path / "logs/cost_report.csv")))
    assert len(rows) == 7 and rows[0]["prompt_tokens"] == "120" and rows[0]["cost_usd"] == "unknown"
    assert "gsk_e2e_secret" not in (tmp_path / "logs/run_log.jsonl").read_text()
    assert len(list((tmp_path / "assets/generated/P00").glob("S*.png"))) == 6


def test_run_py_returns_nonzero_when_api_unreachable(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("GROQ_API_KEY", "gsk_e2e_secret")
    monkeypatch.setenv("LLM_BASE_URL", "http://127.0.0.1:9/v1")      # nothing listens here
    monkeypatch.setenv("NO_PROXY", "127.0.0.1")
    assert run_mod.main(["--brief", str(ROOT / "briefs/practice.yaml")]) == 4
    assert (tmp_path / "outputs/error_report.json").is_file()
