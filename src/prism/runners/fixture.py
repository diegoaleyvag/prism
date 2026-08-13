"""The deterministic fixture/replay runner used in CI and every published result.

For a given case, the runner looks up a canned response by ``case_digest`` and derives
token counts and latency with **no RNG**: "jitter" is a pure hash of ``(profile_id,
case_digest)``, so the same profile + case always yields the same output on any machine.
"""

from __future__ import annotations

from pydantic import JsonValue

from prism.digest import canonical_json, content_digest, stable_int
from prism.models.enums import RunMode
from prism.models.run_record import RunnerIdentity
from prism.models.task_case import TaskCase
from prism.runners.base import BaseRunner, RunnerOutput
from prism.runners.profiles import FixtureProfile, ProfileResponse


def estimate_tokens(value: JsonValue, chars_per_token: int) -> int:
    """Deterministically estimate a token count from a value's canonical length."""
    text = value if isinstance(value, str) else canonical_json(value)
    return max(1, len(text) // chars_per_token)


class FixtureReplayRunner(BaseRunner):
    """A simulated runner backed by a :class:`FixtureProfile`."""

    def __init__(self, profile: FixtureProfile) -> None:
        self.profile = profile
        self.mode = RunMode.FIXTURE_REPLAY
        config_digest = content_digest(
            {
                "base_latency_ms": profile.base_latency_ms,
                "latency_jitter_ms": profile.latency_jitter_ms,
                "token_model": profile.token_model.model_dump(),
                "default_behavior": profile.default_behavior.model_dump(),
            }
        )
        self.identity = RunnerIdentity(
            runner_kind="fixture_replay",
            runner_name=profile.profile_id,
            runner_version=profile.profile_version,
            profile_digest=profile.profile_digest,
            config_digest=config_digest,
        )

    def _resolve(self, case: TaskCase) -> tuple[JsonValue, bool, str | None]:
        """Return ``(output, matched, note)`` for a case."""
        resp: ProfileResponse | None = self.profile.responses.get(case.case_digest)
        if resp is not None:
            return resp.output, True, resp.note
        behavior = self.profile.default_behavior
        if behavior.strategy == "canned_refusal":
            return behavior.canned_output, False, "default_behavior:canned_refusal"
        return None, False, "default_behavior:empty"

    def run(self, case: TaskCase) -> RunnerOutput:
        resp = self.profile.responses.get(case.case_digest)
        output, matched, note = self._resolve(case)

        cpt = self.profile.token_model.chars_per_token
        prompt_material = "\n".join((case.payload.prompt, *case.payload.context))
        input_tokens = (
            resp.input_tokens
            if resp is not None and resp.input_tokens is not None
            else estimate_tokens(prompt_material, cpt)
        )
        output_tokens = (
            resp.output_tokens
            if resp is not None and resp.output_tokens is not None
            else estimate_tokens(output, cpt)
        )

        if resp is not None and resp.latency_ms is not None:
            latency_ms = resp.latency_ms
        else:
            jitter_span = self.profile.latency_jitter_ms + 1
            jitter = stable_int(self.profile.profile_id, case.case_digest, "latency") % jitter_span
            latency_ms = self.profile.base_latency_ms + jitter

        return RunnerOutput(
            raw_output=output,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency_ms=latency_ms,
            mode=RunMode.FIXTURE_REPLAY,
            provenance={
                "profile_id": self.profile.profile_id,
                "profile_version": self.profile.profile_version,
                "profile_digest": self.profile.profile_digest,
                "matched": matched,
                "note": note,
            },
        )


__all__ = ["FixtureReplayRunner", "estimate_tokens"]
