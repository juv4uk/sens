#!/usr/bin/env python3
"""Fail-closed validator for Reality Matrix comparison.json.

This intentionally validates the cross-lane invariants that matter for scientific
comparability without depending on a third-party JSON Schema package.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

VERDICTS = {"sens", "competitor", "pareto", "tie", "inconclusive", "unsupported"}
STATUSES = {"measured", "unsupported", "inconclusive"}
PARITY = {"pass", "fail", "unsupported"}


def fail(message: str) -> None:
    raise SystemExit(f"reality-matrix validation failed: {message}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("comparison", type=Path)
    args = ap.parse_args()

    data = json.loads(args.comparison.read_text(encoding="utf-8"))
    for key in ("system", "sens", "competitor", "environment", "workloads", "verdicts"):
        if key not in data:
            fail(f"missing top-level key {key!r}")

    sens = data["sens"]
    if not sens.get("commit") or not sens.get("contract"):
        fail("SENS commit and Contract version are required")
    if sens.get("contract") != "11.9":
        fail(
            "Reality Matrix current rows require Contract 11.9; "
            "historical contract rows must remain historical provenance"
        )
    ratified_domains = sens.get("ratified_domains")
    if ratified_domains not in {"D1-D7", "D1-D10", "D24+"}:
        fail(
            "ratified_domains must declare the exact in-scope ratified family "
            "(D1-D7, D1-D10, or D24+); do not label research domains ratified"
        )

    competitor = data["competitor"]
    if not competitor.get("name") or not competitor.get("version"):
        fail("competitor name/version are required")

    env = data["environment"]
    for key in ("os", "arch"):
        if not env.get(key):
            fail(f"environment.{key} is required")
    evidence_mode = env.get("evidence_mode")
    if evidence_mode == "performance":
        if env.get("load_context") not in {"idle", "high"}:
            fail("performance evidence requires explicit load_context=idle|high")
        for workload in data["workloads"]:
            if workload.get("parity") == "pass":
                params = workload.get("params", {})
                if "outer_reps" in params and params["outer_reps"] < 10:
                    fail(f"{workload.get('id')}: performance evidence requires >=10 outer_reps")

    workload_ids: set[str] = set()
    for workload in data["workloads"]:
        wid = workload.get("id")
        if not isinstance(wid, str) or not wid:
            fail("workload id must be a non-empty string")
        if wid in workload_ids:
            fail(f"duplicate workload id {wid!r}")
        workload_ids.add(wid)
        parity = workload.get("parity")
        if parity not in PARITY:
            fail(f"{wid}: invalid parity status")

        for measurement in workload.get("measurements", []):
            axis = measurement.get("axis")
            if not isinstance(axis, str) or not axis:
                fail(f"{wid}: measurement axis is required")
            if measurement.get("status") not in STATUSES:
                fail(f"{wid}/{axis}: invalid measurement status")
            if measurement.get("status") == "measured":
                if parity != "pass":
                    fail(f"{wid}/{axis}: measured rows require parity=pass")
                left = measurement.get("sens_samples")
                right = measurement.get("competitor_samples")
                if not isinstance(left, list) or not left or not isinstance(right, list) or not right:
                    fail(f"{wid}/{axis}: measured rows require raw samples")
                if any(not isinstance(value, (int, float)) or value != value for value in left + right):
                    fail(f"{wid}/{axis}: raw samples must be finite numbers")

            # #3698 owns RSS. Only its validated fresh-process GNU-time primitive is admissible.
            if axis == "process_maxrss_kb" and measurement.get("status") == "measured":
                if env.get("rss_measurement") != "gnu-time-per-process-v1":
                    fail(
                        f"{wid}/{axis}: measured RSS requires "
                        "environment.rss_measurement=gnu-time-per-process-v1"
                    )
                for side in ("sens_samples", "competitor_samples"):
                    samples = measurement.get(side, [])
                    if any(value <= 0 for value in samples):
                        fail(f"{wid}/{axis}: RSS samples must be positive")

    seen_axes: set[str] = set()
    for verdict in data["verdicts"]:
        axis = verdict.get("axis")
        value = verdict.get("verdict")
        if not isinstance(axis, str) or not axis:
            fail("verdict axis is required")
        if axis in seen_axes:
            fail(f"duplicate verdict axis {axis!r}")
        seen_axes.add(axis)
        if value not in VERDICTS:
            fail(f"{axis}: invalid verdict {value!r}")
        if not verdict.get("evidence"):
            fail(f"{axis}: evidence text is required")

        # Hosted/CI smoke exists to prove plumbing and parity, never to publish a winner.
        if evidence_mode == "smoke" and value not in {"inconclusive", "unsupported"}:
            fail(f"{axis}: smoke evidence cannot publish verdict={value!r}")

    print(
        f"OK reality-matrix system={data['system']} workloads={len(workload_ids)} "
        f"verdicts={len(seen_axes)} evidence_mode={evidence_mode or 'unspecified'}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
