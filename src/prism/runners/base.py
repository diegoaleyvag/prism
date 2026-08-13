"""Runner interfaces: the boundary between a case and a (simulated or live) answer.

A runner turns a :class:`~prism.models.task_case.TaskCase` into a
:class:`RunnerOutput`. Every output records its :class:`~prism.models.enums.RunMode` and a
``provenance`` dict, so fixture and live results can never be silently conflated downstream.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict, Field, JsonValue

from prism.models.enums import RunMode
from prism.models.run_record import RunnerIdentity
from prism.models.task_case import TaskCase


class RunnerOutput(BaseModel):
    """The transient result of running one case (not itself persisted)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    raw_output: JsonValue
    """The runner's answer. Reduced to a digest + graded form before persistence."""
    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    latency_ms: int = Field(ge=0)
    mode: RunMode
    provenance: dict[str, JsonValue] = Field(default_factory=dict)
    """Explicit statement of where this output came from (profile id, mode, etc.)."""


@runtime_checkable
class Runner(Protocol):
    """Structural interface every runner satisfies."""

    identity: RunnerIdentity
    mode: RunMode

    def run(self, case: TaskCase) -> RunnerOutput: ...


class BaseRunner(ABC):
    """Shared base carrying identity + mode; subclasses implement :meth:`run`."""

    identity: RunnerIdentity
    mode: RunMode

    @abstractmethod
    def run(self, case: TaskCase) -> RunnerOutput:
        """Execute ``case`` and return its output."""
        raise NotImplementedError


__all__ = ["BaseRunner", "Runner", "RunnerOutput"]
