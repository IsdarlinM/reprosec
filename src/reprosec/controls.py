from __future__ import annotations

from collections import Counter, defaultdict
from enum import StrEnum
from typing import Sequence

from pydantic import BaseModel, ConfigDict, Field
from sric.models import ClaimStatus

from .stability import StabilityReport


class ControlRole(StrEnum):
    BASELINE = "BASELINE"
    CANDIDATE = "CANDIDATE"
    NEGATIVE_CONTROL = "NEGATIVE_CONTROL"
    POSITIVE_CONTROL = "POSITIVE_CONTROL"
    STATE_RESET = "STATE_RESET"


class ExperimentSample(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sample_id: str
    role: ControlRole
    request_id: str
    observation_id: str
    actor_id: str
    resource_id: str
    resource_state: str
    session_age_bucket: str
    environment_id: str
    evidence_ids: list[str] = Field(default_factory=list)
    sequence_index: int = Field(ge=0)
    mutating: bool = False


class DifferentialDesignPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid")

    minimum_repetitions: int = Field(default=3, ge=2, le=100)
    require_negative_control: bool = True
    require_positive_control: bool = False
    require_state_reset_after_mutation: bool = True
    require_stable_roles: bool = True


class DifferentialDesignReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: ClaimStatus
    ready_for_validation: bool
    role_counts: dict[str, int]
    missing_roles: list[ControlRole] = Field(default_factory=list)
    under_repeated_roles: list[ControlRole] = Field(default_factory=list)
    context_mismatches: list[str] = Field(default_factory=list)
    missing_state_resets: list[str] = Field(default_factory=list)
    unstable_roles: list[ControlRole] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)


def assess_differential_design(
    samples: Sequence[ExperimentSample],
    *,
    policy: DifferentialDesignPolicy | None = None,
    stability_by_role: dict[ControlRole, StabilityReport] | None = None,
) -> DifferentialDesignReport:
    active = policy or DifferentialDesignPolicy()
    stability = stability_by_role or {}
    counts = Counter(sample.role for sample in samples)
    required = {ControlRole.BASELINE, ControlRole.CANDIDATE}
    if active.require_negative_control:
        required.add(ControlRole.NEGATIVE_CONTROL)
    if active.require_positive_control:
        required.add(ControlRole.POSITIVE_CONTROL)
    missing = sorted(required - set(counts), key=lambda item: item.value)
    under_repeated = sorted(
        [
            role
            for role in required
            if 0 < counts[role] < active.minimum_repetitions
        ],
        key=lambda item: item.value,
    )

    by_role: dict[ControlRole, list[ExperimentSample]] = defaultdict(list)
    for sample in samples:
        by_role[sample.role].append(sample)
    contexts: dict[ControlRole, set[tuple[str, str, str, str]]] = {
        role: {
            (
                sample.resource_id,
                sample.resource_state,
                sample.session_age_bucket,
                sample.environment_id,
            )
            for sample in values
        }
        for role, values in by_role.items()
        if role is not ControlRole.STATE_RESET
    }
    context_mismatches: list[str] = []
    if contexts:
        reference_role = ControlRole.BASELINE if ControlRole.BASELINE in contexts else next(iter(contexts))
        reference = contexts[reference_role]
        for role, values in contexts.items():
            if values != reference:
                context_mismatches.append(
                    f"{role.value} context differs from {reference_role.value}"
                )
        for role, values in contexts.items():
            if len(values) > 1:
                context_mismatches.append(
                    f"{role.value} contains multiple resource/session/environment contexts"
                )

    ordered = sorted(samples, key=lambda item: item.sequence_index)
    resets = {sample.sequence_index for sample in ordered if sample.role is ControlRole.STATE_RESET}
    missing_resets: list[str] = []
    if active.require_state_reset_after_mutation:
        for sample in ordered:
            if not sample.mutating:
                continue
            next_non_reset = next(
                (
                    candidate.sequence_index
                    for candidate in ordered
                    if candidate.sequence_index > sample.sequence_index
                    and candidate.role is not ControlRole.STATE_RESET
                ),
                None,
            )
            has_reset = any(
                index > sample.sequence_index
                and (next_non_reset is None or index < next_non_reset)
                for index in resets
            )
            if not has_reset:
                missing_resets.append(sample.sample_id)

    unstable = sorted(
        [
            role
            for role in required
            if active.require_stable_roles
            and (
                role not in stability
                or not stability[role].deterministic
            )
        ],
        key=lambda item: item.value,
    )

    evidence_ids = sorted({value for sample in samples for value in sample.evidence_ids})
    ready = not any(
        [missing, under_repeated, context_mismatches, missing_resets, unstable]
    )
    limitations = [
        "Design completeness does not validate a vulnerability; it only establishes that deterministic comparison prerequisites are present."
    ]
    if missing:
        limitations.append("Required control roles are missing.")
    if under_repeated:
        limitations.append("Some roles do not meet the minimum repetition count.")
    if context_mismatches:
        limitations.append("Samples are not context-equivalent.")
    if missing_resets:
        limitations.append("Mutating samples are not followed by an explicit state reset.")
    if unstable:
        limitations.append("One or more required roles lack deterministic stability evidence.")

    return DifferentialDesignReport(
        status=ClaimStatus.OBSERVED if ready else ClaimStatus.UNKNOWN,
        ready_for_validation=ready,
        role_counts={role.value: count for role, count in sorted(counts.items(), key=lambda item: item[0].value)},
        missing_roles=missing,
        under_repeated_roles=under_repeated,
        context_mismatches=sorted(set(context_mismatches)),
        missing_state_resets=sorted(missing_resets),
        unstable_roles=unstable,
        evidence_ids=evidence_ids,
        limitations=limitations,
    )
