from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def iso_z(value: datetime) -> str:
    if value.tzinfo is None:
        raise ValueError("timestamp must be timezone-aware")
    return value.astimezone(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


@dataclass(frozen=True)
class EpochState:
    policy_epoch: int
    revocation_epoch: int

    def to_dict(self) -> dict[str, int]:
        return {"policyEpoch": self.policy_epoch, "revocationEpoch": self.revocation_epoch}


@dataclass(frozen=True)
class CandidateActRequest:
    output: str
    originating_system_id: str
    model_id: str
    workflow_id: str
    intended_recipient: str
    intended_tool: str
    intended_sink_id: str
    purpose: str
    jurisdiction: str
    data_class: str
    risk_class: str
    requested_consequence: str
    alf_id: str


@dataclass(frozen=True)
class CandidateAct:
    act_id: str
    request: CandidateActRequest
    output_hash: str
    timestamp: datetime
    status: str = "non-effective"

    def to_dict(self) -> dict[str, Any]:
        r = self.request
        return {
            "actId": self.act_id, "outputHash": self.output_hash,
            "originatingSystemId": r.originating_system_id, "modelId": r.model_id,
            "workflowId": r.workflow_id, "intendedRecipient": r.intended_recipient,
            "intendedTool": r.intended_tool, "intendedSinkId": r.intended_sink_id,
            "purpose": r.purpose, "jurisdiction": r.jurisdiction,
            "dataClass": r.data_class, "riskClass": r.risk_class,
            "requestedConsequence": r.requested_consequence,
            "timestamp": iso_z(self.timestamp), "alfId": r.alf_id, "status": self.status,
        }


@dataclass(frozen=True)
class ValidationContext:
    rbd_id: str
    opc_id: str
    rcae_id: str
    approved_alf_ids: frozenset[str]
    behavior_matches: bool
    provenance_valid: bool
    provenance_fresh: bool
    factual_claims_verified: bool
    consequence_simulation_safe: bool
    evidence_refs: tuple[str, ...]
    permitted_recipient: str
    permitted_purpose: str
    permitted_jurisdiction: str
    permitted_data_class: str
    permitted_consequence_type: str
    max_risk_class: str
    human_approval_ids: tuple[str, ...] = ()
    redaction_completed: bool = False
    sandbox_requested: bool = False
    delay_until_epoch_ms: int = 0
    requested_scope_units: int = 1
    permitted_scope_units: int = 1
    reversible: bool = True
    canary: bool = False


@dataclass(frozen=True)
class HCAD:
    hcad_id: str
    act_id: str
    output_hash: str
    candidate_act_digest: str
    originating_system_id: str
    alf_id: str
    rbd_id: str
    opc_id: str
    rcae_id: str
    epochs: EpochState
    finality_sink_id: str
    recipient: str
    purpose: str
    jurisdiction: str
    risk_class: str
    timestamp: datetime
    nonce: str
    evidence_refs: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "hcadId": self.hcad_id, "actId": self.act_id, "outputHash": self.output_hash,
            "candidateActDigest": self.candidate_act_digest,
            "originatingSystemId": self.originating_system_id, "alfId": self.alf_id,
            "rbdId": self.rbd_id, "opcId": self.opc_id, "rcaeId": self.rcae_id,
            **self.epochs.to_dict(), "finalitySinkId": self.finality_sink_id,
            "recipient": self.recipient, "purpose": self.purpose,
            "jurisdiction": self.jurisdiction, "riskClass": self.risk_class,
            "timestamp": iso_z(self.timestamp), "nonce": self.nonce,
            "evidenceRefs": list(self.evidence_refs),
        }


@dataclass(frozen=True)
class ValidationReceipt:
    receipt_id: str
    act_id: str
    hcad_digest: str
    rcae_digest: str
    predicates: dict[str, bool]
    simulation_digest: str
    decision: str
    issued_at: datetime
    key_id: str
    signature: str = ""

    def unsigned_dict(self) -> dict[str, Any]:
        return {
            "receiptId": self.receipt_id, "actId": self.act_id,
            "hcadDigest": self.hcad_digest, "rcaeDigest": self.rcae_digest,
            "predicates": dict(sorted(self.predicates.items())),
            "simulationDigest": self.simulation_digest, "decision": self.decision,
            "issuedAt": iso_z(self.issued_at),
            "protector": {"type": "HMAC-SHA-256-REFERENCE", "keyId": self.key_id},
        }

    def to_dict(self) -> dict[str, Any]:
        value = self.unsigned_dict(); value["protector"]["signature"] = self.signature
        return value


@dataclass(frozen=True)
class ExecutionHandle:
    handle_id: str
    act_id: str
    hcad_digest: str
    validation_receipt_digest: str
    sink_id: str
    hardware_bound_sink_id: str
    permitted_recipient: str
    permitted_purpose: str
    permitted_jurisdiction: str
    permitted_data_class: str
    permitted_consequence_type: str
    rcae_digest: str
    epochs: EpochState
    nonce: str
    issued_at: datetime
    expires_at: datetime
    execution_material_hint: str
    key_id: str
    one_time_use: bool = True
    signature: str = ""

    def unsigned_dict(self) -> dict[str, Any]:
        return {
            "handleId": self.handle_id, "actId": self.act_id,
            "hcadDigest": self.hcad_digest,
            "validationReceiptDigest": self.validation_receipt_digest,
            "sinkId": self.sink_id, "hardwareBoundSinkId": self.hardware_bound_sink_id,
            "permittedRecipient": self.permitted_recipient,
            "permittedPurpose": self.permitted_purpose,
            "permittedJurisdiction": self.permitted_jurisdiction,
            "permittedDataClass": self.permitted_data_class,
            "permittedConsequenceType": self.permitted_consequence_type,
            "rcaeDigest": self.rcae_digest, **self.epochs.to_dict(), "nonce": self.nonce,
            "issuedAt": iso_z(self.issued_at), "expiresAt": iso_z(self.expires_at),
            "oneTimeUse": self.one_time_use,
            "executionMaterialHint": self.execution_material_hint,
            "protector": {"type": "HMAC-SHA-256-REFERENCE", "keyId": self.key_id},
        }

    def to_dict(self) -> dict[str, Any]:
        value = self.unsigned_dict(); value["protector"]["signature"] = self.signature
        return value
