"""Procedural Motion Graphics Engine for AgentReel (Milestone C Upgrade).

Generates high-production-value, 30fps 1080x1920 vertical motion graphics:
- Dual-tone navy/burgundy gradient backgrounds with subtle grid/stars.
- Gold and warm-white typography and glowing connection lines.
- Animated prompt typing, traveling particle pulses, audio waveforms,
  NLE editing timeline, Critic feedback loop, and smartphone reveal.
"""
from __future__ import annotations

import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1920
FPS = 30

# Colors
NAVY = (11, 17, 32)
BURGUNDY = (59, 10, 26)
CARD_BG = (15, 23, 42)
CARD_BORDER = (51, 65, 85)
GOLD = (245, 158, 11)
LIGHT_GOLD = (251, 191, 36)
AMBER_GLOW = (253, 230, 138)
WHITE = (248, 250, 252)
MUTED = (148, 163, 184)
GREEN = (16, 185, 129)
RED = (239, 68, 68)

FONT_PATHS = [
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
]

_FONT_CACHE: dict[int, ImageFont.FreeTypeFont | ImageFont.ImageFont] = {}


def get_font(size: int):
    if size not in _FONT_CACHE:
        font = None
        for p in FONT_PATHS:
            try:
                font = ImageFont.truetype(p, size)
                break
            except Exception:
                continue
        _FONT_CACHE[size] = font or ImageFont.load_default(size=size)
    return _FONT_CACHE[size]


# Pre-render background gradient once for maximum speed
def _create_bg() -> Image.Image:
    img = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(img)
    for y in range(0, H, 2):
        t = y / (H - 1)
        c = (
            int(NAVY[0] + (BURGUNDY[0] - NAVY[0]) * t),
            int(NAVY[1] + (BURGUNDY[1] - NAVY[1]) * t),
            int(NAVY[2] + (BURGUNDY[2] - NAVY[2]) * t),
        )
        draw.line([(0, y), (W, y)], fill=c, width=2)
    return img


_BG_IMAGE = _create_bg()


def get_base_canvas() -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = _BG_IMAGE.copy()
    draw = ImageDraw.Draw(img)
    return img, draw


def ease_in_out(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return 0.5 * (1 - math.cos(math.pi * t))


def draw_header_badge(draw: ImageDraw.ImageDraw, title: str = "SOMAIYA AGENTIC AI LAB"):
    y = 120
    font = get_font(26)
    w = draw.textlength(title, font=font)
    pad = 30
    draw.rounded_rectangle([(W - w) / 2 - pad, y - 10, (W + w) / 2 + pad, y + 36], radius=16,
                           fill=(20, 28, 48), outline=GOLD, width=2)
    draw.text(((W - w) / 2, y), title, font=font, fill=LIGHT_GOLD)


def draw_caption_banner(draw: ImageDraw.ImageDraw, text: str):
    if not text:
        return
    font = get_font(34)
    # Wrap text to max 80 chars / width
    words = text.split()
    lines, cur = [], ""
    for word in words:
        trial = f"{cur} {word}".strip()
        if draw.textlength(trial, font=font) <= W - 180 or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)

    line_h = 44
    total_h = len(lines) * line_h + 36
    y_start = 1720 - total_h
    draw.rounded_rectangle([60, y_start, W - 60, y_start + total_h], radius=20,
                           fill=(11, 15, 26), outline=(71, 85, 105), width=2)

    cur_y = y_start + 18
    for line in lines:
        w = draw.textlength(line, font=font)
        draw.text(((W - w) / 2, cur_y), line, font=font, fill=WHITE)
        cur_y += line_h


