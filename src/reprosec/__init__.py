"""ReproSec Capsule reference implementation."""

from .capsule_analysis import (
    CapsuleArtifact,
    CapsuleArtifactChange,
    CapsuleComparison,
    CapsuleMinimizationPlan,
    CapsuleSnapshot,
    ManifestChange,
    compare_capsules,
    plan_minimization,
)
from .controls import (
    ControlRole,
    DifferentialDesignPolicy,
    DifferentialDesignReport,
    ExperimentSample,
    assess_differential_design,
)
from .protocols import (
    Direction,
    GraphQLOperationKind,
    GraphQLOperationRecord,
    GrpcMessageRecord,
    ProtocolEvidenceRecord,
    ProtocolKind,
    WebSocketFrameRecord,
    WebSocketOpcode,
)
from .stability import ReplayObservation, StabilityPolicy, StabilityReport, analyze_stability

__all__ = [
    "CapsuleArtifact",
    "CapsuleArtifactChange",
    "CapsuleComparison",
    "CapsuleMinimizationPlan",
    "CapsuleSnapshot",
    "ControlRole",
    "DifferentialDesignPolicy",
    "DifferentialDesignReport",
    "Direction",
    "ExperimentSample",
    "GraphQLOperationKind",
    "GraphQLOperationRecord",
    "GrpcMessageRecord",
    "ManifestChange",
    "ProtocolEvidenceRecord",
    "ProtocolKind",
    "ReplayObservation",
    "StabilityPolicy",
    "StabilityReport",
    "WebSocketFrameRecord",
    "WebSocketOpcode",
    "analyze_stability",
    "assess_differential_design",
    "compare_capsules",
    "plan_minimization",
]
__version__ = "0.4.1"
