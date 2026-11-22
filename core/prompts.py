"""
Prompt Engineering Templates for the C20 Study Plan Generator.
Contains Prompt V1 (Baseline), V2 (Constraint-Aware), V3 (Structured), and V4 (Refined Workflow).
"""

import json
from typing import Dict, Any, List
from core.models import StudentProfile


# ============================================================================
# PROMPT V1: BASELINE (NAIVE PROMPT)
# ============================================================================
def build_v1_baseline_prompt(profile: StudentProfile) -> Dict[str, str]:
    """
    Prompt V1 — Baseline Prompt:
    Basic instructions, subjects, and exam dates without explicit constraints or schema.
    Used as an empirical baseline to show common LLM failures (hallucination, overbooking).
    """
    subject_lines = "\n".join(
        [f"- {s.name}: Exam on {s.exam_date}" for s in profile.subjects]
    )

    system_instruction = (
        "You are an academic assistant. Help students prepare for their exams."
    )

    user_content = f"""Please make me a study timetable for my upcoming exams.

Subjects and Exam Dates:
{subject_lines}

I can study about {profile.available_hours_per_day} hours a day.
My timetable should start on {profile.start_date}.

Please generate a day-wise study plan in a table.
"""
    return {
        "version": "V1_Baseline",
        "name": "Prompt V1 — Baseline Prompt",
        "description": "Naive prompt with minimal instructions, no formal constraints, no output schema.",
        "system_instruction": system_instruction,
        "user_prompt": user_content,
        "expected_format": "Unstructured text or generic markdown table",
    }


# ============================================================================
# PROMPT V2: CONSTRAINT-AWARE PROMPT
# ============================================================================
def build_v2_constraint_prompt(profile: StudentProfile) -> Dict[str, str]:
    """
    Prompt V2 — Constraint-Aware Prompt:
    Injects explicit boundary rules: daily study-hour ceiling, post-exam cutoffs,
    weak subject boosting, and mandatory revision/practice slots.
    """
    subject_details = []
    for s in profile.subjects:
        weak_tag = " (WEAK SUBJECT - Needs priority!)" if s.is_weak else ""
        topics_str = f" [Key Topics: {', '.join(s.topics)}]" if s.topics else ""
        subject_details.append(
            f"- {s.name}: Exam Date = {s.exam_date}, Priority = {s.priority}{weak_tag}{topics_str}"
        )
    subject_block = "\n".join(subject_details)

    weak_list_str = ", ".join(profile.weak_subjects) if profile.weak_subjects else "None"

    system_instruction = (
        "You are an expert academic scheduler and study optimization AI. "
        "Your highest priority is to generate a feasible, strictly bounded study plan "
        "that follows all academic and temporal constraints without exception."
    )

    user_content = f"""Generate a personalized day-wise study timetable for exam preparation.

STUDENT PROFILE & CONSTRAINTS:
1. Start Date: {profile.start_date}
2. Subjects & Examination Dates:
{subject_block}
3. Weak Subjects requiring extra time and foundational drills: {weak_list_str}
4. Hard Daily Limit: Maximum {profile.available_hours_per_day} study hours per day.
5. Preferred Study Session Duration: {profile.preferred_session_hours} hours per session.
6. Daily Start Time: {profile.daily_start_time}

MANDATORY SCHEDULING CONSTRAINTS (DO NOT VIOLATE):
- CONSTRAINT 1 (DAILY HOUR LIMIT): The sum of study hours on any single calendar day MUST NOT EXCEED {profile.available_hours_per_day} hours.
- CONSTRAINT 2 (POST-EXAM CUTOFF): NEVER schedule study for a subject on or after its examination date. All preparation for a subject must conclude BEFORE the exam day.
- CONSTRAINT 3 (WEAK SUBJECT FOCUS): Allocate at least 30-50% more cumulative hours and frequent review sessions to weak subjects ({weak_list_str}).
- CONSTRAINT 4 (REVISION & PRACTICE): Every subject must have at least one dedicated 'Revision' session and one 'Practice Questions / Mock' session before its exam date.
- CONSTRAINT 5 (EXAM PROXIMITY): Prioritize subjects whose examination dates occur earlier.

Format your output as a comprehensive day-by-day timetable table with columns:
Day | Date | Time Slot | Subject | Session Type | Specific Topic | Learning Objective
Include a summary of total hours allocated per subject at the end.
"""
    return {
        "version": "V2_Constraint_Aware",
        "name": "Prompt V2 — Constraint-Aware Prompt",
        "description": "Specifies negative constraints (no post-exam study, strict daily ceiling), weak subject weighting, and revision requirements.",
        "system_instruction": system_instruction,
        "user_prompt": user_content,
        "expected_format": "Markdown table with constraint adherence",
    }


