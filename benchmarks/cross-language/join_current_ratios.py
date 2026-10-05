#!/usr/bin/env python3
"""Join same-machine current-SENS and external-control benchmark rows."""

from __future__ import annotations

import argparse
import csv
import math
import statistics
from collections import defaultdict
from pathlib import Path


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh, delimiter="\t"))


def median_rows(rows: list[dict[str, str]]) -> dict[tuple[str, str], tuple[float, float]]:
    grouped: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[(row["runtime"], row["workload"])].append(row)
    result = {}
    for key, sample in grouped.items():
        result[key] = (
            statistics.median(float(row["i_refs"]) for row in sample),
            statistics.median(float(row["wall_s"]) for row in sample),
        )
    return result


def gmean(values: list[float]) -> float:
    if not values or any(value <= 0 for value in values):
        raise ValueError("geometric mean requires positive values")
    return math.exp(sum(math.log(value) for value in values) / len(values))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--external", type=Path, required=True)
    ap.add_argument("--sens", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    external = read_tsv(args.external)
    sens = read_tsv(args.sens)
    med = median_rows(external + sens)

    workloads = sorted({row["workload"] for row in sens})
    external_runtimes = sorted({row["runtime"] for row in external})
    if {row["runtime"] for row in sens} != {"sens-exact"}:
        raise RuntimeError("SENS file must contain only sens-exact rows")

    args.out.mkdir(parents=True, exist_ok=True)
    detail_rows = []
    iref_ratios: dict[str, list[float]] = defaultdict(list)
    wall_ratios: dict[str, list[float]] = defaultdict(list)

    for workload in workloads:
        sens_iref, sens_wall = med[("sens-exact", workload)]
        for runtime in external_runtimes:
            ext_iref, ext_wall = med[(runtime, workload)]
            i_ratio = sens_iref / ext_iref
            w_ratio = sens_wall / ext_wall
            iref_ratios[runtime].append(i_ratio)
            wall_ratios[runtime].append(w_ratio)
            detail_rows.append(
                {
                    "workload": workload,
                    "runtime": runtime,
                    "sens_i_refs": sens_iref,
                    "external_i_refs": ext_iref,
                    "sens_over_external_i_refs": i_ratio,
                    "sens_wall_s": sens_wall,
                    "external_wall_s": ext_wall,
                    "sens_over_external_wall": w_ratio,
                }
            )

    fields = list(detail_rows[0])
    with (args.out / "ratios.tsv").open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, delimiter="\t")
        writer.writeheader()
        writer.writerows(detail_rows)

    lines = [
        "# Same-machine current SENS vs external controls",
        "",
        "Primary comparison: Cachegrind I refs. Wall time is auxiliary.",
        "All ratios are SENS / external, so values above 1 mean SENS used more.",
        "",
        "| workload | runtime | SENS I refs | external I refs | SENS/external I refs | SENS wall, s | external wall, s | SENS/external wall |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in detail_rows:
        lines.append(
            "| {workload} | {runtime} | {sens_i_refs:,.0f} | {external_i_refs:,.0f} | "
            "{sens_over_external_i_refs:.3f}× | {sens_wall_s:.6f} | {external_wall_s:.6f} | "
            "{sens_over_external_wall:.3f}× |".format(**row)
        )

    lines += [
        "",
        "## Geometric mean across the five workloads",
        "",
        "| runtime | SENS/external I refs | SENS/external wall |",
        "|---|---:|---:|",
    ]
    for runtime in external_runtimes:
        lines.append(
            f"| {runtime} | {gmean(iref_ratios[runtime]):.3f}× | "
            f"{gmean(wall_ratios[runtime]):.3f}× |"
        )

    lines += [
        "",
        "Interpretation boundary:",
        "- current SENS rows use exact D3/D4/D5 call heads through the mixed exact-domain bridge;",
        "- external rows use the validated #3416 implementations and the same workload parameters/oracles;",
        "- all rows in this report come from the same GitHub Actions job and host;",
        "- Rust compile cost is outside the execution row; the SENS runner is likewise prebuilt;",
        "- full-process rows include each runtime's startup plus program execution;",
        "- historical Function8/Sens8 numbers are not part of these ratios.",
        "",
    ]
    report = "\n".join(lines)
    (args.out / "report.md").write_text(report, encoding="utf-8")
    print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
