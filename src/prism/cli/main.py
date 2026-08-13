"""Prism command-line interface.

Commands fail closed: they exit non-zero on any validation error, digest drift or integrity
failure, and print one actionable line per problem. Every command supports ``--json`` for
machine consumption by tests and the artifact pipeline.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Annotated

import typer

from prism import __version__
from prism.dataset.generate import build_cases, write_cases
from prism.dataset.loader import load_cases
from prism.dataset.profiles_gen import build_profiles, write_profiles
from prism.engine.executor import ManifestInvalidError, execute_run
from prism.engine.plan import build_default_manifest
from prism.export.artifacts import build_artifacts, write_artifacts
from prism.metrics.compute import compute_report, verify_reconciliation
from prism.metrics.pricing import default_price_table, load_price_table
from prism.models.enums import ReviewScope
from prism.models.manifest import EvaluationManifest
from prism.models.run_record import RunRecord, compute_record_id
from prism.models.task_case import TaskCase
from prism.runners.profiles import load_profiles
from prism.schema_versions import MANIFEST_V1, RUNRECORD_V1, TASKCASE_V1
from prism.storage.record_store import RecordStore, digest_hex
from prism.validation.manifest_validator import has_errors, validate_manifest

app = typer.Typer(
    add_completion=False,
    help="Prism — a reproducible, SIMULATED evaluation workbench.",
    no_args_is_help=True,
)

CasesDir = Annotated[Path, typer.Option(help="Directory of case JSON files.")]
ProfilesDir = Annotated[Path, typer.Option(help="Directory of *.profile.json files.")]


def _echo_json(payload: object) -> None:
    typer.echo(json.dumps(payload, indent=2, sort_keys=True))


def _load_manifest(path: Path) -> EvaluationManifest:
    return EvaluationManifest.model_validate_json(Path(path).read_text(encoding="utf-8"))


@app.command()
def version(json_out: Annotated[bool, typer.Option("--json")] = False) -> None:
    """Print the Prism version and schema versions."""
    info = {
        "prism": __version__,
        "schemas": {
            "task_case": TASKCASE_V1,
            "run_record": RUNRECORD_V1,
            "manifest": MANIFEST_V1,
        },
        "note": "All Prism results are SIMULATED fixture runs, not named-model performance.",
    }
    if json_out:
        _echo_json(info)
    else:
        typer.echo(f"prism {__version__}  (schemas: {TASKCASE_V1}, {RUNRECORD_V1}, {MANIFEST_V1})")
        typer.echo("SIMULATED workbench — results are deterministic fixtures, not real models.")


@app.command()
def digest(case_path: Annotated[Path, typer.Argument(help="Path to a case JSON file.")]) -> None:
    """Print the content digest of a case (recomputed from its payload)."""
    case = TaskCase.model_validate_json(case_path.read_text(encoding="utf-8"))
    typer.echo(case.case_digest)


@app.command()
def validate(
    manifest_path: Annotated[Path, typer.Argument(help="Path to the manifest JSON.")],
    cases_dir: CasesDir = Path("data/cases"),
    profiles_dir: ProfilesDir = Path("profiles"),
    strict: Annotated[bool, typer.Option(help="Fail on any non-owner_reviewed case.")] = False,
    json_out: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Validate a manifest against the cases and profiles on disk (fail-closed)."""
    manifest = _load_manifest(manifest_path)
    cases = load_cases(cases_dir)
    profiles = load_profiles(profiles_dir)
    problems = validate_manifest(manifest, cases, profiles, strict=strict)

    if json_out:
        _echo_json(
            {
                "ok": not has_errors(problems),
                "problems": [
                    {"level": p.level, "code": p.code, "where": p.where, "message": p.message}
                    for p in problems
                ],
            }
        )
    else:
        for p in problems:
            typer.echo(p.render())
        typer.echo(
            f"{'INVALID' if has_errors(problems) else 'valid'}: "
            f"{len(manifest.cases)} cases, {len(manifest.runners)} runners, "
            f"{sum(p.level == 'error' for p in problems)} errors, "
            f"{sum(p.level == 'warning' for p in problems)} warnings"
        )
    if has_errors(problems):
        raise typer.Exit(code=1)


