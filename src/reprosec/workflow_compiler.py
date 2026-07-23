from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.parse import urlsplit

from .capsule import add_extractor, add_workflow_step
from .models import ExtractorSpec, RequestRecord, ResponseRecord, WorkflowStep

ID_KEYS = {"id", "resource_id", "document_id", "user_id", "tenant_id", "organization_id"}


class WorkflowCompiler:
    """Deterministic candidate workflow compiler. Output remains HYPOTHESIS until replay proves it."""
    def compile(self, capsule: Path) -> dict[str, object]:
        requests=[RequestRecord.model_validate_json(p.read_text()) for p in sorted((capsule/"requests").glob("*.json"))]
        responses=[ResponseRecord.model_validate_json(p.read_text()) for p in sorted((capsule/"responses").glob("*.json"))]
        by_req={r.request_id:r for r in responses}; generated_steps=[]; generated_extractors=[]; known_values:dict[str,tuple[str,str]]={}
        for res in responses:
            if not res.body: continue
            try:data=json.loads(res.body)
            except json.JSONDecodeError: continue
            if isinstance(data,dict):
                for key,val in data.items():
                    if key.casefold() in ID_KEYS and isinstance(val,(str,int)):
                        name=f"auto_{key}"; known_values[str(val)]=(name,res.response_id)
                        ext=ExtractorSpec(response_id=res.response_id,name=name,kind="jsonpath",selector=f"$.{key}")
                        add_extractor(capsule,ext); generated_extractors.append(ext.extractor_id)
        prior_steps:dict[str,str]={}
        for req in requests:
            deps=[]
            haystack=req.url+"\n"+(req.body or "")
            for value,(name,response_id) in known_values.items():
                if value in haystack:
                    source_req=by_req.get(next((rid for rid,r in by_req.items() if r.response_id==response_id),""))
                    if source_req and source_req.request_id in prior_steps: deps.append(prior_steps[source_req.request_id])
            step=WorkflowStep(actor=req.actor_id or "Actor",actor_id=req.actor_id,session_id=req.session_id,request_id=req.request_id,depends_on=sorted(set(deps)),state="HYPOTHESIS")
            add_workflow_step(capsule,step);prior_steps[req.request_id]=step.step_id;generated_steps.append(step.step_id)
        return {"status":"HYPOTHESIS","steps":generated_steps,"extractors":generated_extractors,"deterministic_replay_required":True}