# ------------------------------------------------------------ Scene 1: The Hook
def render_scene1_frame(idx: int, total: int, caption: str) -> Image.Image:
    t = idx / max(1, total - 1)
    img, draw = get_base_canvas()
    draw_header_badge(draw)

    # Title
    t_font = get_font(52)
    t_text = "From Prompt to Product"
    t_w = draw.textlength(t_text, font=t_font)
    draw.text(((W - t_w) / 2, 260), t_text, font=t_font, fill=WHITE)

    sub_font = get_font(32)
    sub_text = "How 7 Autonomous AI Agents Build a Video"
    sub_w = draw.textlength(sub_text, font=sub_font)
    draw.text(((W - sub_w) / 2, 335), sub_text, font=sub_font, fill=LIGHT_GOLD)

    # Terminal prompt box
    box_x1, box_y1, box_x2, box_y2 = 80, 460, W - 80, 860
    draw.rounded_rectangle([box_x1, box_y1, box_x2, box_y2], radius=24,
                           fill=(15, 23, 42), outline=GOLD, width=3)
    # Window header
    draw.rounded_rectangle([box_x1, box_y1, box_x2, box_y1 + 54], radius=24, fill=(30, 41, 59))
    draw.rectangle([box_x1, box_y1 + 30, box_x2, box_y1 + 54], fill=(30, 41, 59))
    # Window controls
    for i, col in enumerate([(239, 68, 68), (245, 158, 11), (16, 185, 129)]):
        draw.ellipse([box_x1 + 24 + i * 28, box_y1 + 18, box_x1 + 42 + i * 28, box_y1 + 36], fill=col)
    head_txt = "prompt.yaml — brief specification"
    draw.text((box_x1 + 130, box_y1 + 16), head_txt, font=get_font(22), fill=MUTED)

    # Prompt text typing simulation
    full_lines = [
        "> brief_id: P00 — Agentic AI Lab",
        "> topic: 'Autonomous Multi-Agent Reel'",
        "> pipeline: [planner, research, script,",
        "             storyboard, asset, edit, critic]",
        "> trigger: deploy_pipeline(seed=42)"
    ]
    chars_to_show = int(t * 1.8 * sum(len(line) for line in full_lines))
    cur_chars = 0
    line_y = box_y1 + 80
    code_font = get_font(28)
    for line in full_lines:
        if cur_chars + len(line) <= chars_to_show:
            draw.text((box_x1 + 40, line_y), line, font=code_font, fill=(52, 211, 153))
            cur_chars += len(line)
        elif cur_chars < chars_to_show:
            part = line[:chars_to_show - cur_chars]
            draw.text((box_x1 + 40, line_y), part + "█", font=code_font, fill=(52, 211, 153))
            cur_chars = chars_to_show
        line_y += 46

    # Constellation burst into 7 agents
    if t > 0.45:
        p_prog = ease_in_out((t - 0.45) / 0.55)
        cx, cy = W / 2, 1260
        r_orbit = 280 * p_prog
        draw.ellipse([cx - 40 * p_prog, cy - 40 * p_prog, cx + 40 * p_prog, cy + 40 * p_prog],
                     fill=GOLD, outline=AMBER_GLOW, width=4)
        c_font = get_font(22)
        c_txt = "BRIEF"
        if p_prog > 0.25:
            agents = ["Planner", "Researcher", "Scriptwriter", "Storyboarder", "Asset Gen", "Editor", "Critic"]
            for i, name in enumerate(agents):
                angle = i * (2 * math.pi / len(agents)) - math.pi / 2
                ax = cx + r_orbit * math.cos(angle)
                ay = cy + r_orbit * math.sin(angle)
                # Beam
                draw.line([(cx, cy), (ax, ay)], fill=GOLD, width=3)
                # Node
                draw.ellipse([ax - 46, ay - 46, ax + 46, ay + 46], fill=(15, 23, 42), outline=GOLD, width=3)
                num = str(i + 1)
                draw.text((ax - 7, ay - 24), num, font=get_font(26), fill=LIGHT_GOLD)
                draw.text((ax - draw.textlength(name, font=get_font(20)) / 2, ay + 6), name, font=get_font(20), fill=WHITE)

    draw_caption_banner(draw, caption)
    return img


