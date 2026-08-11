from __future__ import annotations

import hashlib
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path

from .capsule import build_manifest, initialize_directory, pack, verify_directory, verify_archive
from .models import ActorRecord, CapsuleMetadata, RequestRecord, SessionRecord, WorkflowStep
from .capsule import add_actor, add_request, add_session, add_workflow_step

BASE_REQUIRED_DIRS = {
    "actors", "environment", "workflow", "requests", "responses", "evidence", "assertions",
    "extractors", "timeline", "redactions", "provenance", "signatures", "reports",
}
RCAP03_REQUIRED_DIRS = BASE_REQUIRED_DIRS | {"sessions", "network", "validation"}


@dataclass(frozen=True)
class ConformanceResult:
    conformant: bool
    schema_version: str | None
    checks: dict[str, bool]
    errors: list[str]


def check_conformance(root: Path) -> ConformanceResult:
    errors=[];checks={}
    try:
        meta=CapsuleMetadata.model_validate_json((root/"capsule.json").read_text(encoding="utf-8"));schema=meta.schema_version;checks["metadata_valid"]=True
    except Exception as exc:
        schema=None;checks["metadata_valid"]=False;errors.append(f"metadata invalid: {exc}")
    required=RCAP03_REQUIRED_DIRS if schema=="0.3" else BASE_REQUIRED_DIRS
    missing=sorted(name for name in required if not (root/name).is_dir());checks["required_layout"]=not missing
    if missing:errors.append(f"missing required directories: {', '.join(missing)}")
    integrity=verify_directory(root);checks["manifest_integrity"]=not integrity;errors.extend(integrity)
    deterministic=False
    if checks["metadata_valid"] and checks["required_layout"]:
        try:
            with tempfile.TemporaryDirectory() as td:
                first=Path(td)/"a.rcap";second=Path(td)/"b.rcap";pack(root,first);pack(root,second);deterministic=hashlib.sha256(first.read_bytes()).digest()==hashlib.sha256(second.read_bytes()).digest()
        except Exception as exc:errors.append(f"determinism check failed: {exc}")
    checks["deterministic_pack"]=deterministic
    if not deterministic:errors.append("binary deterministic pack check failed")
    return ConformanceResult(not errors,schema,checks,errors)


def run_public_suite() -> dict[str, object]:
    """Generate a self-contained conformance matrix; no live targets or credentials are used."""
    cases=[]
    with tempfile.TemporaryDirectory() as td:
        base=Path(td)
        minimal=base/"minimal";initialize_directory(minimal,"minimal");build_manifest(minimal)
        cases.append({"name":"valid-minimal-0.3","expected":True,"actual":check_conformance(minimal).conformant})
        multi=base/"multi";initialize_directory(multi,"multi");a=ActorRecord(label="A");b=ActorRecord(label="B");add_actor(multi,a);add_actor(multi,b);sa=SessionRecord(actor_id=a.actor_id,label="A session");add_session(multi,sa);req=RequestRecord(method="GET",url="https://example.invalid/resource/1",actor_id=a.actor_id,session_id=sa.session_id);add_request(multi,req);add_workflow_step(multi,WorkflowStep(actor="A",actor_id=a.actor_id,session_id=sa.session_id,request_id=req.request_id));build_manifest(multi)
        cases.append({"name":"valid-multi-actor-0.3","expected":True,"actual":check_conformance(multi).conformant})
        broken=base/"broken";initialize_directory(broken,"broken");(broken/"evidence").rmdir();build_manifest(broken)
        cases.append({"name":"invalid-missing-evidence-dir","expected":False,"actual":check_conformance(broken).conformant})
        traversal=base/"traversal.rcap"
        with zipfile.ZipFile(traversal,"w") as zf:zf.writestr("../escape","x")
        try:verify_archive(traversal);actual=True
        except ValueError:actual=False
        cases.append({"name":"invalid-path-traversal","expected":False,"actual":actual})
        malformed=base/"malformed";initialize_directory(malformed,"malformed");(malformed/"manifest.json").write_text("{",encoding="utf-8")
        cases.append({"name":"invalid-malformed-manifest","expected":False,"actual":check_conformance(malformed).conformant})
    passed=sum(c["expected"]==c["actual"] for c in cases)
    return {"suite":"RCAP-CONFORMANCE-0.3","passed":passed,"total":len(cases),"cases":cases}
