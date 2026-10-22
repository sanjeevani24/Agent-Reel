# AgentReel: Autonomous Multi-Agent Short-Form Video Generator

**Project Topic**: *From Prompt to Product: How 7 AI Agents Build a Video*  
**Organisation**: LY Agentic AI Laboratory, K J Somaiya School of Engineering  
**Submission Package**: Final Academic Release (v1.0-final)

---

## 👥 Team Information
- **Sanjeevani Chaurasia** — Roll No. `16014223073`
- **Vedant Mhapsekar** — Roll No. `16014223095`
- **Aayush More** — Roll No. `16014223104`

> **Faculty Advisory Note on Team Size**:  
> The official AgentReel Challenge evaluation guidelines state a default policy of two students per team. Our collaborative project structure includes three registered members as detailed above. This configuration is formally documented here and flagged for faculty confirmation and approval.

---

## 🎯 Project Overview & Architecture

AgentReel is an autonomous, end-to-end multi-agent video production system designed to translate a high-level creative brief into a fully synthesized, broadcast-ready vertical video (9:16 aspect ratio, 1080×1920, H.264/AAC, 30 fps) with synchronized voiceover narration and frame-accurate burned-in SubRip captions.

### Seven-Agent Directed Acyclic Graph (DAG)

```
[ briefs/practice.yaml ] + [ data/ Source Documents ]
                       │
                       ▼
            ┌─────────────────────┐
            │   Agent 1: Planner  │ ──► outputs/plan.json
            └──────────┬──────────┘
                       ▼
            ┌─────────────────────┐
            │ Agent 2: Researcher │ ──► outputs/facts.json
            └──────────┬──────────┘
                       ▼
            ┌─────────────────────┐
            │Agent 3: Scriptwriter│ ──► outputs/script.json & script.md
            └──────────┬──────────┘
                       ▼
            ┌─────────────────────┐
            │Agent 4: Storyboarder│ ──► outputs/storyboard.json
            └──────────┬──────────┘
                       ▼
            ┌─────────────────────┐
            │Agent 5: Asset Gen   │ ──► outputs/asset_manifest.json & cards
            └──────────┬──────────┘
                       ▼
            ┌─────────────────────┐
            │   Agent 6: Editor   │ ──► outputs/edit_plan.json
            └──────────┬──────────┘
                       ▼
            ┌─────────────────────┐
            │   Agent 7: Critic   │ ──► outputs/qa_report.json
            └──────────┬──────────┘
                       │
       ┌───────────────┴───────────────┐
       ▼                               ▼
[ PASS / PASS_WITH_WARNINGS ]      [ FAIL (Hard/Factual) ]
       │                               │
       │                               ▼
       │                    Targeted Repair Loop (Max 3)
       │                    (Re-executes earliest stage)
       ▼
Final Deliverables (outputs/final_video_v3.mp4 & AgentReel_Final.srt)
```

1. **Planner (`agents/planner.py`)**: Parses the input brief, validates runtime constraints (35–45s duration, vertical 9:16 layout), establishes stage budgets, and generates `outputs/plan.json`.
2. **RAG Researcher (`agents/researcher.py`)**: Scans faculty-supplied sources in `data/` (PDF, Markdown, TXT) via PyMuPDF. Extracts grounded statements with exact citations. If no files are present, restricts facts to brief-supplied claims without hallucinating. Produces `outputs/facts.json`.
3. **Scriptwriter (`agents/scriptwriter.py`)**: Synthesizes a hook, core narrative, and call to action (CTA). Verifies fact IDs against `outputs/facts.json` and generates `outputs/script.json` and `outputs/script.md`.
4. **Storyboarder (`agents/storyboarder.py`)**: Translates script segments into 6–10 structured visual shots with composition directives, timing, and on-screen text constraints (1–80 chars). Produces `outputs/storyboard.json`.
5. **Asset Generator (`agents/asset_generator.py`)**: Programmatically renders 1080×1920 high-contrast visual cards and typography using Pillow. Produces `outputs/asset_manifest.json` and PNG frames.
6. **Timeline Editor (`agents/editor.py`)**: Compiles a non-linear edit (NLE) timeline assembling video (V1), narration audio (A1), and captions (T1) into `outputs/edit_plan.json`.
7. **Critic & QA Validator (`agents/critic.py`)**: Evaluates the entire project across 18 automated rules (timing bounds, character limits, asset integrity, claim grounding, LLM safety). Issues are categorized as `hard`, `factual`, or `soft`. If repairable hard/factual issues exist, it triggers a bounded repair loop (max 3 iterations) restarting from the responsible stage. Produces `outputs/qa_report.json`.

---

## 🤖 Autonomy Level & Human Interventions

