#!/usr/bin/env python3
"""In-process physical T5 phase accounting; supplements existing process benchmark.

Never subtract independently timed phase medians: decode, D2 parse, session
setup, hot evaluation and full in-memory are DIFFERENT positive observables.
Independent parity with both real physical SENS CLIs precedes all samples.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import platform
import statistics
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = (
    "tests/fixtures/migration-quote-cohort-main/quote-legacy.sens",
    "tests/fixtures/migration-multiform-cohort-main/two-forms.sens",
)
PHASES = ("session", "decode_t5", "parse_d2", "eval_hot", "eval_fresh", "full_in_memory")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def checked(argv: list[str]) -> bytes:
    proc = subprocess.run(argv, cwd=ROOT, capture_output=True, timeout=120, check=False)
    if proc.returncode:
        raise RuntimeError(f"{argv!r}: exit {proc.returncode}, stderr={proc.stderr[-1600:]!r}")
    return proc.stdout


def parse_probe(stdout: bytes, reps: int, inner: int):
    try:
        lines = stdout.decode("ascii").splitlines()
    except UnicodeDecodeError as exc:
        raise ValueError("probe stdout not ASCII") from exc
    header: dict[str, str] = {}
    rows: dict[str, dict[int, int]] = {phase: {} for phase in PHASES}
    for line in lines:
        fields = line.split("\t")
        if fields[0] in ("PROBE", "ORACLE_HEX", "WORDS", "T5_BYTES"):
            if fields[0] in header:
                raise ValueError("duplicate header " + fields[0])
            if fields[0] == "PROBE" and fields != ["PROBE", "version", "1"]:
                raise ValueError("unrecognized measurement schema")
            if fields[0] != "PROBE" and len(fields) != 2:
                raise ValueError("invalid probe header")
            header[fields[0]] = fields[-1]
        elif fields[0] == "SAMPLE":
            if len(fields) != 5:
                raise ValueError("invalid sample field count")
            _, phase, rep, observed_inner, ns = fields
            if phase not in rows:
                raise ValueError("unexpected phase: " + phase)
            index = int(rep)
            if not 0 <= index < reps or int(observed_inner) != inner or int(ns) <= 0:
                raise ValueError("invalid sample range or monotonic duration")
            if index in rows[phase]:
                raise ValueError(f"duplicate sample {phase}/{index}")
            rows[phase][index] = int(ns)
        else:
            raise ValueError("unrecognized probe output: " + line[:120])
    for key in ("PROBE", "ORACLE_HEX", "WORDS", "T5_BYTES"):
        if key not in header:
            raise ValueError("probe omitted required evidence " + key)
    if not header["ORACLE_HEX"] or len(header["ORACLE_HEX"]) % 2:
        raise ValueError("no exact oracle bytes")
    expected = bytes.fromhex(header["ORACLE_HEX"])
    if not expected:
        raise ValueError("empty oracle")
    if int(header["WORDS"]) <= 0 or int(header["T5_BYTES"]) <= 0:
        raise ValueError("invalid file accounting")
    for phase, entries in rows.items():
        if set(entries) != set(range(reps)):
            raise ValueError(f"incomplete {phase} repetitions: {sorted(entries)}")
    return expected, int(header["WORDS"]), int(header["T5_BYTES"]), rows


def nearest_rank(values: list[int], fraction: float) -> int:
    return sorted(values)[max(0, math.ceil(len(values) * fraction) - 1)]


def one_fixture(helper: Path, sens: Path, trit: Path, fixture: Path, *, warmup: int, reps: int, inner: int):
    data = fixture.read_bytes()
    if not data:
        raise ValueError(f"empty physical SENS artifact: {fixture}")
    # Two distinct production binary executables establish byte-exact parity.
    observed_a = checked([str(sens), str(fixture)])
    observed_b = checked([str(trit), "eval", str(fixture)])
    if observed_a != observed_b:
        raise ValueError(f"{fixture.name}: real physical SENS CLIs disagree")
    probe = checked([str(helper), str(fixture), str(warmup), str(reps), str(inner)])
    value, words, t5_bytes, samples = parse_probe(probe, reps, inner)
    if observed_a != value + b"\n":
        raise ValueError(f"{fixture.name}: Rust in-process oracle differs from exact CLI stdout")
    if t5_bytes != len(data):
        raise ValueError(f"{fixture.name}: probe measured a different physical size")

    return {
        "fixture": str(fixture.relative_to(ROOT)),
        "file_sha256": sha256(data),
        "physical_bytes": t5_bytes,
        "typed_words": words,
        "oracle_sha256": sha256(value),
        "parity": "PASS_TWO_PHYSICAL_CLIS_PLUS_CORE",
    }, samples


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--helper", type=Path, required=True)
    ap.add_argument("--sens", type=Path, required=True)
    ap.add_argument("--trit", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--warmup", type=int, default=3)
    ap.add_argument("--reps", type=int, default=11)
    ap.add_argument("--inner", type=int, default=200)
    args = ap.parse_args()
    if args.warmup < 0 or args.reps < 5 or not 1 <= args.inner <= 100_000:
        ap.error("warmup >= 0, reps >= 5, 1 <= inner <= 100000")
    helper, sens, trit = (p.resolve() for p in (args.helper, args.sens, args.trit))
    for executable in (helper, sens, trit):
        if not executable.is_file():
            raise FileNotFoundError(executable)
    raw: list[dict[str, object]] = []
    cases = []
    for name in FIXTURES:
        meta, samples = one_fixture(
            helper, sens, trit, ROOT / name,
            warmup=args.warmup, reps=args.reps, inner=args.inner,
        )
        for phase in PHASES:
            values = [samples[phase][n] / args.inner for n in range(args.reps)]
            meta.setdefault("phases", {})[phase] = {
                "median_ns_per_op": round(statistics.median(values), 3),
                "p95_ns_per_op": round(nearest_rank(list(samples[phase].values()), 0.95) / args.inner, 3),
                "repetitions": args.reps,
                "inner_operations_per_rep": args.inner,
            }
            for rep, ns in sorted(samples[phase].items()):
                raw.append({
                    "fixture": name, "phase": phase, "sample": rep,
                    "inner": args.inner, "wall_ns": ns,
                    "ns_per_operation": f"{ns / args.inner:.6f}",
                })
        cases.append(meta)

    git_sha = checked(["git", "rev-parse", "HEAD"]).decode("ascii").strip()
    evidence = {
        "schema": "sens-physical-t5-inprocess-phases/v1",
        "source_sha": git_sha,
        "host": {"platform": platform.platform(), "processor": platform.processor(),
                 "python": platform.python_version()},
        "binary_sha256": {name: sha256(path.read_bytes()) for name, path in (
            ("probe", helper), ("sens", sens), ("sens-trit", trit)
        )},
        "warmup": args.warmup, "reps": args.reps, "inner": args.inner,
        "phase_definitions": {
            "session": "fresh Session::default only",
            "decode_t5": "in-memory packed T5 bytes -> typed domain words; no disk",
            "parse_d2": "predecoded typed domain words -> canonical D2 expressions",
            "eval_hot": "repeat same parsed expressions in the same already-ready Session",
            "eval_fresh": "new Session + evaluate same parsed expressions",
            "full_in_memory": "decode + parse + new Session + eval, excluding file I/O/startup",
        },
        "claim_boundary": (
            "Only two tiny admitted D3 fixtures. All samples are phase-local wall clocks "
            "within a running process, NOT cold startup or disk I/O; hot-SENS excludes "
            "Core4 and external capabilities. Independent CLI parity is a mechanism "
            "check, not historical-language semantic equivalence. No subtraction of "
            "medians, universal runtime ratio, GPU or FPGA claim."
        ),
        "cases": cases,
    }
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "inprocess.json").write_text(
        json.dumps(evidence, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    with (args.out / "inprocess-raw.tsv").open("w", encoding="utf-8", newline="") as stream:
        keys = ("fixture", "phase", "sample", "inner", "wall_ns", "ns_per_operation")
        writer = csv.DictWriter(stream, keys, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(raw)

    lines = [
        "# In-process physical SENS T5 phases (no startup or disk I/O)",
        "", f"Commit: `{git_sha}`", "",
        "| Physical fixture | Phase | Median ns/op | p95 ns/op |",
        "|---|---|---:|---:|",
    ]
    for case in cases:
        for phase in PHASES:
            row = case["phases"][phase]
            lines.append(
                f"| `{Path(case['fixture']).name}` | {phase} | "
                f"{row['median_ns_per_op']:.1f} | {row['p95_ns_per_op']:.1f} |"
            )
    lines.extend(["", evidence["claim_boundary"], ""])
    (args.out / "inprocess.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, RuntimeError, OSError) as exc:
        print("BLOCK: " + str(exc), file=__import__("sys").stderr)
        raise SystemExit(2)
