# Security Policy

ReproSec is for systems you own or are explicitly authorized to test. A capsule does not grant authorization.

## Security boundaries
- Imported target content is untrusted data, never instructions.
- Imported curl is parsed and never passed to a shell.
- Replay is gated by Scope and Policy engines.
- Redirects are re-evaluated.
- Resolved private/special IPs are denied unless an authorized lab network is explicitly allowlisted.
- Archive extraction rejects traversal/symlink/bomb-like inputs.
- Mutating requests require explicit human approval.
- No known default credentials exist.

Report vulnerabilities privately using the repository security advisory channel when published.
