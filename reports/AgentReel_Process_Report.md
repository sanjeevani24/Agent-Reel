# AgentReel Process Report
## From Prompt to Product: How 7 AI Agents Build a Video

**Organisation:** LY Agentic AI Laboratory, K J Somaiya School of Engineering  
**Date:** October 22, 2026  
**Project Repository:** `agentreel-team` (Somaiya AgentReel Challenge)

### Project Team

| Team Member | Roll Number | Role |
| :--- | :--- | :--- |
| **Sanjeevani Chaurasia** | 16014223073 | Agent Architect, Motion Graphics Engine & FFmpeg Integration |
| **Vedant Mhapsekar** | 16014223095 | Pipeline Orchestrator, LLM Adapter & Schema Validation |
| **Aayush More** | 16014223104 | QA Critic Rules, Testing Suite & Evaluation Engineer |

---

## Executive Summary & Final Deliverable Metrics

The AgentReel project implements an autonomous, multi-agent AI system that converts a structured natural-language brief into a broadcast-ready, vertical (9:16) video with synchronized spoken audio and burned SubRip subtitles. The pipeline operates under a strict contract-driven architecture governed by seven specialized agents: **Planner**, **Researcher (RAG)**, **Scriptwriter**, **Storyboarder**, **Asset Generator**, **Editor**, and **Critic**.

Unlike conventional generative video tools that rely on single-prompt black-box APIs, AgentReel employs a deterministic multi-agent state machine with bounded repair loops, verified fact grounding, mobile safe-zone layout compliance, and local procedural rendering. The final deliverable video—**`outputs/final_video_v3.mp4`**—showcases the educational topic **"From Prompt to Product: How 7 AI Agents Build a Video"** across five dynamic motion-graphics scenes.

### Final Video Deliverable Specifications

| Metric | Target Specification | Delivered Result (`outputs/final_video_v3.mp4`) | Verification Method |
| :--- | :--- | :--- | :--- |
| **Resolution** | 1080 × 1920 (9:16 vertical) | **1080 × 1920** | `ffprobe -show_streams` |
| **Frame Rate** | 30.0 fps | **30.0 fps** (1,320 total frames) | `ffprobe -show_streams` |
| **Total Duration** | 43.0s – 45.0s | **44.02 seconds** | `ffprobe -show_format` |
| **Video Codec** | H.264 / `libx264` (`yuv420p`) | **H.264 / High Profile (CRF 22)** | Bitstream header inspection |
| **Audio Codec** | AAC stereo @ 48,000 Hz | **AAC stereo @ 48 kHz, 192 kbps** | `ffprobe` stream analysis |
| **File Size** | < 100 MB | **2.21 MB** (97.8% under budget) | POSIX `stat()` / disk size |
| **Bitstream Integrity** | 0 decode errors/warnings | **100% Clean (0 errors, 0 warnings)** | `ffmpeg -v error -i ... -f null -` |
| **Subtitles** | Synchronized SubRip format | **`outputs/AgentReel_Final.srt` (6 cues)** | Timestamp & cue validator |
| **Call to Action** | Exact match | *"Come and build with us."* | Visual & audio audit |
| **Mandatory Disclosure**| Safe-zone burned line | *"Created with AI agents — LY Agentic AI Lab"* | Visual & code audit |

---

## 1. Brief Interpretation & Creative Strategy

The input brief (`briefs/practice.yaml`) tasks the multi-agent system with creating an engaging, technically grounded vertical video explaining the autonomous agent workflow developed at the Somaiya Agentic AI Laboratory.

