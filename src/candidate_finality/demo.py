from __future__ import annotations

import json

from .crypto import HMACAuthenticator
from .effects import SimulatedEffectSink
from .models import CandidateActRequest, EpochState, ValidationContext
from .ped import ProtectedEnforcementDomain
from .policy import FinalityPolicy
from .sink import FinalitySink
from .store import SQLiteFinalityStore


CONSEQUENCES = {
    "TOOL_CALL": ("tools.payment.create", "payment-api"),
    "MESSAGE_SEND": ("communications.send", "message-gateway"),
    "DATA_EXPORT": ("data.export", "export-gateway"),
    "DATABASE_MUTATION": ("database.update", "database-commit"),
    "NETWORK_CHANGE": ("network.configure", "network-controller"),
    "SOFTWARE_DEPLOYMENT": ("software.deploy", "deployment-controller"),
    "MEMORY_WRITE": ("agent.memory.write", "memory-commit"),
    "MODEL_UPDATE": ("model.update", "model-registry"),
    "PHYSICAL_ACTUATION": ("robot.actuate", "actuator-controller"),
    "LEGAL_COMMITMENT": ("contract.accept", "legal-commit-sink"),
}


def request_for(consequence: str = "TOOL_CALL") -> CandidateActRequest:
    tool, sink = CONSEQUENCES[consequence]
    return CandidateActRequest(
        output=f"canonical candidate output for {consequence}",
        originating_system_id="agent-runtime-1", model_id="model-approved-7",
        workflow_id="workflow-42", intended_recipient="recipient-9",
        intended_tool=tool, intended_sink_id=sink, purpose="approved-purpose",
        jurisdiction="IN", data_class="INTERNAL", risk_class="MEDIUM",
        requested_consequence=consequence, alf_id="alf-approved-3",
    )


def context_for(request: CandidateActRequest) -> ValidationContext:
    return ValidationContext(
        rbd_id="rbd-approved-3", opc_id="opc-fresh-88", rcae_id="rcae-19",
        approved_alf_ids=frozenset({"alf-approved-3"}), behavior_matches=True,
        provenance_valid=True, provenance_fresh=True, factual_claims_verified=True,
        consequence_simulation_safe=True, evidence_refs=("evidence-source-1",),
        permitted_recipient=request.intended_recipient,
        permitted_purpose=request.purpose,
        permitted_jurisdiction=request.jurisdiction,
        permitted_data_class=request.data_class,
        permitted_consequence_type=request.requested_consequence,
        max_risk_class="HIGH", human_approval_ids=("approval-human-1",),
        requested_scope_units=1, permitted_scope_units=10,
    )


def build_demo(request: CandidateActRequest | None = None):
    request = request or request_for()
    epochs = EpochState(21, 7)
    policy = FinalityPolicy(
        epochs=epochs, permitted_systems={"agent-runtime-1"},
        permitted_models={"model-approved-7"},
        permitted_tools={tool for tool, _ in CONSEQUENCES.values()},
        minimum_human_approvals={"LOW": 0, "MEDIUM": 1, "HIGH": 2, "CRITICAL": 3},
    )
    store = SQLiteFinalityStore()
    auth = HMACAuthenticator(b"candidate-act-reference-key-32bytes!!")
    effects = SimulatedEffectSink()
    ped = ProtectedEnforcementDomain(policy, store, auth)
    sink = FinalitySink(request.intended_sink_id, store, auth, effects, lambda: policy.epochs)
    return policy, store, ped, sink, effects


def main() -> None:
    request = request_for()
    _, store, ped, sink, effects = build_demo(request)
    act = ped.prepare(request)
    hcad, receipt, handle = ped.validate_and_issue(act, context_for(request))
    effect_id = sink.verify_and_effect(act, request, hcad, handle)
    print(json.dumps({
        "initial_status": act.status, "act_id": act.act_id,
        "output_hash": act.output_hash, "hcad_digest": handle.hcad_digest,
        "receipt_id": receipt.receipt_id, "handle_id": handle.handle_id,
        "handle_state": store.state(handle.handle_id), "effect_id": effect_id,
        "simulated_effect_count": len(effects.effects),
    }, indent=2))


if __name__ == "__main__":
    main()
