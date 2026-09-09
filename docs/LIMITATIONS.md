# Limitations

- This is an informative interpretation of an Internet-Draft, not a normative implementation or certification.
- ALF, RBD, OPC/FCU, simulation, RCAE, and human approval are represented by supplied reference inputs; their real derivation and attestation are not implemented.
- HMAC uses an in-process secret. There is no PKI, key rotation, HSM, TPM, TEE, secure boot, remote attestation, or hardware-bound non-exportable authority.
- Reconstructed execution material is a software demonstration. It does not prove that an unauthorized system is physically incapable of completing an act.
- SQLite provides local atomicity only. Multi-process and distributed deployments require carefully designed durable consistency and recovery.
- The deterministic effect adapter does not contact a real service. External idempotency, partial failure, compensation, settlement, and reconciliation remain system-specific.
- No real-time guarantee exists. Wall-clock trust, clock skew, epoch distribution, rollback protection, and long-running act expiry need production design.
- Canonical JSON is deliberately small and not a selected standards-track canonicalization profile.
- Inputs are strings and simple bounds; production schema validation, Unicode policy, size limits, resource quotas, logging privacy, and denial-of-service defenses are incomplete.
- Python is the only implemented language. Tables describing other languages and systems are design guidance, not test results.
- The benchmark is a local microbenchmark and cannot predict networked, hardware-backed, safety-critical, legal, financial, or physical-actuation latency.
- PED and Finality Sink compromise is outside the reference threat model.

