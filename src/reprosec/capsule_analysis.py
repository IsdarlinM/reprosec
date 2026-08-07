from __future__ import annotations

from collections import deque
from enum import StrEnum
from typing import Sequence

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ManifestChange(StrEnum):
    ADDED = "ADDED"
    REMOVED = "REMOVED"
    MODIFIED = "MODIFIED"
    UNCHANGED = "UNCHANGED"


class CapsuleArtifact(BaseModel):
    model_config = ConfigDict(extra="forbid")

    artifact_id: str
    path: str
    sha256: str
    size_bytes: int = Field(ge=0)
    record_type: str
    references: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    required_for_integrity: bool = False
    contains_sensitive_data: bool = False

    @model_validator(mode="after")
    def validate_hash(self) -> "CapsuleArtifact":
        if len(self.sha256) != 64:
            raise ValueError("sha256 must be a 64-character digest")
        try:
            bytes.fromhex(self.sha256)
        except ValueError as exc:
            raise ValueError("sha256 must be hexadecimal") from exc
        return self


class CapsuleSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid")

    capsule_id: str
    schema_version: str
    artifacts: list[CapsuleArtifact]

    @model_validator(mode="after")
    def unique_artifacts(self) -> "CapsuleSnapshot":
        ids = [item.artifact_id for item in self.artifacts]
        paths = [item.path for item in self.artifacts]
        if len(ids) != len(set(ids)):
            raise ValueError("artifact IDs must be unique")
        if len(paths) != len(set(paths)):
            raise ValueError("artifact paths must be unique")
        return self


class CapsuleArtifactChange(BaseModel):
    model_config = ConfigDict(extra="forbid")

    artifact_id: str
    change: ManifestChange
    before_sha256: str | None = None
    after_sha256: str | None = None
    before_size: int | None = None
    after_size: int | None = None
    changed_fields: list[str] = Field(default_factory=list)


class CapsuleComparison(BaseModel):
    model_config = ConfigDict(extra="forbid")

    before_capsule_id: str
    after_capsule_id: str
    schema_changed: bool
    changes: list[CapsuleArtifactChange]
    summary: dict[str, int]
    findings_created: int = 0
    limitations: list[str] = Field(default_factory=list)


class CapsuleMinimizationPlan(BaseModel):
    model_config = ConfigDict(extra="forbid")

    capsule_id: str
    root_artifact_ids: list[str]
    retained_artifact_ids: list[str]
    removable_artifact_ids: list[str]
    sensitive_retained_artifact_ids: list[str]
    missing_references: dict[str, list[str]] = Field(default_factory=dict)
    deterministic: bool = True
    applied: bool = False
    limitations: list[str] = Field(default_factory=list)


def compare_capsules(
    before: CapsuleSnapshot,
    after: CapsuleSnapshot,
    *,
    include_unchanged: bool = False,
) -> CapsuleComparison:
    old = {item.artifact_id: item for item in before.artifacts}
    new = {item.artifact_id: item for item in after.artifacts}
    changes: list[CapsuleArtifactChange] = []
    for artifact_id in sorted(set(old) | set(new)):
        left = old.get(artifact_id)
        right = new.get(artifact_id)
        if left is None:
            change = ManifestChange.ADDED
            fields = ["artifact"]
        elif right is None:
            change = ManifestChange.REMOVED
            fields = ["artifact"]
        else:
            fields = sorted(
                key
                for key in (
                    "path",
                    "sha256",
                    "size_bytes",
                    "record_type",
                    "references",
                    "evidence_ids",
                    "required_for_integrity",
                    "contains_sensitive_data",
                )
                if getattr(left, key) != getattr(right, key)
            )
            change = ManifestChange.MODIFIED if fields else ManifestChange.UNCHANGED
        if include_unchanged or change is not ManifestChange.UNCHANGED:
            changes.append(
                CapsuleArtifactChange(
                    artifact_id=artifact_id,
                    change=change,
                    before_sha256=left.sha256 if left else None,
                    after_sha256=right.sha256 if right else None,
                    before_size=left.size_bytes if left else None,
                    after_size=right.size_bytes if right else None,
                    changed_fields=fields,
                )
            )
    summary = {
        change.value: sum(item.change is change for item in changes)
        for change in ManifestChange
    }
    return CapsuleComparison(
        before_capsule_id=before.capsule_id,
        after_capsule_id=after.capsule_id,
        schema_changed=before.schema_version != after.schema_version,
        changes=changes,
        summary=summary,
        limitations=[
            "A capsule difference is evidence of changed content, not proof of security impact.",
            "Semantic equivalence may require deterministic assertions and workflow context."
        ],
    )


def plan_minimization(
    snapshot: CapsuleSnapshot,
    *,
    root_artifact_ids: Sequence[str],
) -> CapsuleMinimizationPlan:
    artifacts = {item.artifact_id: item for item in snapshot.artifacts}
    missing_roots = sorted(set(root_artifact_ids) - set(artifacts))
    if missing_roots:
        raise ValueError("unknown root artifact IDs: " + ", ".join(missing_roots))

    retained = {
        item.artifact_id for item in snapshot.artifacts if item.required_for_integrity
    }
    retained.update(root_artifact_ids)
    queue: deque[str] = deque(sorted(retained))
    missing_references: dict[str, list[str]] = {}
    while queue:
        artifact_id = queue.popleft()
        artifact = artifacts[artifact_id]
        unresolved = sorted(set(artifact.references) - set(artifacts))
        if unresolved:
            missing_references[artifact_id] = unresolved
        for reference in sorted(set(artifact.references) & set(artifacts)):
            if reference not in retained:
                retained.add(reference)
                queue.append(reference)

    removable = sorted(set(artifacts) - retained)
    sensitive_retained = sorted(
        artifact_id
        for artifact_id in retained
        if artifacts[artifact_id].contains_sensitive_data
    )
    return CapsuleMinimizationPlan(
        capsule_id=snapshot.capsule_id,
        root_artifact_ids=sorted(set(root_artifact_ids)),
        retained_artifact_ids=sorted(retained),
        removable_artifact_ids=removable,
        sensitive_retained_artifact_ids=sensitive_retained,
        missing_references=missing_references,
        limitations=[
            "The plan is non-mutating and must be reviewed before creating a new capsule.",
            "Required integrity/provenance artifacts are always retained.",
            "Sensitive retained artifacts require redaction review before export."
        ],
    )
