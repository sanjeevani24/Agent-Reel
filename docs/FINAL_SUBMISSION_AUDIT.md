# Somaiya AgentReel Challenge 2026 — Final Submission Audit

**Project Title**: From Prompt to Product: How 7 AI Agents Build a Video  
**Organisation**: LY Agentic AI Laboratory, K J Somaiya School of Engineering  
**Submission Date**: October 23, 2026  
**GitHub Repository**: [https://github.com/sanjeevani24/Agent-Reel](https://github.com/sanjeevani24/Agent-Reel)  
**Active Branch**: `main`  
**Root Commit**: `eaed162`  
**Final Commit**: `c61aee1` (`docs: reconcile pipeline terminology, token metrics, and compliance matrix`)  
**Official Release Tag**: `v1.0-final`  
**Final Submission Package**: `agentreel-final-submission.zip` (24.05 MB)

---

## 1. Executive Summary

This document certifies that the **AgentReel** project has completed all technical, verification, documentation, and packaging requirements for academic submission in the **Somaiya AgentReel Challenge 2026**.

The repository implements a fully autonomous multi-agent video generation workflow capable of translating a creative brief into a broadcast-ready 9:16 vertical video with synchronized SubRip subtitles, automated QA telemetry, comprehensive architectural documentation, and zero live secrets.

---

## 2. Deliverable Inventory & Cryptographic Hashes

All core deliverables have been cryptographically verified using SHA-256 hashes across both the local workspace, the Git repository, and the final packaged submission ZIP:

| Deliverable Artifact | Description / Dimensions | File Size | SHA-256 Checksum |
| :--- | :--- | :--- | :--- |
| `outputs/final_video_v3.mp4` | 9:16 broadcast video (1080×1920 @ 30fps H.264/AAC, 44.02s) | 2,316,562 bytes (2.21 MB) | `d3ad9beba6b2bf91f36333329fa2fd6b3c2e6b14ee725fbc2ad1eec8a373ccc8` |
| `outputs/AgentReel_Final.srt` | Standalone SubRip subtitles (6 sequential cues, 00:00:00 to 00:00:44) | 843 bytes | `3e76b27701bb05c015bf0ac757d573bc656a5bf843c55c8f8d91015c6d0a6d1f` |
| `AgentReel_Final_Report.pdf` | Comprehensive 7-page academic and technical engineering report | 5,053,943 bytes (4.82 MB) | `d311f610e3dcb53916ad00e5c6b3e2de26e227d5dff265bad57c88fef162f20c` |
| `docs/process_report.pdf` | Concise 2-page challenge process report with mini-diagram & tables | 1,766,226 bytes (1.68 MB) | `1a29c339f6cbb5a4c4844ca0f73785d87c821246f05b011762e23078568e7053` |
| `docs/agent_graph.png` | Architecture diagram: 7-agent orchestration with repair loop (2000×1250) | 296,721 bytes (290 KB) | `351db07e887336aa935663e150087db9160a0f627f63b1a63ac4f5705138f269` |
| `outputs/render_report_v3.json` | Complete rendering telemetry, scene timeline, and codec parameters | 2,752 bytes | `ed1c4a3679d46b3c910958326d5529eef583b4224c06213afe20069179bcf977` |
| `outputs/qa_report.json` | Critic QA audit results: 18 rules, 0 errors, 5 soft warnings | 4,455 bytes | `68529153ae57ac60e5260f1bfb66fb2a7a0e045bb0212d8de0cc921aa97592cf` |
| `docs/final_compliance_checklist.md` | Formal compliance matrix evaluating guidelines and standards | 4,520 bytes | — |
| `assets/manifest.csv` | Asset attribution and provenance audit | 2,120 bytes | — |
| `agentreel-final-submission.zip` | Standalone submission archive (139 verified project files) | 25,218,240 bytes (24.05 MB) | — |

---

## 3. Detailed Verification Results

### 3.1. Video & Audio Broadcast Standards
- **Resolution & Aspect Ratio**: 1080 × 1920 progressive scan (9:16 vertical orientation).
- **Frame Rate**: Constant 30.0 fps (`r_frame_rate: 30/1`).
- **Video Stream**: H.264 High Profile (`avc1 / 0x31637661`), `yuv420p`, color space `bt709`.
- **Audio Stream**: Advanced Audio Coding (`aac (LC)`), stereo, 48.0 kHz sampling rate, 192 kbps.
- **Duration**: 44.02 seconds (video stream: 44.020000s; audio stream: 44.020317s).
- **Bitrate & File Size**: 421 kbps overall bitrate; 2.21 MB file size (well within 50 MB broadcast limit).
- **Null Decode Verification**: Executed `ffmpeg -v error -i outputs/final_video_v3.mp4 -f null -`; returned exit code 0 with exactly 0 errors, 0 dropped frames, and zero audio drift.

### 3.2. Subtitle Synchronization (`outputs/AgentReel_Final.srt`)
- **Format**: SubRip Subtitle (`.srt`), UTF-8 encoded with standard CRLF line breaks.
- **Sequence**: 6 monotonic, non-overlapping cues spanning from 00:00:00,000 to 00:00:44,000.
- **Alignment**: Spoken narrative timing matches voiceover syllables with sub-second accuracy.

### 3.3. Branding, AI Disclosure & Typography
- **AI Generation Disclosure**: Burned into Scene 5 lower badge: `"Created with AI agents — LY Agentic AI Lab"`.
- **Community Call to Action**: Displayed on Scene 5 visual card and spoken in voiceover: `"Come and build with us."`.
- **Note on Official Logos & External URLs**: As confirmed by inspection, neither an official logo image file nor an official fact-sheet URL was provided in the repository or brief. In accordance with strict academic integrity standards, no placeholder fake logos or synthetic URLs were invented.
- **Safe Margins**: Safe-zone typography enforces >120px top margin and >220px bottom margin, preventing occlusion by mobile platform UI overlays (TikTok, Reels, Shorts).

### 3.4. Architectural Pipeline & Bounded Repair Loop
- **Pipeline Structure**: Seven specialized agents managed by `core/orchestrator.py`:
  1. `agents/planner.py`: Decomposes brief into stages, budgets, and runtime targets.
  2. `agents/researcher.py`: Grounded quote extraction from `data/`.
  3. `agents/scriptwriter.py`: Formulates hook, narrative body, and CTA against Pydantic schemas.
  4. `agents/storyboarder.py`: Sequences visual shots and safe-zone captions (<80 characters).
  5. `agents/asset_generator.py`: Generates procedural 1080×1920 graphic cards via Pillow.
  6. `agents/editor.py`: Compiles multi-track timeline (`outputs/edit_plan.json`) synchronizing V1, A1, and T1 tracks.
  7. `agents/critic.py`: Executes 18 automated validation rules and manages targeted rollback repair loops.
- **Bounded Repair Ceiling**: Bounded to a maximum of 3 iterations, guaranteeing finite execution and zero infinite-cost recursion.

### 3.5. RAG Grounding & Transparent Fallback
- `data/` contains no external faculty PDF documents (`data/README.md` notes faculty sources were not supplied).
- The Researcher agent (`agents/researcher.py`) correctly detected missing documents and safely fell back to brief statements (`B1`, `B2`) without hallucinating citations, recording `"official_sources_present": false` in `outputs/facts.json`.

### 3.6. Automated QA Guardrails
- 18 automated rules executed in `agents/critic.py` and `core/validators.py`.
- Result recorded in `outputs/qa_report.json`: Status `PASS_WITH_WARNINGS`.
- Blocking Defects: **0**.
- Soft Warnings: **5** (minor soft character count limits and notice of empty faculty sources).

### 3.7. Automated Test Suite
- Test Command: `.venv/bin/python -m pytest tests/ -q --ignore=tests/test_e2e_local_server.py`
- Result: **78 passed**, 0 failed, 7 dependency deprecation warnings in 2.47s.
- `tests/test_e2e_local_server.py` tests a mock OpenAI server over local TCP loopback (`127.0.0.1`); under standard sandbox restrictions that disallow network sockets, it reports a connection block; outside sandboxed isolation, it verifies the full repair loop.

### 3.8. Token Economics & Autonomy Evidence
- **Total LLM Calls**: 9 calls to Groq (`openai/gpt-oss-120b`).
- **Total Prompt Tokens**: 12,247 (12,024 pipeline + 223 smoke test).
- **Total Completion Tokens**: 4,604 (4,571 pipeline + 33 smoke test).
- **Total Tokens**: 16,851 tokens.
- **Human Interventions**: Exactly **0 human interventions** recorded in `logs/interventions.md` during automated execution.
- **V3 Offline Video Rendering**: 12.44s execution time, 0 API calls, $0.00 compute expense.

### 3.9. Asset Attribution & Licensing
- Granularly recorded in `assets/manifest.csv`:
  - Visual Scene Cards (`S01.png` - `S07.png`, `preview_v3_*.png`): Procedural layouts generated by Python Pillow 13.0; 0 third-party stock images.
  - Typography: macOS System Helvetica (`/System/Library/Fonts/Helvetica.ttc`) under standard macOS system font licensing.
  - Narration Track (`voiceover.mp3`): Synthesized locally via macOS speech synthesis (`say` command) and muxed via FFmpeg; 0 third-party audio clips.
  - Background Music: Intentionally omitted to prioritize speech intelligibility and prevent audio masking.

### 3.10. Security & Secret Exclusion
- Secret regex audit performed across all tracked files: **0 live credentials or private tokens found**.
- `.env` strictly excluded from Git tracking and submission ZIP via `.gitignore`.
- `.env.example` provides non-sensitive template keys only.

---

## 4. Team Composition & Administrative Advisory

**Project Team Members**:
1. **Sanjeevani Chaurasia** (Roll No. 16014223073) — Orchestration Engine, Audio Synthesis & FFmpeg Rendering Pipeline
2. **Vedant Mhapsekar** (Roll No. 16014223095) — Critic QA Guardrails, Bounded Repair Loop & Schema Enforcement
3. **Aayush More** (Roll No. 16014223104) — RAG Grounding Architecture, Procedural Assets & SubRip Subtitle Alignment

**Administrative Advisory**:  
The challenge guidelines state a 2-student team limit. As this project was developed collaboratively by the three registered students above, this team composition is transparently documented across all project reports, the README, and the submission checklist for faculty review and confirmation.

---

## 5. Submission Package Verification

The final submission package `agentreel-final-submission.zip` was verified with `unzip -t`:
- Total Files Extracted: **139**
- Integrity Status: **OK (0 errors detected)**
- Prohibited Files Check: **0 `.env`, 0 `.venv`, 0 `__pycache__`, 0 `.DS_Store`**
- Ready for academic portal upload and faculty grading.
