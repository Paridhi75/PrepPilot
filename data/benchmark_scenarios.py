"""
Standard Fictional Student Scenarios for Benchmark Evaluation of C20 Prompts.
Provides repeatable test suites for evaluating V1, V2, V3, and V4.
"""

from typing import List, Dict
from datetime import date, timedelta
from core.models import StudentProfile, Subject


def get_benchmark_scenarios(reference_date: date = date(2026, 11, 1)) -> Dict[str, StudentProfile]:
    """
    Returns 4 standardized fictional student scenarios for empirical evaluation.
    All dates are calculated relative to reference_date for deterministic reproducibility.
    """
    d0 = reference_date.isoformat()

    # Scenario 1: Standard Staggered Semester Exam
    # 4 subjects, Discrete Math is weak and has earliest exam (Day 4)
    s1 = StudentProfile(
        student_name="Aarav Sharma (Scenario 1 - Staggered Semester)",
        available_hours_per_day=4.0,
        start_date=d0,
        preferred_session_hours=1.5,
        daily_start_time="09:00",
        scheduling_preferences="Prefers morning focus for difficult math subjects",
        subjects=[
            Subject(
                name="Discrete Mathematics",
                exam_date=(reference_date + timedelta(days=4)).isoformat(),
                is_weak=True,
                priority="Critical",
                topics=["Graph Theory", "Recurrence Relations", "Combinatorics", "Propositional Logic"]
            ),
            Subject(
                name="Data Structures & Algorithms",
                exam_date=(reference_date + timedelta(days=7)).isoformat(),
                is_weak=False,
                priority="High",
                topics=["Dynamic Programming", "Trees & Graphs", "Sorting Algorithms"]
            ),
            Subject(
                name="Operating Systems",
                exam_date=(reference_date + timedelta(days=10)).isoformat(),
                is_weak=False,
                priority="Medium",
                topics=["Process Scheduling", "Virtual Memory", "Deadlocks & Semaphores"]
            ),
            Subject(
                name="Computer Networks",
                exam_date=(reference_date + timedelta(days=12)).isoformat(),
                is_weak=False,
                priority="Medium",
                topics=["TCP/IP Protocol", "Subnetting", "Routing Algorithms", "Data Link Layer"]
            ),
        ]
    )

    # Scenario 2: Emergency 4-Day Crunch
    # High study hours (6h/day), tight timeline, Machine Learning is weak
    s2 = StudentProfile(
        student_name="Priya Patel (Scenario 2 - Emergency Crunch)",
        available_hours_per_day=6.0,
        start_date=d0,
        preferred_session_hours=2.0,
        daily_start_time="08:30",
        scheduling_preferences="Intensive block study with rapid recall drills",
        subjects=[
            Subject(
                name="Machine Learning",
                exam_date=(reference_date + timedelta(days=3)).isoformat(),
                is_weak=True,
                priority="Critical",
                topics=["Loss Functions & Backprop", "Regularization", "SVM & Kernels", "CNN Architectures"]
            ),
            Subject(
                name="Database Management Systems",
                exam_date=(reference_date + timedelta(days=4)).isoformat(),
                is_weak=False,
                priority="High",
                topics=["B+ Trees", "Normalization 1NF-BCNF", "ACID & Transactions", "SQL Queries"]
            )
        ]
    )

    # Scenario 3: Asymmetric Schedule (One Immediate, One Distant)
    # Tests whether prompt hallucinates study for Software Eng after Day 2
    s3 = StudentProfile(
        student_name="Rohan Verma (Scenario 3 - Asymmetric Schedule)",
        available_hours_per_day=3.5,
        start_date=d0,
        preferred_session_hours=1.5,
        daily_start_time="10:00",
        scheduling_preferences="Balanced pacing, avoid late evening fatigue",
        subjects=[
            Subject(
                name="Software Engineering",
                exam_date=(reference_date + timedelta(days=2)).isoformat(),
                is_weak=False,
                priority="High",
                topics=["Agile & Scrum", "Software Testing", "Design Patterns", "UML Diagrams"]
            ),
            Subject(
                name="Cloud Computing & DevOps",
                exam_date=(reference_date + timedelta(days=14)).isoformat(),
                is_weak=True,
                priority="Medium",
                topics=["Kubernetes & Docker", "Serverless Architecture", "CI/CD Pipelines", "AWS IAM"]
            )
        ]
    )

    # Scenario 4: Multiple Weak Subjects (High Complexity)
    # Two weak subjects simultaneously with adjacent exams
    s4 = StudentProfile(
        student_name="Ananya Gupta (Scenario 4 - Multi-Weak Subjects)",
        available_hours_per_day=5.0,
        start_date=d0,
        preferred_session_hours=1.5,
        daily_start_time="09:00",
        scheduling_preferences="Alternate between math proofs and coding practice",
        subjects=[
            Subject(
                name="Theory of Computation",
                exam_date=(reference_date + timedelta(days=7)).isoformat(),
                is_weak=True,
                priority="Critical",
                topics=["DFA/NFA Minimization", "Pumping Lemma", "Turing Machines", "Decidability"]
            ),
            Subject(
                name="Compiler Design",
                exam_date=(reference_date + timedelta(days=8)).isoformat(),
                is_weak=True,
                priority="Critical",
                topics=["LL(1) & LR(1) Parsers", "Syntax Directed Translation", "Intermediate Code Generation"]
            ),
            Subject(
                name="Web Technologies",
                exam_date=(reference_date + timedelta(days=11)).isoformat(),
                is_weak=False,
                priority="Medium",
                topics=["React State Management", "Node.js Event Loop", "RESTful APIs", "JWT Auth"]
            )
        ]
    )

    return {
        "Scenario 1: Staggered Semester": s1,
        "Scenario 2: Emergency 4-Day Crunch": s2,
        "Scenario 3: Asymmetric Schedule": s3,
        "Scenario 4: Multi-Weak Subjects": s4,
    }
