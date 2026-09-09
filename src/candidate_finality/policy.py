from __future__ import annotations

import time
from dataclasses import dataclass

from .errors import Code, Decision, FinalityError
from .models import CandidateAct, EpochState, ValidationContext


RISK_ORDER = {"LOW": 0, "MEDIUM": 1, "HIGH": 2, "CRITICAL": 3}


@dataclass
class FinalityPolicy:
    epochs: EpochState
    permitted_systems: set[str]
    permitted_models: set[str]
    permitted_tools: set[str]
    minimum_human_approvals: dict[str, int]

    def validate(self, act: CandidateAct, ctx: ValidationContext) -> dict[str, bool]:
        r = act.request
        if r.originating_system_id not in self.permitted_systems or r.model_id not in self.permitted_models:
            raise FinalityError(Code.PROVENANCE_FAILURE, "originating system or model is not permitted")
        if r.intended_tool not in self.permitted_tools:
            raise FinalityError(Code.CONSEQUENCE_MISMATCH, "tool is not permitted")
        if r.alf_id not in ctx.approved_alf_ids:
            raise FinalityError(Code.ALF_MISMATCH, "algorithmic logic fingerprint is not approved")
        if not ctx.behavior_matches:
            raise FinalityError(Code.RBD_MISMATCH, "runtime behavior does not match the approved envelope")
        if not ctx.provenance_valid or not ctx.provenance_fresh or not ctx.evidence_refs:
            raise FinalityError(Code.PROVENANCE_FAILURE, "provenance is missing, stale, or invalid")
        if not ctx.factual_claims_verified:
            raise FinalityError(Code.FACTUAL_SUPPORT_FAILURE, "factual claim units lack required support", Decision.QUARANTINE)
        if not ctx.consequence_simulation_safe:
            raise FinalityError(Code.SIMULATION_FAILURE, "predicted consequence is outside the safe envelope")
        if r.intended_recipient != ctx.permitted_recipient:
            raise FinalityError(Code.RECIPIENT_MISMATCH, "recipient is outside RCAE")
        if r.purpose != ctx.permitted_purpose:
            raise FinalityError(Code.PURPOSE_MISMATCH, "purpose is outside RCAE")
        if r.jurisdiction != ctx.permitted_jurisdiction:
            raise FinalityError(Code.JURISDICTION_MISMATCH, "jurisdiction is outside RCAE")
        if r.data_class != ctx.permitted_data_class:
            if r.data_class == "SENSITIVE" and not ctx.redaction_completed:
                raise FinalityError(Code.REDACTION_REQUIRED, "sensitive output requires redaction", Decision.REDACT)
            raise FinalityError(Code.DATA_CLASS_MISMATCH, "data class is outside RCAE")
        if r.requested_consequence != ctx.permitted_consequence_type:
            raise FinalityError(Code.CONSEQUENCE_MISMATCH, "consequence type is outside RCAE")
        if RISK_ORDER.get(r.risk_class, 99) > RISK_ORDER.get(ctx.max_risk_class, -1):
            raise FinalityError(Code.SANDBOX_REQUIRED, "risk exceeds RCAE", Decision.SANDBOX)
        if ctx.requested_scope_units > ctx.permitted_scope_units:
            raise FinalityError(Code.SCOPE_REDUCTION_REQUIRED, "requested scope exceeds RCAE", Decision.REDUCE_SCOPE)
        required = self.minimum_human_approvals.get(r.risk_class, 0)
        if len(set(ctx.human_approval_ids)) < required:
            raise FinalityError(Code.HUMAN_APPROVAL_REQUIRED, "additional protected approval is required", Decision.ESCALATE)
        if ctx.delay_until_epoch_ms and int(time.time() * 1000) < ctx.delay_until_epoch_ms:
            raise FinalityError(Code.DELAY_REQUIRED, "act is intentionally delayed", Decision.DELAY, True)
        return {
            "alf_valid": True, "rbd_valid": True, "opc_valid": True,
            "fcu_valid": True, "rcae_valid": True, "simulation_valid": True,
            "recipient_valid": True, "purpose_valid": True,
            "jurisdiction_valid": True, "data_class_valid": True,
            "consequence_valid": True, "epoch_valid": True,
            "sink_binding_valid": True, "approval_valid": True,
        }

