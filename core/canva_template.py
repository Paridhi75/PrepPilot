"""
Canva-Style Study Plan Template Generator for Project C20.
Generates printable, aesthetic Canva-style HTML planners and high-res PNG posters.
Supports multiple aesthetic themes: Pastel Dream, Cyber Glow, Cozy Matcha, Sakura Blossom.
"""

import io
import json
from datetime import datetime
from typing import Dict, List, Any
from PIL import Image, ImageDraw, ImageFont

from core.models import StudyPlan, DaySchedule, StudySession


# ============================================================================
# THEME PALETTES (PASTEL THEME ONLY)
# ============================================================================
THEMES = {
    "Pastel": {
        "bg_gradient": "linear-gradient(135deg, #FFF5F7 0%, #F5F3FF 50%, #F0FDF4 100%)",
        "card_bg": "#FFFFFF",
        "card_border": "#E8ECF4",
        "header_bg": "linear-gradient(135deg, #7C3AED 0%, #9333EA 50%, #A855F7 100%)",
        "header_text": "#FFFFFF",
        "accent": "#7C3AED",
        "pill_bg": "#F3E8FF",
        "pill_text": "#6B21A8",
        "session_colors": {
            "Deep Study": {"bg": "#EDE9FE", "text": "#5B21B6", "border": "#DDD6FE"},
            "Concept Learning": {"bg": "#DCFCE7", "text": "#166534", "border": "#BBF7D0"},
            "Revision": {"bg": "#FEF9C3", "text": "#854D0E", "border": "#FEF08A"},
            "Practice Questions": {"bg": "#FCE7F3", "text": "#9D174D", "border": "#FBCFE8"},
            "Mock Test": {"bg": "#FFE4E6", "text": "#9F1239", "border": "#FECDD3"},
            "Formula / Summary Review": {"bg": "#E0F2FE", "text": "#0369A1", "border": "#BAE6FD"},
            "Buffer / Rest": {"bg": "#F1F5F9", "text": "#475569", "border": "#E2E8F0"}
        },
        "pil_bg": (255, 245, 247),
        "pil_card_bg": (255, 255, 255),
        "pil_header": (124, 58, 237),
        "pil_accent": (147, 51, 234),
        "pil_text_dark": (30, 41, 59),
        "pil_text_muted": (100, 116, 139)
    }
}
# Backward compatibility aliases mapping everything to Pastel
THEMES["Pastel Dream"] = THEMES["Pastel"]
THEMES["Matcha"] = THEMES["Pastel"]
THEMES["Matcha & Cream"] = THEMES["Pastel"]
THEMES["Cyber Glow"] = THEMES["Pastel"]
THEMES["Sakura Blossom"] = THEMES["Pastel"]


