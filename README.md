# Candidate-Act Finality — Runnable Reference Implementation

This repository is an executable, testable interpretation of `draft-das-protocols-candidate-act-finality-00`, *Stopping AI Hallucinations and Unsafe Acts from Becoming Real-World Consequences (DAS Protocols)*. It demonstrates how an AI output remains a non-effective **Candidate Act** until a Policy Enforcement Decision (PED) validates evidence and scope, records a signed receipt, issues a short-lived one-time **Execution Handle**, and a bound **Finality Sink** revalidates and consumes it atomically.

It is a reference implementation, not a claim of IETF conformance, production security, hardware enforcement, certification, or patent coverage.

## What is implemented

- Candidate Act creation with SHA-256 output binding and `status=non-effective`.
- ALF, runtime-behavior (RBD), provenance/evidence (OPC/FCU), consequence simulation, RCAE, approval, scope, delay, redaction, and sandbox checks.
- Graduated outcomes: allow, deny, quarantine, redact, delay, sandbox, reduce-scope, and escalate.
- Signed validation receipt committed before handle issuance.
- Sink-, recipient-, purpose-, jurisdiction-, data-class-, consequence-, epoch-, HCAD-, and Candidate-Act-bound handles.
- SQLite one-time state transition and replay/concurrent-consumption protection.
- Software reconstruction of execution material immediately before effect.
- Ten system/consequence variants and three portable canonicalization vectors.

The implementation adds `candidateActDigest` to HCAD. This conservative extension binds the complete Candidate Act, including model, workflow, tool, and consequence fields; the draft's illustrative HCAD schema does not contain that exact field.

