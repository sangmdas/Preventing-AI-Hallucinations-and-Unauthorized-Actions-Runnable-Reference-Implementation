# Threat model

## Assets and adversaries

Protected assets are effect authority, output/context integrity, receipt/handle authenticity, one-time use, scope, and audit state. The adversary may control model output, prompts, an agent runtime, network messages, or copied/stale artifacts. The reference assumes PED, sink, configured secrets, clock, epoch provider, and SQLite engine are not compromised.

| Threat | Control and test | Residual limitation |
|---|---|---|
| Hallucinated or injected instruction | Candidate Act is non-effective; facts and simulation checked | Quality depends on external evidence/simulator inputs |
| Output/TOCTOU substitution | Output hash plus Candidate Act and HCAD digests; substitution tests | Canonicalization must match across implementations |
| Model, workflow, tool, ALF or origin swap | Full Candidate Act digest and policy allowlists | Identity issuance is outside this sample |
| Runtime behavior drift | RBD predicate | No live behavior attestation is implemented |
| Stale/forged provenance | validity, freshness and nonempty evidence checks | Evidence verification is supplied as booleans |
| Unsupported factual units | quarantine result | No claim extractor or fact checker is included |
| Unsafe predicted consequence | simulation predicate denies | Simulator soundness is not proven |
| Recipient/purpose/jurisdiction/data drift | RCAE validation at PED and sink | Legal classification remains deployment-specific |
| Handle theft, replay or race | signature, binding, expiry and atomic one-time reservation | Distributed replay needs a strongly consistent store |
| Sink substitution | three-way live/HCAD/handle sink binding | Hardware identity is emulated |
| Policy/revocation change | live epoch comparison | Epoch distribution and rollback protection are external |
| Approval replay/duplication | distinct protected approval IDs counted | Approval signatures are not modeled |
| Receipt tamper/removal | signed receipt and digest resolution | Local secret compromise defeats HMAC |
| Unknown effect result | retain pending; require reconciliation | Adapter-specific idempotency/reconciliation is external |
| Execution-material disclosure | material reconstructed only after reserve | Software process can inspect it; no non-exportability |
| PED or sink compromise | out of threat model | Production isolation and attestation required |
| Availability/DoS | fail closed | No availability guarantee; denial may stop valid acts |

Security invariants are tested, not formally proved. See `SECURITY.md` for deployment requirements.

