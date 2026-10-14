#!/usr/bin/env python3
"""CI_GLUE_NO_SEMANTICS: manual paired T5 Zig/Rust mechanical benchmark.

Only verified transport fixture hashes are used as the equality precondition.
Never claim that this script proves the SENS evaluator's semantics.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import random
import statistics
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
ZIG_SOURCE = "research/zig-codecs/t5/bench.zig"
RUST_EXAMPLE = "target/release/examples/zig_t5_matched_bench"


def checked(command: list[str]) -> str:
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(
            f"command={command!r} code={result.returncode}\n"
            f"stdout={result.stdout[-4000:]}\nstderr={result.stderr[-4000:]}"
        )
    return result.stdout + "\n" + result.stderr


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def records(output: str, kind: str) -> list[dict[str, str]]:
    rows = []
    for line in output.splitlines():
        if not line.startswith(kind + " "):
            continue
        row = {}
        for cell in line.split()[1:]:
            if "=" not in cell:
                raise ValueError(f"bad record: {line}")
            key, value = cell.split("=", 1)
            row[key] = value
        rows.append(row)
    return rows


def quantile_p95(values: list[float]) -> float:
    ordered = sorted(values)
    return ordered[(95 * len(ordered) + 99) // 100 - 1]


def main() -> int:
    cli = argparse.ArgumentParser()
    cli.add_argument("--out-dir", type=Path, required=True)
    cli.add_argument("--pairs", type=int, default=3)
    cli.add_argument("--zig-pin", default="0.16.0", choices=("0.16.0", "0.17.0"))
    args = cli.parse_args()
    if args.pairs < 3:
        raise SystemExit("--pairs must be >=3 independent outer process pairs")

    out = args.out_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)
    meta = {
        "role": "CI_GLUE_NO_SEMANTICS",
        "kind": "mechanical_transport_benchmark_only",
        "git_sha": checked(["git", "rev-parse", "HEAD"]).strip(),
        "os": platform.platform(),
        "cpu": platform.processor() or platform.uname().machine,
        "zig": checked(["zig", "version"]).strip(),
        "rustc": checked(["rustc", "-Vv"]).strip(),
        "pairs": args.pairs,
        "seed": 20261014,
        "zig_flags": "-O ReleaseFast -lc",
        "expected_zig_pin": args.zig_pin,
        "rust_flags": "cargo --locked --release (release profile in Cargo.toml)",
    }
    (out / "environment.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    if meta["zig"] != args.zig_pin:
        raise RuntimeError(f"Zig pin mismatch: expected {args.zig_pin}, actual {meta['zig']}")

    checked(["zig", "test", "research/zig-codecs/t5/t5.zig"])
    checked(["cargo", "build", "--locked", "--release", "-p", "sens",
             "--example", "zig_t5_matched_bench"])
    zig_bin = out / "zig_t5_bench"
    checked(["zig", "build-exe", ZIG_SOURCE, "-O", "ReleaseFast", "-lc",
             f"-femit-bin={zig_bin}"])
    binaries = {"zig": zig_bin, "rust": ROOT / RUST_EXAMPLE}
    meta["binary_sha256"] = {name: digest(path) for name, path in binaries.items()}
    (out / "environment.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")

    rng = random.Random(meta["seed"])
    batches = []
    fixtures = {}
    raw_file = out / "samples.jsonl"
    with raw_file.open("w", encoding="utf-8") as handle:
        for pair in range(args.pairs):
            order = ["zig", "rust"]
            rng.shuffle(order)
            paired_fixtures = {}
            paired_bytes = {}
            for name in order:
                run = subprocess.run([str(binaries[name])], cwd=ROOT,
                                     capture_output=True, text=True, check=True)
                raw = run.stdout + "\n" + run.stderr
                (out / f"pair-{pair:02d}-{name}.txt").write_text(raw, encoding="utf-8")
                fx_rows = records(raw, "fixture")
                physical_rows = records(raw, "physical")
                sample_rows = records(raw, "sample")
                if len(fx_rows) != 4 or len(physical_rows) != 4 or len(sample_rows) != 40:
                    raise RuntimeError(f"UNINFORMATIVE-OUTPUT pair={pair} impl={name}, "
                                       f"fixtures={len(fx_rows)} physical={len(physical_rows)} samples={len(sample_rows)}")
                for f in fx_rows:
                    key = int(f["forms"])
                    paired_fixtures.setdefault(key, {})[name] = (
                        int(f["words"]), int(f["bytes"]), int(f["fnv64"], 16))
                for physical_row in physical_rows:
                    paired_bytes.setdefault(int(physical_row["forms"]), {})[name] = physical_row["hex"]
                for s in sample_rows:
                    row = {
                        "pair": pair, "impl": name, "forms": int(s["forms"]),
                        "op": s["op"], "elapsed_ns": int(s["elapsed_ns"]),
                        "reps": int(s["reps"]),
                    }
                    if row["elapsed_ns"] <= 0 or row["reps"] <= 0:
                        raise RuntimeError(f"INVALID_TIMING {row}")
                    row["ns_per_op"] = row["elapsed_ns"] / row["reps"]
                    handle.write(json.dumps(row) + "\n")
                    batches.append(row)
            for forms, sides in paired_fixtures.items():
                b = paired_bytes.get(forms, {})
                if b.get("zig") is None or b.get("rust") is None or b["zig"] != b["rust"]:
                    (out / "STATUS").write_text(f"BLOCKED_NO_TIMING: physical byte mismatch forms={forms}\\n")
                    raise RuntimeError(f"BLOCKED_NO_TIMING forms={forms}, physical byte mismatch")
                if len(b["zig"]) != 2 * sides["zig"][1]:
                    raise RuntimeError(f"BLOCKED_NO_TIMING forms={forms}, physical length mismatch")
                if sides.get("zig") != sides.get("rust"):
                    (out / "STATUS").write_text(
                        f"BLOCKED_NO_TIMING: fixture mismatch forms={forms} "
                        f"zig={sides.get('zig')} rust={sides.get('rust')}\n")
                    raise RuntimeError(f"BLOCKED_NO_TIMING forms={forms}, parity mismatch")
                fixtures[forms] = sides["zig"]
        if len(fixtures) != 4:
            raise RuntimeError("BLOCKED_NO_TIMING incomplete fixture parity")

    grouped = defaultdict(list)
    for row in batches:
        grouped[(row["forms"], row["op"], row["impl"])].append(row["ns_per_op"])
    lines = ["# Zig ↔ Rust T5 · механічний A/B", "",
             "**ТІЛЬКИ transport**, не SENS semantic oracle.",
             "Формати і bytes/FNV-1a matched; in-process warmed measurements, "
             "3+ зовнішні парні процеси. **Статистика дослідницька, не K–J CI.**",
             "",
             "| Форми | Операція | Zig p50 нс/оп | Rust p50 нс/оп | Rust/Zig | Zig p95 | Rust p95 |",
             "|---:|---|---:|---:|---:|---:|---:|"]
    for forms in (1, 16, 128, 1024):
        for op in ("encode", "decode"):
            z = grouped[(forms, op, "zig")]
            r = grouped[(forms, op, "rust")]
            if len(z) != len(r) or len(z) != 5 * args.pairs:
                raise RuntimeError(f"BLOCKED_NO_TIMING missing paired samples {forms}/{op}")
            zp, rp = statistics.median(z), statistics.median(r)
            lines.append(f"| {forms} | {op} | {zp:.1f} | {rp:.1f} | {rp / zp:.3f}× | "
                         f"{quantile_p95(z):.1f} | {quantile_p95(r):.1f} |")
    lines += ["", "Пам’ять/алокації, cachegrind, cold startup, bootstrap CI: "
              "**NOT_MEASURED**; ці рядки не є дозволом на production cutover.",
              "Raw samples: `samples.jsonl`; environment/SHA: `environment.json`. "
              "Для точного висновку про перевагу потрібен окремий "
              "ієрархічний 95% CI та native SENS receipts."]
    (out / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (out / "STATUS").write_text("TRANSPORT_PARITY_VERIFIED; TIMING_EXPLORATORY; SEMANTICS_NOT_TESTED\n")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError) as exc:
        print(f"BLOCKED_NO_TIMING: {exc}", file=sys.stderr)
        sys.exit(1)
