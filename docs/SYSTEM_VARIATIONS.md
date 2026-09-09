# System variations

The protocol shape is constant; the effect adapter, RCAE fields, approval strength, expiry, and recovery semantics vary by system.

| Variation | Example sink | Important deployment adaptation |
|---|---|---|
| Agent tool call | API gateway | Bind tool name, arguments, tenant and OAuth audience |
| Message send | mail/chat gateway | Bind recipient set, channel and content digest |
| Data export | DLP/export gateway | Classify fields, destination, jurisdiction and volume |
| Database mutation | transaction proxy | Bind database, table/keys and idempotency token |
| Payment/financial action | payment rail adapter | Bind payee, amount, currency, rail and reconciliation ID |
| Network change | controller | Bind devices, commands, maintenance window and rollback |
| Software deployment | release controller | Bind artifact digest, environment, canary and rollback |
| Memory/model update | state or training gate | Bind namespace/model version, provenance and evaluation |
| Physical actuation | safety controller | Hardware interlocks, bounded motion, watchdog and safe state |
| Legal commitment | signature/workflow service | Identity, authority, jurisdiction and human approval |

Architectural placements may include an in-process library for demos, a sidecar or service-mesh enforcement point, a centralized gateway, a kernel/device controller, or a hardware-rooted sink. Distributed variants must provide authenticated transport, consistent time/epoch state, durable atomic consumption, idempotent effects, and reconciliation. The present code implements only a single-process Python/SQLite variation.