# ------------------------------------------------------------ Scene 2: The Workflow
def render_scene2_frame(idx: int, total: int, caption: str) -> Image.Image:
    t = idx / max(1, total - 1)
    img, draw = get_base_canvas()
    draw_header_badge(draw)

    title_font = get_font(46)
    title = "The 7 Specialized AI Agents"
    draw.text(((W - draw.textlength(title, font=title_font)) / 2, 220), title, font=title_font, fill=WHITE)

    agents = [
        ("1. Planner", "Decomposes brief into stages, limits & budget", "Plan & Spec"),
        ("2. Researcher", "Retrieves facts & verifies verbatim quotes", "Source RAG"),
        ("3. Scriptwriter", "Writes timed narration (hook, body, CTA)", "Narrative"),
        ("4. Storyboarder", "Plans visual scenes & on-screen captions", "Shot Design"),
        ("5. Asset Generator", "Renders 9:16 gradient cards with safe zones", "Pillow Visuals"),
        ("6. Editor", "Builds timeline, syncs audio & subtitles", "FFmpeg Assembly"),
        ("7. Critic", "18 automated checks + targeted repair loop", "Quality & Safety")
    ]

    active_agent = int(min(6, t * 7.2))
    card_w = W - 140
    card_h = 135
    start_y = 310
    spacing = 152

    # Draw connecting line behind cards
    draw.line([(140, start_y + 40), (140, start_y + 6 * spacing + 40)], fill=(71, 85, 105), width=6)
    # Traveling highlight
    curr_y = start_y + (t * 6 * spacing)
    draw.line([(140, start_y + 40), (140, min(start_y + 6 * spacing + 40, curr_y + 40))], fill=GOLD, width=6)
    draw.ellipse([140 - 14, curr_y + 40 - 14, 140 + 14, curr_y + 40 + 14], fill=AMBER_GLOW, outline=GOLD, width=3)

    for i, (name, role, badge) in enumerate(agents):
        y = start_y + i * spacing
        is_active = (i == active_agent)
        is_done = (i < active_agent)
        fill_col = (30, 41, 59) if is_active else ((20, 28, 48) if is_done else (15, 23, 42))
        border_col = LIGHT_GOLD if is_active else (GOLD if is_done else CARD_BORDER)
        border_w = 4 if is_active else (2 if is_done else 1)

        draw.rounded_rectangle([180, y, 180 + card_w - 110, y + card_h], radius=18,
                               fill=fill_col, outline=border_col, width=border_w)

        # Node dot
        dot_col = LIGHT_GOLD if is_active else (GOLD if is_done else (71, 85, 105))
        draw.ellipse([140 - 20, y + 48, 140 + 20, y + 88], fill=dot_col, outline=WHITE, width=2)

        # Agent Title
        name_col = LIGHT_GOLD if is_active else WHITE
        draw.text((210, y + 16), name, font=get_font(30), fill=name_col)

        # Badge tag
        b_font = get_font(22)
        bw = draw.textlength(badge, font=b_font)
        draw.rounded_rectangle([180 + card_w - 120 - bw - 24, y + 14, 180 + card_w - 120, y + 50], radius=8,
                               fill=(11, 15, 26), outline=border_col, width=1)
        draw.text((180 + card_w - 120 - bw - 12, y + 20), badge, font=b_font, fill=LIGHT_GOLD)

        # Role description — high contrast slate-200 / white for maximum readability
        role_col = (255, 255, 255) if is_active else (226, 232, 240)
        draw.text((210, y + 70), role, font=get_font(24), fill=role_col)

    draw_caption_banner(draw, caption)
    return img


