#!/usr/bin/env python3
"""Paired old/new *same-host* release T5 decode benchmark.

The CLI tools and workloads are not rewritten: each release build runs the
existing physical_sens_hot_bench with identical canonical packed .sens bytes.
Only timings for equivalent observed values may be reported.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import platform
import statistics
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from sens_t5_codec import decode_bytes, encode_words  # noqa: E402

FORM = ("10", "001", "00", "000", "01")
PHASES = ("t5_open_d2", "t5_direct_d2", "t5_words_d2", "eval_from_ast", "eval_lowered")


def hash_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def cpu_model() -> str:
    try:
        for raw in Path("/proc/cpuinfo").read_text().splitlines():
            if raw.lower().startswith("model name"):
                return raw.split(":", 1)[1].strip()
    except OSError:
        pass
    return platform.processor() or "unknown"


def execute(binary: Path, physical: Path, forms: int, budget: int, samples: int):
    cmd = [str(binary), str(physical), str(forms), str(budget), str(samples)]
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=90)
    if p.returncode:
        raise RuntimeError(f"{binary} failed: {p.stderr[-2000:]}")
    results, raw, observable = {}, [], None
    for line in p.stdout.splitlines():
        fields = line.split("\t")
        if not fields or fields[0] not in ("HOT_BENCH", "HOT_SAMPLE"):
            continue
        row = dict(field.split("=", 1) for field in fields[1:])
        phase = row["phase"]
        if fields[0] == "HOT_SAMPLE":
            raw.append({"phase": phase, "rep": int(row["rep"]), "ns_op": int(row["ns_op"])})
            continue
        assert phase not in results, f"duplicate phase: {phase}"
        if observable is None:
            observable = row["observable"]
        elif observable != row["observable"]:
            raise RuntimeError("observable drift across benchmark phases")
        results[phase] = int(row["median_ns_op"])
    if not set(PHASES).issubset(results) or observable is None:
        raise RuntimeError("missing measured phases or observable")
    for phase in PHASES:
        if len([r for r in raw if r["phase"] == phase]) != samples:
            raise RuntimeError(f"{phase}: missing raw repetitions")
    return results, raw, observable


def median(xs: list[float]) -> float:
    return float(statistics.median(xs))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--baseline-sha", required=True)
    parser.add_argument("--candidate-sha", required=True)
    parser.add_argument("--rounds", type=int, default=4)
    parser.add_argument("--samples", type=int, default=9)
    parser.add_argument("--work-budget", type=int, default=65536)
    args = parser.parse_args()
    if args.rounds < 3 or args.samples < 3 or args.samples % 2 == 0:
        parser.error("need >=3 AB rounds and odd samples>=3")
    binaries = {
        "baseline": args.baseline.resolve(),
        "candidate": args.candidate.resolve(),
    }
    for name, binary in binaries.items():
        if not binary.is_file():
            raise RuntimeError(f"missing {name} release binary {binary}")
    args.out.mkdir(parents=True, exist_ok=True)
    report = {
        "schema": "sens-t5-decoder-same-runner-ab/v1",
        "machine": {"cpu": cpu_model(), "platform": platform.platform(),
                    "python": platform.python_version()},
        "revisions": {"baseline": args.baseline_sha, "candidate": args.candidate_sha},
        "binary_sha256": {name: hash_file(path) for name, path in binaries.items()},
        "rounds": args.rounds, "samples_per_phase_per_round": args.samples,
        "work_budget": args.work_budget,
        "scope": (
            "Exact D3 QUOTE-only workload. Paired old/new release binaries on the same "
            "GitHub runner, rotating process order; in-process median ns/op. "
            "Ratios are workload-specific, not whole-language speedups."
        ),
        "cases": [],
    }
    raw = []
    markdown = [
        "# Same-host A/B: T5 decoder, actual packed SENS", "",
        f"Baseline \`{args.baseline_sha}\` versus candidate \`{args.candidate_sha}\`.",
        f"CPU: {report['machine']['cpu']}.", "",
        "| Forms | Phase | Baseline ns/op | Candidate ns/op | Baseline / candidate |",
        "|---:|---|---:|---:|---:|",
    ]
    with tempfile.TemporaryDirectory(prefix="sens-ab-t5-") as tempdir:
        for forms in (128, 1024):
            words = list(FORM) * forms
            physical_bytes = encode_words(words)
            if decode_bytes(physical_bytes) != words:
                raise RuntimeError("independent T5 codec denied the exact words")
            physical = Path(tempdir) / f"quote-{forms}.sens"
            physical.write_bytes(physical_bytes)

            by_round = []
            for outer in range(args.rounds):
                order = ("baseline", "candidate") if outer % 2 == 0 else ("candidate", "baseline")
                one_round = {}
                observed_values = {}
                for variant in order:
                    phases, samples, observable = execute(
                        binaries[variant], physical, forms, args.work_budget, args.samples
                    )
                    one_round[variant] = phases
                    observed_values[variant] = observable
                    for item in samples:
                        raw.append({
                            "forms": forms, "round": outer + 1, "variant": variant,
                            "phase": item["phase"], "rep": item["rep"],
                            "ns_op": item["ns_op"],
                        })
                if observed_values["baseline"] != observed_values["candidate"]:
                    raise RuntimeError(f"physical observable mismatch in round {outer + 1}")
                by_round.append(one_round)

            values = {}
            for phase in PHASES:
                old = [round_["baseline"][phase] for round_ in by_round]
                new = [round_["candidate"][phase] for round_ in by_round]
                if any(value <= 0 for value in old + new):
                    raise RuntimeError(f"non-positive timing for {phase}")
                old_median, new_median = median(old), median(new)
                ratio = old_median / new_median
                values[phase] = {
                    "baseline_median_ns_op": old_median,
                    "candidate_median_ns_op": new_median,
                    "baseline_to_candidate_ratio": round(ratio, 5),
                    "paired_round_ratios": [round(a / b, 5) for a, b in zip(old, new)],
                }
                markdown.append(
                    f"| {forms} | {phase} | {old_median:.1f} | {new_median:.1f} | {ratio:.3f}× |"
                )
            report["cases"].append({
                "forms": forms, "physical_t5_bytes": len(physical_bytes),
                "packed_sha256": hashlib.sha256(physical_bytes).hexdigest(),
                "observable": observed_values["baseline"],
                "phases": values,
            })
            print(f"PAIR_AB forms={forms} T5_bytes={len(physical_bytes)} "
                  f"decoder_ratio={values['t5_words_d2']['baseline_to_candidate_ratio']:.3f}x",
                  flush=True)
    with (args.out / "raw.tsv").open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file, fieldnames=("forms", "round", "variant", "phase", "rep", "ns_op"),
            delimiter="\t", lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(raw)
    (args.out / "results.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    markdown.extend([
        "", "Each ratio is a paired, same-runner measurement at a pinned merge-base.",
        "Ratios above 1 favor the streaming candidate; at or below 1 do not.",
        "Results include both decode and D2 parse, not an isolated trit-only kernel.",
        "The two variants are not a proof of whole-language performance.",
        "",
    ])
    (args.out / "report.md").write_text("\n".join(markdown), encoding="utf-8")


if __name__ == "__main__":
    main()
