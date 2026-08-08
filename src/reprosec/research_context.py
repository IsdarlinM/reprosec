from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator
from sric.cases import ValidationRecipe
from sric.models import ActionClass


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ScopeSnapshot(BaseModel):
    """Immutable scope facts recorded with a capsule validation attempt."""

    model_config = ConfigDict(extra="forbid")

    snapshot_id: str
    workspace_id: str | None = None
    allowed_hosts: list[str] = Field(default_factory=list)
    allowed_schemes: list[str] = Field(default_factory=lambda: ["https"])
    source: str
    captured_at: datetime = Field(default_factory=utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)


class PolicyDecisionRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    decision_id: str
    action_id: str
    action_class: ActionClass
    allowed: bool
    matched_rule: str
    approval_required: bool = False
    approved_by: str | None = None
    decided_at: datetime = Field(default_factory=utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def destructive_actions_need_approval(self) -> "PolicyDecisionRecord":
        if self.action_class is ActionClass.MUTATING_DESTRUCTIVE:
            if not self.approval_required or not self.approved_by:
                raise ValueError("destructive policy decisions require recorded human approval")
        return self


class ToolProvenanceRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tool: str
    version: str
    component: str
    source_ref: str
    created_at: datetime = Field(default_factory=utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)


class CapsuleResearchContext(BaseModel):
    """Cross-product research metadata stored beside deterministic RCAP evidence."""

    model_config = ConfigDict(extra="forbid")

    sentinel_case_id: str | None = None
    scope_snapshot: ScopeSnapshot | None = None
    policy_decisions: list[PolicyDecisionRecord] = Field(default_factory=list)
    validation_recipes: list[ValidationRecipe] = Field(default_factory=list)
    tool_provenance: list[ToolProvenanceRecord] = Field(default_factory=list)
    counter_evidence_ids: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def recipes_reference_known_policy_decisions(self) -> "CapsuleResearchContext":
        decisions = {item.decision_id for item in self.policy_decisions}
        missing = sorted(
            recipe.policy_decision_id
            for recipe in self.validation_recipes
            if recipe.policy_decision_id and recipe.policy_decision_id not in decisions
        )
        if missing:
            raise ValueError("validation recipes reference unknown policy decisions: " + ", ".join(missing))
        return self

    def sha256(self) -> str:
        payload = self.model_dump(mode="json", exclude_none=True)
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