### Strategic Priorities:
1. **Explainability over Vanity Metrics:** Avoid generic stock footage or black-box AI video generators. The video itself serves as the interactive explanation of the 7-agent pipeline.
2. **Visual Hierarchy & Palette Consistency:** Built on an intentional dual-tone deep navy `(11, 17, 32)` to rich burgundy `(59, 10, 26)` vertical gradient accented by radiant gold `(245, 158, 11)` connection lines and crisp cool-slate typography.
3. **Mobile-First Safe Zones:** All critical text, cards, timelines, and UI indicators respect TikTok/Reels/Shorts platform margins (120px top header margin, 240px bottom UI clearance, 80px side margins).
4. **Pacing and Cognitive Load:** The 44-second duration is balanced across five narrative phases:
   - **Scene 1 (0.0s – 5.5s):** The Prompt — Terminal typing `prompt.yaml` exploding into a 7-node agent constellation.
   - **Scene 2 (5.5s – 22.0s):** The Workflow — 7 vertical agent cards illuminated by a traveling golden highlight pulse.
   - **Scene 3 (22.0s – 30.0s):** Assembly — 4 non-clipped storyboard cards, dynamic audio waveform, and NLE timeline tracks (`[V1]`, `[A1]`, `[T1]`).
   - **Scene 4 (30.0s – 38.0s):** Guardrails & QA — Critic HUD inspection checklist, animated red repair loop arrow, and green `ALL CHECKS PASSED` resolution banner.
   - **Scene 5 (38.0s – 44.0s):** Product Delivery — Smartphone mockup previewing the 1080×1920 MP4, orbiting agent nodes, and the Somaiya Agentic AI Lab CTA.

---

## 2. Multi-Agent System Architecture & Data Flow

The architecture decouples planning, generation, composition, and verification into modular Python modules orchestrated by `core/orchestrator.py`. Communication between agents is strictly mediated via validated Pydantic JSON contracts saved in `outputs/`.

```
User Brief (YAML)
       │
       ▼
[Agent 1: Planner] ───────► outputs/plan.json
       │
       ▼
[Agent 2: Researcher] ────► outputs/facts.json
       │
       ▼
[Agent 3: Scriptwriter] ──► outputs/script.json & script.md
       │
       ▼
[Agent 4: Storyboarder] ──► outputs/storyboard.json
       │
       ▼
[Agent 5: Asset Gen] ─────► outputs/asset_manifest.json (Pillow Visuals)
       │
       ▼
[Agent 6: Timeline Editor] ► outputs/edit_plan.json (Audio & NLE Tracks)
       │
       ▼
[Agent 7: Critic / QA] ───► outputs/qa_report.json
       │
       ├─► [FAIL: Issues Flagged] ──► Targeted Repair Loop (Max 3 passes)
       │                                ├─► Factual/Claim Issue  ──► Rerun Scriptwriter onwards
       │                                ├─► Caption/Shot Issue   ──► Rerun Storyboarder onwards
       │                                └─► Missing Asset Issue  ──► Rerun Asset Gen onwards
       │
       └─► [PASS / PASS_WITH_WARNINGS] ──► Video Export (final_video_v3.mp4 & AgentReel_Final.srt)
```

*(The editable Mermaid diagram source is saved in `reports/AgentReel_Architecture.mmd`)*.

### Orchestration & Deterministic Repair Loop
The `Orchestrator` maintains a bounded state machine:
- **Trace Tracking:** Each stage logs execution timestamps, latency, token consumption, and input parameters.
- **Contract Enforcement:** Stages cannot execute until their prerequisite JSON schemas pass strict Pydantic v2 validation.
- **Bounded Repair Loop:** When the Critic identifies hard errors or unsupported claims, the orchestrator identifies the earliest responsible stage and re-runs only the affected downstream pipeline. The repair loop is strictly capped at three iterations to prevent runaway API spend or infinite loops.

---

## 3. Seven Agent Specifications & Implementation