@app.command()
def run(
    manifest_path: Annotated[Path, typer.Argument(help="Path to the manifest JSON.")],
    out: Annotated[Path, typer.Option(help="Runs root directory.")] = Path("runs"),
    cases_dir: CasesDir = Path("data/cases"),
    profiles_dir: ProfilesDir = Path("profiles"),
    dry_run: Annotated[bool, typer.Option(help="Execute + grade but do not persist.")] = False,
    enable_provider: Annotated[bool, typer.Option(help="Clear the provider guard (never in CI).")] = False,
    json_out: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Validate then execute a manifest, writing immutable records."""
    manifest = _load_manifest(manifest_path)
    cases = load_cases(cases_dir)
    profiles = load_profiles(profiles_dir)
    store = RecordStore(out)
    try:
        summary = execute_run(
            manifest, cases, profiles, store, dry_run=dry_run, allow_provider=enable_provider
        )
    except ManifestInvalidError as exc:
        for line in exc.problems:
            typer.echo(line, err=True)
        raise typer.Exit(code=1) from exc

    passed = sum(r.validation.task_success for r in summary.records)
    payload = {
        "run_dir": summary.run_dir,
        "records": len(summary.records),
        "written": summary.written,
        "skipped": summary.skipped,
        "passed": passed,
        "dry_run": dry_run,
        "simulated": True,
    }
    if json_out:
        _echo_json(payload)
    else:
        typer.echo(
            f"{'(dry-run) ' if dry_run else ''}records={len(summary.records)} "
            f"written={summary.written} skipped={summary.skipped} passed={passed} "
            f"-> {summary.run_dir or '(not persisted)'}"
        )


@app.command()
def verify(
    runs_dir: Annotated[Path, typer.Argument(help="A runs root or a single run directory.")] = Path("runs"),
    json_out: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Recompute every record's content address from disk and check immutability."""
    problems: list[str] = []
    checked = 0
    for manifest_path in sorted(Path(runs_dir).rglob("manifest.snapshot.json")):
        # Loading validates manifest_digest.
        EvaluationManifest.model_validate_json(manifest_path.read_text(encoding="utf-8"))
    for record_path in sorted(Path(runs_dir).rglob("records/**/*.json")):
        checked += 1
        try:
            record = RunRecord.model_validate_json(record_path.read_text(encoding="utf-8"))
        except Exception as exc:
            problems.append(f"{record_path}: load failed: {exc}")
            continue
        if compute_record_id(record) != record.record_id:
            problems.append(f"{record_path}: record_id does not match content")
        if record_path.stem != digest_hex(record.record_id):
            problems.append(f"{record_path}: filename does not match record_id")
        if os.stat(record_path).st_mode & 0o222:
            problems.append(f"{record_path}: record is writable (expected read-only)")

    ok = not problems
    if json_out:
        _echo_json({"ok": ok, "checked": checked, "problems": problems})
    else:
        for p in problems:
            typer.echo(p)
        typer.echo(f"{'OK' if ok else 'FAILED'}: verified {checked} records")
    if not ok:
        raise typer.Exit(code=1)


PriceTableOpt = Annotated[Path | None, typer.Option(help="Price table JSON; omitted uses the default.")]
RunsDir = Annotated[Path, typer.Option(help="Runs root directory.")]
ScopeOpt = Annotated[ReviewScope, typer.Option(help="Review scope for metrics.")]


def _load_records(runs_dir: Path, manifest: EvaluationManifest) -> list[RunRecord]:
    store = RecordStore(runs_dir)
    run_dir = store.run_dir(manifest)
    if not run_dir.exists():
        raise typer.BadParameter(
            f"no run found at {run_dir}; run `prism run {manifest.manifest_id}` first"
        )
    return list(store.iter_records(run_dir))


@app.command()
def metrics(
    manifest_path: Annotated[Path, typer.Argument(help="Path to the manifest JSON.")],
    runs: RunsDir = Path("runs"),
    cases_dir: CasesDir = Path("data/cases"),
    price_table: PriceTableOpt = None,
    scope: ScopeOpt = ReviewScope.RELEASE,
    out: Annotated[Path | None, typer.Option(help="Write the report JSON here.")] = None,
    json_out: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Compute the reconcilable metric report from persisted records."""
    manifest = _load_manifest(manifest_path)
    cases = load_cases(cases_dir)
    records = _load_records(runs, manifest)
    table = load_price_table(price_table) if price_table else default_price_table()
    report = compute_report(records, cases, table, scope=scope)

    problems = verify_reconciliation(report)
    if problems:
        for p in problems:
            typer.echo(f"reconciliation: {p}", err=True)
        raise typer.Exit(code=1)

    if out is not None:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(report.model_dump_json(indent=2) + "\n", encoding="utf-8")

    if json_out:
        typer.echo(report.model_dump_json(indent=2))
    else:
        for prof in report.profiles:
            ts = prof.aggregate.task_success
            typer.echo(
                f"{prof.profile_id}: success {ts.display} "
                f"(ci_reliable={ts.ci_reliable}, flags={list(ts.ci_flags)}) "
                f"cost/case=${prof.aggregate.cost.mean_usd:.6f} "
                f"p90={prof.aggregate.latency.p90_ms:.0f}ms"
            )
        typer.echo(
            f"scope={report.review_scope.value} excluded={report.excluded_count} "
            f"reconciled=yes SIMULATED"
        )


@app.command()
def export(
    manifest_path: Annotated[Path, typer.Argument(help="Path to the manifest JSON.")],
    runs: RunsDir = Path("runs"),
    cases_dir: CasesDir = Path("data/cases"),
    out: Annotated[Path, typer.Option(help="Artifact output directory.")] = Path("artifacts"),
    price_table: PriceTableOpt = None,
    scope: ScopeOpt = ReviewScope.RELEASE,
) -> None:
    """Compute metrics and write the redacted static artifact set for the explorer."""
    manifest = _load_manifest(manifest_path)
    cases = load_cases(cases_dir)
    records = _load_records(runs, manifest)
    table = load_price_table(price_table) if price_table else default_price_table()
    report = compute_report(records, cases, table, scope=scope)

    problems = verify_reconciliation(report)
    if problems:
        for p in problems:
            typer.echo(f"reconciliation: {p}", err=True)
        raise typer.Exit(code=1)

    artifacts = build_artifacts(report, records, cases, table)
    paths = write_artifacts(artifacts, out)
    typer.echo(f"wrote {len(paths)} artifacts to {out} (SIMULATED, redacted)")


dataset_app = typer.Typer(help="Regenerate synthetic dataset artifacts.", no_args_is_help=True)
app.add_typer(dataset_app, name="dataset")


@dataset_app.command("build")
def dataset_build(
    cases_dir: CasesDir = Path("data/cases"),
    profiles_dir: ProfilesDir = Path("profiles"),
    manifests_dir: Annotated[Path, typer.Option(help="Where to write the example manifest.")] = Path("manifests"),
) -> None:
    """Regenerate the 24 cases, both profiles and the example manifest, deterministically."""
    cases = build_cases()
    case_paths = write_cases(cases, cases_dir)
    profiles = build_profiles()
    profile_paths = write_profiles(profiles, str(profiles_dir))

    case_map: dict[str, TaskCase] = {c.case_id: c for c in cases}
    manifest = build_default_manifest(case_map, list(profiles))
    manifests_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = manifests_dir / "example.manifest.json"
    manifest_path.write_text(
        json.dumps(json.loads(manifest.model_dump_json()), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    typer.echo(
        f"wrote {len(case_paths)} cases, {len(profile_paths)} profiles, 1 manifest "
        f"({manifest_path})"
    )


if __name__ == "__main__":
    app()
