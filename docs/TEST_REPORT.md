# Detailed test report

## Scope and method

The tests instantiate the PED, policy, SQLite store, authenticator, sink, and deterministic effect adapter in one process. Each allowed test follows prepare → validate/issue → sink verify/consume/effect. Negative tests mutate one trust-relevant variable or state transition and assert a typed fail-closed result. Concurrency uses two threads racing the same handle. Canonicalization tests load independent JSON vectors from disk.

Command: `PYTHONPATH=src python -m unittest discover -s tests -v`

Result: **74 tests run, 74 passed, 0 failed, 0 skipped** in 0.054 seconds on the recorded environment. Timing is informational and is not the latency benchmark.

## Test groups

| Group | Coverage | Result |
|---|---|---|
| Core flow | non-effective creation, hash, receipt-before-handle, one effect, expiry, epochs, store reopen | Pass |
| Replay/atomicity | same-handle replay, second handle for HCAD, concurrent consume, pending/complete/failure states | Pass |
| Integrity | handle, HCAD and receipt tampering; missing receipt/handle; execution-material dependency | Pass |
| Substitution | output, sink, system, model, workflow, recipient, tool, purpose, jurisdiction, data, risk, consequence and ALF | Pass |
| Policy threats | unapproved origin/model/tool, ALF/RBD drift, provenance, facts, simulation and RCAE violations | Pass |
| Graduated controls | quarantine, redaction, sandbox, scope reduction, escalation and intentional delay | Pass |
| System variants | ten consequence classes listed below | Pass |
| Malformed input | every required Candidate Act request field empty | Pass |
| Portable vectors | tool call, data export and physical actuation canonical JSON/SHA-256 | Pass |

## Consequence/system variants exercised

`TOOL_CALL`, `MESSAGE_SEND`, `DATA_EXPORT`, `DATABASE_MUTATION`, `NETWORK_CHANGE`, `SOFTWARE_DEPLOYMENT`, `MEMORY_WRITE`, `MODEL_UPDATE`, `PHYSICAL_ACTUATION`, and `LEGAL_COMMITMENT`.

## What was not tested

No satellite or RF profile, real payment rail, external API, database cluster, HSM/TPM/TEE, kernel enforcement, packet-loss network, process crash injection, multi-region consensus, formal verification, fuzz campaign, penetration test, or real-world actuation was used. Other programming languages were not executed. Consequently these results validate this Python reference behavior only.

