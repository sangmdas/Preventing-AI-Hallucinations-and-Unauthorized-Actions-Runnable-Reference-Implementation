# Latency targets and measurement

The source draft defines no numeric latency objective. The repository therefore sets two **non-normative regression goals** for this local software configuration: sink verification/consume/effect p99 ≤2 ms and full local path p99 ≤10 ms. They are not protocol requirements or production SLAs.

## Recorded run

CPython 3.12.14; Linux 6.18.35 x86_64 with glibc 2.39; SQLite 3.53.1 `:memory:`; HMAC-SHA-256 in software; in-process deterministic effect adapter; `TOOL_CALL`; 100 warmups followed by 1,000 measured iterations.

| Stage | Mean | p50 | p95 | p99 | Max |
|---|---:|---:|---:|---:|---:|
| Prepare | 0.0130 ms | 0.0092 | 0.0174 | 0.0636 | 0.8265 |
| PED validate/issue | 0.2549 ms | 0.1752 | 0.5165 | 1.8593 | 6.1166 |
| Sink verify/consume/effect | 0.1813 ms | 0.1175 | 0.3341 | 1.5875 | 6.1964 |
| Full local path | 0.4492 ms | 0.3134 | 1.0565 | 2.8546 | 9.2971 |

Both repository goals passed in this run. Measurements exclude network RTT, remote evidence services, real consequence simulation, persistent disk synchronization, HSM/TEE calls, replicated consensus, queueing, rate limits, external effect time, and reconciliation. Production targets should be split into validation, authorization, sink verification, effect-provider, and end-to-end budgets and measured under load with cold starts, failures, contention, and tail latency.

