#!/usr/bin/env python3
"""#3685: first SENS vs Nock artifact-size reality slice."""

from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import os
import platform
import subprocess
import tempfile
from pathlib import Path
from typing import TypeAlias

ROOT = Path(__file__).resolve().parents[4]
FIXTURE = ROOT / "benchmarks" / "current-en-vs-d1d8" / "fixtures" / "d3-smoke.json"
JAM_PY = Path(__file__).with_name("jam.py")
PACK_EXAMPLE = "store_air_load_repr"
CASES = ("d3-quote-empty", "d3-car-empty")

DOCS_SHA = "72133b05e5ee3994449e335a5d314394e9a42cc9"
PY_NOUN_SHA = "c9c91ce142cfe85edbed320138f21c7213aceaab"
VERE_TAG = "vere-v4.6"
VERE_SHA = "8ddc4b786979574dbfcb655e3db1b634f658d0de"

Noun: TypeAlias = int | tuple["Noun", "Noun"]


def load_jam_module():
    spec = importlib.util.spec_from_file_location("reality_nock_jam", JAM_PY)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {JAM_PY}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_text(args: list[str], *, cwd: Path | None = None) -> str:
    return subprocess.check_output(args, cwd=cwd, text=True, stderr=subprocess.STDOUT).strip()