| Agent | Source File | Core Responsibility | Input Contract | Output Contract | Primary Tooling |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **1. Planner** | `agents/planner.py` | Decomposes YAML brief into duration targets, technical specs, budget caps, and 3–8 criteria. | `briefs/practice.yaml` | `outputs/plan.json` | Pydantic, Groq LLM Adapter |
| **2. Researcher** | `agents/researcher.py` | Grounded RAG agent. Extracts facts from `data/` (`.pdf`, `.md`, `.txt`) and verifies exact verbatim quotes. | `data/`, `plan.json` | `outputs/facts.json` | PyMuPDF, Python regex |
| **3. Scriptwriter** | `agents/scriptwriter.py` | Crafts timed voiceover narrative segmented into Hook, Problem, Solution, and CTA. | `plan.json`, `facts.json` | `outputs/script.json`, `outputs/script.md` | Groq LLM Adapter, duration validator |
| **4. Storyboarder** | `agents/storyboarder.py` | Translates script segments into 6–10 visual shots with on-screen text and visual prompts. | `script.json` | `outputs/storyboard.json` | Groq LLM Adapter, caption limiter |
| **5. Asset Generator** | `agents/asset_generator.py`, `agents/motion_graphics.py` | Renders 1080×1920 visual cards and motion graphics elements with platform safe zones. | `storyboard.json` | `outputs/asset_manifest.json`, raw frames | Pillow 13.0, vector drawing math |
| **6. Editor** | `agents/editor.py`, `agents/renderer_v3.py` | Builds NLE timeline, normalizes 48 kHz voiceover audio, burns SubRip captions, and muxes MP4. | `manifest.json`, `storyboard.json` | `outputs/edit_plan.json`, `final_video_v3.mp4` | FFmpeg 9.0.2, macOS `say` |
| **7. Critic** | `agents/critic.py` | Evaluates 18 automated rules (duration bounds, claim grounding, contact checks, caption length, safety). | All intermediate JSON artifacts | `outputs/qa_report.json` | Pydantic, deterministic validators, LLM reviewer |

---

## 4. Technology Stack & Local Rendering Architecture

- **Runtime & Language:** Python 3.12 on macOS (Apple Silicon).
- **Validation & Typing:** Pydantic v2 (`core/schemas.py`, `core/validators.py`).
- **Visual Engine:** Pillow (PIL) 13.0 with procedural RGBA/RGB24 canvas generation and vector-based checkmarks, waveforms, and phone mockups.
- **Document Processing:** PyMuPDF (`fitz`) 2.0 for grounded local RAG parsing.
- **Audio Synthesis:** Local macOS speech synthesis (`say -v Samantha`) with silence padding (`apad=whole_dur`) and automatic stereo fallback (`anullsrc`).
- **Video Assembly:** FFmpeg 9.0.2 compiled without external caption dependencies (`libass`/`drawtext`). To overcome this platform constraint, frames are streamed directly from Pillow into FFmpeg's `stdin` via raw byte pipe (`-f rawvideo -pix_fmt rgb24 -s 1080x1920 -r 30 -i -`), achieving **>75 fps rendering speed** (>2.5× real-time).

---

## 5. Development Progression: Milestone B through V3

| Milestone | Phase Focus | Key Deliverables | Status & Evidence |
| :--- | :--- | :--- | :--- |
| **Milestone B** | Multi-Agent Coordination & Schema Contracts | 7 agents implemented, `core/orchestrator.py`, repair loop, 63 unit tests. First live Groq LLM run (`run_20261021_165923`). | `outputs/plan.json` $\to$ `qa_report.json` generated; `render_status='not_rendered'`. Preserved in `milestone_c_backup/`. |
| **Milestone C** | Playable Video & Subtitles Delivery | `agents/editor.py` render pipeline, voiceover normalization, 39.0s card-based MP4. | `outputs/final_video.mp4` (3.06 MB), `subtitles.srt`, `render_report.json`. Preserved in `milestone_c_backup/`. |
| **V2 Upgrade** | Topic Upgrade & Procedural Motion Graphics | New topic ("How 7 AI Agents Build a Video"), `agents/motion_graphics.py`, raw RGB FFmpeg streaming. | `outputs/final_video_v2.mp4` (43.02s, 2.74 MB), `subtitles_v2.srt`, `preview_v2_1.png`–`preview_v2_5.png`. Preserved in `v2_backup/`. |
| **V3 Final Polish** | Narration Audit, Typography & Safe Margins | Fixed Scene 2 audio cutoff, positive audio headroom across all 5 scenes, non-clipped storyboard cards, high-contrast typography. | `outputs/final_video_v3.mp4` (44.02s, 2.21 MB), `outputs/AgentReel_Final.srt`, `render_report_v3.json`, 78 tests passing. |

---

## 6. The Scene 2 Narration Issue & The V3 Resolution

### The Incident
In the V2 motion graphics release, Scene 2 ("The 7 AI Agents Workflow") audio was prematurely truncated, leaving the final roles (*Editor* and *Critic*) inaudible before the scene abruptly transitioned to Scene 3.

