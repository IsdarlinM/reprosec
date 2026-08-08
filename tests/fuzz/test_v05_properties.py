from __future__ import annotations

from hypothesis import given, strategies as st
from pydantic import ValidationError
from sric.models import ActionClass

from reprosec.research_context import CapsuleResearchContext, PolicyDecisionRecord, ScopeSnapshot


_host = st.from_regex(r"[a-z0-9]{1,12}\.example\.test", fullmatch=True)


@given(st.lists(_host, unique=True, max_size=12))
def test_generated_scope_context_digest_is_stable(hosts: list[str]) -> None:
    context = CapsuleResearchContext(
        sentinel_case_id="case-generated",
        scope_snapshot=ScopeSnapshot(
            snapshot_id="scope-generated",
            allowed_hosts=hosts,
            source="property-test",
        ),
    )
    assert context.sha256() == context.sha256()
    assert len(context.sha256()) == 64


@given(st.booleans())
def test_destructive_decisions_never_bypass_recorded_approval(allowed: bool) -> None:
    try:
        PolicyDecisionRecord(
            decision_id="decision-generated",
            action_id="action-generated",
            action_class=ActionClass.MUTATING_DESTRUCTIVE,
            allowed=allowed,
            matched_rule="generated",
            approval_required=True,
            approved_by=None,
        )
    except ValidationError:
        return
    raise AssertionError("destructive decision accepted without recorded approver")