# ============================================================================
# PROMPT V3: STRUCTURED OUTPUT PROMPT (STRICT JSON SCHEMA)
# ============================================================================
def build_v3_structured_prompt(profile: StudentProfile) -> Dict[str, str]:
    """
    Prompt V3 — Structured Output Prompt:
    Enforces a strict, machine-readable JSON format matching the StudyPlan schema,
    incorporating all constraints, typing instructions, and few-shot formatting.
    """
    subject_details = []
    for s in profile.subjects:
        weak_tag = " [WEAK SUBJECT]" if s.is_weak else ""
        topics_str = f" (Topics: {', '.join(s.topics)})" if s.topics else ""
        subject_details.append(
            f"- {s.name}: Exam on {s.exam_date}, Priority={s.priority}{weak_tag}{topics_str}"
        )
    subject_block = "\n".join(subject_details)

    weak_list_str = ", ".join(profile.weak_subjects) if profile.weak_subjects else "None"

    json_schema_desc = """{
  "plan_id": "PLAN-<unique-id>",
  "student_name": "Student Name",
  "prompt_version": "V3_Structured",
  "days": [
    {
      "date": "YYYY-MM-DD",
      "day_number": 1,
      "total_hours": 3.0,
      "notes": "Focus on high-priority foundational units",
      "sessions": [
        {
          "date": "YYYY-MM-DD",
          "day_number": 1,
          "start_time": "09:00",
          "end_time": "10:30",
          "duration_hours": 1.5,
          "subject": "Subject Name",
          "session_type": "Concept Learning | Deep Study | Revision | Practice Questions | Mock Test | Formula / Summary Review",
          "topic": "Specific Topic Name",
          "learning_objective": "Master key algorithms and solve 5 practice problems",
          "is_weak_subject": true
        }
      ]
    }
  ],
  "subject_hour_summary": {
    "Subject 1": 12.0,
    "Subject 2": 8.0
  },
  "total_study_hours": 20.0
}"""

    system_instruction = (
        "You are an AI study planning engine that outputs ONLY valid, parseable JSON conforming "
        "exactly to the specified schema. Do not include markdown code block backticks (like ```json), "
        "commentary, or preamble. Return raw JSON only."
    )

    user_content = f"""Generate a personalized day-wise study plan in STRICT JSON FORMAT.

STUDENT PROFILE:
- Student: {profile.student_name}
- Start Date: {profile.start_date}
- Daily Study Budget (HARD CAP): Maximum {profile.available_hours_per_day} hours/day.
- Daily Start Time: {profile.daily_start_time}
- Preferred Session Length: {profile.preferred_session_hours} hours.
- Weak Subjects: {weak_list_str}
- Subjects & Exam Dates:
{subject_block}

HARD SCHEDULING CONSTRAINTS:
1. DAILY HOUR CEILING: In every day object, sum of sessions' `duration_hours` MUST NOT exceed {profile.available_hours_per_day}.
2. POST-EXAM PROHIBITION: For each subject, NO session may be scheduled on or after its exam date.
3. WEAK SUBJECT BOOST: Allocate extra sessions and practice tests to weak subjects ({weak_list_str}).
4. BALANCED PEDAGOGY: Include a healthy mix of 'Concept Learning', 'Revision', and 'Practice Questions'.
5. CHRONOLOGICAL ORDER: Days must be sorted sequentially from start date onwards.

SCHEMA REQUIREMENT:
Your response must be a single valid JSON object with the following structure:
{json_schema_desc}

Output raw JSON only.
"""
    return {
        "version": "V3_Structured",
        "name": "Prompt V3 — Structured Output Prompt",
        "description": "Combines constraint-based prompting with strict JSON schema definition for seamless downstream integration.",
        "system_instruction": system_instruction,
        "user_prompt": user_content,
        "expected_format": "Strict Raw JSON adhering to StudyPlan schema",
    }