## Run

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -e .
python -m candidate_finality.demo
python -m unittest discover -s tests -v
python -m candidate_finality.benchmark --iterations 1000 --warmup 100
```

No third-party runtime dependency is required. Python 3.10+ is supported.

## Verified result

On CPython 3.12.14, Linux 6.18.35 x86_64, SQLite 3.53.1: **74/74 tests passed**. With an in-memory store, software HMAC, and in-process effect simulator, 1,000 measured iterations after 100 warmups produced sink p99 **1.5875 ms** and full-path p99 **2.8546 ms**. These are local measurements, not network, hardware-rooted, production, or safety SLAs. The draft specifies no numeric latency target; this repository uses non-normative regression goals of sink p99 ≤2 ms and local full-path p99 ≤10 ms.

## Documentation

- [Implementation reference](docs/IMPLEMENTATION_REFERENCE.md)
- [Test report](docs/TEST_REPORT.md)
- [Threat model](docs/THREAT_MODEL.md)
- [System variations](docs/SYSTEM_VARIATIONS.md)
- [Language variations](docs/LANGUAGE_VARIATIONS.md)
- [Latency](docs/LATENCY.md)
- [Limitations](docs/LIMITATIONS.md)
- [Source and parameter provenance](docs/PARAMETERS_AND_PROVENANCE.md)
- [Security guidance](SECURITY.md)

## Detailed Implementation and Test Report

### 1. Overview

This repository provides a runnable Python reference implementation based on `draft-das-protocols-candidate-act-finality-00`, titled:

**Stopping AI Hallucinations and Unsafe Acts from Becoming Real-World Consequences (DAS Protocols)**

The implementation demonstrates how an AI-generated instruction remains a **non-effective Candidate Act** until policy, provenance, evidence, scope, safety, and consequence checks have succeeded.

A successful validation produces a protected validation receipt and a short-lived, one-time **Execution Handle**. The designated **Finality Sink** independently verifies the handle and the live action before permitting an external effect.

The implemented sequence is:

**AI Output → Candidate Act → Non-Effective State → Policy and Evidence Validation → HCAD → Validation Receipt → Execution Handle → Finality Sink → External Effect**

This is an informative reference implementation. It is not a claim of IETF compliance, production certification, hardware enforcement, or formal security verification.

---

## 2. Implementation Language

The runnable implementation uses:

* **Language:** Python
* **Minimum version:** Python 3.10
* **Tested version:** CPython 3.12.14
* **Runtime dependencies:** Python standard library only
* **Database:** SQLite
* **Cryptographic reference mechanism:** HMAC-SHA-256
* **Hashing:** SHA-256
* **Serialization:** Deterministic sorted-key compact UTF-8 JSON
* **Testing framework:** Python `unittest`
* **Concurrency testing:** Python threads
* **Automation:** GitHub Actions

No third-party runtime package is required.

The repository includes design guidance for implementing equivalent controls in TypeScript, Go, Rust, Java, Kotlin, C#, C/C++, WebAssembly, secure elements, and FPGA-based enforcement systems. These language variations are guidance only; they were not executed or tested in this package.

---

## 3. System Used for Testing

The recorded validation and benchmark environment was:

| Component                | Configuration                      |
| ------------------------ | ---------------------------------- |
| Operating system         | Linux 6.18.35 x86_64               |
| C library                | glibc 2.39                         |
| Python                   | CPython 3.12.14                    |
| SQLite                   | 3.53.1                             |
| Storage mode             | SQLite in-memory database          |
| Cryptographic protection | Software HMAC-SHA-256              |
| Effect adapter           | Deterministic in-process simulator |
| Network calls            | None                               |
| Hardware security        | Not used                           |
| Distributed consensus    | Not used                           |
| Benchmark iterations     | 1,000                              |
| Warm-up iterations       | 100                                |

The tests were also run again after extracting the final TAR.GZ archive into a fresh temporary directory.

---

## 4. Implemented Components

### Candidate Act

An AI-generated output is converted into a Candidate Act containing:

* Action identifier
* SHA-256 output hash
* Originating system
* Model identifier
* Workflow identifier
* Intended recipient
* Intended tool
* Intended Finality Sink
* Purpose
* Jurisdiction
* Data classification
* Risk classification
* Requested consequence
* Algorithmic Logic Fingerprint identifier
* UTC timestamp
* `non-effective` status

The Candidate Act cannot directly call the effect adapter.

### Policy Enforcement Domain

The Protected Enforcement Domain validates:

* Approved originating system
* Approved model
* Approved tool
* Algorithmic Logic Fingerprint
* Runtime behavior
* Provenance validity
* Provenance freshness
* Evidence availability
* Factual-claim support
* Consequence simulation
* Recipient
* Purpose
* Jurisdiction
* Data classification
* Consequence type
* Risk limit
* Requested scope
* Human approval requirements
* Intentional delay requirements

### HCAD

The implementation generates an HCAD containing the validated context, evidence references, scope, epochs, sink identity, nonce, risk class, and Candidate Act binding.

The reference implementation adds a `candidateActDigest` field to HCAD. This is a conservative implementation extension that binds the complete Candidate Act, including the model, workflow, tool, intended consequence, recipient, and other security-relevant fields.

### Validation Receipt

The validation receipt contains:

* Candidate Act identifier
* HCAD digest
* RCAE digest
* Validation predicates
* Consequence-simulation digest
* Allow decision
* Issuance timestamp
* Key identifier
* Integrity signature

The receipt is committed before the Execution Handle is issued.

### Execution Handle

The Execution Handle is:

* Short-lived
* Signed
* One-time-use
* Sink-bound
* Recipient-bound
* Purpose-bound
* Jurisdiction-bound
* Data-class-bound
* Consequence-bound
* HCAD-bound
* Validation-receipt-bound
* Policy-epoch-bound
* Revocation-epoch-bound

Possession of the handle alone is insufficient. The Finality Sink must compare it against the live Candidate Act, HCAD, receipt, current epochs, and sink identity.

### Finality Sink

The Finality Sink performs the last verification before an effect becomes externally effective. It verifies:

* Handle integrity
* Handle expiry
* Intended sink
* HCAD digest
* Candidate Act digest
* Output hash
* Recipient
* Purpose
* Jurisdiction
* Data class
* Consequence
* Originating system
* ALF identifier
* Policy epoch
* Revocation epoch
* Validation receipt
* Allowing validation predicates
* One-time consumption state
* Execution-material reconstruction

The effect adapter is called only after all checks succeed and the handle has been atomically reserved.

---

## 5. Test Results

A total of **74 tests** were executed.

**Result: 74 passed, 0 failed, 0 skipped.**

The complete test suite was run twice:

1. In the development directory
2. From a freshly extracted copy of the final archive

Both executions passed.

### Core Execution Tests

The tests verified:

* Candidate Acts begin in a non-effective state
* Output hashes are correctly calculated
* Validation evidence is recorded before handle issuance
* A valid Candidate Act produces exactly one simulated effect
* An expired handle is rejected
* Policy-epoch changes invalidate existing handles
* Revocation-epoch changes invalidate existing handles
* Persistent SQLite state survives database reopening
* Execution material is required by the effect adapter

### Replay and Atomicity Tests

The suite tested:

* Reuse of the same Execution Handle
* A second handle attempting to use an already-consumed HCAD
* Concurrent consumption by two threads
* Atomic transition from `UNUSED` to `CONSUMED_PENDING`
* Successful transition to `EFFECTUATED`
* Definite effect failure
* Unknown or ambiguous effect result
* Prevention of automatic retry after an ambiguous result

### Tampering Tests

The following modifications were detected and rejected:

* Execution Handle signature modification
* Handle scope modification
* HCAD modification
* Validation-receipt modification
* Missing validation receipt
* Missing registered handle
* Candidate output modification
* Candidate status modification

### Substitution Tests

Separate tests attempted to substitute:

* AI output
* Originating system
* Model
* Workflow
* Recipient
* Tool
* Finality Sink
* Purpose
* Jurisdiction
* Data classification
* Risk classification
* Requested consequence
* Algorithmic Logic Fingerprint

Every substitution was rejected before the external effect.

### Policy and Threat Tests

The suite included tests for:

* Unapproved originating systems
* Unapproved models
* Unapproved tools
* ALF mismatch
* Runtime behavior drift
* Invalid provenance
* Stale provenance
* Missing evidence references
* Unsupported factual claims
* Unsafe consequence simulation
* Recipient outside the RCAE
* Purpose outside the RCAE
* Jurisdiction outside the RCAE
* Data-class mismatch
* Consequence outside the RCAE
* Excessive risk
* Excessive requested scope
* Missing human approval
* Duplicate approval identifiers
* Intentional execution delay

### Graduated Decision Tests

The implementation supports and tests:

* Allow
* Deny
* Quarantine
* Redact
* Delay
* Sandbox
* Reduce scope
* Escalate for protected human approval

---

## 6. System and Consequence Variations

The tests exercised ten different consequence classes:

| Variation             | Example use                                     |
| --------------------- | ----------------------------------------------- |
| `TOOL_CALL`           | Agent invoking an external API or tool          |
| `MESSAGE_SEND`        | Email, chat or notification transmission        |
| `DATA_EXPORT`         | Export of protected or regulated information    |
| `DATABASE_MUTATION`   | Record creation, modification or deletion       |
| `NETWORK_CHANGE`      | Firewall, routing or infrastructure changes     |
| `SOFTWARE_DEPLOYMENT` | Release or configuration deployment             |
| `MEMORY_WRITE`        | Persistent agent or application memory update   |
| `MODEL_UPDATE`        | Model, weight, configuration or training update |
| `PHYSICAL_ACTUATION`  | Robot, device or industrial actuation           |
| `LEGAL_COMMITMENT`    | Signature, agreement or binding workflow        |

A financial or payment deployment can use the same architecture by binding the handle to the payee, amount, currency, payment rail, purpose, jurisdiction, and reconciliation identifier.

Possible deployment architectures include:

* In-process enforcement library
* Sidecar enforcement service
* API gateway
* Service-mesh enforcement point
* Database transaction proxy
* Payment gateway
* Operating-system or kernel boundary
* SmartNIC, DPU or FPGA
* HSM, TPM or trusted execution environment
* Hardware-controlled actuator
* Distributed multi-region Finality Sink

Only the single-process Python and SQLite variation was tested in this repository.

---

## 7. Target Latency

The source Internet-Draft does not specify a mandatory numeric latency target.

The repository therefore defines the following non-normative engineering regression targets:

| Path                              | Repository target |
| --------------------------------- | ----------------: |
| Finality Sink p99                 |            ≤ 2 ms |
| Complete local execution path p99 |           ≤ 10 ms |

### Recorded Benchmark

| Stage                              |      Mean |       p50 |       p95 |       p99 |
| ---------------------------------- | --------: | --------: | --------: | --------: |
| Candidate Act preparation          | 0.0130 ms | 0.0092 ms | 0.0174 ms | 0.0636 ms |
| PED validation and handle issuance | 0.2549 ms | 0.1752 ms | 0.5165 ms | 1.8593 ms |
| Sink verification and effect       | 0.1813 ms | 0.1175 ms | 0.3341 ms | 1.5875 ms |
| Complete local path                | 0.4492 ms | 0.3134 ms | 1.0565 ms | 2.8546 ms |

Both repository targets passed during the recorded local benchmark.

These figures are not production SLAs. They exclude:

* Network round-trip time
* Remote evidence retrieval
* Real consequence-simulation time
* Hardware-security operations
* Persistent replicated storage
* Distributed consensus
* External API response time
* Payment settlement
* Queueing and rate limits
* Multi-region communication
* Failure reconciliation

---

## 8. Threat Model

The reference implementation considers:

* Hallucinated AI output
* Prompt-injected instructions
* Unauthorized agent actions
* Output substitution
* Model or workflow substitution
* Tool substitution
* Runtime behavior drift
* Stale or invalid provenance
* Unsupported factual claims
* Unsafe predicted consequences
* Recipient or purpose drift
* Jurisdiction and data-class violations
* Handle theft
* Replay attacks
* Concurrent handle consumption
* Sink substitution
* Policy or revocation changes
* Duplicate approvals
* Receipt modification or removal
* Ambiguous external-effect results
* Missing execution material
* Canonicalization differences

The trusted computing base assumes that the PED, Finality Sink, configured cryptographic secret, clock, epoch source, and SQLite engine are not compromised.

---

## 9. Limitations

* This is not a standards-conformance certification.
* It does not implement a real AI model or agent runtime.
* Validation evidence is supplied to the reference policy; a real evidence-generation system is not included.
* The consequence simulator is represented by a protected validation result rather than a complete world model.
* HMAC-SHA-256 uses a software-held secret and is not a production key-management design.
* No HSM, TPM, secure enclave, TEE, secure boot or remote attestation was used.
* Hardware-bound non-exportability is not demonstrated.
* The execution-material mechanism is a software emulation and does not prove physical non-completability.
* SQLite provides local atomicity, not distributed consensus.
* No real external API, payment rail, satellite controller, robot, database cluster or production system was contacted.
* External-effect idempotency and reconciliation remain adapter-specific.
* Clock distribution, clock rollback protection and epoch synchronization are not implemented.
* Formal verification, fuzzing, penetration testing and hardware fault injection were not performed.
* Other programming-language variations were documented but not tested.
* The benchmark is a local microbenchmark and must not be interpreted as real-world network, financial, legal, industrial or safety-critical performance.

---

## 10. Reference Source and Parameter Selection

The architecture and terminology were derived from `draft-das-protocols-candidate-act-finality-00`.

The following are repository-selected implementation parameters rather than requirements imposed by the draft:

* Python 3.10+
* SHA-256 hashing
* HMAC-SHA-256 reference authentication
* Sorted-key compact JSON
* SQLite state storage
* Thirty-second demonstration handle lifetime
* Local p99 latency goals
* In-process effect simulator
* `candidateActDigest` HCAD extension

Production deployments must select their own cryptographic algorithms, canonicalization specification, key lifecycle, handle lifetime, evidence policy, approval requirements, latency budget, storage consistency model, and effect-reconciliation mechanism.

---

## Intellectual-Property and Licensing Notice

Copyright © 2026 Sangam Kumar Das.

This repository is licensed under the **Creative Commons Attribution-NonCommercial 4.0 International License — CC BY-NC 4.0**:

https://creativecommons.org/licenses/by-nc/4.0/

Attribution is required. Commercial use requires separate written permission from the rights holder.

This copyright license does not grant patent rights. Commercial implementation may require a separate patent license.

Concepts are associated with the DAS Protocols family, including:

**International Application PCT/IB2026/055615**
**WIPO Publication WO 2026/150382**

https://patentscope.wipo.int/search/en/detail.jsf?docId=WO2026150382

Relevant IETF intellectual-property disclosures should follow BCP 79. This repository does not determine patent scope, validity, essentiality, ownership or licensing terms.




