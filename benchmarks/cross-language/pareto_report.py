#!/usr/bin/env python3
"""Join paired execution rows with scoped footprint evidence and compute Pareto fronts.

Cross-language dominance is intentionally limited to axes that are present and
comparable for every candidate in a comparison. Semantic-authority accounting
is never synthesized for external runtimes and is not collapsed into a scalar.
"""

from __future__ import annotations

import argparse
import csv
import json
import statistics
from pathlib import Path
from typing import Iterable


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh, delimiter="\t"))


def as_int(value: str | None) -> int | None:
    if value is None:
        return None
    text = value.strip()
    if not text or text.upper() == "N/A" or text == "None":
        return None
    return int(float(text))


def as_float(value: str | None) -> float | None:
    if value is None:
        return None
    text = value.strip()
    if not text or text.upper() == "N/A" or text == "None":
        return None
    return float(text)


def median_rows(rows: list[dict[str, str]]) -> list[dict[str, object]]:
    groups: dict[tuple[str, str, str], list[dict[str, str]]] = {}
    for row in rows:
        key = (row["runtime"], row["workload"], row.get("phase", "full"))
        groups.setdefault(key, []).append(row)

    out: list[dict[str, object]] = []
    for (runtime, workload, phase), sample in sorted(groups.items()):
        irefs = [as_int(row.get("i_refs")) for row in sample]
        wall = [as_float(row.get("wall_s")) for row in sample]
        irefs_clean = [x for x in irefs if x is not None]
        wall_clean = [x for x in wall if x is not None]
        out.append(
            {
                "runtime": runtime,
                "workload": workload,
                "phase": phase,
                "i_refs": int(statistics.median(irefs_clean)) if irefs_clean else None,
                "wall_s": statistics.median(wall_clean) if wall_clean else None,
                "samples": len(sample),
            }
        )
    return out


def dominated(a: dict[str, object], b: dict[str, object], axes: tuple[str, ...]) -> bool:
    """Return True when candidate a dominates candidate b on lower-is-better axes."""
    av: list[float] = []
    bv: list[float] = []
    for axis in axes:
        va = a.get(axis)
        vb = b.get(axis)
        if va is None or vb is None:
            return False
        av.append(float(va))
        bv.append(float(vb))
    return all(x <= y for x, y in zip(av, bv)) and any(
        x < y for x, y in zip(av, bv)
    )


def frontier(rows: list[dict[str, object]], axes: tuple[str, ...]) -> list[str]:
    eligible = [
        row for row in rows if all(row.get(axis) is not None for axis in axes)
    ]
    keep: list[str] = []
    for row in eligible:
        if not any(
            other["runtime"] != row["runtime"] and dominated(other, row, axes)
            for other in eligible
        ):
            keep.append(str(row["runtime"]))
    return sorted(keep)


