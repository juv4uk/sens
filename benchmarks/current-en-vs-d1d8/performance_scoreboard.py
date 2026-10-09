#!/usr/bin/env python3
"""Publish measured SENS performance, never a test-only PASS or invented win.

This reporter consumes real CPU phase samples and/or Cachegrind pack samples.
It does NOT infer language performance from the two-case D3 smoke corpus.
"""
from __future__ import annotations

import argparse
import csv
import json
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
        "## Canonical bits vs English surface · same SENS executable",
        "",
        "Measured phase time is inside the helper, excluding process startup. "
        "For repeated execution it is divided by the recorded invocation count.",
        "",
        "| Workload | Phase | English median (ns/op) | Binary median (ns/op) | English / binary | Paired samples |",
        "|---|---|---:|---:|---:|---:|",
    ]
    summaries = []
    for (workload, phase), candidates in sorted(pairs.items()):
        en = candidates.get("english-surface", [])
        bi = candidates.get("canonical-d1d8", [])
        if len(en) != len(bi) or len(en) < 3:
            raise ValueError(f"unpaired or undersampled measurement: {workload}/{phase}")
        a, b = statistics.median(en), statistics.median(bi)
        ratio = (a / b) if b > 0 else None
        show = f"{ratio:.3f}x" if ratio is not None else "n/a"
        out.append(f"| {workload} | {phase} | {a:.1f} | {b:.1f} | {show} | {len(en)} |")
        summaries.append({
            "workload": workload, "phase": phase, "english_median_ns": a,
            "binary_median_ns": b, "english_over_binary": ratio, "samples_per_lane": len(en),
        })
    out += [
        "",
        "> An English/binary ratio above 1 means the binary lane measured faster "
        "for that phase on this runner. These two small D3 smoke programs "
        "cannot establish a general SENS-vs-Lisp or SENS-vs-Python win.",
        "",
    ]
    provenance = rows[0]["provenance"]
    out.append(f"Revision: \x60{next(iter(shas))}\x60; CPU: {provenance.get('cpu', 'unknown')}; "
               f"rustc: {provenance.get('rustc', 'unknown')}.")
    out.append("")
    return out, {"git_sha": next(iter(shas)), "provenance": provenance, "cases": summaries}


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
        "it excludes separate word-boundary framing.",
        "",
        "| Domain workload | Words | Mode | Packed / byte proxy | I-refs / word |",
        "|---|---:|---|---:|---:|",
    ]
    cases = []
    for row in sorted(rows, key=lambda r: (r["workload"], int(r["n"]), r["mode"])):
        density = float(row["packed_to_unpacked_ratio"])
        instructions = float(row["net_i_refs_per_word"])
        if instructions < 0 or not 0 < density <= 1:
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
    ap.add_argument("--pack-tsv", type=Path)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()
    if not args.cpu_jsonl and not args.pack_tsv:
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
