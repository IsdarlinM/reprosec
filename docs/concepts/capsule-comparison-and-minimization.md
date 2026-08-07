# Capsule comparison and minimization

ReproSec 0.4.1 can compare two deterministic capsule artifact snapshots and produce a non-mutating minimization plan.

## Comparison

Comparison reports added, removed, modified and optionally unchanged artifacts using IDs, paths, hashes, sizes, references and evidence metadata. It creates no findings and does not infer security impact.

## Minimization

A minimization plan starts from explicitly selected root artifacts and retains:

- all transitive references;
- artifacts marked required for integrity or provenance;
- sensitive retained artifacts, which are surfaced for redaction review.

Missing references are reported instead of silently discarded. The plan is never applied automatically.

CLI:

```bash
reprosec capsule-analysis compare before.json after.json
reprosec capsule-analysis minimize-plan snapshot.json --root-artifact request-1
```

Loopback API:

```text
POST /api/v1/capsule-analysis/compare
POST /api/v1/capsule-analysis/minimize-plan
```

Run the extended API with:

```bash
python -m uvicorn reprosec.api_vnext:create_app --factory --host 127.0.0.1 --port 8763
```
