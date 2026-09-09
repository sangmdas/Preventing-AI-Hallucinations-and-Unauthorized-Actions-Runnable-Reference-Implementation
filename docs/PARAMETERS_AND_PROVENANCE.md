# Parameters and provenance

## Source reference

Primary input: `draft-das-protocols-candidate-act-finality-00`, *Stopping AI Hallucinations and Unsafe Acts from Becoming Real-World Consequences (DAS Protocols)*, Sangam Das, Independent Submission, August 2026.

The implementation was derived from the draft's Candidate Act, HCAD, PED, ALF, RBD, OPC/FCU, RCAE, consequence simulation, graduated decision, Execution Handle, Finality Sink, receipt-with-release, epoch, fail-closed, and advanced execution-material concepts. The source XML is not redistributed here.

## Repository-selected parameters

| Parameter | Value | Status |
|---|---|---|
| Hash | SHA-256 | Reference choice, not mandated here |
| Authenticator | HMAC-SHA-256 | Demonstration only |
| Handle lifetime | 30 seconds in demo | Repository parameter |
| Store | SQLite, in memory by default | Reference choice |
| Canonical form | sorted-key compact UTF-8 JSON | Reference choice |
| Sink p99 target | ≤2 ms | Non-normative local regression goal |
| Full-path p99 target | ≤10 ms | Non-normative local regression goal |
| Minimum approvals | risk-class map configured by demo | Policy input |
| `candidateActDigest` | HCAD extension | Repository strengthening |

Normative terms and defaults must ultimately come from the applicable published specification and deployment policy, not this sample.

## Intellectual property

The source associates concepts in the DAS Protocols family with International Application **PCT/IB2026/055615** and indicates that IETF disclosure follows BCP 79. This repository does not determine patent scope, validity, essentiality, ownership, or licensing terms. CC BY-NC 4.0 is a copyright license and grants no patent rights; a commercial implementation may require separate written permission and a separate patent license.