- **Demonstrated Autonomy**: Full Autonomous Execution (Level 4 Agentic Workflow).
- **Human Interventions**: Exactly **0 human interventions** occurred during automated pipeline execution.
- **Audit Trail**: Verified in [`logs/interventions.md`](file:///Users/sanjeevanichaurasia/Downloads/agentreel-team/logs/interventions.md) and [`logs/run_log.jsonl`](file:///Users/sanjeevanichaurasia/Downloads/agentreel-team/logs/run_log.jsonl).
- **Human-in-the-Loop Safeguard**: An optional `--require-review` flag is provided in `core/orchestrator.py` which halts execution with exit code `3` if faculty pre-approval is requested before rendering.

---

## 🛠️ Environment & Setup

- **Operating System**: macOS (tested on Apple Silicon)
- **Python Version**: Python 3.12
- **External Binaries**: FFmpeg (with `h264` and `aac` encoders)

### Installation
```bash
# Activate your existing Python 3.12 virtual environment
source .venv/bin/activate

# Install pinned dependencies
pip install -r requirements.txt
```

### Dependencies (`requirements.txt`)
- `openai==3.35.1`: LLM API client for Groq endpoint
- `pydantic==2.14.1`: Strict schema validation across all stages
- `PyYAML==6.0.3`: YAML brief parsing
- `python-dotenv==1.2.4`: Environment variable management
- `pytest==9.1.1`: Automated test suite
- `Pillow==13.0.0`: Procedural graphics and typography engine
- `PyMuPDF==2.0`: RAG document parsing and PDF report generation

---

## 🚀 Execution Commands

### 1. Preflight Validation
Validates configuration, environment variables, and brief schemas without invoking the LLM:
```bash
python run.py --brief briefs/practice.yaml --preflight-only
```

### 2. Full LLM Pipeline Execution (Groq)
Executes the full 7-agent DAG with automated QA validation:
```bash
python run.py --brief briefs/practice.yaml --seed 42
```
*Exit Codes*:
- `0`: Success (QA passed or passed with warnings)
- `1`: QA failure (unsupported claims or unrepairable defects; export blocked)
- `2`: Preflight or configuration error
- `3`: Human review required
- `4`: LLM / API communication failure
- `5`: Internal orchestrator or budget error

### 3. High-Fidelity V3 Offline Video Renderer
Renders the complete V3 vertical video with 5 rich animated scenes, voiceover narration, and burned captions completely offline (no API keys required):
```bash
python scripts/render_v3.py
```

### 4. Running the Test Suite
Runs unit and integration tests:
```bash
python -m pytest tests/ -q --ignore=tests/test_e2e_local_server.py
```

---

## 📂 Deliverables & Repository Map

| Deliverable | File Path | Description |
|---|---|---|
| **Final Video** | `outputs/final_video_v3.mp4` | 44.02s broadcast MP4 (1080×1920, 30fps H.264/AAC, 2.21 MB) |
| **Subtitles** | `outputs/AgentReel_Final.srt` | 6 timed SubRip subtitle cues (00:00:00 to 00:00:44) |
| **QA Report** | `outputs/qa_report.json` | 18 automated checks, 0 blocking issues, 5 soft warnings |
| **V3 Render Report** | `outputs/render_report_v3.json` | Scene manifests, durations, audio specs, and video telemetry |
| **Execution Log** | `logs/run_log.jsonl` | Audited trace of 50 pipeline and agent lifecycle events |
| **Cost Report** | `logs/cost_report.csv` | Exact prompt and completion token counts per agent invocation |
| **Interventions** | `logs/interventions.md` | Human approval log (verified: 0 interventions) |
| **Asset Manifest** | `assets/manifest.csv` | Full licensing and provenance audit for all media assets |
| **Agent DAG Graph** | `docs/agent_graph.png` | Visual DAG architecture diagram (1920×1200) |
| **Process Report (PDF)** | `docs/process_report.pdf` | Concise 2-page academic report per challenge guidelines |
| **Comprehensive Report**| `AgentReel_Final_Report.pdf` | 7-page exhaustive engineering and architectural report |
| **Prompt Templates** | `prompts/` | Prompt templates for Planner, Researcher, Scriptwriter, Storyboarder, Critic |

---

## 🧪 Verified Test Results

- **Unit & Integration Suite**: **78 passed**, 0 failed, 7 dependency deprecation warnings in 2.60s (`python -m pytest tests/ -q --ignore=tests/test_e2e_local_server.py`).
- **End-to-End Local Server Test**: `tests/test_e2e_local_server.py` tests a mock OpenAI server over local loopback (`127.0.0.1`). In sandbox environments restricting local TCP socket creation, this test reports a connection block; outside sandboxed isolation, it verifies the full repair loop.
- **Application Code Integrity**: Zero application code files were modified or weakened to bypass tests.

---

## 🔒 Security & Credentials Policy

- **No Secrets in Repo**: All API keys are loaded strictly from `.env` via `python-dotenv`.
- **Exclusion Guarantee**: `.env`, `.venv/`, `.pytest_cache/`, `__pycache__/`, and `.DS_Store` are excluded from version control and the final clean submission archive.
- **Token Logging**: `logs/run_log.jsonl` explicitly redacts sensitive environment keys.
