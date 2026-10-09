#!/usr/bin/env python3
"""Measure D5 physical T5 hot execution, with the production CLI as the observable gate.

The helper runs the *same evaluator* as the production CLIs. Equality is
mechanism parity, NOT an independent Lisp semantic oracle. Each phase has
raw independent sample series; there is no process spawn inside timed loops.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import platform
import statistics
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from sens_t5_codec import decode_bytes, encode_words, parse_words  # noqa: E402

WORKLOADS = {
    "d5-label-recursion": "examples/binary/d5-label-recursion.bits",
    "d5-label-copy": "examples/binary/d5-label-copy.bits",
    "d5-label-map": "examples/binary/d5-label-map.bits",
}
PHASES = {"t5_decode_parse", "eval_parsed", "eval_lowered"}


def run(command: list[str]) -> str:
    completed = subprocess.run(
        command, cwd=ROOT, capture_output=True, check=False, timeout=120
    )
    if completed.returncode:
        raise RuntimeError(
            f"command failed ({completed.returncode}): {command!r}\n"
            + completed.stderr.decode("utf-8", errors="replace")[-1800:]
        )
    return completed.stdout.decode("utf-8")


def fields(line: str, prefix: str) -> dict[str, str]:
    parts = line.split("\t")
    if parts[0] != prefix:
        raise RuntimeError(f"bad benchmark record {line!r}")
    record = {}
    for token in parts[1:]:
        key, value = token.split("=", 1)
        if key in record:
            raise RuntimeError(f"duplicate measurement key {key!r}")
        record[key] = value
    return record


def cpu() -> str:
    info = Path("/proc/cpuinfo")
    if info.exists():
        for line in info.read_text(errors="replace").splitlines():
            if line.startswith("model name"):
                return line.partition(":")[2].strip()
    return platform.processor() or "unknown"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--helper", type=Path, required=True)
    parser.add_argument("--sens", type=Path, required=True)
    parser.add_argument("--sens-trit", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--reps", type=int, default=9)
    parser.add_argument("--iterations", type=int, default=64)
    args = parser.parse_args()
    if not (3 <= args.reps <= 101 and args.reps % 2 == 1):
        parser.error("reps must be odd in 3..101")
    if not 1 <= args.iterations <= 100_000:
        parser.error("iterations must be 1..100000")
    helper, sens, trit = (str(v.resolve(strict=True)) for v in
                          (args.helper, args.sens, args.sens_trit))
    rows = []
    raw = []
    with tempfile.TemporaryDirectory(prefix="sens-physical-d5-hot-") as temp:
        for name, path in WORKLOADS.items():
            words = parse_words((ROOT / path).read_text(encoding="ascii"))
            physical = encode_words(words)
            if decode_bytes(physical) != words:
                raise RuntimeError(f"{name}: T5 roundtrip changed exact words")
            target = Path(temp) / f"{name}.sens"
            target.write_bytes(physical)
            baseline = run([sens, str(target)])
            trit_output = run([trit, "eval", str(target)])
            if not baseline or baseline != trit_output:
                raise RuntimeError(f"{name}: CLI execution differs on identical T5 bytes")
            # CLI emits final evaluator value plus newline; D5 fixtures have no
            # printing side effects. Compare it against the in-process value.
            expected = baseline.rstrip("\n").encode("utf-8").hex()
            output = run([helper, str(target), name, str(args.iterations), str(args.reps)])
            found = {}
            for line in output.splitlines():
                if line.startswith("HOT_D5_OBSERVABLE\t"):
                    item = fields(line, "HOT_D5_OBSERVABLE")
                    if item["case"] != name or item["value_hex"] != expected:
                        raise RuntimeError(f"{name}: in-process result differs from production CLI")
                    if int(item["physical_bytes"]) != len(physical):
                        raise RuntimeError(f"{name}: physical file size drift")
                    if int(item["word_count"]) != len(words):
                        raise RuntimeError(f"{name}: word count drift")
                elif line.startswith("HOT_D5_SAMPLE\t"):
                    record = fields(line, "HOT_D5_SAMPLE")
                    if record["case"] != name or record["phase"] not in PHASES:
                        raise RuntimeError(f"{name}: invalid phase sample")
                    raw.append({
                        "workload": name, "phase": record["phase"],
                        "rep": int(record["rep"]), "ns_op": int(record["ns_op"]),
                    })
                elif line.startswith("HOT_D5_BENCH\t"):
                    item = fields(line, "HOT_D5_BENCH")
                    if item["case"] != name or item["phase"] not in PHASES:
                        raise RuntimeError(f"{name}: invalid aggregate phase")
                    if item["phase"] in found:
                        raise RuntimeError(f"{name}: duplicate phase aggregate")
                    found[item["phase"]] = item
                else:
                    raise RuntimeError(f"{name}: unexpected helper output {line!r}")
            if set(found) != PHASES:
                raise RuntimeError(f"{name}: absent phase or duplicate observable")
            for phase, item in found.items():
                matches = [r for r in raw if r["workload"] == name and r["phase"] == phase]
                samples = sorted(r["ns_op"] for r in matches)
                reps = [r["rep"] for r in matches]
                if sorted(reps) != list(range(1, args.reps + 1)):
                    raise RuntimeError(f"{name}/{phase}: missing raw samples")
                median = samples[args.reps // 2]
                p95 = samples[math.ceil(args.reps * 0.95) - 1]
                if (int(item["samples"]) != args.reps
                        or int(item["iterations"]) != args.iterations
                        or int(item["median_ns_op"]) != median
                        or int(item["p95_ns_op"]) != p95):
                    raise RuntimeError(f"{name}/{phase}: forged or mismatched aggregates")
                rows.append({
                    "workload": name, "phase": phase, "median_ns_op": median,
                    "p95_ns_op": p95, "samples": args.reps,
                    "iterations_per_sample": args.iterations,
                    "physical_bytes": len(physical), "exact_word_count": len(words),
                    "physical_sha256": hashlib.sha256(physical).hexdigest(),
                    "observable_sha256": hashlib.sha256(baseline.encode("utf-8")).hexdigest(),
                })
            print(f"D5 HOT {name}: {len(words)} words, {len(physical)} T5 bytes, "
                  f"CLI parity PASS, {len(PHASES)} phase medians")
    args.out.mkdir(parents=True, exist_ok=True)
    environment = {
        "schema": "sens-physical-d5-hot/v1",
        "git_sha": run(["git", "rev-parse", "HEAD"]).strip(),
        "cpu": cpu(), "platform": platform.platform(),
        "rustc": run(["rustc", "--version"]).strip(),
        "helper_sha256": hashlib.sha256(Path(helper).read_bytes()).hexdigest(),
        "samples": args.reps, "iterations": args.iterations,
        "scope": "same SENS evaluator, physical T5 to D2 and in-process D5 evaluation",
        "warning": "no independent semantic oracle; timing excludes process startup",
    }
    (args.out / "d5-hot-environment.json").write_text(
        json.dumps(environment, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (args.out / "d5-hot-results.json").write_text(
        json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with (args.out / "d5-hot-raw.tsv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["workload", "phase", "rep", "ns_op"], delimiter="\t")
        writer.writeheader()
        writer.writerows(raw)
    lines = [
        "# Гарячі D5-бенчмарки: реальні двійкові рекурсія, copy, MAP",
        "",
        f"SHA: `{environment['git_sha']}`; {args.reps} серій по {args.iterations} повторів; "
        "час запуску CLI та процесу виключено.",
        "",
        "| Реальна двійкова програма | Фаза | p50 нс/виклик | p95 нс/виклик | T5, Б |",
        "|---|---|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            f"| {row['workload']} | {row['phase']} | {row['median_ns_op']:,} | "
            f"{row['p95_ns_op']:,} | {row['physical_bytes']} |"
        )
    lines.extend([
        "",
        "`eval_parsed` включає lowering на кожному виклику, "
        "`eval_lowered` повторно використовує попередньо знижений AST. "
        "Тому відношення фаз не можна називати прискоренням мови як такої.",
        "",
        "Production `sens` та `sens-trit eval` запускають ті самі фізичні "
        "T5-байти та зобов'язані давати такий самий результат, як hot helper.",
        "Це механічний parity-gate, а не незалежний оракул семантики.",
        "На GitHub-hosted runner порівнювати настінний час між комітами/машинами заборонено.",
        "",
    ])
    report = "\n".join(lines)
    (args.out / "d5-hot-report.md").write_text(report, encoding="utf-8")
    print(report)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RuntimeError, OSError, ValueError, subprocess.SubprocessError) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        raise SystemExit(2)
