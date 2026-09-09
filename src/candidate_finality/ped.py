from __future__ import annotations

import secrets
import uuid
from dataclasses import replace
from datetime import timedelta
from typing import Callable

from .canonical import digest_object, rcae_projection, sha256_hex
from .crypto import Authenticator
from .errors import Code, Decision, FinalityError
from .models import (
    CandidateAct, CandidateActRequest, ExecutionHandle, HCAD,
    ValidationContext, ValidationReceipt, utc_now,
)
from .policy import FinalityPolicy
from .store import SQLiteFinalityStore


class ProtectedEnforcementDomain:
    def __init__(self, policy: FinalityPolicy, store: SQLiteFinalityStore,
                 authenticator: Authenticator, ttl_seconds: float = 10.0,
                 hardware_bound_sink_id: str = "software-emulation-only",
                 clock: Callable = utc_now) -> None:
        self.policy = policy
        self.store = store
        self.authenticator = authenticator
        self.ttl_seconds = ttl_seconds
        self.hardware_bound_sink_id = hardware_bound_sink_id
        self.clock = clock

    def prepare(self, request: CandidateActRequest) -> CandidateAct:
        required = (
            request.output, request.originating_system_id, request.model_id,
            request.workflow_id, request.intended_recipient, request.intended_tool,
            request.intended_sink_id, request.purpose, request.jurisdiction,
            request.data_class, request.risk_class, request.requested_consequence,
            request.alf_id,
        )
        if any(not isinstance(value, str) or not value for value in required):
            raise FinalityError(Code.MALFORMED_ACT, "required Candidate Act field is empty")
        return CandidateAct(
            act_id=str(uuid.uuid4()), request=request,
            output_hash=sha256_hex(request.output), timestamp=self.clock(),
        )

    def validate_and_issue(self, act: CandidateAct, ctx: ValidationContext):
        if act.status != "non-effective" or sha256_hex(act.request.output) != act.output_hash:
            raise FinalityError(Code.OUTPUT_SUBSTITUTION, "Candidate Act output or status changed before validation")
        predicates = self.policy.validate(act, ctx)
        now = self.clock()
        hcad = HCAD(
            hcad_id=str(uuid.uuid4()), act_id=act.act_id, output_hash=act.output_hash,
            candidate_act_digest=digest_object(act.to_dict()),
            originating_system_id=act.request.originating_system_id,
            alf_id=act.request.alf_id, rbd_id=ctx.rbd_id, opc_id=ctx.opc_id,
            rcae_id=ctx.rcae_id, epochs=self.policy.epochs,
            finality_sink_id=act.request.intended_sink_id,
            recipient=act.request.intended_recipient, purpose=act.request.purpose,
            jurisdiction=act.request.jurisdiction, risk_class=act.request.risk_class,
            timestamp=now, nonce=secrets.token_urlsafe(24), evidence_refs=ctx.evidence_refs,
        )
        hcad_digest = digest_object(hcad.to_dict())
        rcae_digest = digest_object(rcae_projection(ctx))
        simulation_digest = digest_object({
            "actId": act.act_id, "consequence": act.request.requested_consequence,
            "safe": ctx.consequence_simulation_safe, "reversible": ctx.reversible,
            "canary": ctx.canary, "scopeUnits": ctx.requested_scope_units,
        })
        receipt = ValidationReceipt(
            receipt_id=str(uuid.uuid4()), act_id=act.act_id,
            hcad_digest=hcad_digest, rcae_digest=rcae_digest,
            predicates=predicates, simulation_digest=simulation_digest,
            decision=Decision.ALLOW.value, issued_at=now, key_id=self.authenticator.key_id,
        )
        receipt = replace(receipt, signature=self.authenticator.sign(receipt.unsigned_dict()))
        self.store.commit_receipt(receipt)
        receipt_digest = digest_object(receipt.to_dict())

        handle_id = str(uuid.uuid4())
        material = self.authenticator.sign({
            "handleId": handle_id, "actId": act.act_id,
            "sinkId": act.request.intended_sink_id,
        })
        handle = ExecutionHandle(
            handle_id=handle_id, act_id=act.act_id, hcad_digest=hcad_digest,
            validation_receipt_digest=receipt_digest,
            sink_id=act.request.intended_sink_id,
            hardware_bound_sink_id=self.hardware_bound_sink_id,
            permitted_recipient=ctx.permitted_recipient,
            permitted_purpose=ctx.permitted_purpose,
            permitted_jurisdiction=ctx.permitted_jurisdiction,
            permitted_data_class=ctx.permitted_data_class,
            permitted_consequence_type=ctx.permitted_consequence_type,
            rcae_digest=rcae_digest, epochs=self.policy.epochs, nonce=hcad.nonce,
            issued_at=now, expires_at=now + timedelta(seconds=self.ttl_seconds),
            execution_material_hint=sha256_hex(material), key_id=self.authenticator.key_id,
        )
        handle = replace(handle, signature=self.authenticator.sign(handle.unsigned_dict()))
        self.store.register_handle(handle, receipt.receipt_id)
        return hcad, receipt, handle
