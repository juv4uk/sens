#!/usr/bin/env python3
"""Publish measured SENS performance, never a test-only PASS or invented win.

This reporter consumes real CPU phase samples and/or Cachegrind pack samples.
It does NOT infer language performance from the two-case D3 smoke corpus.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
from collections import defaultdict
from pathlib import Path


def cpu_report(path: Path) -> tuple[list[str], dict]:
    rows = [json.loads(s) for s in path.read_text(encoding="utf-8").splitlines() if s.strip()]
    if not rows:
        raise ValueError("no CPU measurements produced")
    pairs: dict[tuple[str, str], dict[str, list[float]]] = defaultdict(
        lambda: defaultdict(list)
    )
    shas = {row["git_sha"] for row in rows}
    binaries = {row["binary_sha256"] for row in rows}
    corpora = {row["corpus_sha256"] for row in rows}
    if len(shas) != 1 or len(binaries) != 1 or len(corpora) != 1:
        raise ValueError("mixed revisions or binaries cannot be compared")
    for row in rows:
        if row["oracle_ok"] is not True or row["legacy_identity_used"] is not False:
            raise ValueError("unvalidated or historical execution in timed corpus")
        metric = row["metrics"]
        nanos = metric["phase_elapsed_ns"]
        if not isinstance(nanos, int) or nanos < 0:
            raise ValueError("invalid elapsed nanoseconds")
        if row["phase"] == "repeated":
            count = metric["repeat_n"]
            if not isinstance(count, int) or count < 1:
                raise ValueError("missing positive repeat count")
            nanos = nanos / count
        pairs[(row["workload"], row["phase"])][row["candidate"]].append(float(nanos))
    out = [
        "## Canonical bits vs Ukrainian surface · same SENS executable",
        "",
        "Measured phase time is inside the helper, excluding process startup. "
        "For repeated execution it is divided by the recorded invocation count.",
        "",
        "| Workload | Phase | Ukrainian median (ns/op) | Binary median (ns/op) | Ukrainian / binary | Paired samples |",
        "|---|---|---:|---:|---:|---:|",
    ]
    summaries = []
    for (workload, phase), candidates in sorted(pairs.items()):
        en = candidates.get("ukrainian-surface", [])
        bi = candidates.get("canonical-d1d8", [])
        if len(en) != len(bi) or len(en) < 3:
            raise ValueError(f"unpaired or undersampled measurement: {workload}/{phase}")
        a, b = statistics.median(en), statistics.median(bi)
        ratio = (a / b) if b > 0 else None
        show = f"{ratio:.3f}x" if ratio is not None else "n/a"
        out.append(f"| {workload} | {phase} | {a:.1f} | {b:.1f} | {show} | {len(en)} |")
        summaries.append({
            "workload": workload, "phase": phase, "ukrainian_median_ns": a,
            "binary_median_ns": b, "ukrainian_over_binary": ratio, "samples_per_lane": len(en),
        })
    out += [
        "",
        "> An Ukrainian/binary ratio above 1 means the binary lane measured faster "
        "for that phase on this runner. These two small D3 smoke programs "
        "cannot establish a general SENS-vs-Lisp or SENS-vs-Python win.",
        "",
    ]
    provenance = rows[0]["provenance"]
    out.append(f"Revision: \x60{next(iter(shas))}\x60; CPU: {provenance.get('cpu', 'unknown')}; "
               f"rustc: {provenance.get('rustc', 'unknown')}.")
    out.append("")
    return out, {"git_sha": next(iter(shas)), "provenance": provenance, "cases": summaries}


def physical_hot_report(path: Path) -> tuple[list[str], dict]:
    """Compare actual same-byte T5/D2 mechanisms; never a cross-language win."""
    rows = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(rows, list) or not rows:
        raise ValueError("no measured physical hot rows")
    by_count: dict[int, dict[str, dict]] = defaultdict(dict)
    for row in rows:
        n, phase = row["forms"], row["phase"]
        if not isinstance(n, int) or n < 1 or phase in by_count[n]:
            raise ValueError("invalid or duplicate physical phase")
        for key in ("median_ns_op", "p95_ns_op", "samples", "physical_bytes"):
            if not isinstance(row[key], int):
                raise ValueError(f"{phase}: invalid {key}")
        if (row["median_ns_op"] <= 0 or row["p95_ns_op"] < row["median_ns_op"]
                or row["samples"] < 3 or row["physical_bytes"] < 1):
            raise ValueError(f"{phase}: invalid timing or evidence")
        by_count[n][phase] = row

    env_path = path.with_name("hot-environment.json")
    environment = json.loads(env_path.read_text(encoding="utf-8")) if env_path.is_file() else {}
    results = []
    out = [
        "## Physical T5 to D2 · measured hot CPU",
        "",
        "Same physical T5 bytes and D2 grammar per workload. Warm process; "
        "p50/p95 are nanoseconds per packet; process startup is excluded.",
        "",
        "| D3 QUOTE forms | Physical T5 bytes | T5→text→D2 AST p50 ns | T5→repack→D2 AST p50 ns | T5→typed→D2 AST p50 ns | Repack / typed | Text / typed | Typed p95 ns |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for n, phases in sorted(by_count.items()):
        required = {"t5_visible_parse_d2", "t5_direct_d2", "t5_words_d2"}
        if not required.issubset(phases):
            raise ValueError(f"{n} forms lacks required phases: {sorted(required - set(phases))}")
        same_bytes = {r["physical_bytes"] for r in phases.values()}
        hashes = {r["physical_sha256"] for r in phases.values()}
        observables = {r["observable"] for r in phases.values()}
        if len(same_bytes) != 1 or len(hashes) != 1 or len(observables) != 1:
            raise ValueError(f"{n} forms has mismatched payload or result across phases")
        counts = {phases[name]["samples"] for name in required}
        if len(counts) != 1:
            raise ValueError(f"{n} forms has unpaired sample counts across AST readers")
        visible = phases["t5_visible_parse_d2"]["median_ns_op"]
        prior = phases["t5_direct_d2"]["median_ns_op"]
        typed = phases["t5_words_d2"]["median_ns_op"]
        p95 = phases["t5_words_d2"]["p95_ns_op"]
        result = {
            "forms": n, "physical_bytes": next(iter(same_bytes)),
            "visible_ast_median_ns": visible, "previous_direct_median_ns": prior,
            "typed_word_median_ns": typed, "typed_word_p95_ns": p95,
            "previous_over_typed": prior / typed, "visible_over_typed": visible / typed,
            "samples": phases["t5_words_d2"]["samples"],
            "payload_sha256": next(iter(hashes)),
        }
        results.append(result)
        out.append(
            f"| {n} | {result['physical_bytes']} | {visible:,} | {prior:,} | "
            f"{typed:,} | {prior / typed:.3f}x | {visible / typed:.3f}x | {p95:,} |"
        )
    out += [
        "",
        "Each compared lane starts with identical physical T5 bytes and ends "
        "with a complete D2 AST. Unlike the legacy t5_open_d2 text-only "
        "view, t5_visible_parse_d2 includes both text rendering and D2 parsing. "
        "The repack lane reconstructs a dense payload and width schedule; "
        "the typed lane passes decoded words directly to the SAME D2 reader. "
        "No ratio here is an overall language-execution or cross-runtime claim.",
        "",
        f"Benchmark commit: {environment.get('commit', 'unknown')}; "
        f"samples per phase: {environment.get('samples', 'unknown')}.",
        "",
    ]
    # Compare the *same* binary source and T5 bytes through the historical
    # allocation-heavy encoder versus the current streaming encoder.
    # Measurements are on one runner/SHA and are not an overall-language win.
    encoder_cases = []
    has_any_encoder_phase = any(
        ("t5_encode_two_pass" in phases or "t5_encode_streaming" in phases)
        for phases in by_count.values()
    )
    if has_any_encoder_phase:
        out.extend([
            "## Physical T5 encoding · measured two-pass versus streaming",
            "",
            "Both lanes start with identical exact-domain words, produce the "
            "same physical T5 bytes and run on the same CPU. The ratio "
            "two-pass / streaming above 1 means the streaming encoder won "
            "this specific workload; below 1 means it lost.",
            "",
            "| D3 QUOTE forms | Physical T5 bytes | Two-pass p50 ns | "
            "Streaming p50 ns | Two-pass / streaming | Streaming p95 ns | "
            "Paired series |",
            "|---:|---:|---:|---:|---:|---:|---:|",
        ])
        for n, phases in sorted(by_count.items()):
            needed = {"t5_encode_two_pass", "t5_encode_streaming"}
            if not needed.issubset(phases):
                raise ValueError(
                    f"{n} forms lacks paired T5 encoding phases: "
                    f"{sorted(needed - set(phases))}"
                )
            two_pass = phases["t5_encode_two_pass"]
            streaming = phases["t5_encode_streaming"]
            if two_pass["samples"] != streaming["samples"]:
                raise ValueError(f"{n} forms has unequal encoding series counts")
            if two_pass["physical_sha256"] != streaming["physical_sha256"]:
                raise ValueError(f"{n} forms encoding compared different T5 bytes")
            if two_pass["observable"] != streaming["observable"]:
                raise ValueError(f"{n} forms encoder results differ")
            baseline = two_pass["median_ns_op"]
            current = streaming["median_ns_op"]
            ratio = baseline / current
            result = {
                "forms": n,
                "physical_bytes": streaming["physical_bytes"],
                "two_pass_median_ns": baseline,
                "streaming_median_ns": current,
                "streaming_p95_ns": streaming["p95_ns_op"],
                "two_pass_over_streaming": ratio,
                "paired_series": streaming["samples"],
                "physical_sha256": streaming["physical_sha256"],
            }
            encoder_cases.append(result)
            out.append(
                f"| {n} | {result['physical_bytes']} | {baseline:,} | "
                f"{current:,} | {ratio:.3f}x | "
                f"{streaming['p95_ns_op']:,} | {streaming['samples']} |"
            )
        out.extend([
            "",
            "Measured encoder ratio is an implementation-local T5 packing "
            "comparison, not a claim about interpreter throughput. "
            "Incorrect byte parity blocks timing upstream.",
            "",
        ])
    return out, {"environment": environment, "cases": results, "encoding": encoder_cases}


def pack_report(path: Path) -> tuple[list[str], dict]:
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    if not rows:
        raise ValueError("no Cachegrind packing measurements")
    lines = [
        "## Dense bit packing · Cachegrind I-refs",
        "",
        "I-refs are instruction references, NOT elapsed nanoseconds. "
        "The byte ratio compares packed payload against one-byte-per-word proxy; "
        "it excludes separate word-boundary framing. "
        "For W9 the physical payload legitimately exceeds one byte per word; "
        "ratios above 1 are expansion evidence, not corruption.",
        "",
        "| Domain workload | Words | Mode | Packed / byte proxy | I-refs / word |",
        "|---|---:|---|---:|---:|",
    ]
    cases = []
    for row in sorted(rows, key=lambda r: (r["workload"], int(r["n"]), r["mode"])):
        density = float(row["packed_to_unpacked_ratio"])
        instructions = float(row["net_i_refs_per_word"])
        # W9 needs at least 9 bits/word: 9/8 > 1 compared to a one-byte
        # proxy. Reject only nonfinite, zero or negative observations, never
        # falsify honest expansion by demanding every width compresses.
        if not math.isfinite(density) or not math.isfinite(instructions) or density <= 0 or instructions < 0:
            raise ValueError("invalid pack metric")
        lines.append(f"| {row['workload']} | {row['n']} | {row['mode']} | {density:.4f} | {instructions:.1f} |")
        cases.append({
            "workload": row["workload"], "n": int(row["n"]), "mode": row["mode"],
            "packed_bytes": int(row["packed_bytes"]),
            "unpacked_bytes_proxy": int(row["unpacked_bytes_proxy"]),
            "packed_to_unpacked_ratio": density,
            "net_i_refs_per_word": instructions,
        })
    lines.append("")
    return lines, {"cases": cases}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cpu-jsonl", type=Path)
    ap.add_argument("--physical-hot-json", type=Path)
    ap.add_argument("--pack-tsv", type=Path)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()
    if not args.cpu_jsonl and not args.pack_tsv and not args.physical_hot_json:
        ap.error("supply at least one measured evidence file")
    sections = [
        "# SENS benchmark scoreboard",
        "",
        "Real observations on a shared GitHub-hosted CPU. "
        "Do not compare across machines, revisions or semantic generations.",
        "",
    ]
    report: dict[str, object] = {"schema": "sens-measured-scoreboard/v1"}
    if args.cpu_jsonl:
        text, data = cpu_report(args.cpu_jsonl)
        sections.extend(text)
        report["cpu"] = data
    if args.physical_hot_json:
        text, data = physical_hot_report(args.physical_hot_json)
        sections.extend(text)
        report["physical_hot"] = data
    if args.pack_tsv:
        text, data = pack_report(args.pack_tsv)
        sections.extend(text)
        report["packing"] = data
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("\n".join(sections) + "\n", encoding="utf-8")
    args.out.with_suffix(".json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(args.out.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