# ============================================================================
# PROMPT V4: REFINED WORKFLOW (CRITIQUE-AND-REFINE / CHAIN-OF-VERIFICATION)
# ============================================================================
def build_v4_critic_prompt(draft_json_str: str, profile: StudentProfile) -> Dict[str, str]:
    """
    Prompt V4 - Phase 2: Verification Critic Prompt.
    Audits the generated draft against constraints and flags specific violations.
    """
    system_instruction = (
        "You are an expert Academic Schedule Auditor and Constraint Checker. "
        "Your task is to ruthlessly inspect a study plan draft for logical, temporal, and constraint violations."
    )

    user_content = f"""Inspect the following proposed study timetable against these 5 strict academic constraints:

STUDENT PROFILE CONSTRAINTS:
- Maximum daily study hours: {profile.available_hours_per_day} hours/day
- Start date: {profile.start_date}
- Subject exam dates: {json.dumps({s.name: s.exam_date for s in profile.subjects}, indent=2)}
- Weak subjects: {json.dumps(profile.weak_subjects)}

PROPOSED TIMETABLE DRAFT:
{draft_json_str}

AUDIT CHECKLIST:
1. Daily Hours Check: Did any day exceed {profile.available_hours_per_day} hours? List exact dates.
2. Post-Exam Study Check: Was any subject scheduled on or after its exam date? List subject and dates.
3. Completeness Check: Were any subjects omitted or left with 0 sessions?
4. Weak Subject Check: Did weak subjects receive adequate prioritized focus?
5. Revision Coverage: Did every subject have dedicated revision and practice sessions prior to exam?

OUTPUT FORMAT:
Return a JSON object:
{{
  "has_violations": true/false,
  "violation_count": int,
  "violations_list": [
    {{
      "rule": "RULE_NAME",
      "date": "YYYY-MM-DD or null",
      "subject": "Subject or null",
      "description": "Specific issue description",
      "required_fix": "Exact instruction to resolve"
    }}
  ],
  "audit_verdict": "APPROVED or NEEDS_REVISION"
}}
"""
    return {
        "version": "V4_Critic",
        "name": "Prompt V4 (Step 2) — Constraint Verification Critic",
        "description": "Chain-of-Verification prompt that audits the draft plan against all 5 academic constraints.",
        "system_instruction": system_instruction,
        "user_prompt": user_content,
        "expected_format": "JSON audit report of detected violations",
    }


def build_v4_refinement_prompt(
    draft_json_str: str, critic_feedback: str, profile: StudentProfile
) -> Dict[str, str]:
    """
    Prompt V4 - Phase 3: Self-Correction Refinement Prompt.
    Directs the LLM to patch the detected violations and produce a finalized, compliant plan.
    """
    system_instruction = (
        "You are an AI study plan optimizer. Revise and self-correct the study timetable draft "
        "to resolve 100% of the auditor's detected violations while preserving valid allocations. "
        "Return ONLY the corrected, valid JSON study plan."
    )

    user_content = f"""Here is the study timetable draft and the constraint auditor's findings:

AUDITOR'S DETECTED VIOLATIONS & CRITIQUE:
{critic_feedback}

STUDENT CONSTRAINTS:
- Hard daily limit: {profile.available_hours_per_day} hours
- Subject exam dates: {json.dumps({s.name: s.exam_date for s in profile.subjects})}
- Weak subjects: {json.dumps(profile.weak_subjects)}

ORIGINAL DRAFT TIMETABLE:
{draft_json_str}

REVISION INSTRUCTIONS:
1. Fix every violation identified by the auditor.
2. If daily hours exceeded {profile.available_hours_per_day}h on any day, reduce or redistribute sessions to stay strictly under the limit.
3. If any subject was scheduled on or after its exam date, completely eliminate or move those sessions BEFORE the exam.
4. Ensure every subject has at least 1 revision and 1 practice session before its exam date.
5. Return the finalized, fully compliant study plan conforming to the standard JSON schema.

Output raw JSON only.
"""
    return {
        "version": "V4_Refined_Workflow",
        "name": "Prompt V4 (Step 3) — Self-Correction Revision Prompt",
        "description": "Revises the draft plan using feedback from the constraint verification critic to achieve 100% compliance.",
        "system_instruction": system_instruction,
        "user_prompt": user_content,
        "expected_format": "Strict Raw JSON adhering to StudyPlan schema",
    }
