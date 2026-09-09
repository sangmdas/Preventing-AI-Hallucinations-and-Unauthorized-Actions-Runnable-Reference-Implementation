# Implementation reference

## Processing model

1. `PED.prepare()` hashes the raw output and creates a non-effective Candidate Act.
2. `FinalityPolicy.validate()` evaluates provenance, ALF, RBD, evidence/factual support, simulation, RCAE, risk, scope, approvals, and delay.
3. `PED.validate_and_issue()` constructs HCAD, signs a validation receipt, commits it, then creates a short-lived signed Execution Handle.
4. `FinalitySink.verify_and_effect()` verifies signatures, expiry, sink and live-field bindings, HCAD and receipt digests, epochs, and all allowing predicates.
5. The SQLite store atomically reserves the one-time handle. Only then is execution material reconstructed and passed to the effect adapter.
6. A definite failure returns the handle to a definite-failure state; an unknown result remains pending and requires reconciliation. Success records one effect identifier.

## Source-to-code map

| Draft concept | Reference component | Enforcement point |
|---|---|---|
| Candidate Act | `models.CandidateAct`, `ped.prepare` | Non-effective status and output hash |
| HCAD | `models.HCAD`, `ped.validate_and_issue` | Context, evidence, epoch and sink commitments |
| ALF/RBD/OPC/FCU | `policy.FinalityPolicy` | Approved logic, behavior, provenance and facts |
| RCAE | `models.ValidationContext`, policy and sink | Recipient, purpose, jurisdiction, data, risk and consequence |
| Consequence simulation | `consequence_simulation_safe` predicate | Deny before issuance when unsafe |
| Graduated decision | `errors.Decision` | Typed deny/quarantine/redact/delay/sandbox/reduce/escalate |
| Atomic receipt-with-release | `store.SQLiteFinalityStore` and PED | Receipt committed before handle |
| Execution Handle | `models.ExecutionHandle` | Signed, scoped, expiring, one-time authorization |
| Finality Sink | `sink.FinalitySink` | Last-moment verification and atomic consumption |
| Missing execution material | hint plus reconstructed HMAC material | Software demonstration only |

## Trust boundaries

AI/model output, orchestration, and transport are treated as untrusted. PED and the Finality Sink are separate trusted enforcement points sharing configured verification material and current epochs. SQLite is the reference consistency boundary. A production system must replace the in-process key, simulator, and local database with protected key management, durable consensus/transactions, authenticated transports, and real sink adapters.

## Cryptography and canonicalization

Objects are serialized as sorted-key compact UTF-8 JSON and hashed with SHA-256. Receipts and handles use HMAC-SHA-256 solely to make the example runnable. Production deployments should select interoperable canonicalization and signatures/MACs with explicit algorithm agility, key lifecycle, domain separation, and verification policy. Three JSON vectors lock the reference serialization and digest.

## Failure behavior

Missing, expired, stale, unverifiable, mismatched, ambiguous, or replayed material fails closed. No failure path calls the effect adapter. Unknown adapter results are not safe to retry automatically because the external effect might already exist.