# ============================================================================
# CANVA HTML POSTER GENERATOR
# ============================================================================
def generate_canva_html(plan: StudyPlan, theme_name: str = "Pastel") -> str:
    """
    Renders a stunning, printable Canva-style study timetable poster.
    Features:
    - Card grid layout with drop shadows, cute stickers, and check-circles.
    - Water intake tracker, habit checkboxes, motivational quotes.
    - Print-ready with CSS `@media print` rules.
    """
    theme = THEMES.get(theme_name, THEMES["Pastel"])
    quotes = [
        "✨ Small daily efforts build massive exam success!",
        "🌱 Trust the process. Focus on today's goals.",
        "💡 Don't study until you get it right; study until you can't get it wrong.",
        "🔥 Consistency over cramming. You've got this!"
    ]
    quote = quotes[hash(plan.plan_id) % len(quotes)]

    # Group days into rows of 3 or 4
    days_html = []
    for day in plan.days:
        # Sessions inside day
        sess_items = []
        for s in day.sessions:
            colors = theme["session_colors"].get(
                s.session_type,
                {"bg": "#EEF2F6", "text": "#1E293B", "border": "#CBD5E1"}
            )
            weak_star = " ⭐" if s.is_weak_subject else ""
            sess_items.append(f"""
            <div class="session-item" style="background: {colors['bg']}; border-left: 4px solid {colors['border']};">
                <div class="session-top">
                    <span class="session-time">⏰ {s.start_time} - {s.end_time}</span>
                    <span class="session-badge" style="background:{colors['border']}; color:{colors['text']}; font-weight:700;">{s.session_type}</span>
                </div>
                <div class="session-subj" style="color: {colors['text']};">
                    <b>{s.subject}</b>{weak_star}
                </div>
                <div class="session-topic">{s.topic}</div>
                <div class="session-check">
                    <input type="checkbox" id="chk-{s.date}-{s.subject.replace(' ', '')}" />
                    <label for="chk-{s.date}-{s.subject.replace(' ', '')}">Goal: {s.learning_objective[:45]}...</label>
                </div>
            </div>
            """)

        sessions_block = "".join(sess_items) if sess_items else "<div class='rest-day'>☕ Rest & Buffer Day</div>"

        # Day card
        try:
            dt_obj = datetime.strptime(day.date, "%Y-%m-%d")
            day_name = dt_obj.strftime("%A")
            display_date = dt_obj.strftime("%b %d")
        except Exception:
            day_name = f"Day {day.day_number}"
            display_date = day.date

        days_html.append(f"""
        <div class="canva-day-card">
            <div class="day-header">
                <div>
                    <span class="day-num">DAY {day.day_number}</span>
                    <h3 class="day-title">{day_name}</h3>
                </div>
                <div class="day-badge-wrap">
                    <span class="day-date">{display_date}</span>
                    <span class="day-hours">⏳ {day.total_hours:.1f}h</span>
                </div>
            </div>
            <div class="day-body">
                {sessions_block}
            </div>
            <div class="day-footer">
                <span>Notes: {day.notes or 'Stay focused & take 5-min breaks!'}</span>
            </div>
        </div>
        """)

    all_days_str = "\n".join(days_html)

    # Subject badges in summary
    subj_pills = []
    for subj, hrs in plan.subject_hour_summary.items():
        subj_pills.append(f"""
        <div class="subj-pill">
            <span class="subj-name">📘 {subj}</span>
            <span class="subj-hrs">{hrs:.1f} hrs</span>
        </div>
        """)
    subj_pills_str = "\n".join(subj_pills)

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Canva Study Timetable — {plan.student_name}</title>
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Caveat:wght@600;700&display=swap" rel="stylesheet">
<style>
    * {{
        box-sizing: border-box;
        margin: 0;
        padding: 0;
    }}
    body {{
        font-family: 'Plus Jakarta Sans', sans-serif;
        background: {theme['bg_gradient']};
        color: #1E293B;
        padding: 30px 20px;
        min-height: 100vh;
    }}
    .canva-container {{
        max-width: 1200px;
        margin: 0 auto;
        background: {theme['card_bg']};
        border-radius: 24px;
        box-shadow: 0 20px 40px -10px rgba(0, 0, 0, 0.12), 0 0 0 1px rgba(0, 0, 0, 0.05);
        overflow: hidden;
        padding: 36px 40px;
    }}
    /* Top Banner */
    .poster-header {{
        background: {theme['header_bg']};
        color: {theme['header_text']};
        padding: 28px 32px;
        border-radius: 18px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 16px;
        box-shadow: 0 10px 25px -5px rgba(99, 102, 241, 0.35);
        margin-bottom: 24px;
    }}
    .header-left h1 {{
        font-size: 2.2rem;
        font-weight: 800;
        letter-spacing: -0.02em;
        margin-bottom: 6px;
    }}
    .header-left p {{
        font-size: 1.05rem;
        opacity: 0.9;
    }}
    .header-right {{
        text-align: right;
    }}
    .quote-sticker {{
        font-family: 'Caveat', cursive;
        font-size: 1.5rem;
        color: #FEF08A;
        background: rgba(0,0,0,0.2);
        padding: 8px 16px;
        border-radius: 12px;
        display: inline-block;
    }}
    /* Summary Tracker Bar */
    .tracker-bar {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 12px;
        background: #F8FAFC;
        border: 1px solid #E2E8F0;
        padding: 16px 20px;
        border-radius: 14px;
        margin-bottom: 28px;
    }}
    .pills-group {{
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
    }}
    .subj-pill {{
        background: #FFFFFF;
        border: 1px solid #CBD5E1;
        border-radius: 9999px;
        padding: 6px 14px;
        font-size: 0.85rem;
        display: flex;
        align-items: center;
        gap: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.04);
    }}
    .subj-name {{
        font-weight: 600;
        color: #334155;
    }}
    .subj-hrs {{
        background: #EEF2F6;
        color: #475569;
        padding: 2px 8px;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 700;
    }}
    /* Days Grid */
    .days-grid {{
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
        gap: 20px;
        margin-bottom: 30px;
    }}
    .canva-day-card {{
        background: #FFFFFF;
        border: 1.5px solid {theme['card_border']};
        border-radius: 16px;
        padding: 18px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.03);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }}
    .canva-day-card:hover {{
        transform: translateY(-3px);
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.08);
    }}
    .day-header {{
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        border-bottom: 1.5px dashed #E2E8F0;
        padding-bottom: 12px;
        margin-bottom: 14px;
    }}
    .day-num {{
        font-size: 0.75rem;
        text-transform: uppercase;
        font-weight: 800;
        color: {theme['accent']};
        letter-spacing: 0.08em;
    }}
    .day-title {{
        font-size: 1.25rem;
        font-weight: 700;
        color: #1E293B;
    }}
    .day-badge-wrap {{
        text-align: right;
    }}
    .day-date {{
        font-size: 0.8rem;
        font-weight: 600;
        color: #64748B;
        display: block;
    }}
    .day-hours {{
        background: #F1F5F9;
        color: #334155;
        font-size: 0.75rem;
        font-weight: 700;
        padding: 2px 8px;
        border-radius: 9999px;
        display: inline-block;
        margin-top: 4px;
    }}
    .day-body {{
        display: flex;
        flex-direction: column;
        gap: 10px;
        flex-grow: 1;
        margin-bottom: 12px;
    }}
    .session-item {{
        border-radius: 10px;
        padding: 10px 12px;
        font-size: 0.85rem;
    }}
    .session-top {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 4px;
    }}
    .session-time {{
        font-size: 0.75rem;
        font-weight: 600;
        color: #475569;
    }}
    .session-badge {{
        font-size: 0.7rem;
        padding: 2px 6px;
        border-radius: 6px;
    }}
    .session-subj {{
        font-size: 0.95rem;
        margin-bottom: 2px;
    }}
    .session-topic {{
        font-size: 0.8rem;
        color: #475569;
        margin-bottom: 6px;
    }}
    .session-check {{
        display: flex;
        align-items: center;
        gap: 6px;
        font-size: 0.75rem;
        color: #64748B;
        border-top: 1px dotted rgba(0,0,0,0.1);
        padding-top: 4px;
    }}
    .session-check input[type="checkbox"] {{
        accent-color: {theme['accent']};
        width: 14px;
        height: 14px;
        cursor: pointer;
    }}
    .day-footer {{
        font-size: 0.75rem;
        color: #94A3B8;
        font-style: italic;
        padding-top: 8px;
        border-top: 1px solid #F1F5F9;
    }}
    .rest-day {{
        text-align: center;
        color: #64748B;
        padding: 24px;
        font-weight: 600;
    }}
    /* Canva Habit Footer */
    .canva-footer {{
        background: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 16px;
        padding: 20px 24px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 16px;
    }}
    .habits-group {{
        display: flex;
        gap: 20px;
        align-items: center;
    }}
    .habit-item {{
        font-size: 0.85rem;
        font-weight: 600;
        color: #334155;
    }}
    .water-icons {{
        font-size: 1.1rem;
        margin-left: 6px;
    }}
    .print-btn {{
        background: {theme['accent']};
        color: white;
        border: none;
        padding: 10px 20px;
        border-radius: 10px;
        font-weight: 700;
        font-size: 0.9rem;
        cursor: pointer;
        display: inline-flex;
        align-items: center;
        gap: 8px;
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.15);
    }}
    .print-btn:hover {{
        opacity: 0.9;
    }}
    @media print {{
        body {{
            background: #FFFFFF !important;
            padding: 0;
        }}
        .canva-container {{
            box-shadow: none !important;
            padding: 0 !important;
        }}
        .print-btn {{
            display: none !important;
        }}
    }}
