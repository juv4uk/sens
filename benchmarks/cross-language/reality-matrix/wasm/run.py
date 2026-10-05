#!/usr/bin/env python3
"""#3681: current exact-domain SENS vs minimal WebAssembly controls."""

from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import os
import platform
import statistics
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
FIXTURE = ROOT / "benchmarks" / "current-en-vs-d1d8" / "fixtures" / "d3-smoke.json"
CONTROL_JS = Path(__file__).with_name("wasm_control.js")
MODULE_PY = Path(__file__).with_name("wasm_module.py")
RSS_PY = Path(__file__).resolve().parents[1] / "rss.py"
SENS_EXAMPLE = "current_en_vs_d1d8_cpu"
PACK_EXAMPLE = "store_air_load_repr"
CASES = ("d3-quote-empty", "d3-car-empty")


def run_text(args: list[str], *, cwd: Path | None = None) -> str:
    return subprocess.check_output(args, cwd=cwd, text=True, stderr=subprocess.STDOUT).strip()


def parse_kv(text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for raw in text.splitlines():
        if "=" in raw:
            key, value = raw.split("=", 1)
            out[key.strip()] = value.strip()
    return out


def decode_hex(value: str) -> str:
    return bytes.fromhex(value).decode("utf-8")


def load_module_builders():
    spec = importlib.util.spec_from_file_location("reality_wasm_module", MODULE_PY)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {MODULE_PY}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_rss_module():
    spec = importlib.util.spec_from_file_location("reality_matrix_rss", RSS_PY)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {RSS_PY}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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


def build_sens_helpers() -> tuple[Path, Path]:
    subprocess.run(
        [
            "cargo",
            "build",
            "--release",
            "-p",
            "sens",
            "--example",
            SENS_EXAMPLE,
            "--example",
            PACK_EXAMPLE,
        ],
        cwd=ROOT,
        check=True,
    )
    suffix = ".exe" if os.name == "nt" else ""
    sens = ROOT / "target" / "release" / "examples" / f"{SENS_EXAMPLE}{suffix}"
    pack = ROOT / "target" / "release" / "examples" / f"{PACK_EXAMPLE}{suffix}"
    if not sens.is_file() or not pack.is_file():
        raise FileNotFoundError("expected SENS benchmark helpers were not built")
    return sens, pack


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


def write_sources(tmp: Path, row: dict[str, object]) -> tuple[Path, Path]:
    english = tmp / f"{row['id']}.english.lisp"
    canonical = tmp / f"{row['id']}.canonical.lisp"
    english.write_text(str(row["english_source"]), encoding="utf-8")
    canonical.write_text(str(row["canonical_source"]), encoding="utf-8")
    return english, canonical


def sens_preflight(helper: Path, candidate: str, source: Path) -> dict[str, str]:
    fields = parse_kv(run_text([str(helper), candidate, "preflight", str(source)]))
    return {
        "trace": decode_hex(fields["TRACE_HEX"]),
        "value": decode_hex(fields["VALUE_HEX"]),
        "output": decode_hex(fields["OUTPUT_HEX"]),
    }


def sens_elapsed(helper: Path, candidate: str, phase: str, source: Path, repeat: int = 1) -> int:
    command = [str(helper), candidate, phase, str(source)]
    if phase == "repeated":
        command.append(str(repeat))
    fields = parse_kv(run_text(command))
    return int(fields["ELAPSED_NS"])


def packing_facts(helper: Path, source: Path) -> dict[str, int]:
    fields = parse_kv(run_text([str(helper), str(source), "0"]))
    if fields.get("ROUNDTRIP_WORDS_OK") != "1":
        raise RuntimeError("SENS production packer round-trip failed")
    return {
        "semantic_bits": int(fields["SEMANTIC_PAYLOAD_BITS"]),
        "packed_bytes": int(fields["PHYSICAL_CONTAINER_BYTES"]),
    }


def wasm_elapsed(node: str, module: Path, mode: str, repeat: int = 1) -> int:
    command = [node, str(CONTROL_JS), str(module), mode]
    if mode == "call":
        command.append(str(repeat))
    fields = parse_kv(run_text(command))
    return int(fields["ELAPSED_NS"])


def wasm_value(node: str, module: Path) -> str:
    fields = parse_kv(run_text([node, str(CONTROL_JS), str(module), "preflight"]))
    return fields["VALUE"]


def percentile95(values: list[float]) -> float:
    ordered = sorted(values)
    rank = max(0, min(len(ordered) - 1, (95 * len(ordered) + 99) // 100 - 1))
    return ordered[rank]


def summary(values: list[float]) -> tuple[float, float]:
    return float(statistics.median(values)), float(percentile95(values))


def lower_wins(sens_value: float, competitor_value: float) -> str:
    if sens_value < competitor_value:
        return "sens"
    if competitor_value < sens_value:
        return "competitor"
    return "tie"


def allowed_verdict(args, sens_value: float, wasm_value_: float) -> str:
    if args.evidence_mode != "performance":
        return "inconclusive"
    return lower_wins(sens_value, wasm_value_)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", required=True, type=Path)
    ap.add_argument("--outer-reps", type=int, default=10)
    ap.add_argument("--inner-repeats", type=int, default=10000)
    ap.add_argument("--node", default="node")
    ap.add_argument("--evidence-mode", choices=("smoke", "performance"), default="smoke")
    ap.add_argument("--load-context", choices=("idle", "high", "unknown"), default="unknown")
    args = ap.parse_args()

    if args.outer_reps <= 0 or args.inner_repeats <= 0:
        raise SystemExit("repeat counts must be positive")
    if args.evidence_mode == "performance" and args.outer_reps < 10:
        raise SystemExit("performance mode requires at least 10 outer repetitions")
    if args.evidence_mode == "performance" and args.load_context == "unknown":
        raise SystemExit("performance mode requires explicit idle/high load context")

    node_version = run_text([args.node, "--version"])
    args.out_dir.mkdir(parents=True, exist_ok=True)
    raw_dir = args.out_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    sens, pack = build_sens_helpers()
    fixtures = load_cases()
    builders = load_module_builders()
    rssmod = load_rss_module()
    rss_available = bool(rssmod.GNU_TIME.is_file())

    raw_rows: list[dict[str, object]] = []
    workloads: list[dict[str, object]] = []
    verdicts: list[dict[str, str]] = []

    with tempfile.TemporaryDirectory(prefix="sens-wasm-reality-") as tmp_name:
        tmp = Path(tmp_name)

        for case in CASES:
            row = fixtures[case]
            english, canonical = write_sources(tmp, row)
            module_path = tmp / f"{case}.wasm"
            module_path.write_bytes(builders.MODULES[case]())

            english_pf = sens_preflight(sens, "english-surface", english)
            canonical_pf = sens_preflight(sens, "canonical-d1d8", canonical)
            if english_pf != canonical_pf:
                raise RuntimeError(f"{case}: SENS English/canonical preflight mismatch")
            if canonical_pf["value"] != row["expected_value"] or canonical_pf["output"] != row["expected_output"]:
                raise RuntimeError(f"{case}: SENS fixture oracle mismatch")

            w_value = wasm_value(args.node, module_path)
            if w_value != "0" or row["expected_value"] != "()":
                raise RuntimeError(f"{case}: Wasm control oracle mismatch: VALUE={w_value!r}")

            pack_info = packing_facts(pack, canonical)
            wasm_bytes = module_path.stat().st_size

            sens_ingest: list[float] = []
            wasm_compile: list[float] = []
            sens_warm: list[float] = []
            wasm_warm: list[float] = []
            sens_cold: list[float] = []
            wasm_cold: list[float] = []
            sens_rss: list[float] = []
            wasm_rss: list[float] = []

            for rep in range(args.outer_reps):
                s_ing = float(sens_elapsed(sens, "canonical-d1d8", "ingest", canonical))
                w_comp = float(wasm_elapsed(args.node, module_path, "compile"))
                s_warm = sens_elapsed(
                    sens, "canonical-d1d8", "repeated", canonical, args.inner_repeats
                ) / args.inner_repeats
                w_warm = wasm_elapsed(
                    args.node, module_path, "call", args.inner_repeats
                ) / args.inner_repeats
                s_cold = float(sens_elapsed(sens, "canonical-d1d8", "full", canonical))
                w_cold = float(wasm_elapsed(args.node, module_path, "cold"))

                sens_ingest.append(s_ing)
                wasm_compile.append(w_comp)
                sens_warm.append(s_warm)
                wasm_warm.append(w_warm)
                sens_cold.append(s_cold)
                wasm_cold.append(w_cold)

                s_rss = None
                w_rss = None
                if rss_available:
                    sens_rss_cmd = [
                        str(sens), "canonical-d1d8", "repeated",
                        str(canonical), str(args.inner_repeats),
                    ]
                    wasm_rss_cmd = [
                        args.node, str(CONTROL_JS), str(module_path),
                        "call", str(args.inner_repeats),
                    ]
                    _s_out, _s_err, s_rss = rssmod.measure_peak_rss_kb(sens_rss_cmd)
                    _w_out, _w_err, w_rss = rssmod.measure_peak_rss_kb(wasm_rss_cmd)
                    sens_rss.append(float(s_rss))
                    wasm_rss.append(float(w_rss))

                raw_rows.append(
                    {
                        "workload": case,
                        "rep": rep,
                        "inner_repeats": args.inner_repeats,
                        "sens_ingest_ns": s_ing,
                        "wasm_compile_ns": w_comp,
                        "sens_warm_ns_per_op": s_warm,
                        "wasm_warm_ns_per_op": w_warm,
                        "sens_cold_full_ns": s_cold,
                        "wasm_cold_ns": w_cold,
                        "sens_maxrss_kb": "" if s_rss is None else s_rss,
                        "wasm_maxrss_kb": "" if w_rss is None else w_rss,
                    }
                )

            si_med, si_p95 = summary(sens_ingest)
            wc_med, wc_p95 = summary(wasm_compile)
            sw_med, sw_p95 = summary(sens_warm)
            ww_med, ww_p95 = summary(wasm_warm)
            sc_med, sc_p95 = summary(sens_cold)
            wco_med, wco_p95 = summary(wasm_cold)

            artifact_s_bits = float(pack_info["semantic_bits"])
            artifact_w_bits = float(wasm_bytes * 8)
            container_s_bytes = float(pack_info["packed_bytes"])
            container_w_bytes = float(wasm_bytes)

            measurements = [
                {
                    "axis": "program_semantic_or_module_bits",
                    "status": "measured",
                    "unit": "bits",
                    "sens_samples": [artifact_s_bits],
                    "competitor_samples": [artifact_w_bits],
                    "sens_median": artifact_s_bits,
                    "competitor_median": artifact_w_bits,
                    "sens_p95": artifact_s_bits,
                    "competitor_p95": artifact_w_bits,
                    "notes": "SENS exact semantic payload bits vs complete executable Wasm module bits; both exclude generic runtime binaries.",
                },
                {
                    "axis": "program_container_or_module_bytes",
                    "status": "measured",
                    "unit": "bytes",
                    "sens_samples": [container_s_bytes],
                    "competitor_samples": [container_w_bytes],
                    "sens_median": container_s_bytes,
                    "competitor_median": container_w_bytes,
                    "sens_p95": container_s_bytes,
                    "competitor_p95": container_w_bytes,
                    "notes": "SENS production packed byte container vs complete .wasm module bytes.",
                },
                {
                    "axis": "ingest_vs_compile_ns",
                    "status": "measured",
                    "unit": "ns/op",
                    "sens_samples": sens_ingest,
                    "competitor_samples": wasm_compile,
                    "sens_median": si_med,
                    "competitor_median": wc_med,
                    "sens_p95": si_p95,
                    "competitor_p95": wc_p95,
                    "notes": "Recorded, not ranked: SENS exact-domain ingest is parse/decode only; WebAssembly.Module includes decode, validation and compilation.",
                },
                {
                    "axis": "warm_ready_execution_ns_per_op",
                    "status": "measured",
                    "unit": "ns/op",
                    "sens_samples": sens_warm,
                    "competitor_samples": wasm_warm,
                    "sens_median": sw_med,
                    "competitor_median": ww_med,
                    "sens_p95": sw_p95,
                    "competitor_p95": ww_p95,
                    "notes": "Already-ready SENS interpreter execution vs compiled Wasm exported call.",
                },
                {
                    "axis": "cold_total_internal_ns",
                    "status": "measured",
                    "unit": "ns/op",
                    "sens_samples": sens_cold,
                    "competitor_samples": wasm_cold,
                    "sens_median": sc_med,
                    "competitor_median": wco_med,
                    "sens_p95": sc_p95,
                    "competitor_p95": wco_p95,
                    "notes": "Recorded, not ranked: SENS full includes current Core/session prep; Wasm cold assumes host engine already exists.",
                },
                {
                    "axis": "process_maxrss_kb",
                    "status": "measured" if rss_available else "inconclusive",
                    "unit": "KiB",
                    "sens_samples": sens_rss if rss_available else [],
                    "competitor_samples": wasm_rss if rss_available else [],
                    "sens_median": summary(sens_rss)[0] if rss_available else None,
                    "competitor_median": summary(wasm_rss)[0] if rss_available else None,
                    "sens_p95": summary(sens_rss)[1] if rss_available else None,
                    "competitor_p95": summary(wasm_rss)[1] if rss_available else None,
                    "notes": (
                        "Whole helper-process peak RSS from shared #3698 fresh-process "
                        "GNU-time owner; timing samples are collected separately."
                        if rss_available
                        else "Shared #3698 RSS owner unavailable on this host."
                    ),
                },
            ]

            for axis, s_value, w_value_num, comparable in (
                ("program_semantic_or_module_bits", artifact_s_bits, artifact_w_bits, True),
                ("program_container_or_module_bytes", container_s_bytes, container_w_bytes, True),
                ("ingest_vs_compile_ns", si_med, wc_med, False),
                ("warm_ready_execution_ns_per_op", sw_med, ww_med, True),
                ("cold_total_internal_ns", sc_med, wco_med, False),
            ):
                verdict = (
                    allowed_verdict(args, s_value, w_value_num)
                    if comparable
                    else "inconclusive"
                )
                evidence = (
                    f"SENS={s_value:.3f}; Wasm={w_value_num:.3f}"
                    if args.evidence_mode == "performance" and comparable
                    else f"observation only: SENS={s_value:.3f}; Wasm={w_value_num:.3f}"
                )
                if not comparable:
                    evidence += "; phase/runtime boundary is not equivalent"
                verdicts.append(
                    {
                        "axis": f"{case}:{axis}",
                        "verdict": verdict,
                        "evidence": evidence,
                    }
                )

            if rss_available:
                sr_med, _sr_p95 = summary(sens_rss)
                wr_med, _wr_p95 = summary(wasm_rss)
                verdicts.append(
                    {
                        "axis": f"{case}:process_maxrss_kb",
                        "verdict": (
                            allowed_verdict(args, sr_med, wr_med)
                            if args.evidence_mode == "performance"
                            else "inconclusive"
                        ),
                        "evidence": (
                            f"SENS={sr_med:.0f} KiB; Wasm={wr_med:.0f} KiB"
                            if args.evidence_mode == "performance"
                            else f"smoke observation only: SENS={sr_med:.0f} KiB; Wasm={wr_med:.0f} KiB"
                        ),
                    }
                )
            else:
                verdicts.append(
                    {
                        "axis": f"{case}:process_maxrss_kb",
                        "verdict": "inconclusive",
                        "evidence": "shared #3698 RSS owner unavailable on this host",
                    }
                )

            workloads.append(
                {
                    "id": case,
                    "parity": "pass",
                    "params": {
                        "outer_reps": args.outer_reps,
                        "inner_repeats": args.inner_repeats,
                        "scope": "D3 smoke mechanism control",
                        "evidence_mode": args.evidence_mode,
                        "sens_semantic_bits": pack_info["semantic_bits"],
                        "sens_packed_bytes": pack_info["packed_bytes"],
                        "wasm_module_bytes": wasm_bytes,
                    },
                    "measurements": measurements,
                }
            )

    git_sha = run_text(["git", "rev-parse", "HEAD"], cwd=ROOT)
    rustc = run_text(["rustc", "--version"])
    environment = {
        "os": platform.platform(),
        "arch": platform.machine(),
        "cpu": platform.processor() or None,
        "load_context": args.load_context,
        "evidence_mode": args.evidence_mode,
        "rss_measurement": rssmod.METHOD if rss_available else "unavailable",
        "toolchain": {
            "rustc": rustc,
            "node": node_version,
        },
    }
    comparison = {
        "system": "wasm",
        "sens": {
            "commit": git_sha,
            "contract": contract_version(),
            "ratified_domains": "D1-D7",
        },
        "competitor": {
            "name": "WebAssembly via Node/V8",
            "version": node_version,
            "commit": None,
        },
        "environment": environment,
        "workloads": workloads,
        "semantic_density": None,
        "verdicts": verdicts,
    }

    with (raw_dir / "runs.tsv").open("w", newline="", encoding="utf-8") as fh:
        fields = list(raw_rows[0].keys())
        writer = csv.DictWriter(fh, fieldnames=fields, delimiter="\t")
        writer.writeheader()
        writer.writerows(raw_rows)

    (args.out_dir / "environment.json").write_text(
        json.dumps(environment, indent=2) + "\n", encoding="utf-8"
    )
    (args.out_dir / "comparison.json").write_text(
        json.dumps(comparison, indent=2) + "\n", encoding="utf-8"
    )

    validator = ROOT / "benchmarks" / "cross-language" / "reality-matrix" / "validate.py"
    subprocess.run(["python3", str(validator), str(args.out_dir / "comparison.json")], check=True)

    report = [
        "# SENS vs WebAssembly — D3 reality slice",
        "",
        "This is a mechanism/Pareto control, not a whole-language ranking.",
        f"Evidence mode: {args.evidence_mode}; load context: {args.load_context}.",
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
