"""Manifest validation catches the failure modes the acceptance criteria require."""

from __future__ import annotations

from prism.models.enums import ReviewLabel, TaskFamily
from prism.models.manifest import EvaluationManifest, ManifestEntry, RunnerRef
from prism.models.task_case import TaskCase
from prism.runners.profiles import FixtureProfile
from prism.validation.manifest_validator import has_errors, validate_manifest


def test_valid_manifest_has_no_errors(manifest, cases, profiles) -> None:
    problems = validate_manifest(manifest, cases, profiles)
    assert not has_errors(problems)


def test_missing_case_is_error(manifest, cases, profiles) -> None:
    partial = {cid: c for cid, c in cases.items() if cid != "se-001"}
    problems = validate_manifest(manifest, partial, profiles)
    assert has_errors(problems)
    assert any(p.code == "case-missing" for p in problems)


def test_digest_drift_is_error(
    cases: dict[str, TaskCase], profiles: dict[str, FixtureProfile]
) -> None:
    # Pin a wrong digest for one case.
    entries = tuple(
        ManifestEntry(case_id=cid, case_digest=("sha256:" + "0" * 64 if cid == "se-001"
                                                else cases[cid].case_digest))
        for cid in sorted(cases)
    )
    manifest = EvaluationManifest.build(
        manifest_id="m", manifest_version="1.0.0", title="t",
        families=tuple(TaskFamily),
        runners=(RunnerRef(runner_kind="fixture_replay", profile="deep-thinker"),),
        cases=entries, metrics=("task_success_rate",), seed=1, created_by="t",
    )
    problems = validate_manifest(manifest, cases, profiles)
    assert any(p.code == "digest-drift" for p in problems)


def test_missing_profile_is_error(manifest, cases) -> None:
    problems = validate_manifest(manifest, cases, {})  # no profiles on disk
    assert has_errors(problems)
    assert any(p.code == "profile-missing" for p in problems)


def test_provider_runner_is_guarded(cases, profiles) -> None:
    entries = tuple(
        ManifestEntry(case_id=cid, case_digest=cases[cid].case_digest) for cid in sorted(cases)
    )
    manifest = EvaluationManifest.build(
        manifest_id="m", manifest_version="1.0.0", title="t", families=tuple(TaskFamily),
        runners=(RunnerRef(runner_kind="provider", provider_ref="acme-llm"),),
        cases=entries, metrics=("task_success_rate",), seed=1, created_by="t",
    )
    problems = validate_manifest(manifest, cases, profiles, allow_provider=False)
    assert any(p.code == "provider-guarded" for p in problems)
    # With the guard cleared, the provider ref itself is no longer an error.
    assert not any(
        p.code == "provider-guarded"
        for p in validate_manifest(manifest, cases, profiles, allow_provider=True)
    )


def test_strict_flags_unreviewed_case(manifest, cases, profiles) -> None:
    tampered = dict(cases)
    original = tampered["se-001"]
    tampered["se-001"] = original.model_copy(
        update={"review_label": ReviewLabel.GENERATED_UNREVIEWED}
    )
    problems = validate_manifest(manifest, tampered, profiles, strict=True)
    assert any(p.code == "unreviewed-case" and p.level == "error" for p in problems)
