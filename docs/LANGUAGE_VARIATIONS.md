# Language variations

Only the Python 3.10+ implementation is executable and tested here. Ports must reproduce canonical JSON and the supplied SHA-256 vectors before they can be considered interoperable.

| Language/runtime | Recommended mapping | Main portability risk |
|---|---|---|
| TypeScript/Node.js | immutable interfaces, `crypto`, transactional DB client | number precision, object omission, async races |
| Go | structs with explicit JSON tags, `crypto/hmac`, SQL transaction | zero values and time formatting |
| Rust | Serde types, `sha2`/`hmac`, transactional store | enum/schema compatibility |
| Java/Kotlin | records/data classes, JCA, JDBC transaction | map order and timestamp precision |
| C#/.NET | records, `System.Text.Json`, cryptography, DB transaction | naming policies and date serialization |
| C/C++ | generated schema types, vetted crypto, durable state machine | memory safety and bespoke serialization |
| WebAssembly | host-provided clock, storage, crypto and sink ABI | trusted host boundary and persistence |
| FPGA/secure element | fixed message layout and hardware key slots | feature evolution and canonicalization |

All ports need byte-for-byte UTF-8 canonicalization, timezone-aware UTC timestamps, constant-time authentication comparison, overflow-safe expiry checks, atomic one-time consumption, crash recovery, stable error semantics, and concurrency tests. Do not treat a source-level port as validated until it passes the common vectors plus equivalent negative, replay, race, and recovery tests.

