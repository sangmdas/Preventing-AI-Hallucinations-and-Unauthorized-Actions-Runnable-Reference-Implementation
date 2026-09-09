from __future__ import annotations

import json
import tempfile
import threading
import time
import unittest
from dataclasses import replace
from pathlib import Path

from candidate_finality.canonical import canonical_json, digest_object, rcae_projection, sha256_hex
from candidate_finality.demo import CONSEQUENCES, build_demo, context_for, request_for
from candidate_finality.effects import DefiniteEffectFailure, UnknownEffectResult
from candidate_finality.errors import Code, Decision, FinalityError
from candidate_finality.models import CandidateActRequest, EpochState
from candidate_finality.store import SQLiteFinalityStore


class DefiniteFailEffect:
    def effect(self, consequence_type, output, execution_material, handle_id):
        raise DefiniteEffectFailure("confirmed no external effect")


class UnknownFailEffect:
    def effect(self, consequence_type, output, execution_material, handle_id):
        raise UnknownEffectResult("effect response lost")


class ReferenceCase(unittest.TestCase):
    def setUp(self):
        self.request = request_for()
        self.context = context_for(self.request)
        self.policy, self.store, self.ped, self.sink, self.effects = build_demo(self.request)

    def issue(self, request=None, context=None):
        request = request or self.request
        context = context or context_for(request)
        act = self.ped.prepare(request)
        hcad, receipt, handle = self.ped.validate_and_issue(act, context)
        return act, hcad, receipt, handle

    def deny_sink(self, code, act=None, live=None, hcad=None, handle=None):
        if act is None:
            act, hcad, _, handle = self.issue()
        with self.assertRaises(FinalityError) as caught:
            self.sink.verify_and_effect(act, live or self.request, hcad, handle)
        self.assertEqual(caught.exception.code, code)
        self.assertEqual(len(self.effects.effects), 0)


