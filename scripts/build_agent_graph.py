import os
from PIL import Image, ImageDraw, ImageFont

def create_agent_graph(output_path="docs/agent_graph.png"):
    W, H = 2000, 1250
    img = Image.new("RGBA", (W, H), (13, 17, 23, 255))
    draw = ImageDraw.Draw(img)

    font_path = "/System/Library/Fonts/Helvetica.ttc"
    title_font = ImageFont.truetype(font_path, 38)
    sub_font = ImageFont.truetype(font_path, 20)
    sec_font = ImageFont.truetype(font_path, 22)
    card_title_font = ImageFont.truetype(font_path, 20)
    card_sub_font = ImageFont.truetype(font_path, 15)
    badge_font = ImageFont.truetype(font_path, 13)

    for x in range(0, W, 40):
        draw.line([(x, 0), (x, H)], fill=(22, 27, 34, 150), width=1)
    for y in range(0, H, 40):
        draw.line([(0, y), (W, y)], fill=(22, 27, 34, 150), width=1)

    draw.rounded_rectangle([(40, 30), (W - 40, 140)], radius=16, fill=(21, 27, 38, 255), outline=(56, 189, 248, 120), width=2)
    draw.text((70, 48), "AGENTREEL: 7-AGENT ORCHESTRATION PIPELINE WITH REPAIR LOOP", fill=(248, 250, 252), font=title_font)
    draw.text((70, 96), "Autonomous Brief-to-Broadcast Video Production System with Multi-Track Synthesis & Bounded QA Repair Loop", fill=(148, 163, 184), font=sub_font)
    
    draw.rounded_rectangle([(W - 460, 52), (W - 70, 118)], radius=10, fill=(30, 41, 59, 255), outline=(100, 116, 139, 200), width=1)
    draw.text((W - 440, 64), "LY AGENTIC AI LABORATORY", fill=(56, 189, 248), font=card_sub_font)
    draw.text((W - 440, 88), "K J Somaiya School of Engineering", fill=(203, 213, 225), font=badge_font)

    draw.text((70, 160), "1. INPUT SPECIFICATION", fill=(245, 158, 11), font=sec_font)
    draw.text((450, 160), "2. SEVEN-AGENT ORCHESTRATION PIPELINE (core/orchestrator.py)", fill=(56, 189, 248), font=sec_font)
    draw.text((1550, 160), "3. FINAL DELIVERABLES", fill=(16, 185, 129), font=sec_font)

    def draw_card(box, title, subtitle, artifact="", badge="", bg_col=(21, 27, 38), border_col=(56, 189, 248), badge_col=(56, 189, 248)):
        x0, y0, x1, y1 = box
        draw.rounded_rectangle([box[0], box[1], box[2], box[3]], radius=12, fill=bg_col, outline=border_col, width=2)
        if badge:
            bw = len(badge) * 8 + 16
            draw.rounded_rectangle([(x1 - bw - 14, y0 + 12), (x1 - 14, y0 + 32)], radius=6, fill=(15, 23, 42), outline=badge_col, width=1)
            draw.text((x1 - bw - 6, y0 + 15), badge, fill=badge_col, font=badge_font)
        draw.text((x0 + 18, y0 + 14), title, fill=(248, 250, 252), font=card_title_font)
        draw.text((x0 + 18, y0 + 44), subtitle, fill=(148, 163, 184), font=card_sub_font)
        if artifact:
            draw.text((x0 + 18, y0 + 72), f"Artifact: {artifact}", fill=(110, 231, 183), font=badge_font)

    def draw_arrow(p1, p2, color=(100, 116, 139), width=2, label=""):
        draw.line([p1, p2], fill=color, width=width)
        x1, y1 = p1
        x2, y2 = p2
        if x1 == x2:
            sgn = 1 if y2 > y1 else -1
            draw.polygon([(x2 - 5, y2 - 8 * sgn), (x2 + 5, y2 - 8 * sgn), (x2, y2)], fill=color)
        elif y1 == y2:
            sgn = 1 if x2 > x1 else -1
            draw.polygon([(x2 - 8 * sgn, y2 - 5), (x2 - 8 * sgn, y2 + 5), (x2, y2)], fill=color)
        if label:
            lx, ly = (x1 + x2) // 2, (y1 + y2) // 2 - 14
            draw.text((lx - len(label)*3, ly), label, fill=color, font=badge_font)

    draw_card((50, 210, 390, 320), "Creative Brief", "briefs/practice.yaml\nTopic, Tone, Pacing & Specs", "briefs/practice.yaml", "YAML SPEC", bg_col=(30, 27, 20), border_col=(245, 158, 11), badge_col=(245, 158, 11))
    draw_card((50, 360, 390, 470), "Grounded Sources", "Faculty documents in data/\nPDF, Markdown, plain text", "data/ (verified)", "SOURCE DOCS", bg_col=(30, 27, 20), border_col=(245, 158, 11), badge_col=(245, 158, 11))
    draw_card((50, 510, 390, 620), "Preflight Guard", "Config & API key checks;\nschema verification", "core/validators.py", "PREFLIGHT", bg_col=(25, 30, 45), border_col=(99, 102, 241), badge_col=(99, 102, 241))

    draw_card((440, 210, 920, 315), "Agent 1: Planner", "Decomposes brief into stages, budgets & bounds", "outputs/plan.json", "GROQ / GPT", bg_col=(15, 23, 42), border_col=(56, 189, 248), badge_col=(56, 189, 248))
    draw_card((440, 350, 920, 455), "Agent 2: RAG Researcher", "Verbatim quote extraction & source verification", "outputs/facts.json", "PYMUPDF / RAG", bg_col=(15, 23, 42), border_col=(56, 189, 248), badge_col=(56, 189, 248))
    draw_card((440, 490, 920, 595), "Agent 3: Scriptwriter", "Timed spoken script (Hook, Narrative, CTA)", "outputs/script.json & .md", "GROQ / GPT", bg_col=(15, 23, 42), border_col=(56, 189, 248), badge_col=(56, 189, 248))
    draw_card((440, 630, 920, 735), "Agent 4: Storyboarder", "Visual shot design (6-10 shots, safe-zone captions)", "outputs/storyboard.json", "GROQ / GPT", bg_col=(15, 23, 42), border_col=(56, 189, 248), badge_col=(56, 189, 248))

    draw_card((970, 210, 1470, 315), "Agent 5: Asset Generator", "Procedural 1080x1920 graphic cards & visual layouts", "outputs/asset_manifest.json", "PILLOW GRAPHICS", bg_col=(26, 18, 48), border_col=(168, 85, 247), badge_col=(168, 85, 247))
    draw_card((970, 350, 1470, 455), "Agent 6: Timeline Editor", "Multi-track NLE alignment (V1 video, A1 audio, T1 captions)", "outputs/edit_plan.json", "NLE TIMELINE", bg_col=(26, 18, 48), border_col=(168, 85, 247), badge_col=(168, 85, 247))
    draw_card((970, 490, 1470, 605), "Agent 7: Critic & QA Validator", "18 automated rule checks + LLM claim verification\nIssue grading: Hard / Factual / Soft", "outputs/qa_report.json", "QA GUARDRAILS", bg_col=(45, 15, 25), border_col=(239, 68, 68), badge_col=(239, 68, 68))

    draw.rounded_rectangle([(970, 645), (1470, 755)], radius=12, fill=(40, 20, 20), outline=(245, 158, 11), width=2)
    draw.text((990, 658), "Targeted Bounded Repair Loop", fill=(251, 191, 36), font=card_title_font)
    draw.text((990, 688), "Max 3 iterations; rolls back to earliest responsible agent\n(Scriptwriter for claims, Storyboarder for text bounds)", fill=(214, 211, 209), font=card_sub_font)
    draw.text((990, 728), "Guarantees finite termination with zero infinite-cost recursion", fill=(148, 163, 184), font=badge_font)

    draw_card((1520, 210, 1950, 325), "Final Broadcast MP4", "outputs/final_video_v3.mp4\n1080x1920 | 30fps H.264/AAC | 44.02s", "outputs/final_video_v3.mp4", "BROADCAST VIDEO", bg_col=(10, 35, 25), border_col=(16, 185, 129), badge_col=(16, 185, 129))
    draw_card((1520, 350, 1950, 465), "SubRip Subtitles", "outputs/AgentReel_Final.srt\n6 timed cues strictly mapped to voiceover", "outputs/AgentReel_Final.srt", "SRT CAPTIONS", bg_col=(10, 35, 25), border_col=(16, 185, 129), badge_col=(16, 185, 129))
    draw_card((1520, 490, 1950, 605), "QA & Render Telemetry", "outputs/qa_report.json (18 rules)\noutputs/render_report_v3.json", "outputs/qa_report.json", "AUDITED METRICS", bg_col=(10, 35, 25), border_col=(16, 185, 129), badge_col=(16, 185, 129))
    draw_card((1520, 630, 1950, 745), "Execution Logs & Costs", "logs/run_log.jsonl (50 traces)\nlogs/cost_report.csv (tokens & USD)", "logs/run_log.jsonl", "VERIFIED LOGS", bg_col=(10, 35, 25), border_col=(16, 185, 129), badge_col=(16, 185, 129))

    draw_arrow((390, 265), (440, 265), color=(245, 158, 11), width=2, label="Brief YAML")
    draw_arrow((390, 415), (440, 400), color=(245, 158, 11), width=2, label="RAG Docs")

    draw_arrow((680, 315), (680, 350), color=(56, 189, 248), width=2)
    draw_arrow((680, 455), (680, 490), color=(56, 189, 248), width=2)
    draw_arrow((680, 595), (680, 630), color=(56, 189, 248), width=2)

    draw.line([(920, 680), (945, 680)], fill=(168, 85, 247), width=2)
    draw.line([(945, 680), (945, 265)], fill=(168, 85, 247), width=2)
    draw_arrow((945, 265), (970, 265), color=(168, 85, 247), width=2, label="Shot specs")

    draw_arrow((1220, 315), (1220, 350), color=(168, 85, 247), width=2)
    draw_arrow((1220, 455), (1220, 490), color=(168, 85, 247), width=2)

    draw_arrow((1220, 605), (1220, 645), color=(239, 68, 68), width=2, label="FAIL (Defect)")

    draw.line([(970, 700), (935, 700)], fill=(245, 158, 11), width=2)
    draw.line([(935, 700), (935, 540)], fill=(245, 158, 11), width=2)
    draw_arrow((935, 540), (920, 540), color=(245, 158, 11), width=2, label="Repair Re-run")

    draw.line([(1470, 550), (1495, 550)], fill=(16, 185, 129), width=2)
    draw.line([(1495, 550), (1495, 265)], fill=(16, 185, 129), width=2)
    draw_arrow((1495, 265), (1520, 265), color=(16, 185, 129), width=2, label="PASS")
    draw_arrow((1495, 405), (1520, 405), color=(16, 185, 129), width=2)
    draw_arrow((1495, 550), (1520, 550), color=(16, 185, 129), width=2)
    draw.line([(1495, 550), (1495, 685)], fill=(16, 185, 129), width=2)
    draw_arrow((1495, 685), (1520, 685), color=(16, 185, 129), width=2)

    draw.rounded_rectangle([(40, 800), (W - 40, 1200)], radius=16, fill=(18, 24, 38, 255), outline=(71, 85, 105, 180), width=1)
    draw.text((70, 820), "PIPELINE GUARANTEES & EMPIRICAL EXECUTION METRICS", fill=(248, 250, 252), font=card_title_font)

    draw.rounded_rectangle([(70, 860), (490, 1160)], radius=10, fill=(15, 23, 42), outline=(56, 189, 248, 100), width=1)
    draw.text((95, 880), "AUTONOMY LEVEL", fill=(56, 189, 248), font=card_sub_font)
    draw.text((95, 910), "Full Autonomy (L4)", fill=(248, 250, 252), font=card_title_font)
    draw.text((95, 950), "• 0 Human Interventions\n• Verified in logs/interventions.md\n• Deterministic execution seed (42)\n• Optional human review gate\n  available via --require-review", fill=(148, 163, 184), font=card_sub_font)

    draw.rounded_rectangle([(520, 860), (960, 1160)], radius=10, fill=(15, 23, 42), outline=(239, 68, 68, 100), width=1)
    draw.text((545, 880), "CRITIC QA HUD (18 RULES)", fill=(239, 68, 68), font=card_sub_font)
    draw.text((545, 910), "PASS_WITH_WARNINGS", fill=(248, 250, 252), font=card_title_font)
    draw.text((545, 950), "• 0 Hard / Blocking Errors\n• 5 Non-blocking Soft Warnings\n• Timeline bounds: 35s - 45s checked\n• Safe-zone text checks: 1-80 chars\n• Bounded repair limit: 3 attempts", fill=(148, 163, 184), font=card_sub_font)

    draw.rounded_rectangle([(990, 860), (1440, 1160)], radius=10, fill=(15, 23, 42), outline=(168, 85, 247, 100), width=1)
    draw.text((1015, 880), "TOKEN ECONOMICS & LATENCY", fill=(168, 85, 247), font=card_sub_font)
    draw.text((1015, 910), "Audited LLM & Local Metrics", fill=(248, 250, 252), font=card_title_font)
    draw.text((1015, 950), "• Groq Model: openai/gpt-oss-120b\n• Prompt Tokens: 12,247 (Audited Total)\n• Completion Tokens: 4,604\n• Total LLM Calls: 9 (0 Interventions)\n• Offline V3 Render Time: 12.44s", fill=(148, 163, 184), font=card_sub_font)

    draw.rounded_rectangle([(1470, 860), (W - 70, 1160)], radius=10, fill=(15, 23, 42), outline=(16, 185, 129, 100), width=1)
    draw.text((1495, 880), "BROADCAST COMPLIANCE", fill=(16, 185, 129), font=card_sub_font)
    draw.text((1495, 910), "1080x1920 (9:16) @ 30fps", fill=(248, 250, 252), font=card_title_font)
    draw.text((1495, 950), "• Duration: 44.02s (target: 44.0s)\n• Video Codec: H.264 (High Profile)\n• Audio Codec: AAC (48kHz, Stereo)\n• File Size: 2.21 MB (Clean Decode)\n• Subtitles: 6 Non-overlapping cues", fill=(148, 163, 184), font=card_sub_font)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    img.save(output_path, "PNG", quality=95)
    print(f"Successfully rendered agent graph to: {output_path} ({W}x{H})")

if __name__ == "__main__":
    create_agent_graph()
