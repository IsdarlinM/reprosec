from __future__ import annotations

import pytest
from pydantic import ValidationError
from sric.cases import ValidationRecipe
from sric.models import ActionClass

from reprosec.research_context import (
    CapsuleResearchContext,
    PolicyDecisionRecord,
    ScopeSnapshot,
    ToolProvenanceRecord,
)


def test_context_hash_is_stable() -> None:
    context = CapsuleResearchContext(
        sentinel_case_id="case-1",
        scope_snapshot=ScopeSnapshot(
            snapshot_id="scope-1",
            allowed_hosts=["example.test"],
            source="program-policy",
        ),
        tool_provenance=[
            ToolProvenanceRecord(
                tool="authtwin", version="0.5.0", component="validator", source_ref="claim:1"
            )
        ],
    )
    assert context.sha256() == context.sha256()
    assert len(context.sha256()) == 64


def test_recipe_policy_decision_must_exist() -> None:
    recipe = ValidationRecipe(
        recipe_id="r1",
        artifact_id="a1",
        action_class=ActionClass.READ_ONLY_SAFE,
        target="https://example.test/resource/1",
        method="GET",
        deterministic_success="status=200",
        policy_decision_id="policy-missing",
    )
    with pytest.raises(ValidationError):
        CapsuleResearchContext(validation_recipes=[recipe])


def test_destructive_decision_requires_recorded_approval() -> None:
    with pytest.raises(ValidationError):
        PolicyDecisionRecord(
            decision_id="d1",
            action_id="a1",
            action_class=ActionClass.MUTATING_DESTRUCTIVE,
            allowed=True,
            matched_rule="authorized-lab",
            approval_required=True,
        )
