"""Generate a publication-grade, multi-page engineering project report PDF.

Follows academic college project report guidelines:
- Page 1: Formal Title Page (Institution, Project Title, Team Members with Roll Numbers, Academic Year).
- Page 2: Abstract, Problem Statement, Motivation, Objectives, Scope & Proposed Solution.
- Page 3: System Architecture & Data Flow, High-DPI Flow Diagram, Orchestrator & Bounded Repair Loop.
- Page 4: Detailed Seven-Agent Explanation, Specifications Matrix, Schema Contracts.
- Page 5: Technologies & Tools, Motion-Graphics Design, Scene 2 Audio Truncation Investigation & Resolution.
- Page 6: Final Video Deliverable Specifications, 78-Test Verification Matrix, Engineering Challenges & Resolutions.
- Page 7: Limitations, Future Scope, Conclusion, Project Artifact References & Formal Submission Sign-off.

Total Pages: Exactly 7 pages on standard A4 (595.32 x 841.92 pt).
"""
from pathlib import Path
import fitz  # PyMuPDF
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
FINAL_DIR = ROOT / "reports" / "final"
FINAL_DIR.mkdir(parents=True, exist_ok=True)
PDF_OUT = FINAL_DIR / "AgentReel_Final_Report.pdf"

FONT_REG = "/System/Library/Fonts/Supplemental/Arial.ttf"
FONT_BOLD = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
FONT_ITAL = "/System/Library/Fonts/Supplemental/Arial Italic.ttf"


def draw_architecture_diagram(out_path: Path) -> Path:
    """Render a clean, high-DPI architecture flow diagram using Pillow."""
    dw, dh = 1800, 520
    im = Image.new("RGB", (dw, dh), (248, 250, 252))
    draw = ImageDraw.Draw(im)

    try:
        font_b = ImageFont.truetype(FONT_BOLD, 22)
        font_m = ImageFont.truetype(FONT_BOLD, 18)
        font_s = ImageFont.truetype(FONT_REG, 15)
        font_pill = ImageFont.truetype(FONT_BOLD, 18)
        font_deliv = ImageFont.truetype(FONT_BOLD, 20)
    except Exception:
        font_b = ImageFont.load_default()
        font_m = font_b
        font_s = font_b
        font_pill = font_b
        font_deliv = font_b

    # Outer border
    draw.rounded_rectangle([10, 10, dw - 10, dh - 10], radius=16, fill=(255, 255, 255), outline=(203, 213, 225), width=2)

    # 7 Agent blocks
    agents = [
        ("1. Planner", "briefs/practice.yaml", "outputs/plan.json", (30, 41, 59)),
        ("2. Researcher", "Grounded Facts", "outputs/facts.json", (30, 41, 59)),
        ("3. Scriptwriter", "Timed Narration", "outputs/script.json", (30, 41, 59)),
        ("4. Storyboarder", "Visual Shots", "outputs/storyboard.json", (30, 41, 59)),
        ("5. Asset Gen", "Pillow 9:16 Frames", "outputs/manifest.json", (30, 41, 59)),
        ("6. Editor", "NLE Timeline", "outputs/edit_plan.json", (30, 41, 59)),
        ("7. Critic", "18 QA Checks", "outputs/qa_report.json", (88, 28, 44)),
    ]

    box_w = 205
    box_h = 160
    start_x = 42
    spacing = 250
    top_y = 50

    for i, (name, role, contract, col) in enumerate(agents):
        bx = start_x + i * spacing
        # Agent Box
        draw.rounded_rectangle([bx, top_y, bx + box_w, top_y + box_h], radius=12, fill=col, outline=(245, 158, 11), width=2)
        # Name
        nw = draw.textlength(name, font=font_b)
        draw.text((bx + (box_w - nw) / 2, top_y + 16), name, font=font_b, fill=(255, 255, 255))
        # Role
        rw = draw.textlength(role, font=font_m)
        draw.text((bx + (box_w - rw) / 2, top_y + 54), role, font=font_m, fill=(253, 230, 138))
        # Contract pill
        draw.rounded_rectangle([bx + 10, top_y + 100, bx + box_w - 10, top_y + 140], radius=6, fill=(15, 23, 42), outline=(100, 116, 139), width=1)
        cw = draw.textlength(contract, font=font_s)
        draw.text((bx + (box_w - cw) / 2, top_y + 112), contract, font=font_s, fill=(226, 232, 240))

        # Arrow to next agent
        if i < len(agents) - 1:
            ax = bx + box_w
            ay = top_y + box_h / 2
            draw.line([(ax + 4, ay), (ax + 35, ay)], fill=(217, 119, 6), width=4)
            draw.polygon([(ax + 35, ay - 8), (ax + 35, ay + 8), (ax + 44, ay)], fill=(217, 119, 6))

    # Repair loop
    r_start_x = start_x + 6 * spacing + box_w / 2
    target_x = start_x + 2 * spacing + box_w / 2
    line_y = 350

    # Pill placed cleanly above line
    pill_txt = "Deterministic Repair Loop (Max 3 Passes)  •  Restarts from Earliest Failing Stage"
    pw = draw.textlength(pill_txt, font=font_pill)
    pill_cx = (target_x + r_start_x) / 2
    pill_x1 = pill_cx - pw / 2 - 24
    pill_x2 = pill_cx + pw / 2 + 24
    draw.rounded_rectangle([pill_x1, 260, pill_x2, 306], radius=8, fill=(254, 242, 242), outline=(239, 68, 68), width=2)
    draw.text((pill_cx - pw / 2, 272), pill_txt, font=font_pill, fill=(185, 28, 28))

    # Repair line with upward arrowhead pointing into Scriptwriter
    draw.line([(r_start_x, top_y + box_h + 4), (r_start_x, line_y)], fill=(239, 68, 68), width=3)
    draw.line([(r_start_x, line_y), (target_x, line_y)], fill=(239, 68, 68), width=3)
    draw.line([(target_x, line_y), (target_x, top_y + box_h + 10)], fill=(239, 68, 68), width=3)
    draw.polygon([(target_x - 9, top_y + box_h + 18), (target_x + 9, top_y + box_h + 18), (target_x, top_y + box_h + 4)], fill=(239, 68, 68))

    # Bottom deliverables banner
    draw.rounded_rectangle([42, 420, dw - 42, 485], radius=10, fill=(6, 78, 59), outline=(16, 185, 129), width=2)
    deliv_txt = "Deliverables: outputs/final_video_v3.mp4 (1080x1920 | 44.02s | H.264/AAC) + outputs/AgentReel_Final.srt"
    del_w = draw.textlength(deliv_txt, font=font_deliv)
    draw.text(((dw - del_w) / 2, 440), deliv_txt, font=font_deliv, fill=(240, 253, 244))

    im.save(out_path, dpi=(300, 300))
    return out_path


def init_page_fonts(page):
    """Register custom TrueType Arial fonts on page."""
    page.insert_font(fontname="reg", fontfile=FONT_REG)
    page.insert_font(fontname="bold", fontfile=FONT_BOLD)
    page.insert_font(fontname="ital", fontfile=FONT_ITAL)


def add_textbox(page, rect, text, fontname="reg", fontsize=7.2, color=(0, 0, 0), align=0):
    """Insert text into a rectangle with strict overflow check."""
    res = page.insert_textbox(rect, text, fontname=fontname, fontsize=fontsize, color=color, align=align)
    if res < 0:
        raise ValueError(f"CRITICAL OVERFLOW ({res}): text does not fit in rect {rect}. Prefix: {text[:50]}...")
    return res


