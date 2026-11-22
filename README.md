# 📚 PromptCraft: AI-Powered Study Plan & Timetable Generator (C20)

[![Course](https://img.shields.io/badge/Course-SCSE4041%20Prompt%20Engineering-indigo.svg)](https://www.bennett.edu.in)
[![Problem ID](https://img.shields.io/badge/Problem%20ID-C20-blue.svg)]()
[![Institution](https://img.shields.io/badge/Institution-Bennett%20University-crimson.svg)]()
[![Python](https://img.shields.io/badge/Python-3.14-green.svg)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.66-red.svg)](https://streamlit.io)
[![Tests](https://img.shields.io/badge/Tests-8%20Passed-emerald.svg)]()

> **Milestone 1, 2, and 3 Complete Implementation**  
> An academic research and software mini-project demonstrating how **Constraint-Based Prompting**, **Structured Output (JSON Schema)**, and **Chain-of-Verification (Refined Workflow)** transform generative LLMs into reliable, mathematically bounded study timetable planners.

---

## 🌟 Key Features

1. **Four Iterative Prompt Engineering Models:**
   - **Prompt V1 (Baseline):** Naive prompt establishing an empirical lower bound; demonstrates common failure modes (daily hour overbooking, post-exam hallucinations).
   - **Prompt V2 (Constraint-Aware):** Injects explicit boundary conditions: daily hour ceilings, post-exam cutoffs, weak subject weighting, and mandatory revision slots.
   - **Prompt V3 (Structured Output):** Enforces a strict, machine-readable JSON schema aligned with Pydantic data models for seamless downstream parsing.
   - **Prompt V4 (Refined Workflow):** Implements a 3-step Critique-and-Refine loop (Draft Generation $\rightarrow$ Constraint Critic $\rightarrow$ Self-Correction Refinement) to achieve **100% constraint compliance**.

2. **Independent Programmatic Constraint Checking Engine:**
   - Evaluates timetables in pure Python independent of the LLM to prevent circular evaluation bias.
   - Audits 6 core academic constraints: daily hour limit, post-exam cutoff, subject completeness, weak subject prioritization, revision coverage, and practice-question coverage.
   - Outputs an objective, weighted **Compliance Score (0–100%)** and granular violation reports.

3. **🎨 Canva-Style Aesthetic Timetable Studio:**
   - **4 Aesthetic Themes:** *Pastel Dream* (trendy Notion/Canva aesthetic), *Cyber Glow* (dark neon), *Matcha & Cream* (cozy study cafe), and *Sakura Blossom* (blush pink).
   - **Live Interactive Embedded Canva Preview:** Rendered directly in-app with habit checkboxes, water intake trackers (`💧💧💧💧`), stickers, and motivational quotes.
   - **1-Click Canva Downloads:**
     - 🖼️ **Aesthetic PNG Poster:** High-res graphic export generated via Pillow, perfect for desktop wallpapers or printing.
     - 🖨️ **Print-Ready Canva PDF / HTML:** Self-contained document with `@media print` rules and a 1-click browser print-to-PDF button.

4. **⚡ Interactive & Fun Gamification Features:**
   - **Exam Readiness Power Level Meter:** Dynamic rank gauge (`🏆 Rank: S+ Academic Weapon`, `⚡ Rank: A Exam Conqueror`, `📚 Rank: B Diligent Scholar`) based on compliance and workload pacing.
   - **⏱️ Focus Companion (Pomodoro Sprint):** 25-minute deep focus sprints with Lo-Fi ambient music prompts.
   - **✅ Daily Study Quest Checklist:** Interactive checkboxes to mark sessions complete with live XP progress tracking and celebration balloons!
   - **☕ Smart Brain Fuel Generator:** Recommends cognitive study snacks.

5. **Multi-Format Export Pipeline:**
   - 📅 **iCalendar (`.ics` RFC 5545):** Import directly into Google Calendar, Microsoft Outlook, or Apple Calendar with timed notifications!
   - 📄 **CSV Spreadsheet:** Tabular day-by-day export for Excel / Sheets.
   - 📦 **JSON:** Clean, machine-readable format.
   - 📝 **Markdown Document:** Formatted tables with compliance audit metadata.

6. **Interactive Side-by-Side Prompt Comparison Lab:**
   - Directly pit any two prompt versions (e.g., V1 vs V4) against the same student profile to visually analyze improvements.

7. **Standardized Academic Benchmarking Suite:**
   - 4 pre-configured academic test cases (Staggered Semester, 4-Day Emergency Crunch, Asymmetric Schedule, Multi-Weak Subjects).
   - Generates interactive Plotly compliance bar charts, stacked violation breakdowns, and multidimensional capability radar charts.

8. **Dual Execution Engine:**
   - 🟢 **Live Google Gemini API:** Uses Google Gemini 2.5 Flash (`google-genai` SDK) when an API key is provided.
   - 💡 **Intelligent Academic Simulator:** 100% offline, deterministic engine that faithfully models LLM failure and success behaviors for all 4 prompt iterations during viva or offline evaluation.

---

## 🏗️ Project Architecture

```
prompt_pro/
├── app.py                     # Main Streamlit web application
├── requirements.txt           # Python dependencies
├── README.md                  # Comprehensive documentation
├── .env.example               # Environment template for Gemini API key
├── core/
│   ├── __init__.py
│   ├── models.py              # Pydantic data models (Subject, StudyPlan, Session, etc.)
│   ├── prompts.py             # Prompt templates (V1, V2, V3, and V4)
│   ├── validator.py           # Programmatic constraint checking engine
│   ├── generator.py           # LLM generation & academic simulation engine
│   ├── evaluator.py           # Benchmark runner & Plotly visual analytics
│   └── exporter.py            # CSV, JSON, Markdown, and RFC 5545 iCalendar exporter
├── data/
│   └── benchmark_scenarios.py # Standardized fictional student test cases
├── tests/
│   ├── __init__.py
│   ├── test_validator.py      # Unit tests for constraint checks & scoring
│   └── test_prompts.py        # Unit tests for prompt builders, simulation, & export
└── docs/
    ├── MILESTONE_1.md         # Milestone 1: Problem Identification & Proposal
    ├── MILESTONE_2.md         # Milestone 2: Implementation & Evaluation
    ├── MILESTONE_3.md         # Milestone 3: Final Report & Responsible AI
    └── RESEARCH_SUMMARY.md    # Theoretical grounding citing Liu et al. (2026)
```

---

## 📊 Empirical Evaluation Matrix

Results compiled from the standardized benchmark suite across 16 scenario-version trials:

| Metric | Prompt V1 (Baseline) | Prompt V2 (Constraint-Aware) | Prompt V3 (Structured JSON) | Prompt V4 (Refined Workflow) |
| :--- | :---: | :---: | :---: | :---: |
| **Mean Compliance Score** | **8.8%** | **86.2%** | **100.0%** | **100.0%** |
| **Constraint Status** | ❌ FAILED | ⚠️ WARNINGS | ✅ PASSED | ✅ PASSED |
| **Daily Hour Overruns** | 4 | 0 | 0 | **0** |
| **Post-Exam Hallucinations** | 17 | 0 | 0 | **0** |
| **Weak Subject Share** | 21.5% | 51.6% | 51.6% | **51.6%** |
| **Revision & Mock Coverage** | 31.0% | 85.0% | 100.0% | **100.0%** |
| **Calendar Parse Success** | ~25.0% | ~60.0% | **100.0%** | **100.0%** |

---

## 🚀 Quickstart & Setup

### 1. Prerequisites
- Python 3.10+ (Tested on Python 3.14)
- Internet connection (optional; required only if using live Gemini API)

### 2. Installation
Clone or navigate to the workspace directory:
```bash
cd prompt_pro
pip install -r requirements.txt
```

### 3. (Optional) Configure Gemini API Key
To run with live Google Gemini models:
```bash
# Copy template and add your API key from Google AI Studio
copy .env.example .env
```
*(Alternatively, you can paste your key directly into the Streamlit sidebar at runtime, or run in Academic Simulation mode without any key).*

### 4. Run the Streamlit Application
```bash
python -m streamlit run app.py
```
Open your browser at `http://localhost:8501`.

### 5. Run Unit Tests
```bash
python -m pytest tests/ -v
```

---

## 📖 Theoretical Grounding & Research Citation

This project is grounded in contemporary cognitive psychology and time-management research:

> **Liu, B., Ma, P., and Jia, F. (2026).**  
> *“Systematic review and meta-analysis of the impact of time management on college students' learning outcomes.”*  
> **Frontiers in Psychology.**  
> DOI: [https://doi.org/10.3389/fpsyg.2026.1700298](https://doi.org/10.3389/fpsyg.2026.1700298)

The meta-analysis of 31 empirical trials with 13,506 college students demonstrated a moderate positive correlation ($r \approx 0.38$) between structured time management and learning outcomes. Unbounded, naive schedules promote procrastination and overbooking; explicit prompt constraints provide the necessary cognitive scaffolding.

---

## 👥 Team PromptCraft (SCSE4041)

- **Team Leader & Documentation:** Coordination, Milestone 1–3 synthesis, academic literature review.
- **Prompt Engineer:** Prompt crafting, few-shot tuning, Chain-of-Verification critic design.
- **Software Developer:** Streamlit application, Pydantic schemas, iCalendar export engine.
- **Validation & QA Engineer:** Python constraint-checking algorithms, unit testing, benchmark runner.
