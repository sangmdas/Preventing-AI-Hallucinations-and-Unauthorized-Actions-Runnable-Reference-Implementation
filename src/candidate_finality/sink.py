from __future__ import annotations

from datetime import datetime, timezone
from typing import Callable

from .canonical import digest_object, sha256_hex
from .crypto import Authenticator
from .effects import DefiniteEffectFailure, EffectAdapter, UnknownEffectResult
from .errors import Code, FinalityError
from .models import CandidateAct, CandidateActRequest, EpochState, ExecutionHandle, HCAD
from .store import SQLiteFinalityStore


class FinalitySink:
    def __init__(self, sink_id: str, store: SQLiteFinalityStore,
                 authenticator: Authenticator, effect_adapter: EffectAdapter,
                 current_epochs: Callable[[], EpochState]) -> None:
        self.sink_id = sink_id
        self.store = store
        self.authenticator = authenticator
        self.effect_adapter = effect_adapter
        self.current_epochs = current_epochs

    def verify_and_effect(self, act: CandidateAct, live: CandidateActRequest, hcad: HCAD,
                          handle: ExecutionHandle, now: datetime | None = None) -> str:
        now = now or datetime.now(timezone.utc)
        if not self.authenticator.verify(handle.unsigned_dict(), handle.signature):
            raise FinalityError(Code.INVALID_HANDLE, "Execution Handle integrity failed")
        if now >= handle.expires_at:
            raise FinalityError(Code.EXPIRED_HANDLE, "Execution Handle expired")
        if live.intended_sink_id != self.sink_id or handle.sink_id != self.sink_id or hcad.finality_sink_id != self.sink_id:
            raise FinalityError(Code.SINK_MISMATCH, "live act, HCAD, and handle do not target this sink")
        hcad_digest = digest_object(hcad.to_dict())
        if hcad_digest != handle.hcad_digest:
            raise FinalityError(Code.HCAD_MISMATCH, "live HCAD differs from the handle binding")
        if sha256_hex(live.output) != hcad.output_hash:
            raise FinalityError(Code.OUTPUT_SUBSTITUTION, "live output differs from the Candidate Act")
        live_act = CandidateAct(
            act_id=act.act_id, request=live, output_hash=sha256_hex(live.output),
            timestamp=act.timestamp, status=act.status,
        )
        if digest_object(live_act.to_dict()) != hcad.candidate_act_digest:
            raise FinalityError(Code.HCAD_MISMATCH, "live Candidate Act fields differ from HCAD")

        epochs = self.current_epochs()
        if handle.epochs.policy_epoch != epochs.policy_epoch:
            raise FinalityError(Code.POLICY_EPOCH_MISMATCH, "policy epoch changed")
        if handle.epochs.revocation_epoch != epochs.revocation_epoch:
            raise FinalityError(Code.REVOCATION_EPOCH_MISMATCH, "revocation epoch changed")

        checks = (
            (live.intended_recipient == handle.permitted_recipient == hcad.recipient, Code.RECIPIENT_MISMATCH, "recipient mismatch"),
            (live.purpose == handle.permitted_purpose == hcad.purpose, Code.PURPOSE_MISMATCH, "purpose mismatch"),
            (live.jurisdiction == handle.permitted_jurisdiction == hcad.jurisdiction, Code.JURISDICTION_MISMATCH, "jurisdiction mismatch"),
            (live.data_class == handle.permitted_data_class, Code.DATA_CLASS_MISMATCH, "data class mismatch"),
            (live.requested_consequence == handle.permitted_consequence_type, Code.CONSEQUENCE_MISMATCH, "consequence mismatch"),
            (live.originating_system_id == hcad.originating_system_id, Code.PROVENANCE_FAILURE, "originating system mismatch"),
            (live.alf_id == hcad.alf_id, Code.ALF_MISMATCH, "ALF mismatch"),
        )
        for passed, code, message in checks:
            if not passed:
                raise FinalityError(code, message)

        receipt = self.store.receipt_by_handle(handle.handle_id) if hasattr(self.store, "receipt_by_handle") else None
        if receipt is None:
            raise FinalityError(Code.RECEIPT_MISSING, "validation receipt cannot be resolved")
        receipt_signature = receipt["protector"].pop("signature")
        if not self.authenticator.verify(receipt, receipt_signature):
            raise FinalityError(Code.INVALID_HANDLE, "validation receipt integrity failed")
        restored = dict(receipt); restored["protector"] = dict(receipt["protector"]); restored["protector"]["signature"] = receipt_signature
        if (digest_object(restored) != handle.validation_receipt_digest or
                receipt.get("hcadDigest") != handle.hcad_digest or
                receipt.get("decision") != "allow" or
                not receipt.get("predicates") or not all(receipt["predicates"].values())):
            raise FinalityError(Code.INVALID_HANDLE, "receipt is not an allowing receipt for this handle")

        self.store.reserve(handle.handle_id, hcad_digest, self.sink_id)
        execution_material = self.authenticator.sign({
            "handleId": handle.handle_id, "actId": handle.act_id, "sinkId": handle.sink_id,
        })
        if sha256_hex(execution_material) != handle.execution_material_hint:
            raise FinalityError(Code.INVALID_HANDLE, "execution material cannot be reconstructed")
        try:
            effect_id = self.effect_adapter.effect(live.requested_consequence, live.output, execution_material, handle.handle_id)
        except DefiniteEffectFailure:
            self.store.fail_definite(handle.handle_id); raise
        except UnknownEffectResult as exc:
            raise FinalityError(Code.EFFECT_RESULT_UNKNOWN, "reconcile effect before any retry") from exc
        except Exception as exc:
            raise FinalityError(Code.EFFECT_RESULT_UNKNOWN, "unclassified effect result; fail closed") from exc
        self.store.complete(handle.handle_id, effect_id)
        return effect_id
