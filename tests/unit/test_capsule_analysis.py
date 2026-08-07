import hashlib

import pytest

from reprosec.capsule_analysis import (
    CapsuleArtifact,
    CapsuleSnapshot,
    ManifestChange,
    compare_capsules,
    plan_minimization,
)


def artifact(
    artifact_id: str,
    content: bytes,
    *,
    references: list[str] | None = None,
    required: bool = False,
    sensitive: bool = False,
) -> CapsuleArtifact:
    return CapsuleArtifact(
        artifact_id=artifact_id,
        path=f"records/{artifact_id}.json",
        sha256=hashlib.sha256(content).hexdigest(),
        size_bytes=len(content),
        record_type="record",
        references=references or [],
        evidence_ids=[f"E-{artifact_id}"],
        required_for_integrity=required,
        contains_sensitive_data=sensitive,
    )


def snapshot(capsule_id: str, artifacts: list[CapsuleArtifact]) -> CapsuleSnapshot:
    return CapsuleSnapshot(capsule_id=capsule_id, schema_version="0.3", artifacts=artifacts)


def test_capsule_comparison_reports_content_changes_without_findings() -> None:
    before = snapshot("before", [artifact("A", b"one")])
    after = snapshot("after", [artifact("A", b"two"), artifact("B", b"new")])
    report = compare_capsules(before, after)
    changes = {item.artifact_id: item.change for item in report.changes}
    assert changes == {"A": ManifestChange.MODIFIED, "B": ManifestChange.ADDED}
    assert report.findings_created == 0
    assert "not proof of security impact" in report.limitations[0]


def test_minimization_retains_transitive_references_and_integrity() -> None:
    value = snapshot(
        "capsule",
        [
            artifact("manifest", b"manifest", required=True),
            artifact("request", b"request", references=["response"]),
            artifact("response", b"response", references=["evidence"], sensitive=True),
            artifact("evidence", b"evidence"),
            artifact("unused", b"unused"),
        ],
    )
    plan = plan_minimization(value, root_artifact_ids=["request"])
    assert plan.retained_artifact_ids == ["evidence", "manifest", "request", "response"]
    assert plan.removable_artifact_ids == ["unused"]
    assert plan.sensitive_retained_artifact_ids == ["response"]
    assert plan.applied is False


def test_minimization_requires_at_least_one_root() -> None:
    value = snapshot("capsule", [artifact("manifest", b"manifest", required=True)])
    with pytest.raises(ValueError, match="at least one root"):
        plan_minimization(value, root_artifact_ids=[])


def test_missing_references_are_reported_not_silently_removed() -> None:
    value = snapshot("capsule", [artifact("request", b"request", references=["missing"])])
    plan = plan_minimization(value, root_artifact_ids=["request"])
    assert plan.missing_references == {"request": ["missing"]}


def test_unknown_minimization_root_is_rejected() -> None:
    value = snapshot("capsule", [artifact("request", b"request")])
    with pytest.raises(ValueError, match="unknown root"):
        plan_minimization(value, root_artifact_ids=["missing"])


def test_duplicate_artifact_ids_are_rejected() -> None:
    duplicate = artifact("A", b"one")
    with pytest.raises(ValueError, match="IDs must be unique"):
        snapshot("capsule", [duplicate, duplicate])