class CoreFlowTests(ReferenceCase):
    def test_candidate_starts_non_effective(self):
        act = self.ped.prepare(self.request)
        self.assertEqual(act.status, "non-effective")
        self.assertEqual(len(self.effects.effects), 0)

    def test_allow_effects_once(self):
        act, hcad, _, handle = self.issue()
        self.sink.verify_and_effect(act, self.request, hcad, handle)
        self.assertEqual(self.store.state(handle.handle_id), "EFFECTUATED")
        self.assertEqual(len(self.effects.effects), 1)

    def test_receipt_committed_before_handle(self):
        _, _, receipt, handle = self.issue()
        self.assertIsNotNone(self.store.receipt(receipt.receipt_id))
        self.assertEqual(self.store.state(handle.handle_id), "UNUSED")

    def test_handle_is_sink_bound(self):
        _, _, _, handle = self.issue()
        self.assertEqual(handle.sink_id, self.request.intended_sink_id)

    def test_handle_is_one_time(self):
        _, _, _, handle = self.issue()
        self.assertTrue(handle.one_time_use)

    def test_handle_binds_hcad(self):
        _, hcad, _, handle = self.issue()
        self.assertEqual(handle.hcad_digest, digest_object(hcad.to_dict()))

    def test_hcad_binds_candidate_act(self):
        act, hcad, _, _ = self.issue()
        self.assertEqual(hcad.candidate_act_digest, digest_object(act.to_dict()))

    def test_output_hash_is_sha256(self):
        act = self.ped.prepare(self.request)
        self.assertEqual(act.output_hash, sha256_hex(self.request.output))

    def test_same_handle_replay(self):
        act, hcad, _, handle = self.issue()
        self.sink.verify_and_effect(act, self.request, hcad, handle)
        with self.assertRaises(FinalityError) as caught:
            self.sink.verify_and_effect(act, self.request, hcad, handle)
        self.assertEqual(caught.exception.code, Code.HANDLE_ALREADY_USED)
        self.assertEqual(len(self.effects.effects), 1)

    def test_second_handle_same_hcad_replay(self):
        act, hcad, _, first = self.issue()
        self.sink.verify_and_effect(act, self.request, hcad, first)
        self.store._conn.execute(
            "INSERT INTO handles SELECT ?, act_id, receipt_id, hcad_digest, ?, sink_id, 'UNUSED', NULL, payload, updated_at FROM handles WHERE handle_id=?",
            ("cloned-handle", "cloned-nonce", first.handle_id),
        )
        cloned = replace(first, handle_id="cloned-handle", nonce="cloned-nonce")
        cloned = replace(cloned, signature=self.ped.authenticator.sign(cloned.unsigned_dict()))
        with self.assertRaises(FinalityError) as caught:
            self.sink.verify_and_effect(act, self.request, hcad, cloned)
        self.assertEqual(caught.exception.code, Code.REPLAY_DETECTED)
        self.assertEqual(len(self.effects.effects), 1)

    def test_concurrent_consume_one_effect(self):
        act, hcad, _, handle = self.issue()
        barrier = threading.Barrier(2); outcomes = []
        def worker():
            barrier.wait()
            try: outcomes.append(self.sink.verify_and_effect(act, self.request, hcad, handle))
            except Exception as exc: outcomes.append(exc)
        threads = [threading.Thread(target=worker) for _ in range(2)]
        for thread in threads: thread.start()
        for thread in threads: thread.join()
        self.assertEqual(sum(isinstance(item, str) for item in outcomes), 1)
        self.assertEqual(len(self.effects.effects), 1)

    def test_expiry_boundary(self):
        act, hcad, _, handle = self.issue()
        with self.assertRaises(FinalityError) as caught:
            self.sink.verify_and_effect(act, self.request, hcad, handle, now=handle.expires_at)
        self.assertEqual(caught.exception.code, Code.EXPIRED_HANDLE)

    def test_policy_epoch_change(self):
        act, hcad, _, handle = self.issue()
        self.policy.epochs = EpochState(22, 7)
        self.deny_sink(Code.POLICY_EPOCH_MISMATCH, act=act, hcad=hcad, handle=handle)

    def test_revocation_epoch_change(self):
        act, hcad, _, handle = self.issue()
        self.policy.epochs = EpochState(21, 8)
        self.deny_sink(Code.REVOCATION_EPOCH_MISMATCH, act=act, hcad=hcad, handle=handle)

    def test_tampered_handle_signature(self):
        act, hcad, _, handle = self.issue()
        self.deny_sink(Code.INVALID_HANDLE, act=act, hcad=hcad, handle=replace(handle, signature="invalid"))

    def test_tampered_handle_scope(self):
        act, hcad, _, handle = self.issue()
        changed = replace(handle, permitted_recipient="attacker")
        self.deny_sink(Code.INVALID_HANDLE, act=act, hcad=hcad, handle=changed)

    def test_tampered_hcad(self):
        act, hcad, _, handle = self.issue()
        self.deny_sink(Code.HCAD_MISMATCH, act=act, hcad=replace(hcad, purpose="other"), handle=handle)

    def test_missing_receipt(self):
        act, hcad, receipt, handle = self.issue()
        self.store._conn.execute("PRAGMA foreign_keys=OFF")
        self.store._conn.execute("DELETE FROM receipts WHERE receipt_id=?", (receipt.receipt_id,))
        self.deny_sink(Code.RECEIPT_MISSING, act=act, hcad=hcad, handle=handle)

    def test_tampered_receipt(self):
        act, hcad, receipt, handle = self.issue()
        payload = self.store.receipt(receipt.receipt_id); payload["decision"] = "deny"
        self.store._conn.execute("UPDATE receipts SET payload=? WHERE receipt_id=?", (json.dumps(payload), receipt.receipt_id))
        self.deny_sink(Code.INVALID_HANDLE, act=act, hcad=hcad, handle=handle)

    def test_missing_registered_handle(self):
        act, hcad, _, handle = self.issue()
        self.store._conn.execute("DELETE FROM handles WHERE handle_id=?", (handle.handle_id,))
        self.deny_sink(Code.RECEIPT_MISSING, act=act, hcad=hcad, handle=handle)

    def test_candidate_output_mutated_before_validation(self):
        act = self.ped.prepare(self.request)
        altered = replace(act, request=replace(self.request, output="changed"))
        with self.assertRaises(FinalityError) as caught:
            self.ped.validate_and_issue(altered, self.context)
        self.assertEqual(caught.exception.code, Code.OUTPUT_SUBSTITUTION)

    def test_candidate_status_mutated_before_validation(self):
        act = replace(self.ped.prepare(self.request), status="effectuated")
        with self.assertRaises(FinalityError) as caught:
            self.ped.validate_and_issue(act, self.context)
        self.assertEqual(caught.exception.code, Code.OUTPUT_SUBSTITUTION)

    def test_definite_effect_failure(self):
        act, hcad, _, handle = self.issue()
        self.sink.effect_adapter = DefiniteFailEffect()
        with self.assertRaises(DefiniteEffectFailure):
            self.sink.verify_and_effect(act, self.request, hcad, handle)
        self.assertEqual(self.store.state(handle.handle_id), "FAILED_DEFINITE")

    def test_unknown_effect_result(self):
        act, hcad, _, handle = self.issue()
        self.sink.effect_adapter = UnknownFailEffect()
        with self.assertRaises(FinalityError) as caught:
            self.sink.verify_and_effect(act, self.request, hcad, handle)
        self.assertEqual(caught.exception.code, Code.EFFECT_RESULT_UNKNOWN)
        self.assertEqual(self.store.state(handle.handle_id), "CONSUMED_PENDING")

    def test_execution_material_required_by_adapter(self):
        with self.assertRaises(DefiniteEffectFailure):
            self.effects.effect("TOOL_CALL", "output", "", "handle")

    def test_file_store_reopens(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = SQLiteFinalityStore(f"{tmp}/finality.db"); store.close()
            reopened = SQLiteFinalityStore(f"{tmp}/finality.db")
            self.assertIsNone(reopened.state("none")); reopened.close()


class ValidationThreatTests(ReferenceCase):
    def assert_validation_denied(self, code, request=None, context=None, decision=Decision.DENY):
        request = request or self.request; context = context or self.context
        act = self.ped.prepare(request)
        with self.assertRaises(FinalityError) as caught:
            self.ped.validate_and_issue(act, context)
        self.assertEqual(caught.exception.code, code)
        self.assertEqual(caught.exception.decision, decision)
        self.assertEqual(len(self.effects.effects), 0)

    def test_unapproved_originating_system(self):
        self.assert_validation_denied(Code.PROVENANCE_FAILURE, replace(self.request, originating_system_id="compromised-runtime"))

    def test_unapproved_model(self):
        self.assert_validation_denied(Code.PROVENANCE_FAILURE, replace(self.request, model_id="substituted-model"))

    def test_unapproved_tool(self):
        self.assert_validation_denied(Code.CONSEQUENCE_MISMATCH, replace(self.request, intended_tool="raw.shell"))

    def test_alf_logic_substitution(self):
        self.assert_validation_denied(Code.ALF_MISMATCH, context=replace(self.context, approved_alf_ids=frozenset({"alf-other"})))

    def test_runtime_behavior_drift(self):
        self.assert_validation_denied(Code.RBD_MISMATCH, context=replace(self.context, behavior_matches=False))

    def test_invalid_provenance(self):
        self.assert_validation_denied(Code.PROVENANCE_FAILURE, context=replace(self.context, provenance_valid=False))

    def test_stale_provenance(self):
        self.assert_validation_denied(Code.PROVENANCE_FAILURE, context=replace(self.context, provenance_fresh=False))

    def test_missing_evidence_references(self):
        self.assert_validation_denied(Code.PROVENANCE_FAILURE, context=replace(self.context, evidence_refs=()))

    def test_unsupported_factual_claim_quarantined(self):
        self.assert_validation_denied(Code.FACTUAL_SUPPORT_FAILURE, context=replace(self.context, factual_claims_verified=False), decision=Decision.QUARANTINE)

    def test_unsafe_simulation_denied(self):
        self.assert_validation_denied(Code.SIMULATION_FAILURE, context=replace(self.context, consequence_simulation_safe=False))

    def test_recipient_outside_rcae(self):
        self.assert_validation_denied(Code.RECIPIENT_MISMATCH, context=replace(self.context, permitted_recipient="other"))

    def test_purpose_outside_rcae(self):
        self.assert_validation_denied(Code.PURPOSE_MISMATCH, context=replace(self.context, permitted_purpose="other"))

    def test_jurisdiction_outside_rcae(self):
        self.assert_validation_denied(Code.JURISDICTION_MISMATCH, context=replace(self.context, permitted_jurisdiction="EU"))

    def test_sensitive_data_requires_redaction(self):
        request = replace(self.request, data_class="SENSITIVE")
        self.assert_validation_denied(Code.REDACTION_REQUIRED, request=request, context=self.context, decision=Decision.REDACT)

    def test_data_class_mismatch(self):
        self.assert_validation_denied(Code.DATA_CLASS_MISMATCH, context=replace(self.context, permitted_data_class="PUBLIC"))

    def test_consequence_outside_rcae(self):
        self.assert_validation_denied(Code.CONSEQUENCE_MISMATCH, context=replace(self.context, permitted_consequence_type="DATA_EXPORT"))

    def test_risk_requires_sandbox(self):
        request = replace(self.request, risk_class="CRITICAL")
        self.assert_validation_denied(Code.SANDBOX_REQUIRED, request=request, context=self.context, decision=Decision.SANDBOX)

    def test_scope_reduction(self):
        ctx = replace(self.context, requested_scope_units=100, permitted_scope_units=10)
        self.assert_validation_denied(Code.SCOPE_REDUCTION_REQUIRED, context=ctx, decision=Decision.REDUCE_SCOPE)

    def test_human_approval_escalation(self):
        ctx = replace(self.context, human_approval_ids=())
        self.assert_validation_denied(Code.HUMAN_APPROVAL_REQUIRED, context=ctx, decision=Decision.ESCALATE)

    def test_duplicate_approval_not_counted_twice(self):
        request = replace(self.request, risk_class="HIGH")
        ctx = replace(context_for(request), human_approval_ids=("same", "same"))
        self.assert_validation_denied(Code.HUMAN_APPROVAL_REQUIRED, request=request, context=ctx, decision=Decision.ESCALATE)

    def test_intentional_delay(self):
        ctx = replace(self.context, delay_until_epoch_ms=int(time.time() * 1000) + 60_000)
        self.assert_validation_denied(Code.DELAY_REQUIRED, context=ctx, decision=Decision.DELAY)


SUBSTITUTIONS = {
    "output": "attacker-modified output", "originating_system_id": "runtime-other",
    "model_id": "model-other", "workflow_id": "workflow-other",
    "intended_recipient": "recipient-other", "intended_tool": "tool-other",
    "purpose": "purpose-other", "jurisdiction": "US", "data_class": "PUBLIC",
    "risk_class": "HIGH", "requested_consequence": "DATA_EXPORT", "alf_id": "alf-other",
}


def make_substitution_test(field, value):
    def test(self):
        live = replace(self.request, **{field: value})
        act, hcad, _, handle = self.issue()
        expected = Code.OUTPUT_SUBSTITUTION if field == "output" else Code.HCAD_MISMATCH
        self.deny_sink(expected, act=act, live=live, hcad=hcad, handle=handle)
    return test


class SinkSubstitutionTests(ReferenceCase):
    def test_sink_substitution(self):
        act, hcad, _, handle = self.issue()
        self.deny_sink(Code.SINK_MISMATCH, act=act, live=replace(self.request, intended_sink_id="other-sink"), hcad=hcad, handle=handle)


for _field, _value in SUBSTITUTIONS.items():
    setattr(SinkSubstitutionTests, f"test_{_field}_substitution", make_substitution_test(_field, _value))


def make_domain_allow_test(consequence):
    def test(self):
        request = request_for(consequence)
        _, store, ped, sink, effects = build_demo(request)
        act = ped.prepare(request)
        hcad, _, handle = ped.validate_and_issue(act, context_for(request))
        sink.verify_and_effect(act, request, hcad, handle)
        self.assertEqual(store.state(handle.handle_id), "EFFECTUATED")
        self.assertEqual(len(effects.effects), 1)
    return test


class CrossDomainAllowTests(unittest.TestCase):
    pass


for _consequence in CONSEQUENCES:
    setattr(CrossDomainAllowTests, f"test_allow_{_consequence.lower()}", make_domain_allow_test(_consequence))


class MalformedTests(ReferenceCase):
    def test_each_required_field_empty(self):
        for field in self.request.__dataclass_fields__:
            with self.subTest(field=field):
                with self.assertRaises(FinalityError) as caught:
                    self.ped.prepare(replace(self.request, **{field: ""}))
                self.assertEqual(caught.exception.code, Code.MALFORMED_ACT)


class VectorTests(unittest.TestCase):
    def test_tool_call_vector(self): self._check("tool-call")
    def test_data_export_vector(self): self._check("data-export")
    def test_physical_actuation_vector(self): self._check("physical-actuation")

    def _check(self, name):
        vector = json.loads((Path(__file__).parents[1] / "test-vectors" / f"{name}.json").read_text())
        self.assertEqual(canonical_json(vector["object"]).decode(), vector["expected_canonical_utf8"])
        self.assertEqual(digest_object(vector["object"]), vector["expected_sha256_hex"])


if __name__ == "__main__":
    unittest.main()

