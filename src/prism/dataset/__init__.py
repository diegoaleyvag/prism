"""Synthetic dataset: the 24 seed cases, their graders, and loaders."""

from __future__ import annotations

from prism.dataset.generate import build_cases, write_cases
from prism.dataset.grading import GradeResult, answers_match, check_schema, grade, grader_id
from prism.dataset.loader import load_case, load_cases

__all__ = [
    "GradeResult",
    "answers_match",
    "build_cases",
    "check_schema",
    "grade",
    "grader_id",
    "load_case",
    "load_cases",
    "write_cases",
]
