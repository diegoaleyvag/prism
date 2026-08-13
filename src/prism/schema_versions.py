"""Central registry of versioned schema tags.

Every persisted record carries a ``schema_version`` literal drawn from here. Bumping a
tag is a deliberate, breaking change: because models use ``extra="forbid"`` and pin the
tag with ``Literal[...]``, any drift in the tag or shape fails closed at load time. The
constants are typed as ``Literal`` so they assign directly to those pinned fields.
"""

from __future__ import annotations

from typing import Final, Literal

# --- Domain records --------------------------------------------------------
TASKCASE_V1: Final[Literal["taskcase/v1"]] = "taskcase/v1"
RUNRECORD_V1: Final[Literal["runrecord/v1"]] = "runrecord/v1"
METRICRESULT_V1: Final[Literal["metricresult/v1"]] = "metricresult/v1"
MANIFEST_V1: Final[Literal["manifest/v1"]] = "manifest/v1"
PROFILE_V1: Final[Literal["profile/v1"]] = "profile/v1"

# --- Analysis / pricing ----------------------------------------------------
PRICETABLE_V1: Final[Literal["pricetable/v1"]] = "pricetable/v1"
METRICREPORT_V1: Final[Literal["metricreport/v1"]] = "metricreport/v1"

# --- Static export artifacts ----------------------------------------------
# One tag shared by every artifact file; each artifact also names its own ``artifact``
# field so the explorer can dispatch on it.
ARTIFACT_V1: Final[Literal["artifact/v1"]] = "artifact/v1"

__all__ = [
    "ARTIFACT_V1",
    "MANIFEST_V1",
    "METRICREPORT_V1",
    "METRICRESULT_V1",
    "PRICETABLE_V1",
    "PROFILE_V1",
    "RUNRECORD_V1",
    "TASKCASE_V1",
]
