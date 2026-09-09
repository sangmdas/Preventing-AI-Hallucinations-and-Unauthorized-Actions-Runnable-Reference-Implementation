from __future__ import annotations

import argparse
import json
import platform
import sqlite3
import statistics
import time
from dataclasses import replace

from .demo import build_demo, context_for, request_for


def percentile(values, p):
    ordered = sorted(values); return ordered[min(len(ordered) - 1, int((len(ordered) - 1) * p))]


def summary(values_ns):
    values = [value / 1_000_000 for value in values_ns]
    return {name: round(value, 4) for name, value in {
        "min_ms": min(values), "mean_ms": statistics.fmean(values),
        "p50_ms": percentile(values, .50), "p95_ms": percentile(values, .95),
        "p99_ms": percentile(values, .99), "max_ms": max(values),
    }.items()}


def run(iterations, warmup, consequence):
    base = request_for(consequence)
    _, _, ped, sink, _ = build_demo(base)
    samples = {"prepare": [], "ped_validate_issue": [], "sink_verify_consume_effect": [], "total": []}
    for i in range(iterations + warmup):
        request = replace(base, output=f"{base.output} iteration {i}")
        context = context_for(request)
        t0 = time.perf_counter_ns(); act = ped.prepare(request); t1 = time.perf_counter_ns()
        hcad, _, handle = ped.validate_and_issue(act, context); t2 = time.perf_counter_ns()
        sink.verify_and_effect(act, request, hcad, handle); t3 = time.perf_counter_ns()
        if i >= warmup:
            samples["prepare"].append(t1-t0); samples["ped_validate_issue"].append(t2-t1)
            samples["sink_verify_consume_effect"].append(t3-t2); samples["total"].append(t3-t0)
    return {
        "warning": "Local software benchmark; not a production, hardware-rooted, safety, or distributed-system SLA.",
        "draft_numeric_target": None,
        "reference_engineering_targets": {"sink_p99_ms": 2, "full_local_path_p99_ms": 10, "status": "repository goals only"},
        "environment": {"python": platform.python_version(), "implementation": platform.python_implementation(),
            "platform": platform.platform(), "sqlite": sqlite3.sqlite_version,
            "store": "SQLite :memory:", "authenticator": "HMAC-SHA-256 software",
            "effect_adapter": "in-process simulator", "consequence": consequence},
        "iterations": iterations, "warmup": warmup,
        "results": {name: summary(values) for name, values in samples.items()},
    }


def main():
    parser = argparse.ArgumentParser(); parser.add_argument("--iterations", type=int, default=1000)
    parser.add_argument("--warmup", type=int, default=100)
    parser.add_argument("--consequence", choices=tuple(CONSEQUENCE for CONSEQUENCE in (
        "TOOL_CALL", "MESSAGE_SEND", "DATA_EXPORT", "DATABASE_MUTATION", "NETWORK_CHANGE",
        "SOFTWARE_DEPLOYMENT", "MEMORY_WRITE", "MODEL_UPDATE", "PHYSICAL_ACTUATION", "LEGAL_COMMITMENT")), default="TOOL_CALL")
    args = parser.parse_args()
    if args.iterations < 1 or args.warmup < 0: parser.error("invalid iteration count")
    print(json.dumps(run(args.iterations, args.warmup, args.consequence), indent=2))


if __name__ == "__main__": main()

