from __future__ import annotations

import base64
import hashlib
import json
from typing import Any


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def sha256_hex(value: bytes | str) -> str:
    raw = value.encode("utf-8") if isinstance(value, str) else value
    return hashlib.sha256(raw).hexdigest()


def digest_object(value: Any) -> str:
    return sha256_hex(canonical_json(value))


def b64_sha256(value: Any) -> str:
    digest = hashlib.sha256(canonical_json(value)).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")


def rcae_projection(context) -> dict[str, Any]:
    return {
        "rcaeId": context.rcae_id,
        "permittedRecipient": context.permitted_recipient,
        "permittedPurpose": context.permitted_purpose,
        "permittedJurisdiction": context.permitted_jurisdiction,
        "permittedDataClass": context.permitted_data_class,
        "permittedConsequenceType": context.permitted_consequence_type,
        "maxRiskClass": context.max_risk_class,
        "permittedScopeUnits": context.permitted_scope_units,
        "reversible": context.reversible,
        "canary": context.canary,
    }