def parse_kv(text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for raw in text.splitlines():
        if "=" in raw:
            key, value = raw.split("=", 1)
            out[key.strip()] = value.strip()
    return out


def contract_version() -> str:
    import re

    text = (ROOT / "language-contract.lisp").read_text(encoding="utf-8")
    match = re.search(
        r"\(\(major\s+\.\s+#d(?P<major>[0-9]+)\)\s+\(minor\s+\.\s+(?P<minor>[0-9]+)\)",
        text,
    )
    if match is None:
        raise RuntimeError("cannot read Contract version")
    return f"{match.group('major')}.{match.group('minor')}"


def build_pack_helper() -> Path:
    subprocess.run(
        ["cargo", "build", "--release", "-p", "sens", "--example", PACK_EXAMPLE],
        cwd=ROOT,
        check=True,
    )
    suffix = ".exe" if os.name == "nt" else ""
    helper = ROOT / "target" / "release" / "examples" / f"{PACK_EXAMPLE}{suffix}"
    if not helper.is_file():
        raise FileNotFoundError(helper)
    return helper


def load_cases() -> dict[str, dict[str, object]]:
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    ready = {
        row["id"]: row
        for row in payload["workloads"]
        if row.get("status") == "ready" and row.get("id") in CASES
    }
    missing = sorted(set(CASES) - set(ready))
    if missing:
        raise RuntimeError(f"missing ready fixtures: {missing}")
    return ready


def packing_facts(helper: Path, source: Path) -> tuple[int, int]:
    fields = parse_kv(run_text([str(helper), str(source), "0"]))
    if fields.get("ROUNDTRIP_WORDS_OK") != "1":
        raise RuntimeError("SENS exact-width production round-trip failed")
    return int(fields["SEMANTIC_PAYLOAD_BITS"]), int(fields["PHYSICAL_CONTAINER_BYTES"])


def slot(axis: int, noun: Noun) -> Noun:
    if axis <= 0:
        raise ValueError("Nock axes are positive")
    if axis == 1:
        return noun
    if not isinstance(noun, tuple):
        raise ValueError("axis descends into atom")
    if axis % 2 == 0:
        return slot(axis // 2, noun[0])
    return slot(axis // 2, noun[1])


def nock(subject: Noun, formula: Noun) -> Noun:
    """Tiny correctness oracle for only the 0/1/7 rules used by this slice."""
    if not isinstance(formula, tuple):
        raise ValueError("formula must be a cell")

    op, tail = formula

    if op == 0:
        if not isinstance(tail, int):
            raise ValueError("opcode 0 axis must be an atom")
        return slot(tail, subject)

    if op == 1:
        return tail

    if op == 7:
        if not isinstance(tail, tuple):
            raise ValueError("opcode 7 requires two formulas")
        first, second = tail
        return nock(nock(subject, first), second)

    raise ValueError(f"unsupported control-slice opcode: {op!r}")


def formula_for(case: str) -> Noun:
    if case == "d3-quote-empty":
        # *[0 [1 0]] => 0
        return (1, 0)
    if case == "d3-car-empty":
        # *[0 [7 [1 [0 0]] [0 2]]] => 0
        # First produce the literal cell [0 0], then slot axis 2 (head).
        return (7, ((1, (0, 0)), (0, 2)))
    raise KeyError(case)


def lower_wins(sens_value: float, nock_value: float) -> str:
    if sens_value < nock_value:
        return "sens"
    if nock_value < sens_value:
        return "competitor"
    return "tie"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", required=True, type=Path)
    args = ap.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)
    raw_dir = args.out_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    jammod = load_jam_module()
    jammod.verify_official_vectors()
    pack = build_pack_helper()
    fixtures = load_cases()

    rows: list[dict[str, object]] = []
    workloads: list[dict[str, object]] = []
    verdicts: list[dict[str, str]] = []

    with tempfile.TemporaryDirectory(prefix="sens-nock-reality-") as tmp_name:
        tmp = Path(tmp_name)

        for case in CASES:
            row = fixtures[case]
            canonical = tmp / f"{case}.canonical.lisp"
            canonical.write_text(str(row["canonical_source"]), encoding="utf-8")

            sens_bits, sens_bytes = packing_facts(pack, canonical)
            formula = formula_for(case)
            observed = nock(0, formula)
            if observed != 0 or row["expected_value"] != "()":
                raise RuntimeError(f"{case}: Nock control oracle mismatch: {observed!r}")

            formula_bits = jammod.jam_bit_length(formula)
            formula_bytes = jammod.jam_byte_length(formula)
            capsule = (0, formula)
            capsule_bits = jammod.jam_bit_length(capsule)
            capsule_bytes = jammod.jam_byte_length(capsule)

            measurements = [
                {
                    "axis": "program_semantic_or_jam_bits",
                    "status": "measured",
                    "unit": "bits",
                    "sens_samples": [float(sens_bits)],
                    "competitor_samples": [float(formula_bits)],
                    "sens_median": float(sens_bits),
                    "competitor_median": float(formula_bits),
                    "sens_p95": float(sens_bits),
                    "competitor_p95": float(formula_bits),
                    "notes": "SENS exact semantic payload vs jammed self-contained Nock formula. Generic runtimes excluded.",
                },
                {
                    "axis": "program_container_or_jam_bytes",
                    "status": "measured",
                    "unit": "bytes",
                    "sens_samples": [float(sens_bytes)],
                    "competitor_samples": [float(formula_bytes)],
                    "sens_median": float(sens_bytes),
                    "competitor_median": float(formula_bytes),
                    "sens_p95": float(sens_bytes),
                    "competitor_p95": float(formula_bytes),
                    "notes": "SENS production packed byte container vs byte container needed by jammed Nock formula.",
                },
                {
                    "axis": "nock_execution_capsule_bits",
                    "status": "inconclusive",
                    "unit": "bits",
                    "sens_samples": [],
                    "competitor_samples": [],
                    "sens_median": None,
                    "competitor_median": None,
                    "sens_p95": None,
                    "competitor_p95": None,
                    "notes": f"Diagnostic only: jam([subject=0 formula])={capsule_bits} bits/{capsule_bytes} bytes; SENS session/subject boundary is different.",
                },
            ]

            verdicts.extend(
                [
                    {
                        "axis": f"{case}:program_semantic_or_jam_bits",
                        "verdict": lower_wins(float(sens_bits), float(formula_bits)),
                        "evidence": f"SENS={sens_bits} bits; Nock jam formula={formula_bits} bits",
                    },
                    {
                        "axis": f"{case}:program_container_or_jam_bytes",
                        "verdict": lower_wins(float(sens_bytes), float(formula_bytes)),
                        "evidence": f"SENS={sens_bytes} bytes; Nock jam formula={formula_bytes} bytes",
                    },
                    {
                        "axis": f"{case}:nock_execution_capsule_bits",
                        "verdict": "inconclusive",
                        "evidence": f"Nock subject+formula capsule={capsule_bits} bits/{capsule_bytes} bytes; boundary differs from SENS session",
                    },
                ]
            )

            workloads.append(
                {
                    "id": case,
                    "parity": "pass",
                    "params": {
                        "scope": "artifact-size/correctness only; no Nock runtime speed claim",
                        "nock_subject": 0,
                        "nock_formula": repr(formula),
                        "nock_jam_integer": jammod.jam(formula),
                        "nock_formula_bits": formula_bits,
                        "nock_formula_bytes": formula_bytes,
                        "nock_capsule_bits": capsule_bits,
                        "nock_capsule_bytes": capsule_bytes,
                    },
                    "measurements": measurements,
                }
            )

            rows.append(
                {
                    "workload": case,
                    "sens_bits": sens_bits,
                    "sens_packed_bytes": sens_bytes,
                    "nock_formula": repr(formula),
                    "nock_jam_integer": jammod.jam(formula),
                    "nock_jam_bits": formula_bits,
                    "nock_jam_bytes": formula_bytes,
                    "nock_capsule_bits": capsule_bits,
                    "nock_capsule_bytes": capsule_bytes,
                }
            )

    environment = {
        "os": platform.platform(),
        "arch": platform.machine(),
        "cpu": platform.processor() or None,
        "load_context": "unknown",
        "evidence_mode": "artifact",
        "toolchain": {
            "nock_spec_docs_commit": DOCS_SHA,
            "pynoun_reference_commit": PY_NOUN_SHA,
            "vere_runtime_tag": VERE_TAG,
            "vere_runtime_commit": VERE_SHA,
        },
    }
    comparison = {
        "system": "nock",
        "sens": {
            "commit": run_text(["git", "rev-parse", "HEAD"], cwd=ROOT),
            "contract": contract_version(),
            "ratified_domains": "D1-D7",
        },
        "competitor": {
            "name": "Nock 4K + jam",
            "version": f"docs={DOCS_SHA[:12]} pynoun={PY_NOUN_SHA[:12]}",
            "commit": PY_NOUN_SHA,
        },
        "environment": environment,
        "workloads": workloads,
        "semantic_density": None,
        "verdicts": verdicts,
    }

    with (raw_dir / "artifact.tsv").open("w", newline="", encoding="utf-8") as fh:
        fields = list(rows[0].keys())
        writer = csv.DictWriter(fh, fieldnames=fields, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)

    (args.out_dir / "environment.json").write_text(
        json.dumps(environment, indent=2) + "\n", encoding="utf-8"
    )
    (args.out_dir / "comparison.json").write_text(
        json.dumps(comparison, indent=2) + "\n", encoding="utf-8"
    )

    validator = ROOT / "benchmarks" / "cross-language" / "reality-matrix" / "validate.py"
    subprocess.run(["python3", str(validator), str(args.out_dir / "comparison.json")], check=True)

    report = [
        "# SENS vs Nock — artifact-size reality slice",
        "",
        "Official jam examples are verified before measurement.",
        "Runtime speed is intentionally absent; Vere owns that future evidence.",
        "",
        "| axis | verdict | evidence |",
        "|---|---|---|",
    ]
    for item in verdicts:
        report.append(f"| {item['axis']} | {item['verdict']} | {item['evidence']} |")
    report.append("")
    (args.out_dir / "report.md").write_text("\n".join(report), encoding="utf-8")
    print("\n".join(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