# ------------------------------------------------------------ Scene 3: Creation & Assembly
def render_scene3_frame(idx: int, total: int, caption: str) -> Image.Image:
    t = idx / max(1, total - 1)
    img, draw = get_base_canvas()
    draw_header_badge(draw)

    title_font = get_font(46)
    title = "Multi-Track Creation Engine"
    draw.text(((W - draw.textlength(title, font=title_font)) / 2, 220), title, font=title_font, fill=WHITE)

    # 1. Four storyboard cards positioned strictly inside safe margins (no edge clipping)
    sb_cards = [
        ("S01", "Entrance", "Concept"),
        ("S02", "Workstations", "Workflow"),
        ("S03", "Coding Agents", "Assembly"),
        ("S04", "Review QA", "Delivery")
    ]
    card_w, card_h = 216, 350
    spacing = 236
    active_card = int(min(3, t * 4.0))

    for j, (sid, sname, stage) in enumerate(sb_cards):
        x = 80 + j * spacing
        is_card_active = (j == active_card)
        card_y = 310 if is_card_active else 324
        fill_col = (30, 41, 59) if is_card_active else (15, 23, 42)
        border_col = LIGHT_GOLD if is_card_active else (71, 85, 105)
        border_w = 4 if is_card_active else 2

        draw.rounded_rectangle([x, card_y, x + card_w, card_y + card_h], radius=16,
                               fill=fill_col, outline=border_col, width=border_w)
        # Shot header
        draw.text((x + 18, card_y + 20), sid, font=get_font(28), fill=LIGHT_GOLD if is_card_active else WHITE)
        draw.text((x + 18, card_y + 58), sname, font=get_font(22), fill=(226, 232, 240))
        # Inner preview screen
        draw.rectangle([x + 18, card_y + 115, x + card_w - 18, card_y + 275],
                       fill=(11, 17, 32), outline=(51, 65, 85), width=1)
        draw.text((x + 36, card_y + 185), "1080x1920", font=get_font(22), fill=(203, 213, 225))
        # Stage pill
        draw.rounded_rectangle([x + 18, card_y + 295, x + card_w - 18, card_y + 330], radius=6,
                               fill=(20, 28, 48), outline=border_col, width=1)
        st_w = draw.textlength(stage, font=get_font(20))
        draw.text((x + (card_w - st_w) / 2, card_y + 302), stage, font=get_font(20), fill=AMBER_GLOW if is_card_active else MUTED)

    # 2. Oscillating Audio Waveform
    draw.text((80, 720), "Synchronized Voiceover (48 kHz AAC)", font=get_font(28), fill=LIGHT_GOLD)
    draw.rounded_rectangle([80, 765, W - 80, 930], radius=16, fill=(15, 23, 42), outline=(51, 65, 85), width=2)
    # Draw animated waveform bars
    n_bars = 48
    bar_w = (W - 200) / n_bars
    for b in range(n_bars):
        phase = t * 18 + b * 0.35
        amp = max(4.0, abs(math.sin(phase) * math.cos(phase * 0.7)) * 48 + 6)
        bx = 100 + b * bar_w
        by = 848
        draw.rounded_rectangle([bx, by - amp, bx + bar_w - 4, by + amp], radius=3, fill=GOLD)

    # 3. NLE Timeline Tracks
    draw.text((80, 970), "Assembled Timeline Sequence", font=get_font(28), fill=WHITE)
    t_box_y = 1015
    draw.rounded_rectangle([80, t_box_y, W - 80, t_box_y + 440], radius=18,
                           fill=(15, 23, 42), outline=GOLD, width=2)

    # Track 1: Video
    draw.rounded_rectangle([100, t_box_y + 30, W - 100, t_box_y + 130], radius=12, fill=(20, 28, 48), outline=(51, 65, 85), width=1)
    draw.text((120, t_box_y + 45), "[V1] 7 Video Clips — 30 fps H.264", font=get_font(22), fill=LIGHT_GOLD)
    for k in range(7):
        k_x = 120 + k * 115
        draw.rounded_rectangle([k_x, t_box_y + 80, k_x + 105, t_box_y + 120], radius=6, fill=(59, 130, 246))
        draw.text((k_x + 30, t_box_y + 90), f"S{k+1:02d}", font=get_font(18), fill=WHITE)

    # Track 2: Audio
    draw.rounded_rectangle([100, t_box_y + 150, W - 100, t_box_y + 250], radius=12, fill=(20, 28, 48), outline=(51, 65, 85), width=1)
    draw.text((120, t_box_y + 165), "[A1] Spoken Narration Track — Normalized", font=get_font(22), fill=(52, 211, 153))
    for k in range(7):
        k_x = 120 + k * 115
        draw.rounded_rectangle([k_x, t_box_y + 200, k_x + 105, t_box_y + 240], radius=6, fill=(16, 185, 129))
        draw.text((k_x + 24, t_box_y + 210), f"VO_{k+1}", font=get_font(18), fill=WHITE)

    # Track 3: Subtitles
    draw.rounded_rectangle([100, t_box_y + 270, W - 100, t_box_y + 370], radius=12, fill=(20, 28, 48), outline=(51, 65, 85), width=1)
    draw.text((120, t_box_y + 285), "[T1] SubRip (.srt) Burned Captions", font=get_font(22), fill=AMBER_GLOW)
    for k in range(7):
        k_x = 120 + k * 115
        draw.rounded_rectangle([k_x, t_box_y + 320, k_x + 105, t_box_y + 360], radius=6, fill=(217, 119, 6))
        draw.text((k_x + 24, t_box_y + 330), f"SRT_{k+1}", font=get_font(18), fill=WHITE)

    # Moving timeline playhead
    playhead_x = 120 + t * (W - 240)
    draw.line([(playhead_x, t_box_y + 10), (playhead_x, t_box_y + 390)], fill=RED, width=4)
    draw.polygon([(playhead_x - 12, t_box_y + 10), (playhead_x + 12, t_box_y + 10), (playhead_x, t_box_y + 30)], fill=RED)

    draw_caption_banner(draw, caption)
    return img


