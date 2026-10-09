#!/usr/bin/env python3
"""Hot SENS benchmark: in-process phase timings on physically packed .sens."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import platform
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from sens_t5_codec import decode_bytes, encode_words  # noqa: E402

FORM = ("10", "001", "00", "000", "01")
PHASES = {"t5_open_d2", "d2_parse", "packed_width_d2", "eval_from_ast", "eval_lowered"}


def parse_record(line: str, prefix: str) -> dict[str, str]:
    fields = line.split("\t")
    if fields[0] != prefix:
        raise ValueError(f"unexpected output: {line!r}")
    result = {}
    for field in fields[1:]:
        key, value = field.split("=", 1)
        if key in result:
            raise ValueError(f"duplicate metric: {key}")
        result[key] = value
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binary", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--samples", type=int, default=11)
    parser.add_argument("--work-budget", type=int, default=65536)
    parser.add_argument("--sizes", default="1,16,128,1024")
    args = parser.parse_args()
    if args.samples < 3 or args.samples > 101 or args.samples % 2 != 1:
        parser.error("--samples must be odd and between 3 and 101")
    if args.work_budget < 4:
        parser.error("--work-budget must be >=4")
    sizes = [int(s) for s in args.sizes.split(",")]
    if not sizes or any(n < 1 or n > 2048 for n in sizes) or len(set(sizes)) != len(sizes):
        parser.error("--sizes must be unique counts from 1..2048")
    binary = args.binary.resolve(strict=True)
    output = args.out.resolve()
    output.mkdir(parents=True, exist_ok=True)
    measures = []
    samples = []
    with tempfile.TemporaryDirectory(prefix="sens-hot-t5-") as temp:
        for count in sizes:
            words = list(FORM) * count
            physical = encode_words(words)
            assert decode_bytes(physical) == words
            source = Path(temp) / f"quote-{count}.sens"
            source.write_bytes(physical)
            result = subprocess.run([
                str(binary), str(source), str(count), str(args.work_budget),
                str(args.samples),
            ], check=True, cwd=ROOT, capture_output=True, text=True, timeout=150)
            for line in result.stdout.splitlines():
                if line.startswith("HOT_SAMPLE\t"):
                    sample = parse_record(line, "HOT_SAMPLE")
                    if int(sample["forms"]) != count or sample["phase"] not in PHASES:
                        raise RuntimeError("unrecognized hot benchmark sample")
                    samples.append({
                        "forms": count, "phase": sample["phase"],
                        "rep": int(sample["rep"]), "ns_op": int(sample["ns_op"]),
                    })
                elif line.startswith("HOT_BENCH\t"):
                    item = parse_record(line, "HOT_BENCH")
                    if int(item["forms"]) != count or item["phase"] not in PHASES:
                        raise RuntimeError("unrecognized hot benchmark phase")
                    item = {
                        "forms": count, "phase": item["phase"],
                        "iterations": int(item["iterations"]),
                        "samples": int(item["samples"]),
                        "median_ns_op": int(item["median_ns_op"]),
                        "p95_ns_op": int(item["p95_ns_op"]),
                        "min_ns_op": int(item["min_ns_op"]),
                        "physical_bytes": int(item["physical_bytes"]),
                        "observable": item["observable"],
                        "physical_sha256": hashlib.sha256(physical).hexdigest(),
                        "payload_bits": sum(map(len, words)),
                    }
                    measures.append(item)
                else:
                    raise RuntimeError(f"unrecognized benchmark emission: {line!r}")
            print(f"HOT complete: {count} current D3 QUOTE forms; {len(physical)} T5 bytes", flush=True)

    for count in sizes:
        found = [r for r in measures if r["forms"] == count]
        if len(found) != len(PHASES) or {r["phase"] for r in found} != PHASES:
            raise RuntimeError(f"missing or duplicated benchmark phases at {count}")
        for row in found:
            matching = sorted(
                [s for s in samples if s["forms"] == count and s["phase"] == row["phase"]],
                key=lambda s: s["rep"],
            )
            if len(matching) != args.samples or [s["rep"] for s in matching] != list(range(1, args.samples + 1)):
                raise RuntimeError(f"missing hot samples: {count} {row['phase']}")
            sorted_ns = sorted(s["ns_op"] for s in matching)
            if sorted_ns[args.samples // 2] != row["median_ns_op"]:
                raise RuntimeError(f"invalid hot median: {count} {row['phase']}")
            p95_at = (95 * args.samples + 99) // 100 - 1
            if sorted_ns[p95_at] != row["p95_ns_op"]:
                raise RuntimeError(f"invalid hot p95: {count} {row['phase']}")

    (output / "hot-results.json").write_text(json.dumps(measures, indent=2) + "\n")
    with (output / "hot-raw.tsv").open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=["forms", "phase", "rep", "ns_op"], delimiter="\t")
        writer.writeheader()
        writer.writerows(samples)
    environment = {
        "commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "machine": platform.machine(),
        "platform": platform.platform(),
        "python": platform.python_version(),
        "binary_sha256": hashlib.sha256(binary.read_bytes()).hexdigest(),
        "samples": args.samples,
        "work_budget": args.work_budget,
        "sizes": sizes,
        "timing_scope": "single process, warmed, elapsed/iterations; process startup excluded",
        "caveat": "Same SENS engine; dense W1-W9 payload has an externally supplied exact-word width schedule, not self-framing T5.",
    }
    (output / "hot-environment.json").write_text(json.dumps(environment, indent=2) + "\n")
    lines = [
        "# Гаряче виконання фізичного SENS",
        "",
        f"SHA: `{environment['commit']}`. Без startup; медіана і p95 з {args.samples} незалежних серій.",
        "",
        "| Форми | Фаза | ns/операція, p50 | ns/операція, p95 | Форм/с (p50) |",
        "|---:|---|---:|---:|---:|",
    ]
    for row in measures:
        median = row["median_ns_op"]
        forms_per_second = row["forms"] * 1e9 / median if median else 0.0
        lines.append(f"| {row['forms']} | {row['phase']} | {median:,} | {row['p95_ns_op']:,} | {forms_per_second:,.0f} |")
    # Same already-admitted forms; compare the two isolated D2 reader
    # mechanisms at each size, never conflate either with end-to-end T5.
    lines.extend(["", "## Dense payload vs visible 0/1 D2 parser (same forms)", "",
                  "| Форми | Видимий D2, p50 ns | Щільний D2 + готові межі слів, p50 ns | Visible / packed |",
                  "|---:|---:|---:|---:|"])
    for count in sizes:
        by_phase = {row["phase"]: row for row in measures if row["forms"] == count}
        ascii_ns = by_phase["d2_parse"]["median_ns_op"]
        dense_ns = by_phase["packed_width_d2"]["median_ns_op"]
        ratio = f"{ascii_ns / dense_ns:.3f}x" if dense_ns else "undefined"
        lines.append(f"| {count} | {ascii_ns:,} | {dense_ns:,} | {ratio} |")
    lines.extend([
        "",
        "Це точні payload-біти із зовнішнім відомим розкладом ширин слів. "
        "packed_width_d2 не є самодостатнім форматом T5 і НЕ включає T5 decode.",
        "Паритет результатів direct packed/visible/AST/lowered перевіряється ДО вимірювання.",
        "",
        "t5_open_d2 включає перевірку транспортного T5 і структури D2; d2_parse — лише текстовий читач D2.",
        "eval_from_ast включає lowering; eval_lowered вимірює виконання вже знижених форм.",
        "Інтерпретатор і канонічний оракул тут не є незалежними реалізаціями.",
        "Вимірювання на спільному runner не є універсальною гарантією стабільної частоти CPU.",
        "",
    ])
    report = "\n".join(lines)
    (output / "hot-report.md").write_text(report, encoding="utf-8")
    print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