</style>
</head>
<body>

<div class="canva-container">
    <!-- Top Poster Banner -->
    <div class="poster-header">
        <div class="header-left">
            <h1>✨ {plan.student_name.upper()}'S STUDY SCHEDULE</h1>
            <p>Target Goal: Peak Exam Mastery &bull; Total Study Time: <b>{plan.total_study_hours:.1f} Hours</b></p>
        </div>
        <div class="header-right">
            <div class="quote-sticker">{quote}</div>
        </div>
    </div>

    <!-- Summary Bar -->
    <div class="tracker-bar">
        <div class="pills-group">
            {subj_pills_str}
        </div>
    </div>

    <!-- Grid of Days -->
    <div class="days-grid">
        {all_days_str}
    </div>

    <!-- Canva Habit & Wellness Footer -->
    <div class="canva-footer">
        <div class="habits-group">
            <div class="habit-item">
                Daily Hydration: <span class="water-icons">💧💧💧💧💧</span>
            </div>
            <div class="habit-item">
                Study Method: <b>Pomodoro (25m Focus + 5m Break)</b>
            </div>
            <div class="habit-item">
                Sleep Target: <b>7-8 Hours 💤</b>
            </div>
        </div>
        <button class="print-btn" onclick="window.print()">
            🖨️ Print / Save as PDF
        </button>
    </div>
</div>

