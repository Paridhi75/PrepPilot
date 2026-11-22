"""
C20 AI-Powered Personalized Study Plan Generator
Course: Prompt Engineering (SCSE4041) | Problem ID: C20 | Team: PromptCraft
Main Streamlit Application
"""

import os
import json
from datetime import date, datetime, timedelta
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
import plotly.express as px
import plotly.graph_objects as go

from core.models import StudentProfile, Subject, StudyPlan
from core.generator import StudyPlanGenerator
from core.validator import ConstraintValidator
from core.evaluator import BenchmarkEvaluator
from core.exporter import StudyPlanExporter
from core.canva_template import generate_canva_html, generate_canva_png, THEMES
from core.prompts import (
    build_v1_baseline_prompt,
    build_v2_constraint_prompt,
    build_v3_structured_prompt,
    build_v4_critic_prompt,
    build_v4_refinement_prompt
)
from data.benchmark_scenarios import get_benchmark_scenarios

# ----------------------------------------------------------------------------
# PAGE CONFIGURATION & STYLING
# ----------------------------------------------------------------------------
st.set_page_config(
    page_title="PromptCraft — AI Study Plan Generator (C20)",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern glassmorphism & typography
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }

    .main-header {
        background: linear-gradient(135deg, #1E1B4B 0%, #312E81 50%, #4338CA 100%);
        padding: 2rem;
        border-radius: 1rem;
        color: white;
        margin-bottom: 1.5rem;
        box-shadow: 0 10px 25px -5px rgba(49, 46, 129, 0.4);
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    .main-header h1 {
        color: #FFFFFF !important;
        font-weight: 800;
        font-size: 2.3rem;
        margin-bottom: 0.4rem;
    }
    .main-header p {
        color: #C7D2FE;
        font-size: 1.05rem;
        margin-bottom: 0;
    }
    .metric-card {
        background: #1E293B;
        border: 1px solid #334155;
        border-radius: 0.75rem;
        padding: 1.2rem;
        text-align: center;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
    }
    .metric-title {
        color: #94A3B8;
        font-size: 0.85rem;
        text-transform: uppercase;
        font-weight: 600;
        letter-spacing: 0.05em;
    }
    .metric-value {
        color: #F8FAFC;
        font-size: 1.85rem;
        font-weight: 700;
        margin-top: 0.3rem;
    }
    .badge-pass {
        background-color: #064E3B;
        color: #6EE7B7;
        padding: 0.25rem 0.6rem;
        border-radius: 9999px;
        font-size: 0.8rem;
        font-weight: 600;
        display: inline-block;
    }
    .badge-fail {
        background-color: #7F1D1D;
        color: #FCA5A5;
        padding: 0.25rem 0.6rem;
        border-radius: 9999px;
        font-size: 0.8rem;
        font-weight: 600;
        display: inline-block;
    }
    .badge-warn {
        background-color: #78350F;
        color: #FCD34D;
        padding: 0.25rem 0.6rem;
        border-radius: 9999px;
        font-size: 0.8rem;
        font-weight: 600;
        display: inline-block;
    }
    .badge-rank-s {
        background: linear-gradient(135deg, #EC4899 0%, #8B5CF6 100%);
        color: #FFFFFF;
        padding: 0.35rem 0.85rem;
        border-radius: 9999px;
        font-weight: 800;
        font-size: 0.95rem;
        box-shadow: 0 4px 12px rgba(236, 72, 153, 0.4);
        display: inline-block;
    }
    .step-box {
        background: #0F172A;
        border-left: 4px solid #6366F1;
        padding: 1rem;
        margin-bottom: 0.8rem;
        border-radius: 0 0.5rem 0.5rem 0;
    }
    .canva-banner {
        background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 50%, #DB2777 100%);
        border-radius: 16px;
        padding: 20px 24px;
        color: white;
        margin: 20px 0;
        box-shadow: 0 10px 25px -5px rgba(124, 58, 237, 0.4);
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 14px;
    }
    .canva-banner h2 {
        color: #FFFFFF !important;
        font-size: 1.6rem;
        font-weight: 800;
        margin: 0;
    }
    .canva-preview-frame {
        border-radius: 20px;
        border: 2px solid rgba(255, 255, 255, 0.15);
        box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.35);
        overflow: hidden;
        background: #0F172A;
        margin-top: 15px;
    }
    .pomodoro-card {
        background: linear-gradient(135deg, #1E1B4B 0%, #2E1065 100%);
        border: 1px solid #4C1D95;
        border-radius: 16px;
        padding: 20px;
        color: white;
        text-align: center;
        box-shadow: 0 8px 20px rgba(0,0,0,0.25);
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 6px;
        padding: 8px 18px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)


# ----------------------------------------------------------------------------
# SESSION STATE INITIALIZATION
# ----------------------------------------------------------------------------
if "current_plan" not in st.session_state:
    st.session_state.current_plan = None
if "compare_plan_a" not in st.session_state:
    st.session_state.compare_plan_a = None
if "compare_plan_b" not in st.session_state:
    st.session_state.compare_plan_b = None
if "benchmark_results" not in st.session_state:
    st.session_state.benchmark_results = None

# Default reference date for calendar
TODAY = date.today()

# Background execution config (zero UI clutter)
api_key_input = os.getenv("GEMINI_API_KEY", "")
use_simulation = not bool(api_key_input)

# ----------------------------------------------------------------------------
# SIDEBAR CONFIGURATION
# ----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### 📋 Quick Preset Scenarios")
    presets = get_benchmark_scenarios(reference_date=TODAY)
    preset_choice = st.selectbox(
        "Load Preset Scenario",
        ["Custom Setup"] + list(presets.keys())
    )

    st.markdown("---")
    st.markdown("### 👤 Student Profile")

    if preset_choice != "Custom Setup":
        chosen_profile = presets[preset_choice]
        default_name = chosen_profile.student_name
        default_hours = chosen_profile.available_hours_per_day
        default_start_date = TODAY
        default_sess_len = chosen_profile.preferred_session_hours
    else:
        default_name = "Alex Johnson"
        default_hours = 4.0
        default_start_date = TODAY
        default_sess_len = 1.5

    student_name = st.text_input("Student Name", value=default_name)
    available_hours = st.slider(
        "Daily Study Budget (Hours/Day)",
        min_value=1.0,
        max_value=12.0,
        value=float(default_hours),
        step=0.5,
        help="Hard constraint: sum of hours on any day cannot exceed this limit."
    )
    start_date = st.date_input("Timetable Start Date", value=default_start_date)
    session_pref = st.selectbox(
        "Session Length Preference",
        [1.0, 1.5, 2.0, 2.5, 3.0],
        index=1 if default_sess_len == 1.5 else 0
    )

    st.markdown("---")
    st.markdown("### 🎯 Prompt Engineering Version")
    prompt_version = st.selectbox(
        "Select Prompt Iteration",
        ["V4_Refined_Workflow"],
        index=0,
        format_func=lambda x: "V4 — Refined Workflow (Self-Correction)",
        help="Production Chain-of-Verification pipeline with automated self-correction."
    )


# ============================================================================
# MAIN APPLICATION INTERFACE
# ============================================================================
st.subheader("1. Configure Subjects and Examination Schedule")

# If preset was selected, load its subjects
if preset_choice != "Custom Setup":
    default_subjects = presets[preset_choice].subjects
else:
    default_subjects = [
        Subject(
            name="Data Structures & Algorithms",
            exam_date=(TODAY + timedelta(days=5)).isoformat(),
            is_weak=False,
            priority="High",
            topics=["Binary Trees", "Graphs", "Dynamic Programming"]
        ),
        Subject(
            name="Discrete Mathematics",
            exam_date=(TODAY + timedelta(days=7)).isoformat(),
            is_weak=True,
            priority="Critical",
            topics=["Graph Theory", "Recurrence Relations", "Combinatorics"]
        ),
        Subject(
            name="Operating Systems",
            exam_date=(TODAY + timedelta(days=10)).isoformat(),
            is_weak=False,
            priority="Medium",
            topics=["Process Scheduling", "Virtual Memory", "Deadlocks"]
        ),
    ]

# Subject input form
with st.expander("📝 View / Edit Subject List & Exam Dates", expanded=True):
    st.write("Specify your exam dates, weak subjects, and key topics below:")

    subject_entries = []
    num_subjects = st.number_input("Number of Subjects", min_value=1, max_value=8, value=len(default_subjects))

    cols_header = st.columns([3, 2, 1.5, 2, 3.5])
    cols_header[0].markdown("**Subject Name**")
    cols_header[1].markdown("**Exam Date**")
    cols_header[2].markdown("**Weak Subject?**")
    cols_header[3].markdown("**Priority**")
    cols_header[4].markdown("**Key Topics (Comma Separated)**")

    for i in range(num_subjects):
        s_default = default_subjects[i] if i < len(default_subjects) else None
        c1, c2, c3, c4, c5 = st.columns([3, 2, 1.5, 2, 3.5])

        s_name = c1.text_input(
            f"Subject {i+1}",
            value=s_default.name if s_default else f"Subject {i+1}",
            key=f"subj_name_{i}",
            label_visibility="collapsed"
        )

        # Date calculation
        def_dt = s_default.exam_date_obj if s_default else (TODAY + timedelta(days=(i+1)*3))
        s_exam = c2.date_input(
            f"Exam Date {i+1}",
            value=def_dt,
            key=f"subj_exam_{i}",
            label_visibility="collapsed"
        )

        s_weak = c3.checkbox(
            "Weak",
            value=s_default.is_weak if s_default else False,
            key=f"subj_weak_{i}"
        )

        s_priority = c4.selectbox(
            f"Priority {i+1}",
            ["Low", "Medium", "High", "Critical"],
            index=["Low", "Medium", "High", "Critical"].index(s_default.priority if s_default else "Medium"),
            key=f"subj_prio_{i}",
            label_visibility="collapsed"
        )

        s_topics_str = c5.text_input(
            f"Topics {i+1}",
            value=", ".join(s_default.topics) if s_default else "Unit 1, Unit 2",
            key=f"subj_topics_{i}",
            label_visibility="collapsed"
        )

        topics_list = [t.strip() for t in s_topics_str.split(",") if t.strip()]

        subject_entries.append(
            Subject(
                name=s_name,
                exam_date=s_exam.isoformat(),
                is_weak=s_weak,
                priority=s_priority,
                topics=topics_list
            )
        )

# Build student profile
profile = StudentProfile(
    student_name=student_name,
    available_hours_per_day=available_hours,
    start_date=start_date.isoformat(),
    preferred_session_hours=session_pref,
    daily_start_time="09:00",
    subjects=subject_entries
)

# Generate Button
generate_col, info_col = st.columns([2, 5])
with generate_col:
    btn_generate = st.button("🚀 Generate Study Plan", type="primary", use_container_width=True)

with info_col:
    st.markdown(
        f"**Active Mode:** `{prompt_version}` &bull; "
        f"**Daily Limit:** `{available_hours}h/day` &bull; "
        f"**Subjects:** `{len(subject_entries)}` (Weak: `{len(profile.weak_subjects)}`)"
    )

if btn_generate:
    with st.spinner(f"Running generation via {prompt_version}..."):
        generator = StudyPlanGenerator(api_key=api_key_input)
        plan = generator.generate(profile, version=prompt_version, force_simulation=use_simulation)
        st.session_state.current_plan = plan
        st.success("✨ Study Timetable generated successfully!")

# Display Plan if Available (Streamlined view matching official demo)
plan: StudyPlan = st.session_state.current_plan
if plan:
    st.markdown("---")
    canva_html = generate_canva_html(plan, theme_name="Pastel")
    canva_png = generate_canva_png(plan, theme_name="Pastel")
    file_slug = plan.student_name.lower().replace(' ', '_')

    # Clean 1-Click Download Bar
    st.markdown("### 📥 Download Your Study Plan")
    dl_col1, dl_col2, dl_col3, dl_col4, dl_col5 = st.columns(5)
    with dl_col1:
        st.download_button(
            "🖼️ PNG Poster",
            data=canva_png,
            file_name=f"study_timetable_{file_slug}.png",
            mime="image/png",
            use_container_width=True,
            help="Download aesthetic high-res Canva poster graphic!"
        )
    with dl_col2:
        st.download_button(
            "🖨️ PDF / HTML",
            data=canva_html,
            file_name=f"study_timetable_{file_slug}.html",
            mime="text/html",
            use_container_width=True,
            help="Download print-ready Canva template with 1-click Print to PDF!"
        )
    with dl_col3:
        ics_str = StudyPlanExporter.to_ics(plan)
        st.download_button(
            "📅 Calendar (.ics)",
            data=ics_str,
            file_name=f"study_timetable_{file_slug}.ics",
            mime="text/calendar",
            use_container_width=True,
            help="Import directly into Google Calendar or Outlook!"
        )
    with dl_col4:
        csv_str = StudyPlanExporter.to_csv(plan)
        st.download_button(
            "📄 CSV Sheet",
            data=csv_str,
            file_name=f"study_timetable_{file_slug}.csv",
            mime="text/csv",
            use_container_width=True
        )
    with dl_col5:
        json_str = StudyPlanExporter.to_json(plan)
        st.download_button(
            "📦 JSON Data",
            data=json_str,
            file_name=f"study_timetable_{file_slug}.json",
            mime="application/json",
            use_container_width=True
        )

    # Embedded Aesthetic Pastel Canva Timetable
    st.markdown("### 📅 Study Timetable")
    components.html(canva_html, height=850, scrolling=True)


# ============================================================================
# POMODORO TECHNIQUE & FOCUS COMPANION (100% REAL-TIME COUNTDOWN TIMER)
# ============================================================================
st.markdown("---")
st.markdown("### ⏱️ Pomodoro Study Technique & Focus Companion")
st.markdown(
    "The **Pomodoro Technique** breaks study intervals into 25-minute high-intensity focus sprints separated by "
    "5-minute recovery intervals. This preserves cognitive stamina and aligns with our timetable's fatigue limits."
)

pomodoro_html = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; }
        body { background: transparent; padding: 10px 4px; }
        .pomo-card {
            background: linear-gradient(135deg, #1E1B4B 0%, #2E1065 50%, #3B0764 100%);
            border: 1.5px solid rgba(168, 85, 247, 0.4);
            border-radius: 20px;
            padding: 26px 20px;
            color: white;
            text-align: center;
            box-shadow: 0 15px 35px rgba(0, 0, 0, 0.35);
            max-width: 600px;
            margin: 0 auto;
        }
        .mode-row {
            display: flex;
            justify-content: center;
            gap: 10px;
            margin-bottom: 18px;
            flex-wrap: wrap;
        }
        .mode-btn {
            background: rgba(255, 255, 255, 0.08);
            color: #E9D5FF;
            border: 1px solid rgba(255, 255, 255, 0.15);
            padding: 8px 18px;
            border-radius: 9999px;
            font-size: 0.9rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s ease;
        }
        .mode-btn:hover { background: rgba(255, 255, 255, 0.15); color: #FFFFFF; }
        .mode-btn.active {
            background: #7C3AED;
            color: #FFFFFF;
            border-color: #A855F7;
            box-shadow: 0 0 15px rgba(124, 58, 237, 0.5);
        }
        .timer-display {
            font-size: 4.5rem;
            font-weight: 800;
            font-family: 'Courier New', Courier, monospace;
            color: #FFFFFF;
            letter-spacing: 3px;
            text-shadow: 0 0 25px rgba(168, 85, 247, 0.6);
            margin: 8px 0;
            user-select: none;
        }
        .progress-bar-bg {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 9999px;
            height: 8px;
            width: 80%;
            margin: 0 auto 16px auto;
            overflow: hidden;
        }
        .progress-bar-fill {
            background: linear-gradient(90deg, #A855F7, #EC4899);
            height: 100%;
            width: 100%;
            transition: width 0.9s linear;
        }
        .status-text {
            color: #DDD6FE;
            font-size: 0.95rem;
            margin-bottom: 20px;
            min-height: 24px;
        }
        .ctrl-row {
            display: flex;
            justify-content: center;
            gap: 14px;
        }
        .btn-ctrl {
            border: none;
            padding: 11px 28px;
            border-radius: 12px;
            font-size: 1rem;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.2s ease;
        }
        .btn-start {
            background: #10B981;
            color: white;
            box-shadow: 0 4px 14px rgba(16, 185, 129, 0.4);
        }
        .btn-start:hover { background: #059669; }
        .btn-pause {
            background: #EF4444;
            color: white;
            box-shadow: 0 4px 14px rgba(239, 68, 68, 0.4);
        }
        .btn-pause:hover { background: #DC2626; }
        .btn-reset {
            background: rgba(255, 255, 255, 0.12);
            color: #E2E8F0;
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        .btn-reset:hover { background: rgba(255, 255, 255, 0.2); color: white; }
    </style>
</head>
<body>
    <div class="pomo-card">
        <div class="mode-row">
            <button id="btn-mode-work" class="mode-btn active" onclick="setTimerMode(25, 'work')">🍅 25m Focus</button>
            <button id="btn-mode-short" class="mode-btn" onclick="setTimerMode(5, 'short')">☕ 5m Short Break</button>
            <button id="btn-mode-long" class="mode-btn" onclick="setTimerMode(15, 'long')">🌿 15m Long Break</button>
        </div>
        <div id="display" class="timer-display">25:00</div>
        <div class="progress-bar-bg">
            <div id="progress" class="progress-bar-fill"></div>
        </div>
        <div id="status" class="status-text">🎯 Ready to dive in! 25 minutes of deep focus.</div>
        <div class="ctrl-row">
            <button id="btn-toggle" class="btn-ctrl btn-start" onclick="toggleTimer()">▶️ Start</button>
            <button class="btn-ctrl btn-reset" onclick="resetTimer()">🔄 Reset</button>
        </div>
    </div>

    <script>
        let totalSeconds = 25 * 60;
        let remainingSeconds = totalSeconds;
        let timerId = null;
        let isRunning = false;
        let activeMode = 'work';

        function updateDisplay() {
            const m = Math.floor(remainingSeconds / 60);
            const s = remainingSeconds % 60;
            document.getElementById('display').textContent = 
                `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
            const pct = (remainingSeconds / totalSeconds) * 100;
            document.getElementById('progress').style.width = pct + '%';
        }

        function setTimerMode(mins, mode) {
            if (isRunning) toggleTimer();
            activeMode = mode;
            totalSeconds = mins * 60;
            remainingSeconds = totalSeconds;

            document.querySelectorAll('.mode-btn').forEach(b => b.classList.remove('active'));
            document.getElementById('btn-mode-' + mode).classList.add('active');

            const statusEl = document.getElementById('status');
            if (mode === 'work') {
                statusEl.textContent = '🎯 Ready to dive in! 25 minutes of deep focus.';
            } else if (mode === 'short') {
                statusEl.textContent = '☕ Short Break! Rest your eyes, take 5 deep breaths, and hydrate.';
            } else {
                statusEl.textContent = '🌿 Long Break! Walk around, stretch, and let your brain consolidate knowledge.';
            }
            updateDisplay();
        }

        function playChime() {
            try {
                const ctx = new (window.AudioContext || window.webkitAudioContext)();
                [523.25, 659.25, 783.99, 1046.50].forEach((freq, idx) => {
                    const osc = ctx.createOscillator();
                    const gain = ctx.createGain();
                    osc.frequency.value = freq;
                    osc.type = 'sine';
                    gain.gain.setValueAtTime(0.2, ctx.currentTime + idx * 0.15);
                    gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + idx * 0.15 + 0.4);
                    osc.connect(gain);
                    gain.connect(ctx.destination);
                    osc.start(ctx.currentTime + idx * 0.15);
                    osc.stop(ctx.currentTime + idx * 0.15 + 0.4);
                });
            } catch(e) {}
        }

        function toggleTimer() {
            const btn = document.getElementById('btn-toggle');
            if (!isRunning) {
                isRunning = true;
                btn.textContent = '⏸️ Pause';
                btn.className = 'btn-ctrl btn-pause';
                timerId = setInterval(() => {
                    if (remainingSeconds > 0) {
                        remainingSeconds--;
                        updateDisplay();
                    } else {
                        clearInterval(timerId);
                        isRunning = false;
                        btn.textContent = '▶️ Start';
                        btn.className = 'btn-ctrl btn-start';
                        playChime();
                        document.getElementById('status').textContent = '🎉 Sprint Complete! Awesome job. Time to recharge!';
                    }
                }, 1000);
            } else {
                clearInterval(timerId);
                isRunning = false;
                btn.textContent = '▶️ Start';
                btn.className = 'btn-ctrl btn-start';
            }
        }

        function resetTimer() {
            if (isRunning) toggleTimer();
            remainingSeconds = totalSeconds;
            updateDisplay();
        }

        updateDisplay();
    </script>
</body>
</html>
"""
components.html(pomodoro_html, height=320)


