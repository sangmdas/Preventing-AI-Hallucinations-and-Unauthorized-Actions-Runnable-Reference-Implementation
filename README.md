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

## License and intellectual property

Copyright © 2026 Sangam Kumar Das. Licensed under **CC BY-NC 4.0 International**; attribution is required and commercial use requires separate written permission. This license does not grant patent rights. Commercial implementation may require a separate patent license. See [LICENSE.md](LICENSE.md) and relevant IETF disclosures under BCP 79.