# ------------------------------------------------------------ Scene 4: Review & Repair Loop
def render_scene4_frame(idx: int, total: int, caption: str) -> Image.Image:
    t = idx / max(1, total - 1)
    img, draw = get_base_canvas()
    draw_header_badge(draw)

    title_font = get_font(46)
    title = "Automated QA & Targeted Repair"
    draw.text(((W - draw.textlength(title, font=title_font)) / 2, 220), title, font=title_font, fill=WHITE)

    # Critic HUD Card
    box_y = 310
    draw.rounded_rectangle([80, box_y, W - 80, box_y + 600], radius=24, fill=(15, 23, 42), outline=GOLD, width=3)
    draw.text((120, box_y + 36), "Critic Agent — Inspection Checklist", font=get_font(32), fill=LIGHT_GOLD)

    # Checklist items
    phase_repaired = (t > 0.55)
    checks = [
        ("Script Duration Window [35s - 45s]", True, "39.0s estimated"),
        ("Factual Claims Grounded in data/", True, "0 ungrounded claims"),
        ("AI Disclosure Present in Final Shot", True, "Verified"),
        ("Shot Count Constraint [6 - 10 shots]", True, "7 shots produced"),
        ("On-Screen Caption Length (<= 80 chars)", phase_repaired, "72 chars (OK)" if phase_repaired else "93 chars > 80 chars (ALERT)")
    ]

    for i, (name, passed, detail) in enumerate(checks):
        cy = box_y + 110 + i * 92
        col = GREEN if passed else RED
        draw.ellipse([120, cy + 4, 156, cy + 40], fill=col)
        if passed:
            draw.line([(129, cy + 22), (136, cy + 29), (147, cy + 15)], fill=WHITE, width=3)
        else:
            draw.line([(138, cy + 12), (138, cy + 23)], fill=WHITE, width=3)
            draw.ellipse([136, cy + 28, 140, cy + 32], fill=WHITE)

        draw.text((180, cy), name, font=get_font(26), fill=WHITE if passed else LIGHT_GOLD)
        draw.text((180, cy + 34), detail, font=get_font(20), fill=col)

    # Repair Loop Arrow & Visualization
    if 0.25 <= t <= 0.65:
        # Show animated feedback loop arrow
        arrow_p = (t - 0.25) / 0.40
        draw.rounded_rectangle([120, 960, W - 120, 1140], radius=20, fill=(45, 10, 20), outline=RED, width=3)
        draw.text((160, 990), "REPAIR LOOP TRIGGERED", font=get_font(28), fill=RED)
        draw.text((160, 1040), "Critic -> Storyboarder: Shorten S02 caption", font=get_font(24), fill=WHITE)

        # Curved arrow
        start_pt = (W / 2 + 100, box_y + 490)
        end_pt = (W / 2 - 100, 1100)
        draw.line([start_pt, end_pt], fill=GOLD, width=6)
        draw.polygon([(end_pt[0] - 16, end_pt[1] - 8), (end_pt[0] + 16, end_pt[1] - 8), (end_pt[0], end_pt[1] + 18)], fill=GOLD)

    if phase_repaired:
        # Show big green PASS badge
        badge_y = 960
        draw.rounded_rectangle([120, badge_y, W - 120, badge_y + 240], radius=24,
                               fill=(6, 78, 59), outline=GREEN, width=4)
        draw.line([(165, badge_y + 58), (175, badge_y + 70), (195, badge_y + 44)], fill=WHITE, width=5)
        draw.text((215, badge_y + 40), "ALL CHECKS PASSED", font=get_font(42), fill=WHITE)
        draw.text((200, badge_y + 110), "Status: PASS_WITH_WARNINGS (0 Errors)", font=get_font(26), fill=AMBER_GLOW)
        draw.text((200, badge_y + 155), "Deterministic Repair Loop Completed in 1 Pass", font=get_font(22), fill=WHITE)

    draw_caption_banner(draw, caption)
    return img


