# Replay stability and false-positive control

A single response is not sufficient to establish that a replay assertion is deterministic. Dynamic IDs, timestamps, tracing headers, caches, transient failures, A/B tests and eventual consistency can produce apparent differences without a security-relevant state change.

ReproSec 0.4.1 provides `reprosec.stability.analyze_stability` for repeated observations.

## Rules

- At least three observations are required by default.
- Status, retained headers and normalized body content contribute to the response fingerprint.
- Only explicitly configured fields are ignored.
- A small built-in header list removes transport-generated values such as `Date`, `X-Request-ID` and tracing headers.
- `Set-Cookie`, authorization-relevant headers and application fields are not ignored by default.
- JSON paths can be ignored only through an explicit `StabilityPolicy`.
- Regex substitutions are explicit and remain visible in the validation configuration.
- The dominant normalized fingerprint and total sample count produce a flakiness score.
- A report whose flakiness exceeds policy cannot support a `VALIDATED` finding.

## Example

```python
from reprosec.stability import ReplayObservation, StabilityPolicy, analyze_stability

observations = [
    ReplayObservation(
        observation_id="run-1",
        status_code=200,
        headers={"content-type": "application/json"},
        body='{"allowed":false,"request_id":"a"}',
    ),
    ReplayObservation(
        observation_id="run-2",
        status_code=200,
        headers={"content-type": "application/json"},
        body='{"allowed":false,"request_id":"b"}',
    ),
    ReplayObservation(
        observation_id="run-3",
        status_code=200,
        headers={"content-type": "application/json"},
        body='{"allowed":false,"request_id":"c"}',
    ),
]

report = analyze_stability(
    observations,
    StabilityPolicy(ignored_json_paths={"request_id"}),
)
assert report.deterministic
```

Ignoring a field must be justified in the research notebook. A normalization rule must never remove the exact property being tested, such as an ownership identifier, authorization decision, tenant ID, role, revocation state or protected response content.
