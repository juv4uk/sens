#!/usr/bin/env python3
"""Count actual process instruction references for packed physical SENS T5.

This is Cachegrind evidence, NOT cycles, wall-clock speed, isolated decoder
instruction counts, or independent semantic proof. A shared GitHub-hosted CPU
and the exact same input .sens bytes are used for each paired CLI path.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import platform
import re
import statistics
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from sens_t5_codec import decode_bytes, typed_sha256  # noqa: E402

FIXTURES = (
    "tests/fixtures/migration-quote-cohort-main/quote-legacy.sens",
    "tests/fixtures/migration-multiform-cohort-main/two-forms.sens",
)
I_REFS = re.compile(rb"I\s+refs:\s*([0-9,]+)")


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def run(command: list[str], *, timeout: int = 120) -> subprocess.CompletedProcess[bytes]:
    result = subprocess.run(
        command, cwd=ROOT, capture_output=True, timeout=timeout, check=False
    )
    if result.returncode:
        raise RuntimeError(
            f"exit={result.returncode} command={command!r}; "
            f"stderr={result.stderr[-1500:]!r}"
        )
    return result


def count_irefs(
    valgrind: str, command: list[str], out_file: Path, expected: bytes
) -> int:
    full = [
        valgrind, "--tool=cachegrind", "--cache-sim=no",
        "--branch-sim=no", f"--cachegrind-out-file={out_file}", *command,
    ]
    result = run(full)
    if result.stdout != expected:
        raise RuntimeError(f"Cachegrind changed output for {command!r}")
    match = I_REFS.search(result.stderr)
    if match is None:
        raise RuntimeError(f"missing Cachegrind I refs: {result.stderr[-1500:]!r}")
    return int(match.group(1).replace(b",", b""))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sens", required=True, type=Path)
    parser.add_argument("--trit", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--valgrind", default="valgrind")
    parser.add_argument("--reps", type=int, default=3)
    args = parser.parse_args()
    if not 3 <= args.reps <= 9:
        parser.error("--reps must be in 3..9 (positive repeated observations)")
    sens, trit = args.sens.resolve(strict=True), args.trit.resolve(strict=True)
    args.out.mkdir(parents=True, exist_ok=True)

    binary_shas = {"sens": sha(sens.read_bytes()), "sens-trit": sha(trit.read_bytes())}
    versions = {
        "valgrind": run([args.valgrind, "--version"]).stdout.decode().strip(),
        "rustc": run(["rustc", "--version"]).stdout.decode().strip(),
        "git_sha": run(["git", "rev-parse", "HEAD"]).stdout.decode().strip(),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "binary_sha256": binary_shas,
        "samples_per_lane": args.reps,
        "counter": "Cachegrind I refs including process startup, loader, I/O, runtime and stdout",
        "not_measured": "CPU cycles, cache misses, hot codec-only instruction count, other-language wins",
    }

    observations: list[dict] = []
    rows: list[dict] = []
    with tempfile.TemporaryDirectory(prefix="sens-cachegrind-") as temporary:
        temp = Path(temporary)
        for fixture in FIXTURES:
            packed = (ROOT / fixture).read_bytes()
            words = decode_bytes(packed)
            visible = (" ".join(words) + "\n").encode("ascii")
            cmds = {
                "sens-execute": [str(sens), str(ROOT / fixture)],
                "sens-trit-eval": [str(trit), "eval", str(ROOT / fixture)],
                "sens-trit-open": [str(trit), "open", str(ROOT / fixture)],
            }
            # Fail closed before any measured row: independent Python T5 view
            # and the two production CLI evaluation entrypoints must agree.
            expected = {lane: run(command).stdout for lane, command in cmds.items()}
            if expected["sens-execute"] != expected["sens-trit-eval"]:
                raise RuntimeError(f"{fixture}: SENS CLI execution parity failed")
            if expected["sens-trit-open"] != visible:
                raise RuntimeError(f"{fixture}: Rust/Python T5 projection mismatch")
            counts: dict[str, list[int]] = {lane: [] for lane in cmds}
            lanes = tuple(cmds)
            for index in range(args.reps):
                # Rotate order to reduce simple position-dependent bias.
                ordered = lanes[index % len(lanes):] + lanes[:index % len(lanes)]
                for lane in ordered:
                    amount = count_irefs(
                        args.valgrind, cmds[lane],
                        temp / f"{len(rows)}-{index}-{lane}.cg",
                        expected[lane],
                    )
                    counts[lane].append(amount)
                    observations.append({
                        "fixture": fixture, "lane": lane, "rep": index + 1,
                        "i_refs": amount, "output_sha256": sha(expected[lane]),
                    })
            for lane in lanes:
                vals = sorted(counts[lane])
                row = {
                    "fixture": fixture, "lane": lane,
                    "samples": len(vals),
                    "median_i_refs": int(statistics.median(vals)),
                    "min_i_refs": vals[0], "max_i_refs": vals[-1],
                    "physical_t5_bytes": len(packed),
                    "exact_word_count": len(words),
                    "physical_sha256": sha(packed),
                    "typed_word_sha256": typed_sha256(words),
                    "result_sha256": sha(expected[lane]),
                }
                rows.append(row)
                print(
                    f"IREFS {fixture} {lane}: median={row['median_i_refs']:,} "
                    f"range={row['min_i_refs']:,}..{row['max_i_refs']:,}",
                    flush=True,
                )

    report = {"schema": "sens-physical-t5-cachegrind-irefs/v1",
              "environment": versions, "rows": rows}
    (args.out / "results.json").write_text(
        json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    with (args.out / "raw.tsv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(observations[0]), delimiter="\t")
        writer.writeheader()
        writer.writerows(observations)

    lines = [
        "# Physical SENS T5 — Cachegrind instruction references", "",
        f"Commit: {versions['git_sha']}; samples per lane: {args.reps}.", "",
        "| Physical program | Lane | I refs median | Min | Max | T5 bytes |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            f"| {Path(row['fixture']).name} | {row['lane']} "
            f"| {row['median_i_refs']:,} | {row['min_i_refs']:,} "
            f"| {row['max_i_refs']:,} | {row['physical_t5_bytes']} |"
        )
    lines.extend([
        "", "Instruction references include the **whole new process**, Core load, "
        "file I/O, T5 decode, execution where applicable and output; "
        "they are not CPU cycles or pure T5 codec work.",
        "The two evaluation lanes share SENS semantics; parity was checked "
        "before counting. The open lane only decodes and renders.",
        "Compare paired counts within the same SHA and machine; no general "
        "speed claim versus Python, C, Chez or a different GitHub runner.", "",
    ])
    (args.out / "report.md").write_text("\n".join(lines), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
