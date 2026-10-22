"""Run logging. Everything here is written at execution time, never back-filled."""
from __future__ import annotations

import csv
import json
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

COST_FIELDS = ["timestamp", "run_id", "agent", "provider", "model", "prompt_tokens",
               "completion_tokens", "cost_usd", "cost_status"]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


class RunLogger:
    def __init__(self, log_dir: str | Path = "logs", run_id: str | None = None,
                 secrets: list[str] | None = None):
        self.dir = Path(log_dir)
        self.dir.mkdir(parents=True, exist_ok=True)
        self.run_id = run_id or time.strftime("run_%Y%m%d_%H%M%S")
        self._secrets = [s for s in (secrets or []) if s]
        self._lock = threading.Lock()
        self.jsonl = self.dir / "run_log.jsonl"
        self.cost_csv = self.dir / "cost_report.csv"
        self.interventions = self.dir / "interventions.md"
        if not self.cost_csv.exists():
            with self.cost_csv.open("w", newline="", encoding="utf-8") as f:
                csv.writer(f).writerow(COST_FIELDS)
        if not self.interventions.exists():
            self.interventions.write_text(
                "# Human interventions and approvals\n\n"
                "| time (UTC) | run | type | detail |\n|---|---|---|---|\n", encoding="utf-8")

    def _scrub(self, text: str) -> str:
        for s in self._secrets:
            text = text.replace(s, "***")
        return text

    def scrub(self, text: str) -> str:
        return self._scrub(text)

    def event(self, agent: str, status: str, **fields) -> None:
        rec = {"timestamp": now_iso(), "run_id": self.run_id, "agent": agent,
               "status": status, **fields}
        line = self._scrub(json.dumps(rec, ensure_ascii=False, default=str))
        with self._lock, self.jsonl.open("a", encoding="utf-8") as f:
            f.write(line + "\n")

    def cost(self, agent: str, provider: str, model: str, prompt_tokens, completion_tokens,
             cost_usd) -> None:
        status = "computed_from_configured_prices" if cost_usd is not None else "unknown"
        row = [now_iso(), self.run_id, agent, provider, model,
               "unknown" if prompt_tokens is None else prompt_tokens,
               "unknown" if completion_tokens is None else completion_tokens,
               "unknown" if cost_usd is None else f"{cost_usd:.6f}", status]
        with self._lock, self.cost_csv.open("a", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(row)

    def intervention(self, kind: str, detail: str) -> None:
        detail = self._scrub(detail.replace("|", "/").replace("\n", " "))
        with self._lock, self.interventions.open("a", encoding="utf-8") as f:
            f.write(f"| {now_iso()} | {self.run_id} | {kind} | {detail} |\n")
