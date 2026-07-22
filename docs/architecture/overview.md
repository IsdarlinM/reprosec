# Architecture

ReproSec consumes SRIC models/policy primitives rather than reimplementing them. Imports normalize artifacts into request/response/workflow records. Packing creates an integrity manifest. Replay requires deterministic Scope and Policy decisions before the HTTP executor runs. Assertions operate on stored observed responses, never on model opinion.
