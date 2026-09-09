from dataclasses import dataclass
from enum import Enum


class Decision(str, Enum):
    ALLOW = "allow"
    DENY = "deny"
    QUARANTINE = "quarantine"
    REDACT = "redact"
    DELAY = "delay"
    SANDBOX = "sandbox"
    REDUCE_SCOPE = "reduce-scope"
    ESCALATE = "escalate"


class Code(str, Enum):
    NO_HANDLE = "EF-002"
    HANDLE_ALREADY_USED = "EF-005"
    REPLAY_DETECTED = "EF-006"
    MALFORMED_ACT = "EF-010"
    INVALID_HANDLE = "EF-011"
    EXPIRED_HANDLE = "EF-012"
    RECEIPT_MISSING = "EF-013"
    HCAD_MISMATCH = "EF-020"
    OUTPUT_SUBSTITUTION = "EF-021"
    ALF_MISMATCH = "EF-022"
    RBD_MISMATCH = "EF-023"
    PROVENANCE_FAILURE = "EF-024"
    FACTUAL_SUPPORT_FAILURE = "EF-025"
    RCAE_MISMATCH = "EF-026"
    SIMULATION_FAILURE = "EF-027"
    RECIPIENT_MISMATCH = "EF-028"
    PURPOSE_MISMATCH = "EF-029"
    JURISDICTION_MISMATCH = "EF-030"
    DATA_CLASS_MISMATCH = "EF-031"
    POLICY_EPOCH_MISMATCH = "EF-032"
    REVOCATION_EPOCH_MISMATCH = "EF-033"
    SINK_MISMATCH = "EF-040"
    CONSEQUENCE_MISMATCH = "EF-041"
    HUMAN_APPROVAL_REQUIRED = "EF-070"
    REDACTION_REQUIRED = "EF-071"
    SANDBOX_REQUIRED = "EF-072"
    DELAY_REQUIRED = "EF-073"
    SCOPE_REDUCTION_REQUIRED = "EF-074"
    QUARANTINE_REQUIRED = "EF-075"
    FAIL_CLOSED = "EF-080"
    EFFECT_RESULT_UNKNOWN = "EF-090"


@dataclass
class FinalityError(Exception):
    code: Code
    message: str
    decision: Decision = Decision.DENY
    retryable: bool = False

    def __str__(self) -> str:
        return f"{self.code.value} {self.decision.value}: {self.message}"

