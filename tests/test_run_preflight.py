from pathlib import Path
from run import main

ROOT = Path(__file__).resolve().parent.parent


def test_preflight_ok(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("GROQ_API_KEY", "gsk_abc123")
    assert main(["--brief", str(ROOT / "briefs/practice.yaml"), "--seed", "42", "--preflight-only"]) == 0
    assert (tmp_path / "logs/run_log.jsonl").exists()
    assert "gsk_abc123" not in (tmp_path / "logs/run_log.jsonl").read_text()


def test_preflight_bad_brief(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    assert main(["--brief", "missing.yaml", "--no-key"]) == 2
