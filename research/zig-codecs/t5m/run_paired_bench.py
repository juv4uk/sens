#!/usr/bin/env python3
"""CI_GLUE_NO_SEMANTICS: paired T5M Zig / asm / Rust mechanical benchmark.

T5M — дефолтний фізичний носій (5 трітів/байт). Тут порівнюються три
механічні бекенди того самого кодека: Zig, x86-64 асемблер і Rust.
Рівність фізичних байтів перевіряється ДО таймінгу. Це транспортна
механіка, НЕ SENS-семантика і не дозвіл на production cutover.
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
T5M_DIR = "research/zig-codecs/t5m"
ZIG_SOURCE = "research/zig-codecs/t5m_bench.zig"  # T5M-кодек t5m.zig (5 трітів/байт, дефолт)
ASM_BENCH = f"{T5M_DIR}/bench_asm.zig"
ASM_SOURCES = ["research/asm-t5m/t5m_words.S", "research/asm-t5m/t5m_pack.S"]
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


def percentile_nearest_rank(values: list[float], percentile: int) -> float:
    """Nearest-rank percentile; keep small exploratory samples explicit."""
    if not values:
        raise ValueError("percentile requires at least one sample")
    if not 1 <= percentile <= 100:
        raise ValueError("percentile must be between 1 and 100")
    rank = (percentile * len(values) + 99) // 100
    return sorted(values)[rank - 1]


def build_binaries(out: Path, impls: list[str]) -> dict[str, Path]:
    binaries: dict[str, Path] = {}
    if "zig" in impls:
        zig_bin = out / "zig_t5m_bench"
        checked(["zig", "build-exe", ZIG_SOURCE, "-O", "ReleaseFast", "-lc", f"-femit-bin={zig_bin}"])
        binaries["zig"] = zig_bin
    if "asm" in impls:
        objs = []
        for src in ASM_SOURCES:
            obj = out / (Path(src).stem + ".o")
            checked(["as", "--64", "-o", str(obj), src])
            objs.append(str(obj))
        asm_bin = out / "asm_t5m_bench"
        checked(["zig", "build-exe", ASM_BENCH, *objs, "-O", "ReleaseFast", "-lc",
                 f"-femit-bin={asm_bin}"])
        binaries["asm"] = asm_bin
    if "rust" in impls:
        checked(["cargo", "build", "--locked", "--release", "-p", "sens",
                 "--example", "zig_t5_matched_bench"])
        binaries["rust"] = ROOT / RUST_EXAMPLE
    return binaries


def main() -> int:
    cli = argparse.ArgumentParser()
    cli.add_argument("--out-dir", type=Path, required=True)
    cli.add_argument("--pairs", type=int, default=3)
    cli.add_argument("--impls", default="zig,asm,rust")
    cli.add_argument("--zig-pin", default="0.16.0", choices=("0.16.0",))
    args = cli.parse_args()
    pinned = (ROOT / ".zig-version").read_text(encoding="utf-8").strip()
    if pinned != "0.16.0" or args.zig_pin != pinned:
        raise RuntimeError("Zig pin drift: both repository and benchmark must use 0.16.0")
    if args.pairs < 3:
        raise SystemExit("--pairs must be >=3 independent outer process pairs")
    impls = [name for name in args.impls.split(",") if name]
    if not set(impls) <= {"zig", "asm", "rust"}:
        raise SystemExit("--impls must be a subset of zig,asm,rust")

    out = args.out_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)
    meta = {
        "role": "CI_GLUE_NO_SEMANTICS",
        "kind": "mechanical_transport_benchmark_only",
        "codec": "T5M default: 5 trits per byte (3^5=243<256), separator 2",
        "impls": impls,
        "git_sha": checked(["git", "rev-parse", "HEAD"]).strip(),
        "os": platform.platform(),
        "cpu": platform.processor() or platform.uname().machine,
        "zig": checked(["zig", "version"]).strip(),
        "pairs": args.pairs,
        "seed": 20261020,
        "zig_flags": "-O ReleaseFast -lc",
        "asm_flags": "as --64 (t5m_words.S + t5m_pack.S); zig build-exe bench_asm.zig <objs> -O ReleaseFast -lc",
        "expected_zig_pin": args.zig_pin,
        "scope": "усі бекенди = word->byte end-to-end; рядки прямо порівнювані",
    }
    if meta["zig"] != args.zig_pin:
        raise RuntimeError(f"Zig pin mismatch: expected {args.zig_pin}, actual {meta['zig']}")
    if "rust" in impls:
        meta["rustc"] = checked(["rustc", "-Vv"]).strip()
    (out / "environment.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")

    checked(["zig", "test", "research/zig-codecs/t5m.zig"])
    binaries = build_binaries(out, impls)
    meta["binary_sha256"] = {name: digest(path) for name, path in binaries.items()}
    (out / "environment.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")

    rng = random.Random(meta["seed"])
    batches = []
    fixtures = {}
    with (out / "samples.jsonl").open("w", encoding="utf-8") as handle:
        for pair in range(args.pairs):
            order = list(impls)
            rng.shuffle(order)
            paired_fixtures: dict[int, dict[str, tuple]] = {}
            paired_bytes: dict[int, dict[str, str]] = {}
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
                                       f"fixtures={len(fx_rows)} physical={len(physical_rows)} "
                                       f"samples={len(sample_rows)}")
                for f in fx_rows:
                    key = int(f["forms"])
                    paired_fixtures.setdefault(key, {})[name] = (
                        int(f["words"]), int(f["bytes"]), int(f["fnv64"], 16))
                for physical_row in physical_rows:
                    paired_bytes.setdefault(int(physical_row["forms"]), {})[name] = physical_row["hex"]
                for s in sample_rows:
                    row = {"pair": pair, "impl": name, "forms": int(s["forms"]),
                           "op": s["op"], "elapsed_ns": int(s["elapsed_ns"]), "reps": int(s["reps"])}
                    if row["elapsed_ns"] <= 0 or row["reps"] <= 0:
                        raise RuntimeError(f"INVALID_TIMING {row}")
                    row["ns_per_op"] = row["elapsed_ns"] / row["reps"]
                    handle.write(json.dumps(row) + "\n")
                    batches.append(row)
            for forms, sides in paired_fixtures.items():
                b = paired_bytes.get(forms, {})
                ref_name = order[0]
                if b.get(ref_name) is None:
                    raise RuntimeError(f"BLOCKED_NO_TIMING missing physical bytes forms={forms}")
                if len(set(b.values())) != 1:
                    (out / "STATUS").write_text(f"BLOCKED_NO_TIMING: physical byte mismatch forms={forms}\n")
                    raise RuntimeError(f"BLOCKED_NO_TIMING forms={forms}, physical byte mismatch")
                if len(set(sides.values())) != 1:
                    (out / "STATUS").write_text(f"BLOCKED_NO_TIMING: fixture mismatch forms={forms}\n")
                    raise RuntimeError(f"BLOCKED_NO_TIMING forms={forms}, fixture mismatch")
                if len(b[ref_name]) != 2 * sides[ref_name][1]:
                    raise RuntimeError(f"BLOCKED_NO_TIMING forms={forms}, physical length mismatch")
                fixtures[forms] = sides[ref_name]
        if len(fixtures) != 4:
            raise RuntimeError("BLOCKED_NO_TIMING incomplete fixture parity")

    grouped = defaultdict(list)
    for row in batches:
        grouped[(row["forms"], row["op"], row["impl"])].append(row["ns_per_op"])
    metrics = [(name, stat) for name in impls for stat in ("p50", "p90")]
    header = "| Форми | Операція | " + " | ".join(f"{name} {stat} нс/оп" for name, stat in metrics) + " |"
    sep = "|---:|---|" + "---:|" * len(metrics)
    lines = ["# Zig ↔ asm ↔ Rust T5M · механічний A/B", "",
             "**ТІЛЬКИ transport**, не SENS semantic oracle. T5M = 5 трітів/байт.",
             "Фізичні bytes/FNV-1a matched між усіма бекендами; усі бекенди міряють "
             "word→byte end-to-end. p50 — медіана, p90 — nearest-rank над сирими пробами. "
             "**Статистика дослідницька, не K–J CI і не доказ швидкості мови.**", "",
             header, sep]
    for forms in (1, 16, 128, 1024):
        for op in ("encode", "decode"):
            cells = []
            ok = True
            for name in impls:
                vals = grouped[(forms, op, name)]
                if len(vals) != 5 * args.pairs:
                    ok = False
                    break
                p50 = statistics.median(vals)
                p90 = percentile_nearest_rank(vals, 90)
                cells.extend((f"{p50:.1f}", f"{p90:.1f}"))
            if not ok:
                raise RuntimeError(f"BLOCKED_NO_TIMING missing paired samples {forms}/{op}")
            lines.append(f"| {forms} | {op} | " + " | ".join(cells) + " |")
    lines += ["", "Пам'ять/алокації, cachegrind, cold startup, bootstrap CI: **NOT_MEASURED**.",
              "Raw samples: `samples.jsonl`; environment/SHA: `environment.json`."]
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
