"""
Core module for C20 AI-Powered Study Plan Generator.
"""

from core.models import (
    Subject,
    StudentProfile,
    StudySession,
    DaySchedule,
    ConstraintViolation,
    ValidationReport,
    StudyPlan,
)
from core.validator import ConstraintValidator
from core.generator import StudyPlanGenerator
from core.evaluator import BenchmarkEvaluator
from core.exporter import StudyPlanExporter
from core.canva_template import generate_canva_html, generate_canva_png, THEMES

__all__ = [
    "Subject",
    "StudentProfile",
    "StudySession",
    "DaySchedule",
    "ConstraintViolation",
    "ValidationReport",
    "StudyPlan",
    "ConstraintValidator",
    "StudyPlanGenerator",
    "BenchmarkEvaluator",
    "StudyPlanExporter",
    "generate_canva_html",
    "generate_canva_png",
    "THEMES",
]
