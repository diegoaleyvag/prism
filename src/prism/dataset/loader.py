"""Load and validate cases from ``data/cases`` (fails closed on drift or duplicate ids)."""

from __future__ import annotations

from pathlib import Path

from prism.models.task_case import TaskCase


def load_case(path: Path) -> TaskCase:
    """Load and validate a single case JSON file."""
    return TaskCase.model_validate_json(Path(path).read_text(encoding="utf-8"))


def load_cases(root: Path) -> dict[str, TaskCase]:
    """Load every case under ``root`` (recursively), keyed by ``case_id``.

    Raises on a duplicate ``case_id`` across the tree — a fail-closed guard against
    accidentally shadowing a case.
    """
    out: dict[str, TaskCase] = {}
    for path in sorted(Path(root).rglob("*.json")):
        case = load_case(path)
        if case.case_id in out:
            raise ValueError(f"duplicate case_id {case.case_id!r} at {path}")
        out[case.case_id] = case
    return out


__all__ = ["load_case", "load_cases"]