def write_tsv(path: Path, rows: Iterable[dict[str, object]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, delimiter="\t")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--external", type=Path, required=True)
    ap.add_argument("--sens", type=Path, required=True)
    ap.add_argument("--footprint", type=Path, required=True)
    ap.add_argument(
        "--semantic-json",
        type=Path,
        help="optional #1973 semantic-accounting vector; never used as a scalar score",
    )
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    execution = read_tsv(args.external) + read_tsv(args.sens)
    medians = median_rows(execution)
    footprint_rows = read_tsv(args.footprint)
    footprint_by_runtime = {row["runtime"]: row for row in footprint_rows}
    footprint_by_runtime_workload = {
        (row["runtime"], row.get("workload", "")): row for row in footprint_rows
    }

    joined: list[dict[str, object]] = []
    for row in medians:
        runtime = str(row["runtime"])
        workload = str(row["workload"])
        fp_runtime = footprint_by_runtime.get(runtime)
        fp_workload = footprint_by_runtime_workload.get((runtime, workload))
        if fp_runtime is None:
            artifact = text = program = None
        else:
            artifact = as_int(fp_runtime.get("artifact_bytes"))
            text = as_int(fp_runtime.get("text_section_bytes"))
            program = as_int(fp_runtime.get("program_source_bytes"))
        # RSS is workload-specific. Never project a fib RSS measurement onto
        # ackermann/closures/etc just because the runtime name matches.
        rss = as_int(fp_workload.get("rss_bytes")) if fp_workload else None
        joined.append(
            {
                **row,
                "artifact_bytes": artifact,
                "text_section_bytes": text,
                "rss_bytes": rss,
                "program_source_bytes": program,
                "semantic_axis": "N/A",
                "semantic_completeness": "N/A",
            }
        )

    semantic = None
    if args.semantic_json:
        semantic = json.loads(args.semantic_json.read_text(encoding="utf-8"))
        if semantic.get("source_issue") != "#1973":
            raise RuntimeError(
                "semantic accounting must declare source_issue=#1973; "
                "do not inject benchmark-local semantic authority"
            )
        scope = semantic.get("scope")
        completeness = semantic.get("completeness")
        if not scope or completeness not in {"family-only", "whole-language"}:
            raise RuntimeError(
                "semantic accounting must declare scope and completeness="
                "family-only|whole-language"
            )
        for row in joined:
            if row["runtime"] == "sens-exact":
                row["semantic_axis"] = f"#1973-vector:{scope}"
                row["semantic_completeness"] = completeness

    dominance_rows: list[dict[str, object]] = []
    report: list[str] = [
        "# Pareto report — paired execution × scoped footprint",
        "",
        "Lower is better on every dominance axis. Missing axes are N/A, never zero.",
        "Semantic authority is not inferred from binaries and is not part of",
        "cross-language dominance unless comparable evidence exists for every runtime.",
        "RSS is workload-specific; a footprint row is joined to RSS only when runtime",
        "and workload both match. Executable artifact bytes remain runtime-scoped.",
        "",
    ]

    keys = sorted({(str(row["workload"]), str(row["phase"])) for row in joined})
    for workload, phase in keys:
        block = [
            row
            for row in joined
            if row["workload"] == workload and row["phase"] == phase
        ]
        for axes, label in [
            (("i_refs", "artifact_bytes"), "I-refs × executable bytes"),
            (("i_refs", "rss_bytes"), "I-refs × max RSS"),
        ]:
            front = frontier(block, axes)
            report += [
                f"## {workload} / {phase} — {label}",
                "",
                f"Pareto frontier: {', '.join(front) if front else 'N/A'}",
                "",
                "| runtime | I refs | artifact bytes | RSS bytes | frontier |",
                "|---|---:|---:|---:|:---:|",
            ]
            for row in sorted(block, key=lambda x: str(x["runtime"])):
                report.append(
                    f"| {row['runtime']} | {row['i_refs'] or 'N/A'} | "
                    f"{row['artifact_bytes'] or 'N/A'} | {row['rss_bytes'] or 'N/A'} | "
                    f"{'yes' if row['runtime'] in front else 'no'} |"
                )
            report.append("")

            eligible = [
                row for row in block if all(row.get(axis) is not None for axis in axes)
            ]
            for a in eligible:
                for b in eligible:
                    if a["runtime"] == b["runtime"]:
                        continue
                    if dominated(a, b, axes):
                        dominance_rows.append(
                            {
                                "workload": workload,
                                "phase": phase,
                                "axes": "+".join(axes),
                                "dominator": a["runtime"],
                                "dominated": b["runtime"],
                            }
                        )

    if semantic is None:
        report += [
            "## Semantic-authority axis",
            "",
            "N/A in this run. Final #3528 three-part report remains incomplete until",
            "a machine-readable vector explicitly sourced from #1973 is supplied.",
            "",
        ]
    else:
        report += [
            "## SENS semantic-authority vector",
            "",
            f"Source: #1973. Scope: {semantic['scope']}. Completeness: {semantic['completeness']}.",
            "Preserved as a vector; not collapsed into a weighted score.",
            "",
            "```json",
            json.dumps(semantic, ensure_ascii=False, indent=2),
            "```",
            "",
        ]

    args.out.mkdir(parents=True, exist_ok=True)
    joined_fields = [
        "runtime",
        "workload",
        "phase",
        "samples",
        "i_refs",
        "wall_s",
        "artifact_bytes",
        "text_section_bytes",
        "rss_bytes",
        "program_source_bytes",
        "semantic_axis",
        "semantic_completeness",
    ]
    write_tsv(args.out / "joined.tsv", joined, joined_fields)
    write_tsv(
        args.out / "dominance.tsv",
        dominance_rows,
        ["workload", "phase", "axes", "dominator", "dominated"],
    )

    payload = {
        "semantic_accounting": semantic,
        "cross_language_semantic_comparable": False,
        "joined": joined,
        "dominance": dominance_rows,
    }
    (args.out / "pareto.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (args.out / "report.md").write_text("\n".join(report), encoding="utf-8")
    print("\n".join(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
