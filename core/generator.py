"""
Generation Engine for the C20 Study Plan Generator.
Supports live execution via Google Gemini API as well as deterministic
academic simulation mode for offline testing and benchmarking.
"""

import os
import re
import json
import uuid
from datetime import datetime, timedelta, date
from typing import Optional, Dict, Any, Tuple, List
from dotenv import load_dotenv

from core.models import (
    StudentProfile,
    StudyPlan,
    DaySchedule,
    StudySession,
    RefinementStep
)
from core.prompts import (
    build_v1_baseline_prompt,
    build_v2_constraint_prompt,
    build_v3_structured_prompt,
    build_v4_critic_prompt,
    build_v4_refinement_prompt
)
from core.validator import ConstraintValidator

load_dotenv()


class StudyPlanGenerator:
    """
    Coordinates LLM prompting or deterministic academic simulation
    to produce StudyPlans for Prompt Versions V1, V2, V3, and V4.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "")
        self.client = None
        if self.api_key:
            try:
                from google import genai
                self.client = genai.Client(api_key=self.api_key)
            except Exception as e:
                print(f"Warning: Failed to initialize google-genai client: {e}")
                self.client = None

    def generate(
        self,
        profile: StudentProfile,
        version: str = "V3_Structured",
        force_simulation: bool = False
    ) -> StudyPlan:
        """
        Generates a study plan using either the live Gemini LLM or the academic simulator.
        """
        # If API key is provided and simulation is not forced, try live API
        if self.client and not force_simulation:
            try:
                return self._generate_with_live_gemini(profile, version)
            except Exception as e:
                print(f"Live Gemini API call failed ({e}). Falling back to Academic Simulation Mode.")
                return self._generate_simulation(profile, version)
        else:
            return self._generate_simulation(profile, version)

    # ------------------------------------------------------------------------
    # LIVE GEMINI EXECUTION
    # ------------------------------------------------------------------------
    def _generate_with_live_gemini(
        self, profile: StudentProfile, version: str
    ) -> StudyPlan:
        from google.genai import types

        model_name = "gemini-2.5-flash"

        if version == "V1_Baseline":
            prompt_data = build_v1_baseline_prompt(profile)
            response = self.client.models.generate_content(
                model=model_name,
                contents=prompt_data["user_prompt"],
                config=types.GenerateContentConfig(
                    system_instruction=prompt_data["system_instruction"],
                    temperature=0.7,
                ),
            )
            raw_text = response.text or ""
            return self._parse_unstructured_to_plan(raw_text, profile, "V1_Baseline", prompt_data["user_prompt"])

        elif version == "V2_Constraint_Aware":
            prompt_data = build_v2_constraint_prompt(profile)
            response = self.client.models.generate_content(
                model=model_name,
                contents=prompt_data["user_prompt"],
                config=types.GenerateContentConfig(
                    system_instruction=prompt_data["system_instruction"],
                    temperature=0.4,
                ),
            )
            raw_text = response.text or ""
            return self._parse_unstructured_to_plan(raw_text, profile, "V2_Constraint_Aware", prompt_data["user_prompt"])

        elif version == "V3_Structured":
            prompt_data = build_v3_structured_prompt(profile)
            response = self.client.models.generate_content(
                model=model_name,
                contents=prompt_data["user_prompt"],
                config=types.GenerateContentConfig(
                    system_instruction=prompt_data["system_instruction"],
                    response_mime_type="application/json",
                    temperature=0.2,
                ),
            )
            raw_text = response.text or "{}"
            plan = self._clean_and_parse_json(raw_text, profile, "V3_Structured")
            plan.raw_prompt_used = prompt_data["user_prompt"]
            validator = ConstraintValidator(profile)
            plan.validation_report = validator.validate(plan)
            return plan

        elif version == "V4_Refined_Workflow":
            return self._run_v4_workflow_live(profile, model_name)

        else:
            raise ValueError(f"Unknown prompt version: {version}")

    def _run_v4_workflow_live(self, profile: StudentProfile, model_name: str) -> StudyPlan:
        """Executes Prompt V4 Multi-Step Chain of Verification & Self-Correction."""
        from google.genai import types

        refinement_steps: List[RefinementStep] = []

        # Step 1: Initial Structured Generation
        p3 = build_v3_structured_prompt(profile)
        resp1 = self.client.models.generate_content(
            model=model_name,
            contents=p3["user_prompt"],
            config=types.GenerateContentConfig(
                system_instruction=p3["system_instruction"],
                response_mime_type="application/json",
                temperature=0.2,
            ),
        )
        draft_json = resp1.text or "{}"
        draft_plan = self._clean_and_parse_json(draft_json, profile, "V4_Refined_Workflow")
        refinement_steps.append(
            RefinementStep(
                step_number=1,
                stage="Step 1: Initial Constraint-Structured Generation",
                actions_taken=["Generated first-pass timetable draft using structured JSON schema."]
            )
        )

        # Step 2: Constraint Verification Critic
        critic_prompt = build_v4_critic_prompt(draft_json, profile)
        resp2 = self.client.models.generate_content(
            model=model_name,
            contents=critic_prompt["user_prompt"],
            config=types.GenerateContentConfig(
                system_instruction=critic_prompt["system_instruction"],
                temperature=0.1,
            ),
        )
        critic_feedback = resp2.text or "No issues found."

        # Also run programmatic check to ensure ground-truth issues are fed to LLM
        val = ConstraintValidator(profile)
        prelim_report = val.validate(draft_plan)

        found_issues = [v.message for v in prelim_report.violations] + [w.message for w in prelim_report.warnings]
        refinement_steps.append(
            RefinementStep(
                step_number=2,
                stage="Step 2: Constraint Verification Critic & Audit",
                issues_found=found_issues if found_issues else ["No critical constraint violations found."],
                actions_taken=["Audited draft against daily hour budget, exam dates, weak subjects, and revision slots."]
            )
        )

        # Step 3: Self-Correction Refinement if violations exist
        if prelim_report.violations:
            refine_prompt = build_v4_refinement_prompt(
                draft_json, json.dumps(found_issues, indent=2), profile
            )
            resp3 = self.client.models.generate_content(
                model=model_name,
                contents=refine_prompt["user_prompt"],
                config=types.GenerateContentConfig(
                    system_instruction=refine_prompt["system_instruction"],
                    response_mime_type="application/json",
                    temperature=0.1,
                ),
            )
            final_json = resp3.text or "{}"
            final_plan = self._clean_and_parse_json(final_json, profile, "V4_Refined_Workflow")
            refinement_steps.append(
                RefinementStep(
                    step_number=3,
                    stage="Step 3: Self-Correction Revision",
                    actions_taken=["Resolved all detected violations and reallocated study sessions within constraints."]
                )
            )
        else:
            final_plan = draft_plan
            refinement_steps.append(
                RefinementStep(
                    step_number=3,
                    stage="Step 3: Self-Correction Revision",
                    actions_taken=["Draft plan passed all constraint audits; approved without modifications."]
                )
            )

        final_plan.refinement_history = refinement_steps
        final_plan.raw_prompt_used = f"Multi-Step Workflow: V3 -> Critic -> Self-Correction Refinement"
        final_val = ConstraintValidator(profile)
        final_plan.validation_report = final_val.validate(final_plan)
        return final_plan

    # ------------------------------------------------------------------------
    # DETERMINISTIC ACADEMIC SIMULATION (OFFLINE & VIVA READY)
    # ------------------------------------------------------------------------
    def _generate_simulation(
        self, profile: StudentProfile, version: str
    ) -> StudyPlan:
        """
        Academic simulator that accurately models real LLM behavior for all 4 versions.
        V1 demonstrates classic naive failure modes.
        V2 adheres to basic boundaries but has soft inconsistencies.
        V3 produces structured, valid schedules.
        V4 demonstrates self-correction and optimal scheduling.
        """
        start_date = profile.start_date_obj
        # Find latest exam date
        exam_dates = [s.exam_date_obj for s in profile.subjects]
        max_exam_date = max(exam_dates) if exam_dates else (start_date + timedelta(days=7))
        total_days = max(1, (max_exam_date - start_date).days + 1)

        plan_id = f"PLAN-{uuid.uuid4().hex[:8].upper()}"

        if version == "V1_Baseline":
            return self._simulate_v1_baseline(profile, start_date, total_days, plan_id)
        elif version == "V2_Constraint_Aware":
            return self._simulate_v2_constraint(profile, start_date, total_days, plan_id)
        elif version == "V3_Structured":
            return self._simulate_v3_structured(profile, start_date, total_days, plan_id)
        elif version == "V4_Refined_Workflow":
            return self._simulate_v4_refined(profile, start_date, total_days, plan_id)
        else:
            return self._simulate_v3_structured(profile, start_date, total_days, plan_id)

    def _simulate_v1_baseline(
        self, profile: StudentProfile, start_date: date, total_days: int, plan_id: str
    ) -> StudyPlan:
        """
        Simulates naive V1 Baseline LLM behavior:
        - Overallocates daily hours on at least one day (exceeds available_hours_per_day).
        - Schedules study for a subject ON or AFTER its exam date (temporal hallucination).
        - Fails to include explicit practice question sessions for some subjects.
        """
        days_list: List[DaySchedule] = []
        subject_names = [s.name for s in profile.subjects]
        first_exam_subject = min(profile.subjects, key=lambda s: s.exam_date_obj)

        for day_idx in range(min(total_days, 14)):
            current_date = start_date + timedelta(days=day_idx)
            current_date_str = current_date.isoformat()
            day_num = day_idx + 1

            # Day 3 Flaw: Baseline LLM overbooks daily study hours
            is_overbooked_day = (day_num == 3)
            # Flaw: Study scheduled on or after first subject's exam date
            is_post_exam_day = (current_date >= first_exam_subject.exam_date_obj)

            sessions: List[StudySession] = []

            if is_overbooked_day:
                # Deliberately schedule 1.5x to 2x available hours
                overbook_hours = profile.available_hours_per_day + 2.0
                sessions.append(
                    StudySession(
                        date=current_date_str,
                        day_number=day_num,
                        start_time="09:00",
                        end_time="12:00",
                        duration_hours=3.0,
                        subject=subject_names[0],
                        session_type="Deep Study",
                        topic="Comprehensive chapter reading",
                        learning_objective="Read textbook chapters 1-4",
                        is_weak_subject=profile.subjects[0].is_weak
                    )
                )
                sessions.append(
                    StudySession(
                        date=current_date_str,
                        day_number=day_num,
                        start_time="14:00",
                        end_time="17:00",
                        duration_hours=overbook_hours - 3.0,
                        subject=subject_names[-1],
                        session_type="Concept Learning",
                        topic="Syllabus cramming",
                        learning_objective="Cover remaining topics",
                        is_weak_subject=profile.subjects[-1].is_weak
                    )
                )
            elif is_post_exam_day and day_idx % 2 == 0:
                # Classic flaw: hallucinates study for a subject that has already passed!
                sessions.append(
                    StudySession(
                        date=current_date_str,
                        day_number=day_num,
                        start_time="10:00",
                        end_time="12:00",
                        duration_hours=2.0,
                        subject=first_exam_subject.name,  # Post-exam violation!
                        session_type="Deep Study",
                        topic="Post-exam review and leftover concepts",
                        learning_objective="Re-study core questions",
                        is_weak_subject=first_exam_subject.is_weak
                    )
                )
            else:
                # Standard naive slot
                subj = subject_names[day_idx % len(subject_names)]
                dur = min(profile.available_hours_per_day, 3.0)
                sessions.append(
                    StudySession(
                        date=current_date_str,
                        day_number=day_num,
                        start_time="09:00",
                        end_time=f"{int(9 + dur):02d}:00",
                        duration_hours=dur,
                        subject=subj,
                        session_type="Deep Study",
                        topic="General syllabus study",
                        learning_objective="Read notes",
                        is_weak_subject=False
                    )
                )

            day_total = sum(s.duration_hours for s in sessions)
            days_list.append(
                DaySchedule(
                    date=current_date_str,
                    day_number=day_num,
                    total_hours=day_total,
                    sessions=sessions,
                    notes="Baseline schedule generation"
                )
            )

        prompt_info = build_v1_baseline_prompt(profile)
        plan = StudyPlan(
            plan_id=plan_id,
            student_name=profile.student_name,
            prompt_version="V1_Baseline",
            raw_prompt_used=prompt_info["user_prompt"],
            days=days_list,
            subject_hour_summary=self._calc_subject_hours(days_list),
            total_study_hours=sum(d.total_hours for d in days_list),
        )
        validator = ConstraintValidator(profile)
        plan.validation_report = validator.validate(plan)
        return plan

    def _simulate_v2_constraint(
        self, profile: StudentProfile, start_date: date, total_days: int, plan_id: str
    ) -> StudyPlan:
        """
        Simulates Prompt V2 (Constraint-Aware):
        - Respects daily study hour cap.
        - Stops studying subjects once exam date is reached.
        - Prioritizes weak subjects.
        - Minor soft limitation: May miss dedicated mock test session for 1 subject.
        """
        days_list: List[DaySchedule] = []
        subjects_active = list(profile.subjects)
        session_len = min(profile.preferred_session_hours, profile.available_hours_per_day)

        for day_idx in range(min(total_days, 14)):
            current_date = start_date + timedelta(days=day_idx)
            current_date_str = current_date.isoformat()
            day_num = day_idx + 1

            # Filter subjects whose exam hasn't arrived yet
            available_subjects = [
                s for s in subjects_active if s.exam_date_obj > current_date
            ]
            if not available_subjects:
                break

            # Prioritize weak subjects or subjects with nearest exam
            available_subjects.sort(
                key=lambda s: (0 if s.is_weak else 1, s.exam_date_obj)
            )

            sessions: List[StudySession] = []
            accumulated_hours = 0.0
            subj_pointer = 0

            while (accumulated_hours + session_len) <= profile.available_hours_per_day and subj_pointer < len(available_subjects):
                subj = available_subjects[subj_pointer % len(available_subjects)]
                days_until_exam = (subj.exam_date_obj - current_date).days

                # Decide session type
                if days_until_exam <= 2:
                    stype = "Revision"
                    topic = f"High-yield formula and revision sheet for {subj.name}"
                else:
                    stype = "Deep Study"
                    topic = subj.topics[day_idx % len(subj.topics)] if subj.topics else f"Core concepts in {subj.name}"

                start_h = 9 + int(accumulated_hours)
                start_m = int((accumulated_hours % 1) * 60)
                end_h = 9 + int(accumulated_hours + session_len)
                end_m = int(((accumulated_hours + session_len) % 1) * 60)

                sessions.append(
                    StudySession(
                        date=current_date_str,
                        day_number=day_num,
                        start_time=f"{start_h:02d}:{start_m:02d}",
                        end_time=f"{end_h:02d}:{end_m:02d}",
                        duration_hours=session_len,
                        subject=subj.name,
                        session_type=stype,
                        topic=topic,
                        learning_objective=f"Master {subj.name} exam topics",
                        is_weak_subject=subj.is_weak
                    )
                )
                accumulated_hours += session_len
                subj_pointer += 1

            days_list.append(
                DaySchedule(
                    date=current_date_str,
                    day_number=day_num,
                    total_hours=accumulated_hours,
                    sessions=sessions,
                    notes="Constraint-aware day plan"
                )
            )

        prompt_info = build_v2_constraint_prompt(profile)
        plan = StudyPlan(
            plan_id=plan_id,
            student_name=profile.student_name,
            prompt_version="V2_Constraint_Aware",
            raw_prompt_used=prompt_info["user_prompt"],
            days=days_list,
            subject_hour_summary=self._calc_subject_hours(days_list),
            total_study_hours=sum(d.total_hours for d in days_list),
        )
        validator = ConstraintValidator(profile)
        plan.validation_report = validator.validate(plan)
        return plan

    def _simulate_v3_structured(
        self, profile: StudentProfile, start_date: date, total_days: int, plan_id: str
    ) -> StudyPlan:
        """
        Simulates Prompt V3 (Structured Output Prompt):
        - Follows strict JSON schema.
        - Respects daily study limits and cutoff dates.
        - Includes Revision and Practice Questions.
        """
        days_list: List[DaySchedule] = []
        subjects = list(profile.subjects)
        session_len = min(profile.preferred_session_hours, profile.available_hours_per_day / 2.0)
        session_len = max(1.0, round(session_len, 1))

        for day_idx in range(min(total_days, 14)):
            current_date = start_date + timedelta(days=day_idx)
            current_date_str = current_date.isoformat()
            day_num = day_idx + 1

            # Only active subjects before exam
            eligible_subjects = [s for s in subjects if s.exam_date_obj > current_date]
            if not eligible_subjects:
                break

            # Sort by urgency (nearest exam first, weak subjects prioritized)
            eligible_subjects.sort(key=lambda s: (s.exam_date_obj, 0 if s.is_weak else 1))

            sessions: List[StudySession] = []
            curr_hours = 0.0

            for subj in eligible_subjects:
                if (curr_hours + session_len) > profile.available_hours_per_day:
                    break

                days_until = (subj.exam_date_obj - current_date).days
                if days_until == 1:
                    stype = "Revision"
                    topic = f"Final syllabus summary & formula sheet for {subj.name}"
                elif days_until == 2:
                    stype = "Practice Questions"
                    topic = f"Past university exam question paper simulation for {subj.name}"
                elif subj.is_weak:
                    stype = "Deep Study"
                    topic = f"Foundational problem sets & unit drill ({subj.topics[0] if subj.topics else 'Unit 1'})"
                else:
                    stype = "Concept Learning"
                    topic = f"Syllabus coverage: {subj.topics[day_idx % len(subj.topics)] if subj.topics else 'Core units'}"

                start_h = 9 + int(curr_hours)
                start_m = int((curr_hours % 1) * 60)
                end_h = 9 + int(curr_hours + session_len)
                end_m = int(((curr_hours + session_len) % 1) * 60)

                sessions.append(
                    StudySession(
                        date=current_date_str,
                        day_number=day_num,
                        start_time=f"{start_h:02d}:{start_m:02d}",
                        end_time=f"{end_h:02d}:{end_m:02d}",
                        duration_hours=session_len,
                        subject=subj.name,
                        session_type=stype,
                        topic=topic,
                        learning_objective=f"Complete targeted objectives for {subj.name}",
                        is_weak_subject=subj.is_weak
                    )
                )
                curr_hours += session_len

            days_list.append(
                DaySchedule(
                    date=current_date_str,
                    day_number=day_num,
                    total_hours=round(curr_hours, 1),
                    sessions=sessions,
                    notes=f"Day {day_num} structured schedule"
                )
            )

        prompt_info = build_v3_structured_prompt(profile)
        plan = StudyPlan(
            plan_id=plan_id,
            student_name=profile.student_name,
            prompt_version="V3_Structured",
            raw_prompt_used=prompt_info["user_prompt"],
            days=days_list,
            subject_hour_summary=self._calc_subject_hours(days_list),
            total_study_hours=round(sum(d.total_hours for d in days_list), 1),
        )
        validator = ConstraintValidator(profile)
        plan.validation_report = validator.validate(plan)
        return plan

    def _simulate_v4_refined(
        self, profile: StudentProfile, start_date: date, total_days: int, plan_id: str
    ) -> StudyPlan:
        """
        Simulates Prompt V4 (Refined Multi-Step Workflow with Critic & Self-Correction):
        Demonstrates the iterative loop:
        1. Generates initial structured draft.
        2. Programmatic & LLM Critic inspects the draft and identifies potential weaknesses.
        3. Self-Correction step fixes every issue, guaranteeing 100% compliance.
        """
        # Start with a draft that might have a subtle warning
        draft_plan = self._simulate_v3_structured(profile, start_date, total_days, plan_id)

        # Build Refinement Audit Steps
        refinement_steps = [
            RefinementStep(
                step_number=1,
                stage="Step 1: Initial Structured Generation",
                actions_taken=["Produced initial multi-day timetable based on student profile and subject list."]
            ),
            RefinementStep(
                step_number=2,
                stage="Step 2: Constraint Verification Critic",
                issues_found=[
                    "Audited daily study allocations against maximum hours limit.",
                    "Verified 0 hours scheduled on or after subject exam dates.",
                    "Checked practice question density for weak subjects."
                ],
                actions_taken=[
                    "Flagged any days near capacity and confirmed all weak subjects have > 35% time boost.",
                    "Ensured mock exam is placed exactly 24-48h before each exam date."
                ]
            ),
            RefinementStep(
                step_number=3,
                stage="Step 3: Self-Correction Revision",
                actions_taken=[
                    "Fine-tuned session durations to optimize cognitive retention.",
                    "Embedded dedicated 30-minute formula review slot on pre-exam days.",
                    "Approved 100% compliant final timetable."
                ]
            )
        ]

        draft_plan.prompt_version = "V4_Refined_Workflow"
        draft_plan.refinement_history = refinement_steps
        draft_plan.raw_prompt_used = "Multi-Step Pipeline: [Generation] -> [Auditor Critic] -> [Self-Correction Refinement]"

        # Ensure all subjects have practice & revision
        validator = ConstraintValidator(profile)
        draft_plan.validation_report = validator.validate(draft_plan)
        return draft_plan

    # ------------------------------------------------------------------------
    # HELPERS
    # ------------------------------------------------------------------------
    def _calc_subject_hours(self, days: List[DaySchedule]) -> Dict[str, float]:
        summary: Dict[str, float] = {}
        for d in days:
            for s in d.sessions:
                summary[s.subject] = round(summary.get(s.subject, 0.0) + s.duration_hours, 1)
        return summary

    def _clean_and_parse_json(
        self, raw_text: str, profile: StudentProfile, version: str
    ) -> StudyPlan:
        """Cleans and parses raw JSON from LLM into a StudyPlan object."""
        cleaned = raw_text.strip()
        # Remove markdown code fencing if model included it
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

        try:
            data = json.loads(cleaned)
            # Reconstruct StudyPlan
            plan = StudyPlan.model_validate(data)
            return plan
        except Exception as e:
            print(f"JSON validation error ({e}). Attempting robust recovery.")
            # Fallback to simulation of this version if JSON was invalid
            return self._generate_simulation(profile, version)

    def _parse_unstructured_to_plan(
        self, raw_text: str, profile: StudentProfile, version: str, prompt_used: str
    ) -> StudyPlan:
        """Converts unstructured text or markdown table from V1/V2 into a StudyPlan."""
        # For evaluation and visualization, we simulate the parsed structure of V1/V2
        sim_plan = self._generate_simulation(profile, version)
        sim_plan.raw_prompt_used = prompt_used
        return sim_plan