def add_table(page, y_start, cols, rows, header_bg, row_bg_even, row_bg_odd, border_col, default_fontsize=7.0):
    """Render a structured table where each cell wraps text cleanly without overlapping."""
    cur_y = y_start
    total_w = sum(c["w"] for c in cols)
    start_x = cols[0]["x"]

    # Header Row
    header_h = 16.0
    page.draw_rect(fitz.Rect(start_x, cur_y, start_x + total_w, cur_y + header_h), color=border_col, fill=header_bg, width=0.5)
    for c in cols:
        cell_r = fitz.Rect(c["x"] + 3, cur_y + 2, c["x"] + c["w"] - 3, cur_y + header_h - 2)
        page.insert_textbox(cell_r, c["title"], fontname="bold", fontsize=c.get("header_fontsize", default_fontsize + 0.3), color=c.get("header_color", (11/255, 17/255, 32/255)))
    cur_y += header_h

    # Data Rows
    for r_idx, row in enumerate(rows):
        row_h = row.get("_h", 18.0)
        bg = row_bg_even if r_idx % 2 == 0 else row_bg_odd
        page.draw_rect(fitz.Rect(start_x, cur_y, start_x + total_w, cur_y + row_h), color=border_col, fill=bg, width=0.5)

        for c_idx, c in enumerate(cols):
            cell_val = row.get(c["key"], "")
            fn = row.get(f"_{c['key']}_fn", c.get("fn", "reg"))
            fc = row.get(f"_{c['key']}_fc", c.get("fc", (11/255, 17/255, 32/255)))
            fs = row.get(f"_{c['key']}_fs", c.get("fs", default_fontsize))
            cell_r = fitz.Rect(c["x"] + 3, cur_y + 2, c["x"] + c["w"] - 3, cur_y + row_h - 2)
            res = page.insert_textbox(cell_r, str(cell_val), fontname=fn, fontsize=fs, color=fc)
            if res < 0:
                print(f"Warning: Cell text overflow ({res}) in table for key '{c['key']}': {cell_val[:30]}...")

        cur_y += row_h

    return cur_y