### Root Cause Diagnosis
1. **Narration Duration Mismatch:** The previous spoken script required **19.25 seconds** at natural speaking pace (175 wpm). However, `agents/renderer_v2.py` allocated only **15.50 seconds** to Scene 2.
2. **Hard FFmpeg Truncation:** During audio track preparation, the script executed:
   ```bash
   ffmpeg -y -i scene_2.aiff -af "apad=whole_dur=15.5" -t 15.5 -ar 48000 -ac 2 scene_2_padded.wav
   ```
   The `-t 15.5` argument strictly cut off the audio stream at exactly 15.5 seconds, dropping the last 3.75 seconds of narration.

### The V3 Engineering Correction
1. **Verbatim 7-Agent Narration Script:** Re-phrased the voiceover to ensure concise, natural cadence while explicitly naming all seven agents:
   > *"In our pipeline, seven specialized agents coordinate: Planner sets the plan, Researcher checks facts, Scriptwriter writes the story, Storyboarder designs shots, Asset Generator creates visuals, Editor builds the edit, and Critic verifies quality."*
2. **Audio Headroom & Scene Retiming:**
   - Spoken duration measured at 180 wpm: **15.90 seconds**.
   - Scene 2 duration extended to **16.50 seconds**.
   - Net headroom: **+0.60 seconds** of clean silence before transitioning to Scene 3.
3. **Global Video Pacing:** All 5 scenes were tuned to maintain positive headroom (+0.29s to +0.99s), bringing total video duration to **44.02 seconds** (well within the 43–45s specification).

---

## 7. Quality Assurance, Guardrails & Testing Evidence

### Automated Test Suite: 78 Tests Passing in 2.66s
The project maintains comprehensive test coverage across all pipeline layers (`pytest -k "not local_server"`):
- `tests/test_agents.py`: Planner budget clamping, Scriptwriter timing rules, Storyboard shot limits, Asset generation.
- `tests/test_validators.py`: Word count/speech rate math, duration tolerance windows, factual claim verification.
- `tests/test_critic.py`: Unsupported claim detection, duration mismatch enforcement, missing disclosure handling.
- `tests/test_orchestrator.py`: Stage sequence order, targeted repair reruns, 3-loop cap safety stop.
- `tests/test_renderer.py`: Caption truncation at word boundaries (`limit_caption`), SRT format formatting, end card dimensions.
- `tests/test_motion_v2.py`: V2 procedural frame rendering, time formatting, backup directory integrity.
- `tests/test_motion_v3.py`: V3 1080×1920 frame rendering, subtitle timestamp continuity ending at 44.0s, explicit verification that Scene 2 names all 7 agents, and dual backup preservation.

### Critic Agent 18-Rule Automated Audit
In the live Groq pipeline run (`outputs/qa_report.json`), the Critic executed 18 automated rules:
- **Status:** `PASS_WITH_WARNINGS` (0 Hard Errors, 0 Factual Failures).
- **Resolved Soft Warning:** Shot `S02` on-screen text length (`93 chars > 80 chars`) was caught and automatically resolved via deterministic word-boundary truncation (`limit_caption(..., 80)`).
- **Data Source Note:** Fact groundedness flagged that no external documents existed in `data/`, falling back safely to brief-provided statements without fabricating ungrounded claims.

---

## 8. Runtime, Cost & Token Economics (Audited Logs)

Based strictly on the verified execution records in `logs/cost_report.csv` and `logs/run_log.jsonl` (Run ID: `run_20261021_165923`, Model: `openai/gpt-oss-120b` on Groq):

| Pipeline Stage | LLM Calls | Prompt Tokens | Completion Tokens | Total Tokens | Stage Latency |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Planner** | 2 | 2,030 | 589 | 2,619 | 2.09s |
| **Researcher (RAG)**| 0 | 0 | 0 | 0 | 0.001s |
| **Scriptwriter** | 2 | 3,749 | 1,715 | 5,464 | 25.56s (incl. repair) |
| **Storyboarder** | 2 | 3,708 | 1,504 | 5,212 | 27.29s (incl. repair) |
| **Asset Generator** | 0 | 0 | 0 | 0 | 0.119s |
| **Editor** | 0 | 0 | 0 | 0 | 0.001s |
| **Critic / QA** | 2 | 2,537 | 763 | 3,300 | 14.62s (incl. repair) |
| **Pipeline Total** | **8 calls** | **12,024** | **4,571** | **16,895 tokens** | **69.68s** |

