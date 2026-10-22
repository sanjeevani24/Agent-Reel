from pathlib import Path
import fitz  # PyMuPDF
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(".").resolve()
DOCS_DIR = ROOT / "docs"
DOCS_DIR.mkdir(parents=True, exist_ok=True)
PDF_OUT = DOCS_DIR / "process_report.pdf"

FONT_REG = "/System/Library/Fonts/Supplemental/Arial.ttf"
FONT_BOLD = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
FONT_ITAL = "/System/Library/Fonts/Supplemental/Arial Italic.ttf"

def draw_mini_diagram(out_path):
    dw, dh = 1600, 360
    im = Image.new("RGB", (dw, dh), (248, 250, 252))
    draw = ImageDraw.Draw(im)
    try:
        font_b = ImageFont.truetype(FONT_BOLD, 18)
        font_s = ImageFont.truetype(FONT_REG, 13)
        font_badge = ImageFont.truetype(FONT_BOLD, 12)
    except:
        font_b = ImageFont.load_default()
        font_s = font_b
        font_badge = font_b

    draw.rounded_rectangle([10, 10, dw - 10, dh - 10], radius=12, fill=(255, 255, 255), outline=(203, 213, 225), width=2)
    
    stages = [
        ("1. Planner", "outputs/plan.json", "Budget & Specs"),
        ("2. Researcher", "outputs/facts.json", "Grounded Quotes"),
        ("3. Scriptwriter", "outputs/script.json", "Spoken Narrative"),
        ("4. Storyboarder", "outputs/storyboard.json", "Visual Shots"),
        ("5. Asset Gen", "outputs/asset_manifest.json", "Pillow 9:16"),
        ("6. Editor", "outputs/edit_plan.json", "NLE Timeline"),
        ("7. Critic", "outputs/qa_report.json", "18 QA Checks"),
    ]
    
    box_w = 185
    box_h = 120
    start_x = 35
    spacing = 38
    y = 40
    
    for i, (name, art, desc) in enumerate(stages):
        x = start_x + i * (box_w + spacing)
        col = (239, 68, 68) if i == 6 else (37, 99, 235)
        bg = (254, 242, 242) if i == 6 else (239, 246, 255)
        draw.rounded_rectangle([x, y, x + box_w, y + box_h], radius=8, fill=bg, outline=col, width=2)
        draw.text((x + 12, y + 14), name, fill=(15, 23, 42), font=font_b)
        draw.text((x + 12, y + 42), desc, fill=(71, 85, 105), font=font_s)
        draw.text((x + 12, y + 75), art, fill=col, font=font_badge)
        
        if i < 6:
            ax = x + box_w
            ay = y + box_h // 2
            draw.line([(ax, ay), (ax + spacing, ay)], fill=(148, 163, 184), width=2)
            draw.polygon([(ax + spacing, ay), (ax + spacing - 8, ay - 5), (ax + spacing - 8, ay + 5)], fill=(148, 163, 184))

    draw.rounded_rectangle([35, 210, dw - 35, 320], radius=8, fill=(255, 251, 235), outline=(245, 158, 11), width=2)
    draw.text((55, 225), "CRITIC REPAIR LOOP: Automated Feedback & Rollback (Bounded Max 3 Iterations)", fill=(180, 83, 9), font=font_b)
    draw.text((55, 255), "- Hard / Factual / Caption failures route backward to earliest responsible agent (Scriptwriter, Storyboarder, or Asset Gen).", fill=(120, 53, 15), font=font_s)
    draw.text((55, 285), "- PASS / PASS_WITH_WARNINGS triggers final MP4 video compilation & burned SubRip subtitle generation.", fill=(120, 53, 15), font=font_s)
    
    im.save(out_path, "PNG")