# ------------------------------------------------------------ Scene 5: Final Reveal & CTA
def render_scene5_frame(idx: int, total: int, caption: str) -> Image.Image:
    t = idx / max(1, total - 1)
    img, draw = get_base_canvas()
    draw_header_badge(draw)

    title_font = get_font(46)
    title = "From Prompt to Final Video"
    draw.text(((W - draw.textlength(title, font=title_font)) / 2, 220), title, font=title_font, fill=WHITE)

    # Smartphone frame in center
    phone_w, phone_h = 440, 780
    cx, cy = W / 2, 680
    px1, py1 = cx - phone_w / 2, cy - phone_h / 2
    px2, py2 = cx + phone_w / 2, cy + phone_h / 2

    # Glowing outer border
    draw.rounded_rectangle([px1 - 6, py1 - 6, px2 + 6, py2 + 6], radius=44, fill=None, outline=GOLD, width=4)
    draw.rounded_rectangle([px1, py1, px2, py2], radius=40, fill=(15, 23, 42), outline=(71, 85, 105), width=3)
    # Speaker bar & camera
    draw.rounded_rectangle([cx - 40, py1 + 14, cx + 40, py1 + 22], radius=4, fill=(51, 65, 85))

    # Inner video preview screen
    draw.rounded_rectangle([px1 + 18, py1 + 36, px2 - 18, py2 - 24], radius=28, fill=(30, 41, 59))
    draw.polygon([(cx - 75, cy - 72), (cx - 75, cy - 48), (cx - 52, cy - 60)], fill=LIGHT_GOLD)
    draw.text((cx - 40, cy - 75), "PLAYING", font=get_font(30), fill=LIGHT_GOLD)
    draw.text((cx - 95, cy - 20), "1080x1920 MP4", font=get_font(24), fill=WHITE)
    draw.text((cx - 90, cy + 25), "44.0s @ 30fps", font=get_font(22), fill=(203, 213, 225))

    # Orbiting agent badges around phone
    agents_s5 = ["Plan", "RAG", "Script", "Story", "Asset", "Edit", "QA"]
    r_orbit = 340
    for i, ag in enumerate(agents_s5):
        angle = t * 1.5 + i * (2 * math.pi / len(agents_s5))
        bx = cx + r_orbit * math.cos(angle)
        by = cy + r_orbit * 0.7 * math.sin(angle)
        draw.ellipse([bx - 36, by - 36, bx + 36, by + 36], fill=(20, 28, 48), outline=GOLD, width=2)
        draw.text((bx - draw.textlength(ag, font=get_font(18)) / 2, by - 9), ag, font=get_font(18), fill=WHITE)

    # CTA Card below phone
    cta_y = 1140
    draw.rounded_rectangle([80, cta_y, W - 80, cta_y + 360], radius=24, fill=(30, 41, 59), outline=GOLD, width=4)

    header_cta = "SOMAIYA AGENTIC AI LAB"
    h_w = draw.textlength(header_cta, font=get_font(28))
    draw.text(((W - h_w) / 2, cta_y + 35), header_cta, font=get_font(28), fill=LIGHT_GOLD)

    big_cta = "Come and build with us."
    b_font = get_font(58)
    b_w = draw.textlength(big_cta, font=b_font)
    draw.text(((W - b_w) / 2, cta_y + 105), big_cta, font=b_font, fill=WHITE)

    sub_cta = "Turn your prompts into autonomous multi-agent reality."
    s_w = draw.textlength(sub_cta, font=get_font(26))
    draw.text(((W - s_w) / 2, cta_y + 200), sub_cta, font=get_font(26), fill=AMBER_GLOW)

    # Mandatory Legal/AI-disclosure footer inside safe zone
    disclosure = "Created with AI agents — LY Agentic AI Lab"
    d_font = get_font(24)
    d_w = draw.textlength(disclosure, font=d_font)
    draw.text(((W - d_w) / 2, cta_y + 285), disclosure, font=d_font, fill=MUTED)

    draw_caption_banner(draw, caption)
    return img