*(Note: Cost in USD is listed as `unknown` in logs because `LLM_PRICE_IN_PER_M` and `LLM_PRICE_OUT_PER_M` were unconfigured. V3 video rendering executed 100% locally and offline in 12.44s with 0 API calls)*.

### Human Intervention Log
`logs/interventions.md` records **0 human interventions**. The autonomous orchestrator handled preflight validation, planning, fact extraction, drafting, QA evaluation, and targeted repair autonomously.

---

## 9. Limitations, Ethics & Future Work

### Known Limitations
1. **Local Document Corpus:** In the initial run, `data/` contained no external PDFs, limiting verified facts to statements provided in the brief.
2. **System Voice Variety:** TTS relies on macOS `say` with voice `Samantha`. While natural and clear, voice variety is bound to the host operating system.
3. **FFmpeg Compilation Limits:** The local Homebrew FFmpeg binary lacked `libass` and `libfreetype`, requiring procedural Pillow frame rendering rather than filter-graph subtitle burning.

### Ethical Considerations & Guardrails
- **Anti-Hallucination Constraints:** Scriptwriter and Storyboarder are strictly prohibited from inventing statistics, phone numbers, or email addresses.
- **Mandatory AI Disclosure:** In compliance with ethical AI transparency guidelines, Scene 5 permanently burns the disclosure: *"Created with AI agents — LY Agentic AI Lab"*.

### Future Improvements
1. **Local Open-Source LLMs:** Support local Ollama / vLLM execution (e.g. Llama 3.3 70B) for zero-cloud, 100% air-gapped pipeline runs.
2. **Multi-Speaker TTS:** Integrate local neural TTS engines (e.g. Piper or Coqui) for natural multi-agent dialogue.
3. **Hardware Acceleration:** Implement Apple Silicon VideoToolbox encoding (`h264_videotoolbox`) for sub-second rendering.

---

## 10. Deliverables Manifest & Conclusion

All required project deliverables are generated and verified on disk:

1. **Final Video (V3):** [`outputs/final_video_v3.mp4`](file:///Users/sanjeevanichaurasia/Downloads/agentreel-team/outputs/final_video_v3.mp4) (44.02s, 1080×1920, 2.21 MB).
2. **Standalone Subtitles:** [`outputs/AgentReel_Final.srt`](file:///Users/sanjeevanichaurasia/Downloads/agentreel-team/outputs/AgentReel_Final.srt) (6 audio-verified cues).
3. **V3 Render Report:** [`outputs/render_report_v3.json`](file:///Users/sanjeevanichaurasia/Downloads/agentreel-team/outputs/render_report_v3.json).
4. **Scene Preview Frames:** [`outputs/preview_v3_1.png`](file:///Users/sanjeevanichaurasia/Downloads/agentreel-team/outputs/preview_v3_1.png) to [`outputs/preview_v3_5.png`](file:///Users/sanjeevanichaurasia/Downloads/agentreel-team/outputs/preview_v3_5.png).
5. **Architecture Diagram:** [`reports/AgentReel_Architecture.mmd`](file:///Users/sanjeevanichaurasia/Downloads/agentreel-team/reports/AgentReel_Architecture.mmd).
6. **Process Report (Markdown):** [`reports/AgentReel_Process_Report.md`](file:///Users/sanjeevanichaurasia/Downloads/agentreel-team/reports/AgentReel_Process_Report.md).
7. **Process Report (PDF):** [`reports/AgentReel_Process_Report.pdf`](file:///Users/sanjeevanichaurasia/Downloads/agentreel-team/reports/AgentReel_Process_Report.pdf).
8. **Preserved Milestone Backups:** [`outputs/milestone_c_backup/`](file:///Users/sanjeevanichaurasia/Downloads/agentreel-team/outputs/milestone_c_backup/) and [`outputs/v2_backup/`](file:///Users/sanjeevanichaurasia/Downloads/agentreel-team/outputs/v2_backup/).

The AgentReel project successfully demonstrates that complex, broadcast-ready vertical video generation can be reliably decomposed into modular, deterministic, and self-repairing AI agents.
