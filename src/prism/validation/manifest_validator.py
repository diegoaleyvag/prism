"""Fail-closed manifest validation with actionable, per-problem messages.

Validation cross-checks a manifest against the cases and profiles on disk. It catches the
failure modes the acceptance criteria call out: duplicate case ids (already rejected at
manifest load), pinned-digest drift (a case file changed underneath the manifest), missing
cases/profiles, families not declared, and provider references that require the guard.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from prism.models.enums import ReviewLabel
from prism.models.manifest import EvaluationManifest
from prism.models.task_case import TaskCase
from prism.runners.profiles import FixtureProfile


@dataclass(frozen=True)
class Problem:
    """One validation finding. ``level`` is ``"error"`` (fails closed) or ``"warning"``."""

    level: str
    code: str
    where: str
    message: str

    def render(self) -> str:
        return f"[{self.level}] {self.code} @ {self.where}: {self.message}"


def validate_manifest(
    manifest: EvaluationManifest,
    cases: Mapping[str, TaskCase],
    profiles: Mapping[str, FixtureProfile],
    *,
    strict: bool = False,
    allow_provider: bool = False,
) -> list[Problem]:
    """Return all problems; an empty list means the manifest is valid to run."""
    problems: list[Problem] = []

    declared_families = set(manifest.families)

    for entry in manifest.cases:
        case = cases.get(entry.case_id)
        if case is None:
            problems.append(
                Problem("error", "case-missing", entry.case_id,
                        "manifest references a case that is not present on disk")
            )
            continue
        if case.case_digest != entry.case_digest:
            problems.append(
                Problem(
                    "error", "digest-drift", entry.case_id,
                    f"pinned case_digest {entry.case_digest} != on-disk {case.case_digest} "
                    "(case content or schema changed)",
                )
            )
        if case.payload.family not in declared_families:
            problems.append(
                Problem("error", "family-undeclared", entry.case_id,
                        f"case family {case.payload.family.value!r} is not in manifest.families")
            )
        if strict and case.review_label != ReviewLabel.OWNER_REVIEWED:
            problems.append(
                Problem("error", "unreviewed-case", entry.case_id,
                        "strict mode: case is not owner_reviewed")
            )
        elif case.review_label != ReviewLabel.OWNER_REVIEWED:
            problems.append(
                Problem("warning", "unreviewed-case", entry.case_id,
                        "case is not owner_reviewed; excluded from release metrics")
            )

    for i, ref in enumerate(manifest.runners):
        where = f"runners[{i}]"
        if ref.runner_kind == "fixture_replay":
            if ref.profile not in profiles:
                problems.append(
                    Problem("error", "profile-missing", where,
                            f"fixture profile {ref.profile!r} is not present on disk")
                )
        else:  # provider
            if not allow_provider:
                problems.append(
                    Problem(
                        "error", "provider-guarded", where,
                        f"provider runner {ref.provider_ref!r} requires the explicit guard "
                        "(PRISM_ENABLE_PROVIDER=1 and --enable-provider); it is disabled by "
                        "default and never runs in CI",
                    )
                )

    return problems


def has_errors(problems: list[Problem]) -> bool:
    return any(p.level == "error" for p in problems)


__all__ = ["Problem", "has_errors", "validate_manifest"]
