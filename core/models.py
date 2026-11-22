"""
Data models for the C20 AI-Powered Study Plan Generator.
Using Pydantic for structured validation and serialisation.
"""

from datetime import date, datetime
from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field


class Subject(BaseModel):
    """Represents an academic subject with exam details and priority."""
    name: str = Field(..., description="Subject title or course code, e.g. 'Operating Systems'")
    exam_date: str = Field(..., description="Exam date in YYYY-MM-DD format")
    is_weak: bool = Field(default=False, description="Whether the student considers this a weak subject")
    topics: List[str] = Field(default_factory=list, description="Key topics or syllabus units to cover")
    priority: Literal["Low", "Medium", "High", "Critical"] = Field(
        default="Medium", description="Subject preparation priority"
    )

    @property
    def exam_date_obj(self) -> date:
        return datetime.strptime(self.exam_date, "%Y-%m-%d").date()


class StudentProfile(BaseModel):
    """Student inputs and scheduling constraints."""
    student_name: str = Field(default="Student", description="Name or identifier of the student")
    subjects: List[Subject] = Field(..., description="List of subjects to be prepared")
    available_hours_per_day: float = Field(
        ..., gt=0.0, le=16.0, description="Maximum study hours available per day (hard constraint)"
    )
    start_date: str = Field(..., description="Start date for the timetable in YYYY-MM-DD format")
    preferred_session_hours: float = Field(
        default=1.5, ge=0.5, le=4.0, description="Target duration per study session in hours"
    )
    daily_start_time: str = Field(
        default="09:00", description="Preferred start time for study sessions (HH:MM)"
    )
    scheduling_preferences: str = Field(
        default="", description="Additional preferences (e.g. morning vs evening study, break frequency)"
    )

    @property
    def start_date_obj(self) -> date:
        return datetime.strptime(self.start_date, "%Y-%m-%d").date()

    @property
    def weak_subjects(self) -> List[str]:
        return [s.name for s in self.subjects if s.is_weak]


class StudySession(BaseModel):
    """An individual study slot/session in the day-wise timetable."""
    date: str = Field(..., description="Date of the session in YYYY-MM-DD format")
    day_number: int = Field(..., ge=1, description="Sequential day index (Day 1, Day 2, ...)")
    start_time: str = Field(default="09:00", description="Start time (HH:MM)")
    end_time: str = Field(default="10:30", description="End time (HH:MM)")
    duration_hours: float = Field(..., gt=0.0, description="Duration of this study session in hours")
    subject: str = Field(..., description="Name of the subject being studied")
    session_type: Literal[
        "Concept Learning",
        "Deep Study",
        "Revision",
        "Practice Questions",
        "Mock Test",
        "Formula / Summary Review",
        "Buffer / Rest"
    ] = Field(default="Deep Study", description="Pedagogical type of the session")
    topic: str = Field(..., description="Specific topic, chapter, or problem set being studied")
    learning_objective: str = Field(
        default="", description="Specific measurable goal for this session"
    )
    is_weak_subject: bool = Field(
        default=False, description="Flag indicating if this targets an identified weak subject"
    )


class DaySchedule(BaseModel):
    """All study sessions scheduled for a particular calendar day."""
    date: str = Field(..., description="Date in YYYY-MM-DD format")
    day_number: int = Field(..., ge=1, description="Day number in the timetable")
    total_hours: float = Field(..., ge=0.0, description="Sum of study hours scheduled on this day")
    sessions: List[StudySession] = Field(default_factory=list, description="Ordered list of study sessions")
    notes: str = Field(default="", description="Day-specific notes, e.g. 'Final review before Math exam'")


class ConstraintViolation(BaseModel):
    """Record of a constraint check failure or warning."""
    rule_id: str = Field(..., description="Machine-readable rule ID, e.g. 'RULE_DAILY_HOURS_EXCEEDED'")
    rule_name: str = Field(..., description="Human-readable rule name")
    severity: Literal["CRITICAL", "WARNING", "INFO"] = Field(
        ..., description="Severity level of the violation"
    )
    date: Optional[str] = Field(default=None, description="Date where the violation occurred")
    subject: Optional[str] = Field(default=None, description="Subject related to the violation")
    message: str = Field(..., description="Clear explanation of the violation")
    current_value: Optional[float] = Field(default=None, description="Observed value")
    expected_limit: Optional[float] = Field(default=None, description="Target or allowed constraint limit")


class ValidationReport(BaseModel):
    """Programmatic audit report produced by the constraint checking engine."""
    is_valid: bool = Field(..., description="True if no CRITICAL violations exist")
    compliance_score: float = Field(
        ..., ge=0.0, le=100.0, description="Percentage score indicating constraint adherence"
    )
    total_checks: int = Field(default=0, description="Total number of constraint checks executed")
    passed_checks: int = Field(default=0, description="Number of checks that passed completely")
    violations: List[ConstraintViolation] = Field(
        default_factory=list, description="List of critical violations requiring fix"
    )
    warnings: List[ConstraintViolation] = Field(
        default_factory=list, description="Non-critical warnings or optimization suggestions"
    )
    metrics_summary: Dict[str, Any] = Field(
        default_factory=dict, description="Numerical metrics such as max daily hours, weak ratio, etc."
    )


class RefinementStep(BaseModel):
    """Records an iteration in the Prompt V4 Self-Correction workflow."""
    step_number: int
    stage: str  # e.g., "Draft Generation", "Critic Verification", "Self-Correction Refinement"
    issues_found: List[str] = Field(default_factory=list)
    actions_taken: List[str] = Field(default_factory=list)


class StudyPlan(BaseModel):
    """Complete generated study timetable and metadata."""
    plan_id: str = Field(..., description="Unique identifier for this plan")
    student_name: str = Field(default="Student")
    prompt_version: Literal["V1_Baseline", "V2_Constraint_Aware", "V3_Structured", "V4_Refined_Workflow"] = Field(
        ..., description="Which prompt iteration generated this plan"
    )
    generated_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    raw_prompt_used: str = Field(default="", description="The exact prompt string sent to the model")
    days: List[DaySchedule] = Field(default_factory=list, description="Day-wise scheduled days")
    subject_hour_summary: Dict[str, float] = Field(
        default_factory=dict, description="Total hours scheduled per subject"
    )
    total_study_hours: float = Field(default=0.0, description="Sum of all study hours in plan")
    validation_report: Optional[ValidationReport] = Field(
        default=None, description="Audit report from the constraint checking engine"
    )
    refinement_history: List[RefinementStep] = Field(
        default_factory=list, description="Audit trail for V4 self-correction iterations"
    )
