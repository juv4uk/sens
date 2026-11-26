#!/usr/bin/env python3
"""Offline, fail-closed validation of RAPL calibration *records*, not a meter.

No host collection, no energy estimates from TDP, no semantic oracle for SENS.
A structural PASS is never physical calibration or statistical evidence.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")
PACKAGE_PATH = re.compile(r"^/sys/class/powercap/intel-rapl:[0-9]+$")
PACKAGE_NAME = re.compile(r"^package-[0-9]+$")
UTC_TIMESTAMP = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]{1,6})?Z$")


class InvalidRecord(ValueError):
    """The provided record cannot support a measurement claim."""


def require(condition: bool, code: str) -> None:
    if not condition:
        raise InvalidRecord(code)


def nonempty(value: object, code: str) -> str:
    require(isinstance(value, str) and bool(value.strip()), code)
    return value


def positive_int(value: object, code: str) -> int:
    require(type(value) is int and value > 0, code)
    return value


def natural_int(value: object, code: str) -> int:
    require(type(value) is int and value >= 0, code)
    return value


def sha40(value: object, code: str) -> str:
    require(isinstance(value, str) and bool(HEX40.fullmatch(value)), code)
    return value


def unique_json_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    """Preserve raw provenance: reject ambiguous duplicate keys at every depth."""
    result: dict[str, object] = {}
    for key, value in pairs:
        require(key not in result, f"DUPLICATE_JSON_KEY:{key}")
        result[key] = value
    return result


def reject_json_constant(value: str) -> None:
    """Python accepts NaN/Infinity extensions by default; raw JSON must not."""
    raise InvalidRecord(f"NONFINITE_JSON_CONSTANT:{value}")


def reject_nonfinite_float(raw: str) -> float:
    """Reject JSON exponent overflow before it can become an infinite float."""
    value = float(raw)
    require(math.isfinite(value), "NONFINITE_JSON_FLOAT")
    return value


def parse_raw_json(payload: str) -> object:
    """Read JSON without discarding duplicates or admitting nonfinite values."""
    return json.loads(
        payload,
        object_pairs_hook=unique_json_object,
        parse_constant=reject_json_constant,
        parse_float=reject_nonfinite_float,
    )


def utc_instant(value: object, code: str) -> datetime:
    """Require a real RFC3339 UTC instant; normalize fractional forms for equality.

    Timestamp integrity is necessary for provenance, never proof that sessions
    were independent physical repetitions.
    """
    require(isinstance(value, str) and UTC_TIMESTAMP.fullmatch(value) is not None, code)
    try:
        instant = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise InvalidRecord(code) from exc
    require(instant.tzinfo == timezone.utc, code)
    return instant


def validate_counter(raw: object, *, energy_range: int, max_power_w: int, label: str) -> int:
    """Validate single-wrap *plausibility* using an externally documented ceiling.

    A ceiling does not prove correct measurement or that the power actually
    stayed under that bound; collector provenance is externally verified.
    This deliberately does not implement RAPL acquisition from issue #6275.
    """
    require(isinstance(raw, dict), f"{label}:NOT_OBJECT")
    elapsed_ns = positive_int(raw.get("elapsed_ns"), f"{label}:INVALID_ELAPSED_NS")
    start = natural_int(raw.get("start_uj"), f"{label}:INVALID_COUNTER_START")
    end = natural_int(raw.get("end_uj"), f"{label}:INVALID_COUNTER_END")
    require(start < energy_range and end < energy_range, f"{label}:COUNTER_OUT_OF_RANGE")
    # Power[W] * time[ns] / 1000 = upper bound in microjoules.
    # Strictly below one complete counter range is necessary to exclude >=2 wraps.
    require(max_power_w * elapsed_ns < energy_range * 1000,
            f"{label}:MULTIPLE_WRAP_NOT_EXCLUDED")
    delta = end - start if end >= start else end + energy_range - start
    require(delta > 0, f"{label}:ZERO_DELTA_NOT_MEASUREMENT")
    require(delta * 1000 <= max_power_w * elapsed_ns,
            f"{label}:DELTA_EXCEEDS_DOCUMENTED_POWER_CEILING")
    return delta


def validate(data: object) -> dict[str, object]:
    require(isinstance(data, dict), "ROOT_NOT_OBJECT")
    require(data.get("schema") == "sens-energy-calibration/v1", "UNSUPPORTED_SCHEMA")
    require(data.get("mode") in ("SYNTHETIC", "PHYSICAL"), "INVALID_MODE")
    provenance = data.get("provenance")
    require(isinstance(provenance, dict), "PROVENANCE_MISSING")
    for key in ("machine_id", "cpu_model", "os_release", "kernel", "governor",
                "sensor_name", "functional_unit", "clock", "power_ceiling_reference",
                "recorded_at_utc"):
        nonempty(provenance.get(key), f"MISSING_{key.upper()}")
    for key in ("source_sha", "collector_sha", "input_sha"):
        sha40(provenance.get(key), f"INVALID_{key.upper()}")
    require(provenance["clock"] == "monotonic_ns", "CLOCK_NOT_MONOTONIC")
    utc_instant(provenance["recorded_at_utc"], "INVALID_PROVENANCE_UTC_TIMESTAMP")
    require(PACKAGE_NAME.fullmatch(provenance["sensor_name"]) is not None,
            "NOT_CPU_PACKAGE_DOMAIN")
    require(isinstance(provenance.get("sensor_path"), str) and
            PACKAGE_PATH.fullmatch(provenance["sensor_path"]) is not None,
            "INVALID_PACKAGE_SENSOR_PATH")
    require(provenance.get("energy_unit") == "microjoule", "ENERGY_UNIT_MISMATCH")
    energy_range = positive_int(provenance.get("max_energy_range_uj"),
                                "INVALID_MAX_ENERGY_RANGE")
    max_power_w = positive_int(provenance.get("documented_max_package_power_w"),
                               "POWER_CEILING_NOT_DOCUMENTED")
    require(isinstance(provenance.get("sensor_access_confirmed"), bool),
            "SENSOR_ACCESS_STATUS_MISSING")
    if not provenance["sensor_access_confirmed"]:
        raise InvalidRecord("ENERGY_NOT_MEASURED:SENSOR_UNAVAILABLE")
    sessions = data.get("sessions")
    require(isinstance(sessions, list) and len(sessions) >= 2,
            "NOT_ENOUGH_SESSION_RECORDS")
    seen_sessions: set[str] = set()
    seen_session_instants: set[datetime] = set()
    binary_shas: dict[str, str] = {}
    outputs: set[str] = set()
    unit_count: int | None = None
    blocks_count = 0
    for session in sessions:
        require(isinstance(session, dict), "SESSION_NOT_OBJECT")
        name = nonempty(session.get("id"), "SESSION_ID_MISSING")
        require(name not in seen_sessions, "DUPLICATE_SESSION_ID")
        seen_sessions.add(name)
        instant = utc_instant(session.get("recorded_at_utc"),
                              "INVALID_SESSION_UTC_TIMESTAMP")
        require(instant not in seen_session_instants, "DUPLICATE_SESSION_INSTANT")
        seen_session_instants.add(instant)
        temperature = session.get("cpu_temperature_c")
        require(type(temperature) in (int, float) and 0 <= temperature <= 110,
                "INVALID_TEMPERATURE_C")
        overhead = positive_int(session.get("read_overhead_ns"), "MISSING_READ_OVERHEAD_NS")
        idle = session.get("idle_control")
        validate_counter(idle, energy_range=energy_range,
                         max_power_w=max_power_w, label="IDLE")
        require(idle["elapsed_ns"] > overhead, "IDLE_SHORTER_THAN_SENSOR_READ")
        blocks = session.get("blocks")
        require(isinstance(blocks, list) and len(blocks) == 2,
                "BALANCED_BLOCK_PAIR_REQUIRED")
        orders = set()
        seen_blocks = set()
        for block in blocks:
            require(isinstance(block, dict), "BLOCK_NOT_OBJECT")
            block_id = nonempty(block.get("id"), "BLOCK_ID_MISSING")
            require(block_id not in seen_blocks, "DUPLICATE_BLOCK_ID")
            seen_blocks.add(block_id)
            order = block.get("order")
            require(order in ("AB", "BA"), "INVALID_BLOCK_ORDER")
            orders.add(order)
            runs = block.get("runs")
            require(isinstance(runs, list) and len(runs) == 2,
                    "PAIRED_RUNS_REQUIRED")
            require([r.get("arm") if isinstance(r, dict) else None for r in runs]
                    == list(order), "AB_BA_ORDER_MISMATCH")
            for run in runs:
                arm = run["arm"]
                sha = sha40(run.get("binary_sha"), "INVALID_BINARY_SHA")
                if arm in binary_shas:
                    require(binary_shas[arm] == sha, "BINARY_CHANGED_DURING_STUDY")
                binary_shas[arm] = sha
                output = run.get("output_sha256")
                require(isinstance(output, str) and HEX64.fullmatch(output) is not None,
                        "INVALID_OUTPUT_DIGEST")
                outputs.add(output)
                units = positive_int(run.get("functional_units"), "INVALID_WORK_UNITS")
                if unit_count is not None:
                    require(units == unit_count, "UNEQUAL_FUNCTIONAL_UNITS")
                unit_count = units
                validate_counter(run, energy_range=energy_range,
                                 max_power_w=max_power_w, label="RUN")
                require(run["elapsed_ns"] > overhead, "RUN_SHORTER_THAN_SENSOR_READ")
                rss = run.get("peak_rss_bytes")
                require(type(rss) is int and rss > 0, "PEAK_RSS_NOT_RECORDED")
                require(run.get("exit_code") == 0 and type(run.get("exit_code")) is int,
                        "WORKLOAD_FAILED")
            blocks_count += 1
        require(orders == {"AB", "BA"}, "BALANCED_AB_BA_REQUIRED")
    require(len(outputs) == 1, "OUTPUT_PARITY_MISMATCH")
    # Deliberately no joules, estimated energy, performance ranking, independence,
    # 'calibrated' or SCI score in this output: no physical provenance verification.
    return {"status": "STRUCTURAL_PASS", "record_mode": data["mode"],
            "sessions": len(seen_sessions), "blocks": blocks_count,
            "result_parity": "DIGEST_MATCH_ONLY",
            "energy": "PHYSICAL_CALIBRATION_NOT_VERIFIED",
            "sensor": "CPU_PACKAGE_INCLUDES_BACKGROUND"}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate offline RAPL calibration metadata and raw counter records")
    parser.add_argument("record", type=Path, help="JSON raw calibration record; no sensor is queried")
    args = parser.parse_args(argv)
    try:
        data = parse_raw_json(args.record.read_text(encoding="utf-8"))
        result = validate(data)
    except (InvalidRecord, OSError, UnicodeError, json.JSONDecodeError,
            RecursionError) as exc:
        reason = ("JSON_TOO_DEEP" if isinstance(exc, RecursionError)
                  else str(exc))
        status = "ENERGY_NOT_MEASURED" if "ENERGY_NOT_MEASURED" in reason else "CALIBRATION_REJECTED"
        print(json.dumps({"status": status, "reason": reason}, ensure_ascii=False, sort_keys=True))
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
