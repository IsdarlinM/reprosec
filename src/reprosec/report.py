from __future__ import annotations
import html
import json
from pathlib import Path
from .models import CapsuleMetadata


def render_markdown(root: Path) -> str:
    meta = CapsuleMetadata.model_validate_json((root / "capsule.json").read_text(encoding="utf-8"))
    reqs = list((root / "requests").glob("*.json"))
    res = list((root / "responses").glob("*.json"))
    assertions = list((root / "assertions").glob("*.json"))
    return f"""# {meta.title}\n\n## Summary\nReproducible Security Capsule `{meta.capsule_id}`.\n\n## Scope\nDefined by the operator at replay time; the capsule itself does not grant authorization.\n\n## Evidence\n- Requests: {len(reqs)}\n- Responses: {len(res)}\n- Assertions: {len(assertions)}\n\n## Facts / Inferences / Hypotheses\nThis report preserves capsule state labels. AI-generated candidates must not be represented as validated findings without deterministic replay/assertion evidence.\n\n## Reproduction\nUse `reprosec verify` before replay. Replay requires explicit scope policy and approval for mutating methods.\n\n## Limitations\nA capsule proves only the captured/replayed behavior and stated assertions; it does not establish business impact by itself.\n"""


def write_report(root: Path, output: Path, fmt: str) -> Path:
    md = render_markdown(root)
    if fmt == "md":
        output.write_text(md, encoding="utf-8")
    elif fmt == "json":
        output.write_text(json.dumps({"report_markdown": md}, indent=2), encoding="utf-8")
    elif fmt == "html":
        output.write_text(
            "<!doctype html><meta charset=utf-8><title>ReproSec Report</title><pre>"
            + html.escape(md)
            + "</pre>",
            encoding="utf-8",
        )
    else:
        raise ValueError("format must be md, json or html")
    return output
