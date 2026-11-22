"""
Export utilities for the C20 Study Plan Generator.
Supports CSV, JSON, Markdown, and iCalendar (.ics) exports.
"""

import io
import csv
import json
from datetime import datetime
from typing import List
from core.models import StudyPlan


class StudyPlanExporter:
    """Handles multi-format serialization of generated study plans."""

    @staticmethod
    def to_csv(plan: StudyPlan) -> str:
        """Exports the study sessions to a CSV formatted string."""
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "Day",
            "Date",
            "Start Time",
            "End Time",
            "Duration (Hours)",
            "Subject",
            "Session Type",
            "Topic / Focus Area",
            "Learning Objective",
            "Weak Subject Focus"
        ])

        for day in plan.days:
            for s in day.sessions:
                writer.writerow([
                    f"Day {s.day_number}",
                    s.date,
                    s.start_time,
                    s.end_time,
                    s.duration_hours,
                    s.subject,
                    s.session_type,
                    s.topic,
                    s.learning_objective,
                    "Yes" if s.is_weak_subject else "No"
                ])

        return output.getvalue()

    @staticmethod
    def to_json(plan: StudyPlan) -> str:
        """Exports the study plan to a formatted JSON string."""
        return plan.model_dump_json(indent=2)

    @staticmethod
    def to_markdown(plan: StudyPlan) -> str:
        """Exports the study plan to a clean Markdown document with tables."""
        lines = [
            f"# 📚 Personalized Study Plan: {plan.student_name}",
            f"**Plan ID:** `{plan.plan_id}` | **Prompt Version:** `{plan.prompt_version}`",
            f"**Total Study Hours:** {plan.total_study_hours:.1f}h | **Generated:** {plan.generated_at[:10]}",
            "",
            "## 📊 Subject Time Allocation Summary",
            "| Subject | Total Hours Scheduled |",
            "| :--- | :--- |"
        ]

        for subj, hours in plan.subject_hour_summary.items():
            lines.append(f"| **{subj}** | {hours:.1f} hours |")

        lines.extend([
            "",
            "## 📅 Day-Wise Study Timetable",
            "| Day | Date | Time | Subject | Type | Topic | Objective |",
            "| :--- | :--- | :--- | :--- | :--- | :--- | :--- |"
        ])

        for day in plan.days:
            for s in day.sessions:
                lines.append(
                    f"| Day {s.day_number} | {s.date} | {s.start_time}-{s.end_time} ({s.duration_hours}h) | "
                    f"**{s.subject}** | `{s.session_type}` | {s.topic} | {s.learning_objective} |"
                )

        if plan.validation_report:
            lines.extend([
                "",
                "## 🛡️ Constraint Compliance Audit",
                f"- **Compliance Score:** {plan.validation_report.compliance_score}%",
                f"- **Audit Status:** {'✅ PASSED' if plan.validation_report.is_valid else '❌ VIOLATIONS FOUND'}",
                f"- **Total Checks:** {plan.validation_report.total_checks} | **Passed Checks:** {plan.validation_report.passed_checks}"
            ])
            if plan.validation_report.violations:
                lines.append("\n### ⚠️ Critical Violations:")
                for v in plan.validation_report.violations:
                    lines.append(f"- **[{v.rule_name}]** ({v.date or 'General'}): {v.message}")

        return "\n".join(lines)

    @staticmethod
    def to_ics(plan: StudyPlan) -> str:
        """
        Exports the study plan to standard iCalendar (.ics RFC 5545) format.
        Compatible with Google Calendar, Microsoft Outlook, and Apple Calendar.
        """
        lines = [
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//Bennett University//Prompt Engineering C20 Study Plan//EN",
            "CALSCALE:GREGORIAN",
            "METHOD:PUBLISH",
            f"X-WR-CALNAME:Study Plan - {plan.student_name}"
        ]

        for day in plan.days:
            for s in day.sessions:
                try:
                    # Parse start and end timestamps
                    # Format: YYYYMMDDTHHMMSS
                    clean_date = s.date.replace("-", "")
                    start_hh, start_mm = s.start_time.split(":")
                    end_hh, end_mm = s.end_time.split(":")
                    dt_start = f"{clean_date}T{int(start_hh):02d}{int(start_mm):02d}00"
                    dt_end = f"{clean_date}T{int(end_hh):02d}{int(end_mm):02d}00"
                except Exception:
                    # Fallback default 0900 to 1100
                    clean_date = s.date.replace("-", "")
                    dt_start = f"{clean_date}T090000"
                    dt_end = f"{clean_date}T110000"

                uid = f"study-{clean_date}-{s.subject.replace(' ', '')}-{s.day_number}@promptcraft.edu"
                summary = f"[{s.session_type}] {s.subject}: {s.topic}"
                description = (
                    f"Subject: {s.subject}\\n"
                    f"Session Type: {s.session_type}\\n"
                    f"Topic: {s.topic}\\n"
                    f"Learning Objective: {s.learning_objective}\\n"
                    f"Duration: {s.duration_hours} hours\\n"
                    f"Generated by PromptCraft C20"
                )

                lines.extend([
                    "BEGIN:VEVENT",
                    f"UID:{uid}",
                    f"DTSTAMP:{datetime.now().strftime('%Y%m%dT%H%M%SZ')}",
                    f"DTSTART:{dt_start}",
                    f"DTEND:{dt_end}",
                    f"SUMMARY:{summary}",
                    f"DESCRIPTION:{description}",
                    "STATUS:CONFIRMED",
                    "BEGIN:VALARM",
                    "TRIGGER:-PT15M",
                    "ACTION:DISPLAY",
                    f"DESCRIPTION:Study Reminder: {s.subject}",
                    "END:VALARM",
                    "END:VEVENT"
                ])

        lines.append("END:VCALENDAR")
        return "\r\n".join(lines)
