from reprosec.controls import (
    ControlRole,
    DifferentialDesignPolicy,
    ExperimentSample,
    assess_differential_design,
)
from reprosec.stability import StabilityReport
from sric.models import ClaimStatus


def sample(
    sample_id: str,
    role: ControlRole,
    sequence: int,
    *,
    actor: str = "actor-a",
    resource: str = "resource-1",
    state: str = "active",
    environment: str = "lab",
    mutating: bool = False,
) -> ExperimentSample:
    return ExperimentSample(
        sample_id=sample_id,
        role=role,
        request_id=f"REQ-{sample_id}",
        observation_id=f"OBS-{sample_id}",
        actor_id=actor,
        resource_id=resource,
        resource_state=state,
        session_age_bucket="fresh",
        environment_id=environment,
        evidence_ids=[f"E-{sample_id}"],
        sequence_index=sequence,
        mutating=mutating,
    )


def stability(deterministic: bool = True) -> StabilityReport:
    return StabilityReport(
        sample_count=3,
        dominant_fingerprint_count=3 if deterministic else 2,
        flakiness_score=0.0 if deterministic else 0.333333,
        deterministic=deterministic,
        stable_status=deterministic,
        stable_headers=deterministic,
        stable_body=deterministic,
    )


def complete_samples() -> list[ExperimentSample]:
    values: list[ExperimentSample] = []
    index = 0
    for role, actor in (
        (ControlRole.BASELINE, "owner"),
        (ControlRole.CANDIDATE, "other"),
        (ControlRole.NEGATIVE_CONTROL, "anonymous"),
    ):
        for iteration in range(3):
            values.append(sample(f"{role.value}-{iteration}", role, index, actor=actor))
            index += 1
    return values


def stable_roles() -> dict[ControlRole, StabilityReport]:
    return {
        ControlRole.BASELINE: stability(),
        ControlRole.CANDIDATE: stability(),
        ControlRole.NEGATIVE_CONTROL: stability(),
    }


def test_complete_differential_design_is_observed_not_validated() -> None:
    report = assess_differential_design(
        complete_samples(), stability_by_role=stable_roles()
    )

    assert report.ready_for_validation is True
    assert report.status is ClaimStatus.OBSERVED
    assert "does not validate" in report.limitations[0]


def test_missing_negative_control_remains_unknown() -> None:
    samples = [
        value
        for value in complete_samples()
        if value.role is not ControlRole.NEGATIVE_CONTROL
    ]
    stability_values = stable_roles()
    stability_values.pop(ControlRole.NEGATIVE_CONTROL)

    report = assess_differential_design(samples, stability_by_role=stability_values)

    assert report.status is ClaimStatus.UNKNOWN
    assert report.missing_roles == [ControlRole.NEGATIVE_CONTROL]


def test_under_repeated_role_is_reported() -> None:
    samples = [
        value
        for value in complete_samples()
        if value.role is not ControlRole.CANDIDATE
        or value.sample_id.endswith("-0")
    ]
    report = assess_differential_design(samples, stability_by_role=stable_roles())

    assert report.ready_for_validation is False
    assert report.under_repeated_roles == [ControlRole.CANDIDATE]


def test_context_mismatch_blocks_comparison() -> None:
    samples = complete_samples()
    candidate = next(value for value in samples if value.role is ControlRole.CANDIDATE)
    candidate.environment_id = "different-region"

    report = assess_differential_design(samples, stability_by_role=stable_roles())

    assert report.ready_for_validation is False
    assert report.context_mismatches


def test_unstable_role_blocks_validation_readiness() -> None:
    values = stable_roles()
    values[ControlRole.CANDIDATE] = stability(False)

    report = assess_differential_design(complete_samples(), stability_by_role=values)

    assert report.unstable_roles == [ControlRole.CANDIDATE]
    assert report.status is ClaimStatus.UNKNOWN


def test_mutating_sample_requires_state_reset() -> None:
    samples = complete_samples()
    samples[0].mutating = True

    report = assess_differential_design(samples, stability_by_role=stable_roles())

    assert samples[0].sample_id in report.missing_state_resets


def test_state_reset_between_mutation_and_next_sample_satisfies_policy() -> None:
    samples = [
        sample("mutation", ControlRole.BASELINE, 0, mutating=True),
        sample("reset", ControlRole.STATE_RESET, 1),
    ]
    index = 2
    for role in (
        ControlRole.BASELINE,
        ControlRole.CANDIDATE,
        ControlRole.NEGATIVE_CONTROL,
    ):
        existing = 1 if role is ControlRole.BASELINE else 0
        for iteration in range(3 - existing):
            samples.append(sample(f"{role.value}-{iteration}", role, index))
            index += 1

    report = assess_differential_design(samples, stability_by_role=stable_roles())

    assert report.missing_state_resets == []


def test_policy_can_disable_negative_control_requirement() -> None:
    samples = [
        value
        for value in complete_samples()
        if value.role is not ControlRole.NEGATIVE_CONTROL
    ]
    report = assess_differential_design(
        samples,
        policy=DifferentialDesignPolicy(require_negative_control=False),
        stability_by_role={
            ControlRole.BASELINE: stability(),
            ControlRole.CANDIDATE: stability(),
        },
    )

    assert report.ready_for_validation is True