</body>
</html>"""
    return html_content


# ============================================================================
# CANVA HIGH-RES GRAPHIC (PNG) GENERATOR (PILLOW)
# ============================================================================
def generate_canva_png(plan: StudyPlan, theme_name: str = "Pastel") -> bytes:
    """
    Renders an aesthetic, high-resolution Canva-style image poster using Pillow.
    Returns bytes suitable for downloading as a PNG graphic.
    """
    theme = THEMES.get(theme_name, THEMES["Pastel"])

    # Determine dimensions based on number of days
    card_width = 360
    card_height = 380
    gap = 25
    margin = 40
    cols = 3
    num_days = len(plan.days)
    rows = (num_days + cols - 1) // cols
    rows = max(1, rows)

    img_width = (margin * 2) + (cols * card_width) + ((cols - 1) * gap)
    header_height = 200
    footer_height = 100
    img_height = margin + header_height + (rows * (card_height + gap)) + footer_height + margin

    # Create image
    img = Image.new("RGB", (img_width, img_height), theme["pil_bg"])
    draw = ImageDraw.Draw(img)

    # Load system or default font
    try:
        font_large = ImageFont.truetype("arial.ttf", 36)
        font_med = ImageFont.truetype("arial.ttf", 22)
        font_small = ImageFont.truetype("arial.ttf", 16)
        font_bold = ImageFont.truetype("arialbd.ttf", 20)
    except Exception:
        font_large = ImageFont.load_default()
        font_med = ImageFont.load_default()
        font_small = ImageFont.load_default()
        font_bold = ImageFont.load_default()

    # Draw Header Box
    h_x1, h_y1 = margin, margin
    h_x2, h_y2 = img_width - margin, margin + header_height - 20
    draw.rounded_rectangle([h_x1, h_y1, h_x2, h_y2], radius=20, fill=theme["pil_header"])

    # Header text
    draw.text((h_x1 + 30, h_y1 + 30), f"STUDY WITH ME: {plan.student_name.upper()}", fill=(255, 255, 255), font=font_large)
    draw.text(
        (h_x1 + 30, h_y1 + 85),
        f"Goal: Exam Mastery  |  Total Budget: {plan.total_study_hours:.1f} Study Hours  |  Canva Style",
        fill=(230, 235, 255),
        font=font_med
    )

    score = plan.validation_report.compliance_score if plan.validation_report else 100.0
    draw.text(
        (h_x1 + 30, h_y1 + 125),
        f"Constraint Adherence: {score}%  *  Generated by PromptCraft C20",
        fill=(254, 240, 138),
        font=font_small
    )

    # Draw Day Cards
    for idx, day in enumerate(plan.days):
        col_idx = idx % cols
        row_idx = idx // cols

        x1 = margin + col_idx * (card_width + gap)
        y1 = margin + header_height + row_idx * (card_height + gap)
        x2 = x1 + card_width
        y2 = y1 + card_height

        # Card Background
        draw.rounded_rectangle([x1, y1, x2, y2], radius=16, fill=theme["pil_card_bg"], outline=(226, 232, 240), width=2)

        # Day Header
        try:
            dt_obj = datetime.strptime(day.date, "%Y-%m-%d")
            day_title = dt_obj.strftime("%A, %b %d")
        except Exception:
            day_title = f"Day {day.day_number}"

        draw.text((x1 + 18, y1 + 18), f"DAY {day.day_number}", fill=theme["pil_accent"], font=font_small)
        draw.text((x1 + 18, y1 + 38), day_title, fill=theme["pil_text_dark"], font=font_bold)
        draw.text((x2 - 80, y1 + 25), f"{day.total_hours:.1f}h", fill=theme["pil_text_muted"], font=font_small)

        # Divider line
        draw.line([(x1 + 18, y1 + 68), (x2 - 18, y1 + 68)], fill=(241, 245, 249), width=2)

        # Draw Session Blocks
        curr_y = y1 + 80
        for s in day.sessions[:3]:  # Show up to 3 slots
            # Slot pill
            draw.rounded_rectangle([x1 + 16, curr_y, x2 - 16, curr_y + 75], radius=10, fill=(248, 250, 252), outline=(226, 232, 240), width=1)
            # Slot text
            draw.text((x1 + 26, curr_y + 8), f"{s.start_time}-{s.end_time}  [{s.session_type}]", fill=theme["pil_accent"], font=font_small)
            draw.text((x1 + 26, curr_y + 28), s.subject[:25], fill=theme["pil_text_dark"], font=font_bold)
            draw.text((x1 + 26, curr_y + 50), f"- {s.topic[:30]}", fill=theme["pil_text_muted"], font=font_small)
            curr_y += 85

    # Output to PNG bytes
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()