def build_pdf():
    doc = fitz.open()
    diag_img_path = DOCS_DIR / "temp_mini_dag.png"
    draw_mini_diagram(diag_img_path)

    NAVY = (15/255, 23/255, 42/255)
    SLATE = (71/255, 85/255, 105/255)
    BLUE = (37/255, 99/255, 235/255)
    LIGHT_BG = (248/255, 250/255, 252/255)
    BORDER = (226/255, 232/255, 240/255)
    AMBER_BG = (254/255, 243/255, 199/255)
    AMBER_TXT = (146/255, 64/255, 14/255)
    WHITE = (1, 1, 1)

    # PAGE 1
    page1 = doc.new_page(width=595.32, height=841.92)
    # Header Banner
    page1.draw_rect(fitz.Rect(36, 32, 559.32, 115), color=None, fill=LIGHT_BG)
    page1.draw_rect(fitz.Rect(36, 32, 559.32, 115), color=BORDER, width=1)
    page1.insert_text(fitz.Point(48, 52), "AGENTREEL PROCESS REPORT: FROM PROMPT TO PRODUCT", fontsize=13, fontname="helv", fontfile=FONT_BOLD, color=NAVY)
    page1.insert_text(fitz.Point(48, 68), "How 7 Autonomous AI Agents Build a Broadcast-Ready Vertical Video", fontsize=9.5, fontname="helv", fontfile=FONT_ITAL, color=BLUE)
    page1.insert_text(fitz.Point(48, 86), "Organisation: LY Agentic AI Laboratory, K J Somaiya School of Engineering", fontsize=8.5, fontname="helv", fontfile=FONT_REG, color=SLATE)
    page1.insert_text(fitz.Point(48, 102), "Team: Sanjeevani Chaurasia (16014223073) | Vedant Mhapsekar (16014223095) | Aayush More (16014223104)", fontsize=8.5, fontname="helv", fontfile=FONT_BOLD, color=NAVY)

    # Faculty Callout Box
    page1.draw_rect(fitz.Rect(36, 122, 559.32, 152), color=(245/255, 158/255, 11/255), fill=AMBER_BG, width=1)
    page1.insert_text(fitz.Point(48, 136), "Faculty Advisory Note on Team Composition:", fontsize=8, fontname="helv", fontfile=FONT_BOLD, color=AMBER_TXT)
    page1.insert_text(fitz.Point(48, 146), "The challenge guidelines specify a 2-student team limit. Our project team includes 3 registered students as listed above, submitted for faculty confirmation.", fontsize=7.5, fontname="helv", fontfile=FONT_REG, color=AMBER_TXT)

    # Section 1: Creative Strategy & Brief Translation
    y = 170
    page1.insert_text(fitz.Point(36, y), "1. Creative Strategy & Brief Translation", fontsize=11, fontname="helv", fontfile=FONT_BOLD, color=NAVY)
    page1.draw_line(fitz.Point(36, y+3), fitz.Point(559.32, y+3), color=BLUE, width=1.5)
    
    body1 = (
        "The creative brief (briefs/practice.yaml) tasks the system with translating a single prompt into an engaging 44-second "
        "vertical video titled 'From Prompt to Product: How 7 AI Agents Build a Video'. The creative architecture decomposes "
        "the presentation into 5 balanced visual and narrative scenes designed for maximum viewer retention:\n"
        "- Scene 1 (The Prompt, 5.5s): Hook introducing the creative brief, audience parameters, and runtime constraints.\n"
        "- Scene 2 (7 AI Agents Workflow, 16.5s): Comprehensive breakdown of the 7-agent pipeline (Planner to Critic).\n"
        "- Scene 3 (Multi-Track Timeline Assembly, 8.0s): Synchronized composition of Pillow cards, speech, and subtitles.\n"
        "- Scene 4 (Critic QA HUD & Repair Loop, 8.0s): Demonstration of automated rule auditing and targeted repair loops.\n"
        "- Scene 5 (Final Video Reveal & Call to Action, 6.0s): Showcase of the broadcast MP4 and Somaiya Lab community CTA.\n"
        "This narrative strategy guarantees tight pacing (averaging 2.3 words/sec), high legibility, and zero cognitive overload."
    )
    rect1 = fitz.Rect(36, y+8, 559.32, y+110)
    page1.insert_textbox(rect1, body1, fontsize=8.0, fontname="helv", fontfile=FONT_REG, color=NAVY, lineheight=1.2)

    # Section 2: Seven-Agent Directed Acyclic Graph (DAG)
    y = 295
    page1.insert_text(fitz.Point(36, y), "2. Seven-Agent Directed Acyclic Graph (DAG) Architecture", fontsize=11, fontname="helv", fontfile=FONT_BOLD, color=NAVY)
    page1.draw_line(fitz.Point(36, y+3), fitz.Point(559.32, y+3), color=BLUE, width=1.5)
    
    diag_rect = fitz.Rect(36, y+10, 559.32, y+135)
    page1.insert_image(diag_rect, filename=str(diag_img_path))

    # Architecture Description Table
    y_table = y + 145
    col_w = [95, 195, 115, 118.32]
    headers = ["Agent & Stage", "Role & Core Responsibilities", "Primary Technology", "Output Artifact"]
    
    page1.draw_rect(fitz.Rect(36, y_table, 559.32, y_table + 16), color=None, fill=NAVY)
    cur_x = 36
    for i, h in enumerate(headers):
        page1.insert_text(fitz.Point(cur_x + 5, y_table + 11), h, fontsize=7.5, fontname="helv", fontfile=FONT_BOLD, color=WHITE)
        cur_x += col_w[i]
    
    rows = [
        ("1. Planner", "Decomposes brief into stages, budgets & timeline", "Groq / gpt-oss-120b", "outputs/plan.json"),
        ("2. RAG Researcher", "Extracts verbatim facts & citations from data/", "PyMuPDF / Exact Quote", "outputs/facts.json"),
        ("3. Scriptwriter", "Crafts timed spoken script (Hook, Body, CTA)", "Groq / Pydantic Schema", "outputs/script.json & .md"),
        ("4. Storyboarder", "Plans 6-10 visual shots & text (<80 chars)", "Groq / JSON Strict", "outputs/storyboard.json"),
        ("5. Asset Generator", "Renders 1080x1920 procedural graphic cards", "Pillow 13.0 (RGBA)", "outputs/asset_manifest.json"),
        ("6. Timeline Editor", "Aligns V1, A1, T1 tracks into NLE edit timeline", "Timeline Engine / JSON", "outputs/edit_plan.json"),
        ("7. Critic & QA", "Audits 18 quality rules; manages repair loop", "Deterministic + LLM", "outputs/qa_report.json"),
    ]
    
    row_y = y_table + 16
    for r_idx, r in enumerate(rows):
        bg = LIGHT_BG if r_idx % 2 == 0 else WHITE
        page1.draw_rect(fitz.Rect(36, row_y, 559.32, row_y + 17), color=BORDER, fill=bg, width=0.5)
        cur_x = 36
        for i, val in enumerate(r):
            page1.insert_text(fitz.Point(cur_x + 5, row_y + 12), val, fontsize=7.2, fontname="helv", fontfile=FONT_REG, color=NAVY)
            cur_x += col_w[i]
        row_y += 17

    page1.draw_line(fitz.Point(36, 810), fitz.Point(559.32, 810), color=BORDER, width=1)
    page1.insert_text(fitz.Point(36, 822), "AgentReel Process Report - K J Somaiya School of Engineering - Agentic AI Laboratory", fontsize=7.5, fontname="helv", fontfile=FONT_REG, color=SLATE)
    page1.insert_text(fitz.Point(510, 822), "Page 1 of 2", fontsize=7.5, fontname="helv", fontfile=FONT_BOLD, color=NAVY)

    # PAGE 2
    page2 = doc.new_page(width=595.32, height=841.92)
    
    # Section 3: Empirical Execution Metrics & Token Economics
    y = 40
    page2.insert_text(fitz.Point(36, y), "3. Empirical Execution Metrics & Token Economics", fontsize=11, fontname="helv", fontfile=FONT_BOLD, color=NAVY)
    page2.draw_line(fitz.Point(36, y+3), fitz.Point(559.32, y+3), color=BLUE, width=1.5)

    y_table2 = y + 12
    headers2 = ["Stage / Agent", "Provider & Model", "Latency", "Prompt Tok", "Compl Tok", "Cost Status"]
    col_w2 = [105, 140, 65, 70, 70, 73.32]
    page2.draw_rect(fitz.Rect(36, y_table2, 559.32, y_table2 + 16), color=None, fill=NAVY)
    cur_x = 36
    for i, h in enumerate(headers2):
        page2.insert_text(fitz.Point(cur_x + 5, y_table2 + 11), h, fontsize=7.5, fontname="helv", fontfile=FONT_BOLD, color=WHITE)
        cur_x += col_w2[i]

    metrics_rows = [
        ("Smoke Test", "groq: openai/gpt-oss-120b", "0.85s", "223", "33", "unknown (free tier)"),
        ("Planner (Initial)", "groq: openai/gpt-oss-120b", "1.13s", "836", "297", "unknown (free tier)"),
        ("Planner (Refined)", "groq: openai/gpt-oss-120b", "1.13s", "1,194", "292", "unknown (free tier)"),
        ("Scriptwriter", "groq: openai/gpt-oss-120b", "1.74s", "1,354", "662", "unknown (free tier)"),
        ("Storyboarder", "groq: openai/gpt-oss-120b", "2.01s", "1,280", "738", "unknown (free tier)"),
        ("Critic & QA", "groq: openai/gpt-oss-120b", "1.99s", "1,262", "677", "unknown (free tier)"),
        ("Script Repair", "groq: openai/gpt-oss-120b", "2.38s", "2,395", "1,053", "unknown (free tier)"),
        ("Storyboard Repair", "groq: openai/gpt-oss-120b", "2.86s", "2,428", "766", "unknown (free tier)"),
        ("Critic Verification", "groq: openai/gpt-oss-120b", "1.15s", "1,275", "86", "unknown (free tier)"),
    ]
    row_y = y_table2 + 16
    for r_idx, r in enumerate(metrics_rows):
        bg = LIGHT_BG if r_idx % 2 == 0 else WHITE
        page2.draw_rect(fitz.Rect(36, row_y, 559.32, row_y + 14), color=BORDER, fill=bg, width=0.5)
        cur_x = 36
        for i, val in enumerate(r):
            page2.insert_text(fitz.Point(cur_x + 5, row_y + 10.5), val, fontsize=7.0, fontname="helv", fontfile=FONT_REG, color=NAVY)
            cur_x += col_w2[i]
        row_y += 14

    # Section 4: Critic QA HUD & Bounded Repair Loop
    y = row_y + 16
    page2.insert_text(fitz.Point(36, y), "4. Critic QA HUD & Bounded Repair Loop", fontsize=11, fontname="helv", fontfile=FONT_BOLD, color=NAVY)
    page2.draw_line(fitz.Point(36, y+3), fitz.Point(559.32, y+3), color=BLUE, width=1.5)

    critic_text = (
        "The Critic agent (agents/critic.py) implements 18 automated validation checks across duration boundaries (35s-45s), "
        "scene continuity, timeline coverage, verbatim source quote verification, safe-zone typography (<80 chars), and LLM claim "
        "grounding. In our audited execution (outputs/qa_report.json), the pipeline achieved status PASS_WITH_WARNINGS with 0 blocking "
        "issues and 5 soft warnings (e.g. minor caption length soft limits and empty faculty docs notice).\n"
        "To prevent runaway recursion or infinite API expense, the repair loop is strictly bounded to a maximum of 3 iterations. "
        "Repairs rollback deterministically to the earliest offending agent (Scriptwriter for factual discrepancies, Storyboarder for "
        "shot/caption bounds) before re-verifying downstream artifacts."
    )
    rect_c = fitz.Rect(36, y+8, 559.32, y+80)
    page2.insert_textbox(rect_c, critic_text, fontsize=8.0, fontname="helv", fontfile=FONT_REG, color=NAVY, lineheight=1.2)

    # Section 5: Human Interventions & Tested Autonomy Level
    y = y + 96
    page2.insert_text(fitz.Point(36, y), "5. Human Interventions & Tested Autonomy Level", fontsize=11, fontname="helv", fontfile=FONT_BOLD, color=NAVY)
    page2.draw_line(fitz.Point(36, y+3), fitz.Point(559.32, y+3), color=BLUE, width=1.5)

    autonomy_text = (
        "- Tested Autonomy: Level 4 Autonomous Workflow. The entire 7-agent pipeline executed from YAML input to final video "
        "generation without manual prompts, hand-crafted edits, or human steering.\n"
        "- Human Intervention Audit: logs/interventions.md records exactly 0 human interventions during automated execution.\n"
        "- Determinism & Reproducibility: Seed fixed at 42; schemas pinned via Pydantic; LLM temperature set to 0.2.\n"
        "- Human-in-the-Loop Safeguard: An optional --require-review flag halts execution prior to export if pre-approval is required."
    )
    rect_a = fitz.Rect(36, y+8, 559.32, y+70)
    page2.insert_textbox(rect_a, autonomy_text, fontsize=8.0, fontname="helv", fontfile=FONT_REG, color=NAVY, lineheight=1.2)

    # Section 6: Broadcast Deliverables & Subtitle Alignment
    y = y + 80
    page2.insert_text(fitz.Point(36, y), "6. Broadcast Deliverables & Subtitle Alignment", fontsize=11, fontname="helv", fontfile=FONT_BOLD, color=NAVY)
    page2.draw_line(fitz.Point(36, y+3), fitz.Point(559.32, y+3), color=BLUE, width=1.5)

    media_text = (
        "- Final Video Deliverable (outputs/final_video_v3.mp4): Broadcast-ready 9:16 vertical video (1080x1920) at 30.0 fps, "
        "encoded with H.264 High Profile and stereo AAC audio (48,000 Hz). Total file size: 2.21 MB; duration: 44.02s (target: 44.0s).\n"
        "- Subtitle Synchronization (outputs/AgentReel_Final.srt): 6 SubRip subtitle cues ordered sequentially from 00:00:00 to "
        "00:00:44. Timings are strictly non-overlapping and mapped verbatim to the voiceover narration track, guaranteeing full "
        "broadcast compliance across social media players."
    )
    rect_m = fitz.Rect(36, y+8, 559.32, y+70)
    page2.insert_textbox(rect_m, media_text, fontsize=8.0, fontname="helv", fontfile=FONT_REG, color=NAVY, lineheight=1.2)

    # Section 7: Production Limitations & Future Roadmap
    y = y + 80
    page2.insert_text(fitz.Point(36, y), "7. Production Limitations & Future Improvements", fontsize=11, fontname="helv", fontfile=FONT_BOLD, color=NAVY)
    page2.draw_line(fitz.Point(36, y+3), fitz.Point(559.32, y+3), color=BLUE, width=1.5)

    limits_text = (
        "1. API Rate Limiting: Cloud LLM providers (e.g. Groq free tier) impose aggressive TPM limits. In Milestone B, an HTTP 429 "
        "prompted configuring max_retries=0 and fallback handling. Future releases should integrate exponential backoff with multi-provider failover.\n"
        "2. TTS Voice Diversity: Current local narration relies on macOS say/FFmpeg synthesis. Integrating neural TTS (e.g. ElevenLabs or "
        "Coqui TTS) will enable emotion-aware intonation and multi-character voice acting.\n"
        "3. Dynamic Audio Ducking: Background music was intentionally omitted to prioritize speech clarity. Future iterations should add an "
        "automated sidechain audio ducker to lower ambient music during active speech."
    )
    rect_l = fitz.Rect(36, y+8, 559.32, y+90)
    page2.insert_textbox(rect_l, limits_text, fontsize=8.0, fontname="helv", fontfile=FONT_REG, color=NAVY, lineheight=1.2)

    page2.draw_line(fitz.Point(36, 810), fitz.Point(559.32, 810), color=BORDER, width=1)
    page2.insert_text(fitz.Point(36, 822), "AgentReel Process Report - K J Somaiya School of Engineering - Agentic AI Laboratory", fontsize=7.5, fontname="helv", fontfile=FONT_REG, color=SLATE)
    page2.insert_text(fitz.Point(510, 822), "Page 2 of 2", fontsize=7.5, fontname="helv", fontfile=FONT_BOLD, color=NAVY)

    doc.save(PDF_OUT)
    doc.close()
    if diag_img_path.exists():
        diag_img_path.unlink()
    print(f"Successfully generated concise 2-page process report at: {PDF_OUT}")

if __name__ == "__main__":
    build_pdf()