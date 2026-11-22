"""
Rule-Based Constraint Validation Engine for the C20 Study Plan Generator.
Provides programmatic verification independent of the LLM to audit timetables.
"""

from datetime import datetime, date
from typing import List, Dict, Any, Tuple
from core.models import (
    StudentProfile,
    StudyPlan,
    ValidationReport,
    ConstraintViolation,
    DaySchedule,
    StudySession
)


class ConstraintValidator:
    """
    Evaluates a generated StudyPlan against hard and soft academic scheduling constraints.
    Returns a comprehensive ValidationReport with an objective compliance score (0-100%).
    """

    def __init__(self, profile: StudentProfile):
        self.profile = profile
        self.exam_dates: Dict[str, date] = {
            s.name.strip().lower(): s.exam_date_obj for s in profile.subjects
        }
        self.weak_subjects = {
            s.name.strip().lower() for s in profile.subjects if s.is_weak
        }
        self.all_subject_names = [s.name for s in profile.subjects]

    def validate(self, plan: StudyPlan) -> ValidationReport:
        """Runs all constraint validation checks and returns the audit report."""
        violations: List[ConstraintViolation] = []
        warnings: List[ConstraintViolation] = []
        total_checks = 0
        passed_checks = 0

        # Check 1: Daily Study-Hour Limit (Hard Constraint)
        hour_violations, hour_passed, hour_total = self._check_daily_hours(plan)
        violations.extend(hour_violations)
        passed_checks += hour_passed
        total_checks += hour_total

        # Check 2: Post-Exam Study Prevention (Hard Constraint)
        post_exam_violations, post_passed, post_total = self._check_post_exam_study(plan)
        violations.extend(post_exam_violations)
        passed_checks += post_passed
        total_checks += post_total

        # Check 3: Subject Completeness (Hard Constraint)
        comp_violations, comp_passed, comp_total = self._check_subject_completeness(plan)
        violations.extend(comp_violations)
        passed_checks += comp_passed
        total_checks += comp_total

        # Check 4: Weak Subject Prioritization (Soft / Important Constraint)
        weak_warnings, weak_passed, weak_total = self._check_weak_subject_priority(plan)
        warnings.extend(weak_warnings)
        passed_checks += weak_passed
        total_checks += weak_total

        # Check 5: Revision & Practice Coverage (Soft Constraint)
        rev_warnings, rev_passed, rev_total = self._check_revision_and_practice(plan)
        warnings.extend(rev_warnings)
        passed_checks += rev_passed
        total_checks += rev_total

        # Check 6: Chronological Sanity (Start Date to Exam Date)
        chrono_violations, chrono_passed, chrono_total = self._check_chronology(plan)
        violations.extend(chrono_violations)
        passed_checks += chrono_passed
        total_checks += chrono_total

        # Calculate Objective Compliance Score (0 to 100%)
        # Critical violations deduct 20 points each; warnings deduct 5 points each
        penalty = (len(violations) * 20.0) + (len(warnings) * 5.0)
        compliance_score = max(0.0, min(100.0, 100.0 - penalty))

        # Compile Metrics Summary
        metrics = self._compute_summary_metrics(plan)

        is_valid = len(violations) == 0

        return ValidationReport(
            is_valid=is_valid,
            compliance_score=round(compliance_score, 1),
            total_checks=total_checks,
            passed_checks=passed_checks,
            violations=violations,
            warnings=warnings,
            metrics_summary=metrics
        )

    def _check_daily_hours(
        self, plan: StudyPlan
    ) -> Tuple[List[ConstraintViolation], int, int]:
        """Ensures that daily study hours do not exceed available_hours_per_day."""
        violations = []
        limit = self.profile.available_hours_per_day
        tolerance = 0.1  # 6-minute rounding buffer
        total_days = len(plan.days)
        passed_days = 0

        for day in plan.days:
            # Recompute total hours directly from sessions to prevent manipulated day.total_hours
            actual_day_hours = sum(s.duration_hours for s in day.sessions) if day.sessions else day.total_hours

            if actual_day_hours > (limit + tolerance):
                overrun = round(actual_day_hours - limit, 2)
                violations.append(
                    ConstraintViolation(
                        rule_id="RULE_DAILY_HOURS_EXCEEDED",
                        rule_name="Daily Study Hour Limit",
                        severity="CRITICAL",
                        date=day.date,
                        message=(
                            f"Exceeded daily limit on {day.date} (Day {day.day_number}): "
                            f"Scheduled {actual_day_hours:.1f}h exceeds student limit of {limit:.1f}h by {overrun:.1f}h."
                        ),
                        current_value=round(actual_day_hours, 2),
                        expected_limit=limit,
                    )
                )
            else:
                passed_days += 1

        return violations, passed_days, total_days

    def _check_post_exam_study(
        self, plan: StudyPlan
    ) -> Tuple[List[ConstraintViolation], int, int]:
        """Ensures no subject is scheduled for preparation on or after its exam date."""
        violations = []
        checks_count = 0
        passed_count = 0

        for day in plan.days:
            try:
                day_date = datetime.strptime(day.date, "%Y-%m-%d").date()
            except ValueError:
                continue

            for session in day.sessions:
                subj_clean = session.subject.strip().lower()
                # Find matching subject in profile
                matched_exam_date = None
                for orig_subj, exam_dt in self.exam_dates.items():
                    if orig_subj in subj_clean or subj_clean in orig_subj:
                        matched_exam_date = exam_dt
                        break

                if matched_exam_date:
                    checks_count += 1
                    # A study session scheduled ON or AFTER the exam date is invalid
                    if day_date >= matched_exam_date:
                        violations.append(
                            ConstraintViolation(
                                rule_id="RULE_POST_EXAM_STUDY",
                                rule_name="Post-Exam Study Prevention",
                                severity="CRITICAL",
                                date=day.date,
                                subject=session.subject,
                                message=(
                                    f"Scheduled preparation for '{session.subject}' on {day.date}, "
                                    f"which is on or after its exam date ({matched_exam_date.isoformat()}). "
                                    f"Preparation should conclude prior to the exam day."
                                ),
                                current_value=session.duration_hours,
                                expected_limit=0.0,
                            )
                        )
                    else:
                        passed_count += 1

        return violations, passed_count, max(checks_count, 1)

    def _check_subject_completeness(
        self, plan: StudyPlan
    ) -> Tuple[List[ConstraintViolation], int, int]:
        """Ensures all requested subjects have at least one study session."""
        violations = []
        scheduled_subjects = set()

        for day in plan.days:
            for session in day.sessions:
                subj_clean = session.subject.strip().lower()
                for orig_subj in self.exam_dates.keys():
                    if orig_subj in subj_clean or subj_clean in orig_subj:
                        scheduled_subjects.add(orig_subj)

        missing = set(self.exam_dates.keys()) - scheduled_subjects
        total = len(self.exam_dates)
        passed = total - len(missing)

        for miss in missing:
            # Find proper original casing
            display_name = next(
                (s.name for s in self.profile.subjects if s.name.strip().lower() == miss),
                miss
            )
            violations.append(
                ConstraintViolation(
                    rule_id="RULE_SUBJECT_OMISSION",
                    rule_name="Subject Completeness",
                    severity="CRITICAL",
                    subject=display_name,
                    message=f"Subject '{display_name}' was requested but has ZERO study sessions scheduled.",
                    current_value=0.0,
                    expected_limit=1.0,
                )
            )

        return violations, passed, total

    def _check_weak_subject_priority(
        self, plan: StudyPlan
    ) -> Tuple[List[ConstraintViolation], int, int]:
        """Checks if weak subjects receive prioritized hours compared to regular subjects."""
        warnings = []
        if not self.weak_subjects:
            return warnings, 1, 1

        hours_by_subj: Dict[str, float] = {orig: 0.0 for orig in self.exam_dates.keys()}

        for day in plan.days:
            for session in day.sessions:
                subj_clean = session.subject.strip().lower()
                for orig in self.exam_dates.keys():
                    if orig in subj_clean or subj_clean in orig:
                        hours_by_subj[orig] += session.duration_hours

        weak_hours = [hours_by_subj[s] for s in self.weak_subjects if s in hours_by_subj]
        non_weak_hours = [
            hours_by_subj[s] for s in self.exam_dates.keys() if s not in self.weak_subjects
        ]

        avg_weak = sum(weak_hours) / len(weak_hours) if weak_hours else 0.0
        avg_non_weak = sum(non_weak_hours) / len(non_weak_hours) if non_weak_hours else 0.0

        total_checks = len(self.weak_subjects)
        passed = 0

        # Compute available prep days for each subject (from start_date to exam_date)
        start_dt = self.profile.start_date_obj
        prep_days_by_subj = {}
        for s in self.profile.subjects:
            key = s.name.strip().lower()
            days_span = max(1, (s.exam_date_obj - start_dt).days)
            prep_days_by_subj[key] = days_span

        # Study intensity = hours / prep_days
        intensity_by_subj = {
            s: (hours_by_subj[s] / prep_days_by_subj.get(s, 1))
            for s in self.exam_dates.keys()
        }

        non_weak_intensities = [
            intensity_by_subj[s] for s in self.exam_dates.keys() if s not in self.weak_subjects
        ]
        avg_non_weak_intensity = (
            sum(non_weak_intensities) / len(non_weak_intensities) if non_weak_intensities else 0.0
        )

        total_checks = len(self.weak_subjects)
        passed = 0

        # Weak subjects should have either higher total hours OR higher daily study intensity
        for weak_s in self.weak_subjects:
            h = hours_by_subj.get(weak_s, 0.0)
            intens = intensity_by_subj.get(weak_s, 0.0)
            display_name = next(
                (s.name for s in self.profile.subjects if s.name.strip().lower() == weak_s),
                weak_s
            )

            # Pass if intensity >= avg non-weak intensity (with small tolerance) OR total hours >= avg
            if (intens + 0.05) >= avg_non_weak_intensity or h >= avg_non_weak or not non_weak_hours:
                passed += 1
            else:
                warnings.append(
                    ConstraintViolation(
                        rule_id="WARN_WEAK_SUBJECT_UNDERALLOCATION",
                        rule_name="Weak Subject Prioritization",
                        severity="WARNING",
                        subject=display_name,
                        message=(
                            f"Weak subject '{display_name}' received study intensity of {intens:.2f}h/day "
                            f"(total {h:.1f}h), which is less than non-weak subject average ({avg_non_weak_intensity:.2f}h/day). "
                            f"Should be prioritized with extra review."
                        ),
                        current_value=round(intens, 2),
                        expected_limit=round(avg_non_weak_intensity, 2),
                    )
                )

        return warnings, passed, total_checks

    def _check_revision_and_practice(
        self, plan: StudyPlan
    ) -> Tuple[List[ConstraintViolation], int, int]:
        """Checks if every subject has dedicated revision and practice sessions."""
        warnings = []
        revision_by_subj: Dict[str, int] = {orig: 0 for orig in self.exam_dates.keys()}
        practice_by_subj: Dict[str, int] = {orig: 0 for orig in self.exam_dates.keys()}

        for day in plan.days:
            for session in day.sessions:
                subj_clean = session.subject.strip().lower()
                stype = session.session_type.lower()
                topic = session.topic.lower()

                is_rev = "revision" in stype or "revision" in topic or "review" in stype or "formula" in stype
                is_prac = "practice" in stype or "mock" in stype or "practice" in topic or "question" in topic

                for orig in self.exam_dates.keys():
                    if orig in subj_clean or subj_clean in orig:
                        if is_rev:
                            revision_by_subj[orig] += 1
                        if is_prac:
                            practice_by_subj[orig] += 1

        total_checks = len(self.exam_dates) * 2
        passed = 0

        for orig in self.exam_dates.keys():
            display_name = next(
                (s.name for s in self.profile.subjects if s.name.strip().lower() == orig),
                orig
            )
            if revision_by_subj[orig] == 0:
                warnings.append(
                    ConstraintViolation(
                        rule_id="WARN_NO_REVISION",
                        rule_name="Revision Coverage",
                        severity="WARNING",
                        subject=display_name,
                        message=f"'{display_name}' has no dedicated revision sessions before its exam.",
                        current_value=0.0,
                        expected_limit=1.0,
                    )
                )
            else:
                passed += 1

            if practice_by_subj[orig] == 0:
                warnings.append(
                    ConstraintViolation(
                        rule_id="WARN_NO_PRACTICE",
                        rule_name="Practice Question Coverage",
                        severity="WARNING",
                        subject=display_name,
                        message=f"'{display_name}' has no practice-question or mock test sessions scheduled.",
                        current_value=0.0,
                        expected_limit=1.0,
                    )
                )
            else:
                passed += 1

        return warnings, passed, total_checks

    def _check_chronology(
        self, plan: StudyPlan
    ) -> Tuple[List[ConstraintViolation], int, int]:
        """Checks that dates are sequential and starting on/after profile start date."""
        violations = []
        start_dt = self.profile.start_date_obj
        passed = 0
        total = len(plan.days)

        for day in plan.days:
            try:
                day_dt = datetime.strptime(day.date, "%Y-%m-%d").date()
                if day_dt < start_dt:
                    violations.append(
                        ConstraintViolation(
                            rule_id="RULE_PRE_START_DATE",
                            rule_name="Chronological Sanity",
                            severity="CRITICAL",
                            date=day.date,
                            message=f"Scheduled day {day.date} occurs before profile start date {start_dt.isoformat()}.",
                            current_value=0.0,
                            expected_limit=0.0
                        )
                    )
                else:
                    passed += 1
            except ValueError:
                violations.append(
                    ConstraintViolation(
                        rule_id="RULE_INVALID_DATE_FORMAT",
                        rule_name="Invalid Date Format",
                        severity="CRITICAL",
                        date=day.date,
                        message=f"Day date '{day.date}' is not a valid YYYY-MM-DD date.",
                        current_value=0.0,
                        expected_limit=0.0
                    )
                )

        return violations, passed, max(total, 1)

    def _compute_summary_metrics(self, plan: StudyPlan) -> Dict[str, Any]:
        """Computes numerical summary metrics for the validation report."""
        total_hours = sum(
            sum(s.duration_hours for s in d.sessions) if d.sessions else d.total_hours
            for d in plan.days
        )
        day_hours = [
            sum(s.duration_hours for s in d.sessions) if d.sessions else d.total_hours
            for d in plan.days
        ]
        max_day_hours = max(day_hours) if day_hours else 0.0
        avg_day_hours = (total_hours / len(plan.days)) if plan.days else 0.0

        # Hours per subject
        subj_hours: Dict[str, float] = {}
        for day in plan.days:
            for s in day.sessions:
                subj_hours[s.subject] = round(
                    subj_hours.get(s.subject, 0.0) + s.duration_hours, 1
                )

        # Revision vs New vs Practice
        session_type_counts: Dict[str, int] = {}
        for day in plan.days:
            for s in day.sessions:
                session_type_counts[s.session_type] = (
                    session_type_counts.get(s.session_type, 0) + 1
                )

        return {
            "total_study_hours": round(total_hours, 1),
            "max_daily_hours": round(max_day_hours, 1),
            "avg_daily_hours": round(avg_day_hours, 1),
            "total_days_scheduled": len(plan.days),
            "total_sessions": sum(len(d.sessions) for d in plan.days),
            "subject_hours": subj_hours,
            "session_type_breakdown": session_type_counts,
        }