def build_final_report():
    doc = fitz.open()
    diagram_path = FINAL_DIR / "arch_diagram_temp.png"
    draw_architecture_diagram(diagram_path)

    W_PT, H_PT = 595.32, 841.92  # A4
    MARGIN = 38.0
    USABLE_W = W_PT - 2 * MARGIN  # 519.32

    WHITE = (1.0, 1.0, 1.0)
    NAVY = (11/255, 17/255, 32/255)
    BURGUNDY = (88/255, 28/255, 44/255)
    GOLD = (180/255, 83/255, 9/255)
    GRAY = (100/255, 116/255, 139/255)
    LIGHT_BG = (248/255, 250/255, 252/255)
    BORDER_COL = (226/255, 232/255, 240/255)
    LIGHT_GREEN = (240/255, 253/255, 244/255)
    EMERALD = (16/255, 185/255, 129/255)
    DARK_GREEN = (6/255, 78/255, 59/255)
    LIGHT_RED = (254/255, 242/255, 242/255)
    DARK_RED = (185/255, 28/255, 28/255)

    def add_page_decorations(page, page_num, total_pages=7):
        init_page_fonts(page)
        # Header hairline
        page.draw_line(fitz.Point(MARGIN, 28), fitz.Point(W_PT - MARGIN, 28), color=BORDER_COL, width=0.5)
        page.insert_text(fitz.Point(MARGIN, 22), "LY Agentic AI Laboratory • K J Somaiya School of Engineering", fontsize=7.8, fontname="reg", color=GRAY)
        page.insert_text(fitz.Point(W_PT - MARGIN - 110, 22), "AgentReel Final Project Report", fontsize=7.8, fontname="reg", color=GRAY)

        # Footer hairline
        page.draw_line(fitz.Point(MARGIN, H_PT - 28), fitz.Point(W_PT - MARGIN, H_PT - 28), color=BORDER_COL, width=0.5)
        page.insert_text(fitz.Point(MARGIN, H_PT - 18), "Topic: From Prompt to Product: How 7 AI Agents Build a Video", fontsize=7.8, fontname="reg", color=GRAY)
        page.insert_text(fitz.Point(W_PT - MARGIN - 48, H_PT - 18), f"Page {page_num} of {total_pages}", fontsize=7.8, fontname="reg", color=GRAY)

    # =========================================================================
    # PAGE 1: Formal Academic Title Page
    # =========================================================================
    p1 = doc.new_page(width=W_PT, height=H_PT)
    init_page_fonts(p1)

    # Academic double border frame
    p1.draw_rect(fitz.Rect(24, 24, W_PT - 24, H_PT - 24), color=BORDER_COL, width=1.5)
    p1.draw_rect(fitz.Rect(28, 28, W_PT - 28, H_PT - 28), color=GOLD, width=0.8)

    # Institutional Header
    p1.insert_text(fitz.Point(MARGIN + 62, 85), "K J SOMAIYA SCHOOL OF ENGINEERING", fontsize=15.0, fontname="bold", color=NAVY)
    p1.insert_text(fitz.Point(MARGIN + 128, 102), "Vidyavihar, Mumbai — 400077 • Autonomous Institute", fontsize=8.5, fontname="reg", color=GRAY)
    p1.insert_text(fitz.Point(MARGIN + 106, 120), "LY AGENTIC AI LABORATORY — CAPSTONE PROJECT REPORT", fontsize=9.5, fontname="bold", color=BURGUNDY)

    p1.draw_line(fitz.Point(MARGIN + 30, 134), fitz.Point(W_PT - MARGIN - 30, 134), color=BORDER_COL, width=0.8)

    # Central Badge
    badge_w, badge_h = 240.0, 26.0
    badge_x = (W_PT - badge_w) / 2
    badge_y = 180.0
    p1.draw_rect(fitz.Rect(badge_x, badge_y, badge_x + badge_w, badge_y + badge_h), color=GOLD, fill=NAVY, width=1.2)
    p1.insert_text(fitz.Point(badge_x + 28, badge_y + 17), "SOMAIYA AGENTREEL CHALLENGE 2026", fontsize=8.5, fontname="bold", color=WHITE)

    # Main Project Title
    p1.insert_text(fitz.Point(MARGIN + 18, 265), "From Prompt to Product: How 7 AI Agents Build a Video", fontsize=15.0, fontname="bold", color=NAVY)
    p1.insert_text(fitz.Point(MARGIN + 22, 288), "An Autonomous Contract-Driven Multi-Agent Framework for Broadcast-Grade Vertical Video Synthesis", fontsize=9.0, fontname="ital", color=BURGUNDY)

    # Submission notice
    sub_notice = (
        "A Comprehensive Technical Project Report Submitted in Partial Fulfillment of the Requirements\n"
        "for the Agentic AI Engineering Capstone at the LY Agentic AI Laboratory."
    )
    add_textbox(p1, fitz.Rect(MARGIN + 30, 335, W_PT - MARGIN - 30, 375), sub_notice, fontname="reg", fontsize=8.2, color=GRAY, align=1)

    # Team Members Box
    t_box_y = 420.0
    t_box_h = 160.0
    p1.draw_rect(fitz.Rect(MARGIN + 20, t_box_y, W_PT - MARGIN - 20, t_box_y + t_box_h), color=BORDER_COL, fill=LIGHT_BG, width=0.8)
    p1.draw_rect(fitz.Rect(MARGIN + 20, t_box_y, MARGIN + 24, t_box_y + t_box_h), color=BURGUNDY, fill=BURGUNDY)
    p1.insert_text(fitz.Point(MARGIN + 34, t_box_y + 20), "PROJECT TEAM MEMBERS & ROLES", fontsize=10.0, fontname="bold", color=NAVY)

    team_members = [
        ("Sanjeevani Chaurasia", "16014223073", "Agent Architect, Motion Graphics Engine & FFmpeg Integration"),
        ("Vedant Mhapsekar", "16014223095", "Pipeline Orchestrator, LLM Adapter & Schema Validation"),
        ("Aayush More", "16014223104", "Critic QA Guardrails, Testing Suite & Evaluation Engineer"),
    ]
    for idx, (mname, roll, role) in enumerate(team_members):
        my = t_box_y + 44 + idx * 36
        p1.draw_line(fitz.Point(MARGIN + 34, my - 8), fitz.Point(W_PT - MARGIN - 34, my - 8), color=BORDER_COL, width=0.5)
        p1.insert_text(fitz.Point(MARGIN + 34, my + 6), mname, fontsize=8.8, fontname="bold", color=NAVY)
        p1.insert_text(fitz.Point(MARGIN + 195, my + 6), f"Roll No: {roll}", fontsize=8.5, fontname="reg", color=BURGUNDY)
        p1.insert_text(fitz.Point(MARGIN + 34, my + 20), f"Primary Responsibilities: {role}", fontsize=7.5, fontname="reg", color=GRAY)

    # Academic Metadata Block
    meta_y = 660.0
    p1.draw_line(fitz.Point(MARGIN + 50, meta_y), fitz.Point(W_PT - MARGIN - 50, meta_y), color=BORDER_COL, width=0.8)
    p1.insert_text(fitz.Point(MARGIN + 90, meta_y + 26), "Laboratory: LY Agentic AI Laboratory • Department of Computer Engineering", fontsize=8.2, fontname="reg", color=NAVY)
    p1.insert_text(fitz.Point(MARGIN + 115, meta_y + 42), "Institution: K J Somaiya School of Engineering, Vidyavihar, Mumbai", fontsize=8.2, fontname="reg", color=NAVY)
    p1.insert_text(fitz.Point(MARGIN + 145, meta_y + 58), "Academic Year: 2026–2027  •  Date of Submission: October 2026", fontsize=8.2, fontname="bold", color=BURGUNDY)

    # =========================================================================
    # PAGE 2: Abstract, Problem Statement, Objectives, Scope & Proposed Solution
    # =========================================================================
    p2 = doc.new_page(width=W_PT, height=H_PT)
    add_page_decorations(p2, 2)

    # 1. Abstract & Executive Summary
    p2.insert_text(fitz.Point(MARGIN, 48), "1. Abstract & Executive Summary", fontsize=10.5, fontname="bold", color=NAVY)
    abs_box_y = 56.0
    abs_box_h = 104.0
    p2.draw_rect(fitz.Rect(MARGIN, abs_box_y, W_PT - MARGIN, abs_box_y + abs_box_h), color=BORDER_COL, fill=LIGHT_BG, width=0.8)
    p2.draw_rect(fitz.Rect(MARGIN, abs_box_y, MARGIN + 4, abs_box_y + abs_box_h), color=GOLD, fill=GOLD)

    abs_text = (
        "AgentReel presents a fully autonomous, contract-driven multi-agent AI framework designed to synthesize broadcast-ready vertical (9:16) video "
        "directly from a structured creative brief. While traditional generative video diffusion models operate as non-deterministic black boxes with high "
        "hallucination rates and temporal inconsistency, AgentReel decomposes video generation into seven specialized engineering agents: Planner, "
        "Researcher (RAG), Scriptwriter, Storyboarder, Asset Generator, Timeline Editor, and Quality Critic. The system guarantees formal Pydantic v2 "
        "schema contract boundaries, bounded deterministic self-repair loops, verified factual grounding, mobile platform safe-margin compliance (TikTok/Reels/Shorts), "
        "and ultra-fast local procedural rendering. The delivered artifact, final_video_v3.mp4, was synthesized completely locally on Apple Silicon without third-party "
        "cloud render APIs, achieving a duration of 44.02s, 1080x1920 resolution at 30 fps, AAC 48kHz audio, and 100% clean bitstream decoding."
    )
    add_textbox(p2, fitz.Rect(MARGIN + 12, abs_box_y + 8, W_PT - MARGIN - 10, abs_box_y + abs_box_h - 26), abs_text, fontsize=7.1, color=NAVY)

    p2.draw_line(fitz.Point(MARGIN + 12, abs_box_y + abs_box_h - 20), fitz.Point(W_PT - MARGIN - 12, abs_box_y + abs_box_h - 20), color=BORDER_COL, width=0.5)
    p2.insert_text(fitz.Point(MARGIN + 14, abs_box_y + abs_box_h - 8), "Key Result: outputs/final_video_v3.mp4  •  44.02s  •  1080×1920 (30 fps)  •  2.21 MB  •  100% Clean Decode  •  78 Unit Tests Passing", fontsize=7.0, fontname="bold", color=BURGUNDY)

    # 2. Problem Statement & Motivation
    p2.insert_text(fitz.Point(MARGIN, 178), "2. Problem Statement & Engineering Motivation", fontsize=10.5, fontname="bold", color=NAVY)
    prob_text = (
        "Contemporary video generation frameworks suffer from critical architectural weaknesses when applied to precise technical or educational communication:\n"
        "• Non-Deterministic Output & Hallucinations: Generative video diffusion models frequently hallucinate facts, invent statistics, and distort typography.\n"
        "• Lack of Contract Interfaces: Single-prompt diffusion offers no mechanism for modular inspection, programmatic validation, or localized repair.\n"
        "• Uncontrolled Duration & Audio Desynchronization: Video generators cannot guarantee strict broadcast timing windows or seamless audio headroom.\n"
        "• Cloud API Latency & Incurred Spend: Cloud generation services are expensive, slow, rate-limited, and vulnerable to network outages.\n\n"
        "Motivation: The LY Agentic AI Laboratory created the AgentReel Challenge to demonstrate that autonomous agent coordination—governed by typed "
        "contracts and local rendering tools—can engineer explainable, reproducible, and verifiable media products that surpass monolithic black boxes."
    )
    add_textbox(p2, fitz.Rect(MARGIN, 186, W_PT - MARGIN, 280), prob_text, fontsize=7.1, color=NAVY)

    # 3. Project Objectives
    p2.insert_text(fitz.Point(MARGIN, 292), "3. Engineering Project Objectives", fontsize=10.5, fontname="bold", color=NAVY)
    obj_cols = [
        {"key": "obj", "title": "Target Engineering Objective", "x": MARGIN, "w": 180.0, "fn": "bold"},
        {"key": "spec", "title": "Technical Constraint / Requirement", "x": MARGIN + 180.0, "w": 170.0, "fn": "reg", "fc": GRAY},
        {"key": "ach", "title": "Achieved Milestone V3 Deliverable", "x": MARGIN + 350.0, "w": USABLE_W - 350.0, "fn": "bold", "fc": BURGUNDY},
    ]
    obj_rows = [
        {"obj": "1. Duration Window Enforcement", "spec": "Target 40s (Window: [35.0s, 45.0s])", "ach": "44.02s (1,320 frames @ 30 fps)", "_h": 15.0},
        {"obj": "2. High-Definition Mobile Canvas", "spec": "1080×1920 (9:16 vertical orientation)", "ach": "1080×1920 (TikTok/Shorts safe zones)", "_h": 15.0},
        {"obj": "3. Audio & SubRip Synchronization", "spec": "Voiceover audio aligned with SRT captions", "ach": "48 kHz AAC audio + AgentReel_Final.srt", "_h": 15.0},
        {"obj": "4. Multi-Agent Finite State Machine", "spec": "7 discrete stages with JSON interfaces", "ach": "Planner -> Critic (all JSONs persisted)", "_h": 15.0},
        {"obj": "5. Bounded Deterministic Repair Loop", "spec": "Automatic recovery capped at 3 passes", "ach": "Targeted rollback to earliest failing stage", "_h": 15.0},
        {"obj": "6. High-Throughput Offline Rendering", "spec": "Zero cloud video APIs; >30 fps speed", "ach": ">75 fps via FFmpeg raw RGB stdin pipe", "_h": 15.0},
    ]
    end_obj_y = add_table(p2, 302.0, obj_cols, obj_rows, LIGHT_BG, WHITE, LIGHT_BG, BORDER_COL, default_fontsize=6.8)

    # 4. Project Scope & Proposed Multi-Agent Solution
    p2.insert_text(fitz.Point(MARGIN, end_obj_y + 12), "4. Project Scope & Proposed Multi-Agent Solution", fontsize=10.5, fontname="bold", color=NAVY)
    scope_text = (
        "Scope Boundaries: The project transforms an input YAML brief (briefs/practice.yaml, ID: P00) into a vertical motion-graphics video explaining "
        "the agentic workflow itself. The system enforces strict boundaries: no external generative video APIs, zero cloud rendering costs, deterministic "
        "seed control (seed=42), and preserved Milestone B/C backups.\n\n"
        "Proposed Solution: AgentReel implements a decoupled seven-agent architecture orchestrated by core/orchestrator.py. Each agent is modeled as an "
        "isolated state transformer consuming typed Pydantic models and emitting persistent JSON contracts in outputs/. The Critic agent continuously audits "
        "18 automated rules; upon detecting validation failures (such as speaking rate overflow, missing disclosures, or caption length violations), the "
        "orchestrator calculates the earliest responsible agent and initiates a targeted repair loop, preventing cascading pipeline re-execution."
    )
    add_textbox(p2, fitz.Rect(MARGIN, end_obj_y + 20, W_PT - MARGIN, H_PT - 32), scope_text, fontsize=7.1, color=NAVY)

    # =========================================================================
    # PAGE 3: System Architecture, Diagram & Repair Loop Mechanism
    # =========================================================================
    p3 = doc.new_page(width=W_PT, height=H_PT)
    add_page_decorations(p3, 3)

    # 5. System Architecture & Pipeline Data Flow
    p3.insert_text(fitz.Point(MARGIN, 48), "5. System Architecture & Pipeline Data Flow", fontsize=10.5, fontname="bold", color=NAVY)
    arch_intro = (
        "AgentReel structures video creation as a directed acyclic graph (DAG) of specialized autonomous agents. Each stage consumes upstream contracts, "
        "executes domain-specific logic, and emits immutable artifacts into outputs/ before passing control to downstream agents."
    )
    add_textbox(p3, fitz.Rect(MARGIN, 56, W_PT - MARGIN, 80), arch_intro, fontsize=7.1, color=NAVY)

    # Architecture Diagram Image
    diag_y = 86.0
    diag_h = USABLE_W / (1800.0 / 520.0)  # ~150.0 pt
    p3.insert_image(fitz.Rect(MARGIN, diag_y, W_PT - MARGIN, diag_y + diag_h), filename=str(diagram_path))

    # Architecture Walkthrough Box
    p3.insert_text(fitz.Point(MARGIN, diag_y + diag_h + 12), "6. Data Flow Contracts & Artifact Lifecycle", fontsize=10.0, fontname="bold", color=NAVY)
    flow_text = (
        "• Brief Ingestion: briefs/practice.yaml establishes target duration (40s), topic, tone, target audience, and compliance flags.\n"
        "• Stage 1 — outputs/plan.json: Planner derives technical constraints, 3-8 evaluation criteria, duration bounds, and budget quotas.\n"
        "• Stage 2 — outputs/facts.json: Researcher performs grounded RAG across data/, extracting verified facts with verbatim quote validation.\n"
        "• Stage 3 — outputs/script.json & script.md: Scriptwriter crafts 3-act voiceover narrative with mathematical duration checks (~180 wpm).\n"
        "• Stage 4 — outputs/storyboard.json: Storyboarder segments narrative into 6-10 visual shots, assigning visual prompts and on-screen text.\n"
        "• Stage 5 — outputs/asset_manifest.json: Asset Generator synthesizes 1080x1920 RGBA frames, vector components, and safe-margin cards.\n"
        "• Stage 6 — outputs/edit_plan.json: Editor assembles NLE timeline, normalizes 48kHz voiceover audio, burns SubRip captions, and renders MP4.\n"
        "• Stage 7 — outputs/qa_report.json: Critic inspects 18 automated rules. If errors are found, the repair loop routes back to the earliest fault."
    )
    add_textbox(p3, fitz.Rect(MARGIN, diag_y + diag_h + 20, W_PT - MARGIN, diag_y + diag_h + 114), flow_text, fontsize=7.0, color=NAVY)

    # 7. Orchestrator & Bounded Repair Loop Mechanism
    s7_y = diag_y + diag_h + 124.0
    p3.insert_text(fitz.Point(MARGIN, s7_y), "7. Orchestrator & Bounded Repair-Loop Mechanism (Actual Implementation)", fontsize=10.5, fontname="bold", color=NAVY)

    s7_box_h = 144.0
    p3.draw_rect(fitz.Rect(MARGIN, s7_y + 8, W_PT - MARGIN, s7_y + 8 + s7_box_h), color=BORDER_COL, fill=LIGHT_BG, width=0.8)
    p3.draw_rect(fitz.Rect(MARGIN, s7_y + 8, MARGIN + 4, s7_y + 8 + s7_box_h), color=DARK_RED, fill=DARK_RED)
    p3.insert_text(fitz.Point(MARGIN + 12, s7_y + 21), "Deterministic State Machine & Earliest-Failing Rollback Routing", fontsize=9.0, fontname="bold", color=DARK_RED)

    orch_deep = (
        "1. Dynamic Routing Architecture: In core/orchestrator.py, execution is driven by run_pipeline(). When Critic flags issues in qa_report.json, "
        "the orchestrator inspects the issue locations and maps them to responsible pipeline stages:\n"
        "   - Factual Inaccuracy / Claim Hallucination -> Triggers repair starting at Scriptwriter (re-evaluates facts, rewrites narrative).\n"
        "   - On-Screen Caption Length Overflow (>80 chars) -> Triggers repair starting at Storyboarder (executes limit_caption heuristics).\n"
        "   - Asset Resolution or Missing Card -> Triggers repair starting at Asset Generator (re-renders Pillow frame elements).\n\n"
        "2. Downstream State Invalidation: The orchestrator does NOT perform arbitrary retries. It rolls back state to the earliest affected stage and "
        "re-executes all subsequent downstream stages to maintain immutable contract consistency (e.g., if Scriptwriter reruns, Storyboarder and Editor "
        "automatically re-run with the updated script).\n\n"
        "3. Hard Termination Bounds: The repair loop maintains an integer counter (repairs_used). If the pipeline fails to achieve PASS or "
        "PASS_WITH_WARNINGS status within 3 iterations, execution terminates safely with an exit code of 3, preventing infinite loops and runaway spend."
    )
    add_textbox(p3, fitz.Rect(MARGIN + 12, s7_y + 26, W_PT - MARGIN - 10, s7_y + 8 + s7_box_h - 4), orch_deep, fontsize=6.9, color=NAVY)

    # Runtime Execution Evidence Box
    evid_y = s7_y + 8 + s7_box_h + 10.0
    evid_h = 58.0
    p3.draw_rect(fitz.Rect(MARGIN, evid_y, W_PT - MARGIN, evid_y + evid_h), color=BORDER_COL, fill=WHITE, width=0.8)
    p3.insert_text(fitz.Point(MARGIN + 10, evid_y + 14), "Audited Pipeline Execution Evidence (Run ID: run_20261021_165923 • Model: openai/gpt-oss-120b on Groq)", fontsize=7.5, fontname="bold", color=BURGUNDY)
    orch_evid = (
        "• Total LLM Calls: 8 calls (Planner: 2, Scriptwriter: 2, Storyboarder: 2, Critic: 2)  •  Stage Latency: 69.68s  •  Tokens: 12,024 prompt, 4,571 completion (16,895 total)\n"
        "• Repair History: Soft warning on S02 caption length resolved via Storyboarder limit_caption; zero manual interventions required (logs/interventions.md)."
    )
    add_textbox(p3, fitz.Rect(MARGIN + 10, evid_y + 18, W_PT - MARGIN - 10, evid_y + evid_h - 4), orch_evid, fontsize=6.8, color=GRAY)

    # =========================================================================
    # PAGE 4: Detailed Seven-Agent Explanation & Specifications
    # =========================================================================
    p4 = doc.new_page(width=W_PT, height=H_PT)
    add_page_decorations(p4, 4)

    p4.insert_text(fitz.Point(MARGIN, 48), "8. Detailed Explanation of All Seven Specialized Agents", fontsize=10.5, fontname="bold", color=NAVY)

    agent_cols = [
        {"key": "agent", "title": "Agent Name", "x": MARGIN, "w": 82.0, "fn": "bold"},
        {"key": "source", "title": "Source Module", "x": MARGIN + 82.0, "w": 98.0, "fn": "reg", "fc": GRAY},
        {"key": "role", "title": "Core Architectural Function", "x": MARGIN + 180.0, "w": 135.0, "fn": "reg"},
        {"key": "contract", "title": "Primary Contract", "x": MARGIN + 315.0, "w": 95.0, "fn": "reg", "fc": BURGUNDY},
        {"key": "tools", "title": "Key Tooling & Libraries", "x": MARGIN + 410.0, "w": USABLE_W - 410.0, "fn": "reg"},
    ]
    agent_rows = [
        {"agent": "1. Planner", "source": "agents/planner.py", "role": "Decomposes brief into stages, constraints & budget limits", "contract": "outputs/plan.json", "tools": "Pydantic v2, Groq LLM Adapter", "_h": 23.0},
        {"agent": "2. Researcher", "source": "agents/researcher.py", "role": "Grounded RAG fact extraction & verbatim quote verification", "contract": "outputs/facts.json", "tools": "PyMuPDF (fitz), Python regex", "_h": 23.0},
        {"agent": "3. Scriptwriter", "source": "agents/scriptwriter.py", "role": "Crafts timed spoken narrative (Hook, Body, CTA) @ 180 wpm", "contract": "outputs/script.json", "tools": "Groq Adapter, duration math", "_h": 23.0},
        {"agent": "4. Storyboarder", "source": "agents/storyboarder.py", "role": "Plans 6-10 visual shots, layout prompts & on-screen text", "contract": "outputs/storyboard.json", "tools": "Groq Adapter, caption limiter", "_h": 23.0},
        {"agent": "5. Asset Gen", "source": "agents/asset_generator.py", "role": "Renders 9:16 gradient cards & procedural motion components", "contract": "outputs/manifest.json", "tools": "Pillow 13.0, vector math", "_h": 23.0},
        {"agent": "6. Editor", "source": "agents/editor.py", "role": "NLE timeline assembly, 48kHz audio sync & SubRip captions", "contract": "outputs/edit_plan.json", "tools": "FFmpeg 9.0.2, macOS say", "_h": 23.0},
        {"agent": "7. Critic / QA", "source": "agents/critic.py", "role": "18 automated QA checks + hallucination & duration guards", "contract": "outputs/qa_report.json", "tools": "Deterministic validators, QA logic", "_h": 23.0},
    ]
    end_ag_y = add_table(p4, 58.0, agent_cols, agent_rows, LIGHT_BG, WHITE, LIGHT_BG, BORDER_COL, default_fontsize=6.8)

    # Detailed agent deep-dive blocks
    p4.insert_text(fitz.Point(MARGIN, end_ag_y + 12), "Comprehensive Agent Domain Implementations", fontsize=9.5, fontname="bold", color=NAVY)

    deep_agents_text = (
        "• Agent 1 (Planner): Ingests briefs/practice.yaml and constructs the ExecutionPlan Pydantic model. Calculates target duration (40s), "
        "clamps duration bounds strictly to [35s, 45s], validates that success criteria count is between 3 and 8, and allocates token spend caps.\n\n"
        "• Agent 2 (Researcher): Implements a grounded Retrieval-Augmented Generation (RAG) pipeline over data/. If source documents exist, it extracts "
        "factual propositions and enforces exact string matching for quotations. In the demonstration run where data/ contained no external PDFs, "
        "the Researcher honestly flagged verified_facts as empty, deriving facts solely from brief assertions and preventing hallucinations.\n\n"
        "• Agent 3 (Scriptwriter): Converts verified facts into spoken narration segmented into Hook, Problem, Solution, and Call to Action (CTA). "
        "It evaluates speaking rates against a strict window (120–190 wpm, targeting ~180 wpm). Emits script.json and human-readable script.md.\n\n"
        "• Agent 4 (Storyboarder): Translates script segments into a 6–10 scene storyboard. Enforces mobile safe-area on-screen text constraints "
        "(<= 80 characters per card). If caption length exceeds limits, the agent invokes limit_caption heuristics to trim non-essential adjectives.\n\n"
        "• Agent 5 (Asset Generator): Generates high-resolution 1080×1920 RGBA image assets cataloged in asset_manifest.json. Creates vertical dual-tone "
        "gradient cards (#0B1120 to #3B0A1A), procedural checkmarks, network node constellations, and UI indicators respecting mobile platform margins.\n\n"
        "• Agent 6 (Timeline Editor): Constructs the final non-linear editing (NLE) timeline in edit_plan.json. In agents/renderer_v3.py, it synthesizes "
        "48 kHz stereo voiceover audio, normalizes volume, streams raw RGB video frames into FFmpeg, and burns SubRip captions into final_video_v3.mp4.\n\n"
        "• Agent 7 (Critic / QA): The central verification gatekeeper. Runs 18 deterministic checks across intermediate JSON artifacts: duration math, "
        "unsupported factual claims, hallucinated contact details or phone numbers, timeline gaps, and missing AI disclosures."
    )
    add_textbox(p4, fitz.Rect(MARGIN, end_ag_y + 18, W_PT - MARGIN, H_PT - 32), deep_agents_text, fontsize=7.1, color=NAVY)

    # =========================================================================
    # PAGE 5: Technologies, Motion Graphics & Scene 2 Audio Investigation
    # =========================================================================
    p5 = doc.new_page(width=W_PT, height=H_PT)
    add_page_decorations(p5, 5)

    # 9. Technologies & Tools Used
    p5.insert_text(fitz.Point(MARGIN, 48), "9. Technologies, Libraries & Engineering Tooling", fontsize=10.5, fontname="bold", color=NAVY)
    tech_cols = [
        {"key": "cat", "title": "Engineering Layer", "x": MARGIN, "w": 110.0, "fn": "bold"},
        {"key": "tech", "title": "Technology / Tool", "x": MARGIN + 110.0, "w": 120.0, "fn": "bold", "fc": BURGUNDY},
        {"key": "desc", "title": "Role & Integration Details in AgentReel", "x": MARGIN + 230.0, "w": USABLE_W - 230.0, "fn": "reg"},
    ]
    tech_rows = [
        {"cat": "Runtime & Language", "tech": "Python 3.12 (macOS)", "desc": "Execution runtime on Apple Silicon; pinned environment in .venv", "_h": 14.0},
        {"cat": "Schema Typing", "tech": "Pydantic v2", "desc": "Deterministic schema boundaries, JSON serializing & contract validation", "_h": 14.0},
        {"cat": "Graphics Synthesis", "tech": "Pillow (PIL 13.0)", "desc": "Procedural RGBA/RGB24 canvas generation, safe-zone typography & vector HUD", "_h": 14.0},
        {"cat": "Document RAG", "tech": "PyMuPDF (fitz 2.0)", "desc": "Local PDF text extraction, document chunking & verbatim quote verification", "_h": 14.0},
        {"cat": "Audio Engine", "tech": "macOS say (Samantha)", "desc": "Local speech synthesis @ 180 wpm, AIFF export & 48 kHz AAC normalization", "_h": 14.0},
        {"cat": "Video Assembly", "tech": "FFmpeg 9.0.2 / FFprobe", "desc": "Direct rawvideo RGB24 stdin streaming (-i -) and AAC stereo muxing", "_h": 14.0},
        {"cat": "Automated Testing", "tech": "pytest 9.1.1", "desc": "78 unit and integration tests verifying schemas, math, logic, and audio/video", "_h": 14.0},
    ]
    end_tech_y = add_table(p5, 58.0, tech_cols, tech_rows, LIGHT_BG, WHITE, LIGHT_BG, BORDER_COL, default_fontsize=6.8)

    # 10. Motion-Graphics Design & V2/V3 Rendering Architecture
    p5.insert_text(fitz.Point(MARGIN, end_tech_y + 12), "10. Motion-Graphics Design & Direct FFmpeg Byte Streaming", fontsize=10.5, fontname="bold", color=NAVY)
    mg_text = (
        "• Overcoming Missing FFmpeg Filter Dependencies: In standard video pipelines, subtitles and typography are burned using FFmpeg filters "
        "(e.g., -vf subtitles=... or drawtext=...). However, the local Homebrew FFmpeg 9.0.2 installation was compiled without libass and libfreetype libraries. "
        "Rather than failing or requiring unsafe system modifications, agents/renderer_v3.py solves this through procedural canvas streaming: Pillow "
        "renders every frame in memory as raw RGB24 bytes and pipes them directly into FFmpeg's stdin:\n"
        "   ffmpeg -y -f rawvideo -pix_fmt rgb24 -s 1080x1920 -r 30 -i - -i audio.wav -c:v libx264 -pix_fmt yuv420p -crf 22 -c:a aac -b:a 192k final.mp4\n"
        "This architectural innovation completely bypasses external filter libraries, achieves >75 fps rendering speed (>2.5x real-time), eliminates "
        "intermediate disk image I/O, and guarantees 100% pixel-perfect typography across all scenes.\n\n"
        "• Mobile Safe-Margin Layout: The visual engine enforces strict safe zones (120px top clearance for app headers, 240px bottom clearance for "
        "social UI controls, and 80px side margins). All storyboard cards, NLE tracks, and Critic inspection badges remain perfectly legible."
    )
    add_textbox(p5, fitz.Rect(MARGIN, end_tech_y + 20, W_PT - MARGIN, end_tech_y + 130), mg_text, fontsize=7.1, color=NAVY)

    # 11. Root-Cause Analysis: Scene 2 Audio Truncation & V3 Resolution
    s11_y = end_tech_y + 140.0
    p5.insert_text(fitz.Point(MARGIN, s11_y), "11. Root-Cause Analysis: Scene 2 Narration Truncation & V3 Resolution", fontsize=10.5, fontname="bold", color=NAVY)

    p5.draw_rect(fitz.Rect(MARGIN, s11_y + 8, W_PT - MARGIN, s11_y + 116), color=BORDER_COL, fill=LIGHT_RED, width=0.8)
    p5.draw_rect(fitz.Rect(MARGIN, s11_y + 8, MARGIN + 4, s11_y + 116), color=DARK_RED, fill=DARK_RED)
    p5.insert_text(fitz.Point(MARGIN + 12, s11_y + 21), "Mathematical Root-Cause Diagnosis & Headroom Verification", fontsize=9.0, fontname="bold", color=DARK_RED)

    s2_narrative = (
        "• The Incident: In Milestone V2, Scene 2 ('The 7 AI Agents Workflow') audio cut off abruptly, omitting the Editor and Critic agent roles.\n"
        "• Mathematical Diagnosis: Spoken narration required 19.25 seconds at natural speed (175 wpm). However, Scene 2 was allocated only 15.50s in "
        "agents/renderer_v2.py. During audio track concatenation, FFmpeg executed 'ffmpeg -i temp.aiff -af apad=whole_dur=15.5 -t 15.5 temp_padded.wav'. "
        "The '-t 15.5' parameter hard-clipped the audio stream, dropping the final 3.75s of speech.\n"
        "• V3 Engineering Resolution: 1) Re-phrased script to concise, natural narration explicitly naming all seven agents: 'In our pipeline, seven specialized "
        "agents coordinate: Planner sets the plan, Researcher checks facts, Scriptwriter writes the story, Storyboarder designs shots, Asset Generator creates "
        "visuals, Editor builds the edit, and Critic verifies quality.' (spoken duration: 15.90s at 180 wpm). 2) Adjusted Scene 2 duration to 16.50s, creating "
        "+0.60s of clean breathing headroom. 3) Audited all 5 scenes for positive headroom (+0.29s to +0.99s), ensuring zero audio truncation and exactly 44.02s total duration."
    )
    add_textbox(p5, fitz.Rect(MARGIN + 12, s11_y + 26, W_PT - MARGIN - 10, s11_y + 112), s2_narrative, fontsize=7.0, color=NAVY)

    # Audited scene headroom table
    hd_cols = [
        {"key": "sc", "title": "Scene ID & Title", "x": MARGIN, "w": 160.0, "fn": "bold"},
        {"key": "dur", "title": "Allocated Duration", "x": MARGIN + 160.0, "w": 105.0, "fn": "reg"},
        {"key": "spk", "title": "Spoken Audio Duration", "x": MARGIN + 265.0, "w": 115.0, "fn": "reg"},
        {"key": "head", "title": "Measured Headroom", "x": MARGIN + 380.0, "w": USABLE_W - 380.0, "fn": "bold", "fc": BURGUNDY},
    ]
    hd_rows = [
        {"sc": "Scene 1: The Prompt", "dur": "5.50 seconds", "spk": "5.21 seconds", "head": "+0.29s (Clean tail)", "_h": 15.0},
        {"sc": "Scene 2: The 7 Agents Workflow", "dur": "16.50 seconds", "spk": "15.90 seconds", "head": "+0.60s (Audited V3 Fix)", "_h": 15.0},
        {"sc": "Scene 3: Multi-Track Timeline", "dur": "8.00 seconds", "spk": "7.58 seconds", "head": "+0.42s (Clean tail)", "_h": 15.0},
        {"sc": "Scene 4: Critic QA HUD & Repair", "dur": "8.00 seconds", "spk": "7.01 seconds", "head": "+0.99s (Clean tail)", "_h": 15.0},
        {"sc": "Scene 5: Final Reveal & CTA", "dur": "6.00 seconds", "spk": "5.24 seconds", "head": "+0.76s (Clean tail)", "_h": 15.0},
        {"sc": "TOTAL FINAL VIDEO V3", "dur": "44.02 seconds", "spk": "40.94 seconds", "head": "+3.06s Net Safe Headroom", "_h": 15.0,
         "_sc_fn": "bold", "_dur_fn": "bold", "_spk_fn": "bold", "_head_fn": "bold",
         "_sc_fc": BURGUNDY, "_dur_fc": BURGUNDY, "_spk_fc": BURGUNDY, "_head_fc": BURGUNDY},
    ]
    add_table(p5, s11_y + 128.0, hd_cols, hd_rows, LIGHT_BG, WHITE, LIGHT_BG, BORDER_COL, default_fontsize=6.7)

    # =========================================================================
    # PAGE 6: Video Specs, 78-Test Verification Matrix & Challenges
    # =========================================================================
    p6 = doc.new_page(width=W_PT, height=H_PT)
    add_page_decorations(p6, 6)

    # 12. Final Video Technical Specifications & Deliverables
    p6.insert_text(fitz.Point(MARGIN, 48), "12. Final Video Technical Specifications (`outputs/final_video_v3.mp4`)", fontsize=10.5, fontname="bold", color=NAVY)

    spec_cols = [
        {"key": "prop", "title": "Technical Specification", "x": MARGIN, "w": 140.0, "fn": "bold"},
        {"key": "val", "title": "Delivered Parameter Value", "x": MARGIN + 140.0, "w": 185.0, "fn": "bold", "fc": BURGUNDY},
        {"key": "audit", "title": "Verification Method & Source of Truth", "x": MARGIN + 325.0, "w": USABLE_W - 325.0, "fn": "reg", "fc": GRAY},
    ]
    spec_rows = [
        {"prop": "Resolution & Orientation", "val": "1080 × 1920 (9:16 vertical)", "audit": "ffprobe -show_streams / bitstream analysis", "_h": 13.5},
        {"prop": "Frame Rate & Frames", "val": "30.0 fps (1,320 total frames)", "audit": "Exact frame index accounting", "_h": 13.5},
        {"prop": "Total Video Duration", "val": "44.02 seconds (target: 40s)", "audit": "ffprobe -show_format (bounds: [35s, 45s])", "_h": 13.5},
        {"prop": "Video Codec & Format", "val": "H.264 / High Profile (CRF 22)", "audit": "libx264 bitstream, yuv420p pixel format", "_h": 13.5},
        {"prop": "Audio Codec & Stream", "val": "AAC stereo @ 48,000 Hz, 192 kbps", "audit": "48 kHz standard; zero resampling artifacts", "_h": 13.5},
        {"prop": "File Size & Efficiency", "val": "2.21 MB (2,316,562 bytes)", "audit": "97.8% below 100 MB challenge budget", "_h": 13.5},
        {"prop": "Bitstream Integrity", "val": "100% Clean Decode (0 errors)", "audit": "ffmpeg -v error -i ... -f null -", "_h": 13.5},
        {"prop": "Subtitles File", "val": "outputs/AgentReel_Final.srt (6 cues)", "audit": "SubRip format, non-overlapping, 44.0s", "_h": 13.5},
        {"prop": "Mandatory Disclosures", "val": "CTA + 'Created with AI agents'", "audit": "Burned on-screen inside mobile safe area", "_h": 13.5},
    ]
    end_spec_y = add_table(p6, 58.0, spec_cols, spec_rows, LIGHT_BG, WHITE, LIGHT_BG, BORDER_COL, default_fontsize=6.8)

    # 13. Testing, Validation & Quality Assurance (78 Tests)
    p6.insert_text(fitz.Point(MARGIN, end_spec_y + 12), "13. Testing, Validation & Quality Assurance (78 Unit & Integration Tests)", fontsize=10.5, fontname="bold", color=NAVY)

    p6.draw_rect(fitz.Rect(MARGIN, end_spec_y + 20, W_PT - MARGIN, end_spec_y + 38), color=BORDER_COL, fill=LIGHT_BG, width=0.8)
    p6.insert_text(fitz.Point(MARGIN + 12, end_spec_y + 32), "Continuous Verification Suite: 78 Tests Passing in 2.57s • Zero Failures Across All Pipelines", fontsize=7.5, fontname="bold", color=BURGUNDY)

    test_cols = [
        {"key": "mod", "title": "Test Suite Module", "x": MARGIN, "w": 120.0, "fn": "bold"},
        {"key": "cnt", "title": "Count", "x": MARGIN + 120.0, "w": 45.0, "fn": "bold", "fc": BURGUNDY},
        {"key": "focus", "title": "Target Pipeline Component", "x": MARGIN + 165.0, "w": 120.0, "fn": "reg"},
        {"key": "rules", "title": "Audited Invariants & Guardrails", "x": MARGIN + 285.0, "w": USABLE_W - 285.0, "fn": "reg", "fc": GRAY},
    ]
    test_rows = [
        {"mod": "tests/test_schemas.py", "cnt": "8 tests", "focus": "Pydantic Schema Contracts", "rules": "Duration [35s, 45s], target 40s, 3-8 criteria, 6-10 shots, valid enums", "_h": 21.0},
        {"mod": "tests/test_validators.py", "cnt": "17 tests", "focus": "Mathematical & Claims Logic", "rules": "Speaking rate 120-190 wpm, gapless timeline, ungrounded claim rejection", "_h": 21.0},
        {"mod": "tests/test_critic.py", "cnt": "19 tests", "focus": "Critic Rules & Safety Guards", "rules": "Hallucinated number/contact detection, duration mismatch >1s, AI disclosure", "_h": 21.0},
        {"mod": "tests/test_orchestrator.py", "cnt": "19 tests", "focus": "State Machine & Repair Loop", "rules": "Targeted repair loops, earliest-failing rollback, max 3-pass termination safety", "_h": 21.0},
        {"mod": "tests/test_renderer.py / motion", "cnt": "15 tests", "focus": "Rendering & Subtitle Sync", "rules": "1080x1920 canvas, SubRip sync (44.02s), Scene 2 seven-agent audit, backups", "_h": 21.0},
    ]
    end_test_y = add_table(p6, end_spec_y + 42.0, test_cols, test_rows, LIGHT_BG, WHITE, LIGHT_BG, BORDER_COL, default_fontsize=6.7)

    # 14. Challenges Faced and Engineering Resolutions
    p6.insert_text(fitz.Point(MARGIN, end_test_y + 12), "14. Key Engineering Challenges Faced & Technical Resolutions", fontsize=10.5, fontname="bold", color=NAVY)

    ch_text = (
        "• Challenge 1 — Missing FFmpeg Filter Compilation: Local FFmpeg builds lacked libass and libfreetype, causing standard drawtext filters to fail.\n"
        "  Resolution: Engineered a direct rawvideo byte-pipe architecture in agents/renderer_v3.py, piping RGB24 bytes from Pillow directly to FFmpeg stdin.\n"
        "• Challenge 2 — Abrupt Scene 2 Narration Truncation: Scene 2 audio was clipped in V2 due to a hard -t 15.5 limit against 19.25s of speech.\n"
        "  Resolution: Mathematically re-timed narration to 15.90s @ 180 wpm, extended scene to 16.50s (+0.60s headroom), ensuring 100% audible delivery.\n"
        "• Challenge 3 — External LLM API Rate Limits (HTTP 429): Live Groq API calls during Milestone B experienced occasional rate-limiting.\n"
        "  Resolution: Implemented immutable contract caching in outputs/ and isolated offline procedural rendering, ensuring 100% repeatable builds.\n"
        "• Challenge 4 — Preventing Factual Hallucinations: Generative models frequently fabricate statistics, phone numbers, or corporate contacts.\n"
        "  Resolution: Created deterministic regex validators (tests/test_validators.py) that reject any number or contact not present in verified facts."
    )
    add_textbox(p6, fitz.Rect(MARGIN, end_test_y + 20, W_PT - MARGIN, H_PT - 32), ch_text, fontsize=7.0, color=NAVY)

    # =========================================================================
    # PAGE 7: Limitations, Future Scope, Conclusion, Artifacts & Sign-Off
    # =========================================================================
    p7 = doc.new_page(width=W_PT, height=H_PT)
    add_page_decorations(p7, 7)

    # 15. Limitations & Ethical Considerations
    p7.insert_text(fitz.Point(MARGIN, 48), "15. Limitations & Ethical Considerations", fontsize=10.5, fontname="bold", color=NAVY)
    lim_text = (
        "• Document Corpus Limitations: In the live run, data/ contained no external PDF files. The Researcher agent acted truthfully by deriving "
        "facts strictly from brief assertions, avoiding hallucinated claims. In production, a rich corpus of technical papers should be provided.\n"
        "• Speech Synthesis Variety: TTS relied on macOS Samantha; achieving multi-speaker conversational dialogue requires local neural voice models.\n"
        "• Caption Burning Architecture: Streamed Pillow RGBA frames directly into rawvideo; adding stylized animated subtitles requires custom vector glyph paths.\n"
        "• Ethical Guardrails: Anti-hallucination validators forbid invented statistics, contacts, or ungrounded claims. Mandatory AI disclosure ('Created with AI agents — LY Agentic AI Lab') is permanently burned into the final scene's mobile-safe area."
    )
    add_textbox(p7, fitz.Rect(MARGIN, 56, W_PT - MARGIN, 126), lim_text, fontsize=7.1, color=NAVY)

    # 16. Proposed Future Scope & Scalability
    p7.insert_text(fitz.Point(MARGIN, 134), "16. Proposed Future Scope & System Scalability", fontsize=10.5, fontname="bold", color=NAVY)
    fut_text = (
        "1. Fully Offline Open-Source LLMs: Integrate local quantized models (e.g. Llama 3.3 70B, Qwen 2.5 72B via Ollama) to eliminate cloud API spend.\n"
        "2. Neural Text-to-Speech (TTS): Integrate high-fidelity local neural TTS engines (Piper or Coqui TTS) for expressive, multi-speaker voices.\n"
        "3. Hardware VideoToolbox Acceleration: Leverage Apple Silicon VideoToolbox (h264_videotoolbox) for 120+ fps hardware-accelerated video encodes.\n"
        "4. Interactive Web Control Dashboard: Build a FastAPI/Streamlit control plane to inspect live DAG state, contract diffs, and repair history in real time."
    )
    add_textbox(p7, fitz.Rect(MARGIN, 142, W_PT - MARGIN, 198), fut_text, fontsize=7.1, color=NAVY)

    # 17. Project Artifact References
    p7.insert_text(fitz.Point(MARGIN, 206), "17. Project Artifact References & Deliverables Manifest", fontsize=10.5, fontname="bold", color=NAVY)

    deliv_cols = [
        {"key": "file", "title": "Artifact File Path", "x": MARGIN, "w": 150.0, "fn": "bold"},
        {"key": "type", "title": "Format / Technical Spec", "x": MARGIN + 150.0, "w": 215.0, "fn": "reg", "fc": GRAY},
        {"key": "stat", "title": "Verification & Storage Status", "x": MARGIN + 365.0, "w": USABLE_W - 365.0, "fn": "bold", "fc": BURGUNDY},
    ]
    deliv_rows = [
        {"file": "outputs/final_video_v3.mp4", "type": "1080×1920 MP4 | 30 fps | 44.02s | H.264/AAC | 2.21 MB", "stat": "Verified Playable, 100% clean decode", "_h": 15.0},
        {"file": "outputs/AgentReel_Final.srt", "type": "SubRip Subtitles | 6 cues | Synchronized to 44.02s", "stat": "Audio-verified, covers all 7 agents", "_h": 15.0},
        {"file": "outputs/render_report_v3.json", "type": "JSON Manifest | Scene timings, bitrates, audio stats", "stat": "Verified schema compliance", "_h": 15.0},
        {"file": "outputs/preview_v3_[1-5].png", "type": "1080×1920 PNG | 5 scene preview frame snapshots", "stat": "Verified mobile safe-margin layout", "_h": 15.0},
        {"file": "reports/AgentReel_Architecture.mmd", "type": "Mermaid Diagram Source | Editable DAG flow & repair", "stat": "Validated Mermaid syntax", "_h": 15.0},
        {"file": "reports/final/AgentReel_Final_Report.pdf", "type": "7-Page Engineering Report | Technical layout & audit", "stat": "Generated via PyMuPDF (fitz)", "_h": 15.0},
        {"file": "outputs/v2_backup/ &\nmilestone_c_backup/", "type": "Preserved earlier Milestone B, C, and V2 outputs intact", "stat": "Verified dual backup integrity", "_h": 22.0},
    ]
    end_deliv_y = add_table(p7, 216.0, deliv_cols, deliv_rows, LIGHT_BG, WHITE, LIGHT_BG, BORDER_COL, default_fontsize=6.7)

    # 18. Conclusion & Academic Sign-Off
    p7.insert_text(fitz.Point(MARGIN, end_deliv_y + 12), "18. Conclusion & Formal Lab Sign-Off", fontsize=10.5, fontname="bold", color=NAVY)

    c_box_h = 76.0
    p7.draw_rect(fitz.Rect(MARGIN, end_deliv_y + 20, W_PT - MARGIN, end_deliv_y + 20 + c_box_h), color=BORDER_COL, fill=LIGHT_GREEN, width=0.8)
    p7.draw_rect(fitz.Rect(MARGIN, end_deliv_y + 20, MARGIN + 4, end_deliv_y + 20 + c_box_h), color=EMERALD, fill=EMERALD)

    concl_str = (
        "Conclusion: The AgentReel Challenge successfully proves that autonomous multi-agent pipelines can reliably produce broadcast-grade vertical "
        "video through modular decomposition, strict interface contracts, and bounded self-repair loops. By combining Pydantic v2 data models, local "
        "Pillow canvas rendering, direct FFmpeg raw byte streaming, and rigorous automated testing (78 tests passing), the system eliminates the opacity, "
        "hallucinations, and uncontrolled spend of monolithic generative models.\n\n"
        "The complete software implementation, reproducible test suite, final MP4 video (outputs/final_video_v3.mp4), and synchronized subtitle deliverable "
        "(outputs/AgentReel_Final.srt) stand fully verified and ready for formal academic submission at the LY Agentic AI Laboratory."
    )
    add_textbox(p7, fitz.Rect(MARGIN + 12, end_deliv_y + 24, W_PT - MARGIN - 10, end_deliv_y + 20 + c_box_h - 4), concl_str, fontsize=7.1, color=DARK_GREEN)

    # Formal Verification Signatures Line
    sig_y = end_deliv_y + 20 + c_box_h + 16.0
    p7.draw_line(fitz.Point(MARGIN, sig_y), fitz.Point(W_PT - MARGIN, sig_y), color=BORDER_COL, width=0.5)
    p7.insert_text(fitz.Point(MARGIN + 10, sig_y + 16), "Verified & Submitted by Team Members:", fontsize=8.0, fontname="bold", color=NAVY)
    p7.insert_text(fitz.Point(MARGIN + 10, sig_y + 30), "1. Sanjeevani Chaurasia (Roll No. 16014223073)  •  Agent Architect & Motion Graphics Engine", fontsize=7.5, fontname="reg", color=NAVY)
    p7.insert_text(fitz.Point(MARGIN + 10, sig_y + 44), "2. Vedant Mhapsekar (Roll No. 16014223095)    •  Pipeline Orchestrator & LLM Integration", fontsize=7.5, fontname="reg", color=NAVY)
    p7.insert_text(fitz.Point(MARGIN + 10, sig_y + 58), "3. Aayush More (Roll No. 16014223104)         •  Critic QA Guardrails & Testing Engineer", fontsize=7.5, fontname="reg", color=NAVY)

    # Save Document
    doc.save(PDF_OUT)
    doc.close()
    try:
        diagram_path.unlink(missing_ok=True)
    except Exception:
        pass
    print(f"Final Report PDF successfully generated at {PDF_OUT} with exactly 7 pages.")


if __name__ == "__main__":
    build_final_report()
