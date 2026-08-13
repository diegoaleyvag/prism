"""The evaluation manifest: the pinned, versioned description of a run.

A manifest names the cases (each pinned by ``case_digest``), the runners (fixture profiles
and/or the guarded provider scaffold), the metrics to compute and a seed. Pinning case
digests makes silent content drift a load-time failure: if a case file changes, its digest
no longer matches the manifest entry and validation fails closed.
"""

from __future__ import annotations

from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, model_validator

from prism.digest import content_digest
from prism.models.enums import TaskFamily
from prism.schema_versions import MANIFEST_V1


class ManifestEntry(BaseModel):
    """A case reference pinned to an exact content digest."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    case_id: str
    case_digest: str


class RunnerRef(BaseModel):
    """A runner the manifest wants executed.

    ``fixture_replay`` requires a ``profile`` id; ``provider`` requires a ``provider_ref``
    and can only run behind the disabled-by-default guard (see ``runners/provider.py``).
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    runner_kind: Literal["fixture_replay", "provider"]
    profile: str | None = None
    provider_ref: str | None = None
    version_constraint: str | None = None

    @model_validator(mode="after")
    def _check_kind_fields(self) -> Self:
        if self.runner_kind == "fixture_replay":
            if not self.profile:
                raise ValueError("fixture_replay runner requires 'profile'")
            if self.provider_ref is not None:
                raise ValueError("fixture_replay runner must not set 'provider_ref'")
        else:  # provider
            if not self.provider_ref:
                raise ValueError("provider runner requires 'provider_ref'")
            if self.profile is not None:
                raise ValueError("provider runner must not set 'profile'")
        return self


class EvaluationManifest(BaseModel):
    """A reproducible evaluation specification."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["manifest/v1"] = MANIFEST_V1
    manifest_id: str
    manifest_version: str
    """Semver of this manifest document."""
    title: str
    description: str | None = None
    families: tuple[TaskFamily, ...]
    runners: tuple[RunnerRef, ...]
    cases: tuple[ManifestEntry, ...]
    metrics: tuple[str, ...]
    seed: int
    created_by: str
    manifest_digest: str

    @model_validator(mode="after")
    def _verify(self) -> Self:
        ids = [e.case_id for e in self.cases]
        if len(ids) != len(set(ids)):
            dupes = sorted({i for i in ids if ids.count(i) > 1})
            raise ValueError(f"duplicate case_id(s) in manifest: {dupes}")
        if not self.runners:
            raise ValueError("manifest must reference at least one runner")
        expected = compute_manifest_digest(self)
        if self.manifest_digest != expected:
            raise ValueError(
                f"manifest_digest drift: stored={self.manifest_digest} computed={expected}"
            )
        return self

    @classmethod
    def build(
        cls,
        *,
        manifest_id: str,
        manifest_version: str,
        title: str,
        families: tuple[TaskFamily, ...],
        runners: tuple[RunnerRef, ...],
        cases: tuple[ManifestEntry, ...],
        metrics: tuple[str, ...],
        seed: int,
        created_by: str,
        description: str | None = None,
    ) -> EvaluationManifest:
        """Construct a manifest with its ``manifest_digest`` computed from its body."""
        draft = {
            "schema_version": MANIFEST_V1,
            "manifest_id": manifest_id,
            "manifest_version": manifest_version,
            "title": title,
            "description": description,
            "families": families,
            "runners": runners,
            "cases": cases,
            "metrics": metrics,
            "seed": seed,
            "created_by": created_by,
        }
        digest = content_digest(draft)
        return cls(
            schema_version=MANIFEST_V1,
            manifest_id=manifest_id,
            manifest_version=manifest_version,
            title=title,
            description=description,
            families=families,
            runners=runners,
            cases=cases,
            metrics=metrics,
            seed=seed,
            created_by=created_by,
            manifest_digest=digest,
        )


def compute_manifest_digest(manifest: EvaluationManifest) -> str:
    """Content digest over the manifest body, excluding the digest field itself."""
    body = manifest.model_dump(exclude={"manifest_digest"})
    return content_digest(body)


__all__ = ["EvaluationManifest", "ManifestEntry", "RunnerRef", "compute_manifest_digest"]
