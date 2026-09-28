#!/usr/bin/env python3
"""#1665: summarize the post-M8 EN-text / SENS-text / SENS-FASL run.

The raw TSV is the authority for measurements. This reporter derives:
- load/parse/decode cost = load - empty session;
- steady call cost = (repeat(N) - ready) / N;
- total one-call cost = full - empty session.

No automatic winner threshold is applied. Ratios are evidence, not language law.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
from collections import defaultdict
from pathlib import Path

TRANSPORTS = ("en-text", "sens-text", "sens-fasl")
MODES = ("load", "ready", "repeat", "full")


def median(values):
    return statistics.median(values)


def geomean(values):
    if not values:
        return float("nan")
    if any(value <= 0 for value in values):
        raise ValueError("geometric mean requires positive ratios")
    return math.exp(sum(math.log(value) for value in values) / len(values))


def spread_pct(values):
    mid = median(values)
    return 0.0 if mid == 0 else (max(values) - min(values)) / mid * 100.0


def read_environment(path):
    if not path:
        return {}
    result = {}
    with open(path, encoding="utf-8") as handle:
        reader = csv.reader(handle, delimiter="\t")
        header = next(reader, None)
        if header != ["key", "value"]:
            raise ValueError(f"{path}: expected environment header key/value")
        for row in reader:
            if len(row) != 2:
                raise ValueError(f"{path}: malformed environment row: {row!r}")
            result[row[0]] = row[1]
    return result


def read_raw(path):
    rows = defaultdict(list)
    params = {}
    repeat_n = {}
    with open(path, encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        expected = [
            "workload",
            "params",
            "transport",
            "mode",
            "rep",
            "repeat_n",
            "instructions",
        ]
        if reader.fieldnames != expected:
            raise ValueError(f"{path}: unexpected header {reader.fieldnames!r}")

        for row in reader:
            count = int(row["instructions"])
            if count <= 0:
                raise ValueError(f"{path}: non-positive instruction count: {row!r}")

            if row["workload"] == "empty":
                if row["mode"] != "empty":
                    raise ValueError("empty rows must use mode=empty")
                rows[("empty", "-", "empty")].append(count)
                continue

            transport = row["transport"]
            mode = row["mode"]
            if transport not in TRANSPORTS:
                raise ValueError(f"unknown transport {transport!r}")
            if mode not in MODES:
                raise ValueError(f"unknown mode {mode!r}")

            name = row["workload"]
            params.setdefault(name, row["params"])
            if params[name] != row["params"]:
                raise ValueError(f"{name}: params changed inside one run")

            if mode == "repeat":
                n = int(row["repeat_n"])
                if n <= 0:
                    raise ValueError(f"{name}/{transport}: repeat_n must be positive")
                repeat_n.setdefault((name, transport), n)
                if repeat_n[(name, transport)] != n:
                    raise ValueError(f"{name}/{transport}: repeat_n changed inside one run")
            elif row["repeat_n"] != "-":
                raise ValueError(f"{name}/{transport}/{mode}: repeat_n must be '-'")

            rows[(name, transport, mode)].append(count)

    if ("empty", "-", "empty") not in rows:
        raise ValueError("raw evidence has no empty-session measurements")

    names = sorted(params)
    for name in names:
        for transport in TRANSPORTS:
            for mode in MODES:
                key = (name, transport, mode)
                if key not in rows:
                    raise ValueError(f"missing evidence row for {key}")
            if (name, transport) not in repeat_n:
                raise ValueError(f"missing repeat_n for {name}/{transport}")
    return rows, params, repeat_n


def derive(rows, params, repeat_n):
    empty_values = rows[("empty", "-", "empty")]
    empty = median(empty_values)
    metrics = {}

    for name in sorted(params):
        for transport in TRANSPORTS:
            med = {
                mode: median(rows[(name, transport, mode)])
                for mode in MODES
            }
            n = repeat_n[(name, transport)]
            load = med["load"] - empty
            setup = med["ready"] - med["load"]
            steady = (med["repeat"] - med["ready"]) / n
            total = med["full"] - empty

            if load <= 0:
                raise ValueError(f"{name}/{transport}: load-empty is non-positive ({load})")
            if steady <= 0:
                raise ValueError(
                    f"{name}/{transport}: repeat-ready per call is non-positive ({steady}); "
                    "increase REPEAT_N instead of clamping noise"
                )
            if total <= 0:
                raise ValueError(f"{name}/{transport}: full-empty is non-positive ({total})")

            metrics[(name, transport)] = {
                "load": load,
                "setup": setup,
                "steady_call": steady,
                "total": total,
                "repeat_n": n,
                "raw_medians": med,
                "spread_pct": {
                    mode: spread_pct(rows[(name, transport, mode)])
                    for mode in MODES
                },
            }
    return empty, spread_pct(empty_values), metrics


def fmt_int(value):
    return f"{value:,.0f}"


def build_report(raw_path, environment, params, empty, empty_spread, metrics):
    names = sorted(params)
    lines = [
        "# Post-M8 three-way benchmark (#1665)",
        "",
        "Один current-main бінарник, однакові workload-и й oracle:",
        "",
        "- **EN text** — людська англійська поверхня, text parse;",
        "- **SENS text** — exact 8-bit reader spelling, text parse;",
        "- **SENS FASL** — exact one-byte function transport, binary decode.",
        "",
        "Primary metric: Cachegrind I refs, median repeated runs. "
        "Ніякого автоматичного performance verdict/threshold немає.",
        "",
    ]

    if environment:
        lines += [
            "## Provenance",
            "",
            f"- git SHA: {environment.get('git_sha', 'unknown')}",
            f"- dirty tracked tree: {environment.get('git_dirty', 'unknown')}",
            f"- CPU: {environment.get('cpu', 'unknown')}",
            f"- Valgrind: {environment.get('valgrind', 'unknown')}",
            f"- rustc: {environment.get('rustc', 'unknown')}",
            f"- channels.scm sha256: {environment.get('channels_sha256', 'unknown')}",
            f"- raw evidence: {raw_path}",
            "",
        ]

    lines += [
        "## Load / parse / decode",
        "",
        "Net instructions = load - empty session.",
        "",
        "| workload · params | EN text | SENS text | SENS FASL | EN/FASL | SENS-text/FASL |",
        "|---|---:|---:|---:|---:|---:|",
    ]

    en_fasl_load = []
    sens_fasl_load = []
    for name in names:
        en = metrics[(name, "en-text")]["load"]
        st = metrics[(name, "sens-text")]["load"]
        sf = metrics[(name, "sens-fasl")]["load"]
        r1 = en / sf
        r2 = st / sf
        en_fasl_load.append(r1)
        sens_fasl_load.append(r2)
        lines.append(
            f"| {name} · {params[name]} | {fmt_int(en)} | {fmt_int(st)} | {fmt_int(sf)} "
            f"| ×{r1:.3f} | ×{r2:.3f} |"
        )
    lines += [
        f"| **geomean** | | | | **×{geomean(en_fasl_load):.3f}** "
        f"| **×{geomean(sens_fasl_load):.3f}** |",
        "",
        "## Steady call execution",
        "",
        "Per-call instructions = (repeat(N) - ready) / N; load and setup are excluded.",
        "",
        "| workload · params | EN text | SENS text | SENS FASL | EN/SENS-text | EN/FASL | SENS-text/FASL |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]

    en_st_exec = []
    en_sf_exec = []
    st_sf_exec = []
    for name in names:
        en = metrics[(name, "en-text")]["steady_call"]
        st = metrics[(name, "sens-text")]["steady_call"]
        sf = metrics[(name, "sens-fasl")]["steady_call"]
        r_en_st = en / st
        r_en_sf = en / sf
        r_st_sf = st / sf
        en_st_exec.append(r_en_st)
        en_sf_exec.append(r_en_sf)
        st_sf_exec.append(r_st_sf)
        lines.append(
            f"| {name} · {params[name]} | {fmt_int(en)} | {fmt_int(st)} | {fmt_int(sf)} "
            f"| ×{r_en_st:.3f} | ×{r_en_sf:.3f} | ×{r_st_sf:.3f} |"
        )
    lines += [
        f"| **geomean** | | | | **×{geomean(en_st_exec):.3f}** "
        f"| **×{geomean(en_sf_exec):.3f}** | **×{geomean(st_sf_exec):.3f}** |",
        "",
        "## One-call end-to-end",
        "",
        "Net instructions = full - empty session; includes load + setup + one call.",
        "",
        "| workload · params | EN text | SENS text | SENS FASL | EN/FASL |",
        "|---|---:|---:|---:|---:|",
    ]

    end_ratios = []
    for name in names:
        en = metrics[(name, "en-text")]["total"]
        st = metrics[(name, "sens-text")]["total"]
        sf = metrics[(name, "sens-fasl")]["total"]
        end_ratios.append(en / sf)
        lines.append(
            f"| {name} · {params[name]} | {fmt_int(en)} | {fmt_int(st)} | {fmt_int(sf)} "
            f"| ×{en / sf:.3f} |"
        )
    lines += [
        f"| **geomean** | | | | **×{geomean(end_ratios):.3f}** |",
        "",
        "## Interpretation boundary",
        "",
        "- Ratios near or far from 1 are measurements, not a semantic law.",
        "- EN-text vs SENS-text steady execution tests whether M8 removed the old runtime name-resolution tax.",
        "- SENS-text vs SENS-FASL steady execution tests whether transport choice leaks into execution after loading.",
        "- Load ratios isolate text parse/lowering versus binary decode.",
        "- A contrary result is valid evidence; do not modify evaluator/registry semantics to improve this table.",
        "",
        "<details><summary>Raw repeat spread</summary>",
        "",
        f"Empty-session median: {fmt_int(empty)} I refs; spread {empty_spread:.3f}%.",
        "",
        "| workload | transport | load spread | ready spread | repeat spread | full spread |",
        "|---|---|---:|---:|---:|---:|",
    ]

    for name in names:
        for transport in TRANSPORTS:
            spreads = metrics[(name, transport)]["spread_pct"]
            lines.append(
                f"| {name} | {transport} | {spreads['load']:.3f}% | {spreads['ready']:.3f}% "
                f"| {spreads['repeat']:.3f}% | {spreads['full']:.3f}% |"
            )
    lines += ["", "</details>", ""]
    return "\n".join(lines)


def json_summary(environment, params, empty, empty_spread, metrics):
    return {
        "schema": "sens-post-m8-three-way/1",
        "environment": environment,
        "empty_session": {
            "median_instructions": empty,
            "spread_pct": empty_spread,
        },
        "workloads": {
            name: {
                "params": params[name],
                "transports": {
                    transport: metrics[(name, transport)]
                    for transport in TRANSPORTS
                },
            }
            for name in sorted(params)
        },
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("raw_tsv")
    parser.add_argument("--environment")
    parser.add_argument("--markdown-out")
    parser.add_argument("--json-out")
    args = parser.parse_args()

    rows, params, repeat_n = read_raw(args.raw_tsv)
    environment = read_environment(args.environment)
    empty, empty_spread, metrics = derive(rows, params, repeat_n)
    report = build_report(args.raw_tsv, environment, params, empty, empty_spread, metrics)
    summary = json_summary(environment, params, empty, empty_spread, metrics)

    if args.markdown_out:
        Path(args.markdown_out).write_text(report + "\n", encoding="utf-8")
    else:
        print(report)

    if args.json_out:
        Path(args.json_out).write_text(
            json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )


if __name__ == "__main__":
    main()
