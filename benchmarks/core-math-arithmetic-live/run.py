#!/usr/bin/env python3
"""#2698 arithmetic-live evidence runner.

Correctness/semantic parity is blocking.  Cachegrind instruction counts are
reported as evidence only and never choose semantic authority.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import subprocess


def run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def semantic_rows(binary: Path, program: Path, mode: str) -> list[str]:
    proc = run([str(binary), mode, str(program), "1"])
    return [line for line in proc.stdout.splitlines() if line.startswith("CASE=")]


def cachegrind_ir(binary: Path, program: Path, mode: str, iterations: int, out: Path) -> int:
    cg = out / f"{mode}.cachegrind"
    run([
        "valgrind",
        "--tool=cachegrind",
        "--cache-sim=no",
        "--branch-sim=no",
        f"--cachegrind-out-file={cg}",
        str(binary),
        mode,
        str(program),
        str(iterations),
        "--quiet",
    ])
    events = None
    summary = None
    for line in cg.read_text(encoding="utf-8").splitlines():
        if line.startswith("events:"):
            events = line.split()[1:]
        elif line.startswith("summary:"):
            summary = [int(x) for x in line.split()[1:]]
    if events is None or summary is None:
        raise RuntimeError(f"missing cachegrind events/summary in {cg}")
    values = dict(zip(events, summary, strict=True))
    return values["Ir"]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--binary", type=Path, required=True)
    ap.add_argument("--program", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--iterations", type=int, default=5000)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    factor_rows = semantic_rows(args.binary, args.program, "factorized")
    flat_rows = semantic_rows(args.binary, args.program, "six-table")
    assert factor_rows == flat_rows, (factor_rows, flat_rows)
    assert len(factor_rows) == 7

    factor_ir = cachegrind_ir(
        args.binary, args.program, "factorized", args.iterations, args.out
    )
    flat_ir = cachegrind_ir(
        args.binary, args.program, "six-table", args.iterations, args.out
    )

    perf_rows = [
        {
            "mode": "factorized",
            "iterations": args.iterations,
            "cachegrind_Ir": factor_ir,
            "Ir_per_case_iteration": factor_ir / (args.iterations * len(factor_rows)),
        },
        {
            "mode": "six-table-control",
            "iterations": args.iterations,
            "cachegrind_Ir": flat_ir,
            "Ir_per_case_iteration": flat_ir / (args.iterations * len(factor_rows)),
        },
    ]
    with (args.out / "instruction-counts.tsv").open(
        "w", newline="", encoding="utf-8"
    ) as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=list(perf_rows[0].keys()),
            delimiter="	",
            lineterminator="
",
        )
        writer.writeheader()
        writer.writerows(perf_rows)

    fact_rows = [
        {
            "model": "factorized",
            "charged_semantic_facts": 7,
            "per_result_runtime_rows": 0,
            "facts": "|".join([
                "additive-family-operation-law",
                "multiplicative-family-operation-law",
                "additive-identity-0",
                "multiplicative-identity-1",
                "generic-inverse-quotient-role-law",
                "multiplicative-zero-partiality",
                "binary-family-role-coordinate-law",
            ]),
            "interpretation": "generative structure; no raw fact-count win claimed",
        },
        {
            "model": "six-independent-control",
            "charged_semantic_facts": 6,
            "per_result_runtime_rows": 6,
            "facts": "|".join([
                "ADD-direct-law",
                "MUL-direct-law",
                "NEG-direct-law",
                "SUB-direct-law",
                "RECIP-direct-law-with-zero-partiality",
                "DIV-direct-law-with-zero-partiality",
            ]),
            "interpretation": "flat control; direct rows encode every familiar result separately",
        },
    ]
    with (args.out / "semantic-facts.tsv").open(
        "w", newline="", encoding="utf-8"
    ) as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=list(fact_rows[0].keys()),
            delimiter="	",
            lineterminator="
",
        )
        writer.writeheader()
        writer.writerows(fact_rows)

    artifact = {
        "schema": "core-math-arithmetic-live/v1",
        "authority": "research-only",
        "phase": "SENS-DERIVATION/integration",
        "domain": "exact-Q Core-Math through typed research lowering",
        "semantic_parity": True,
        "cases": factor_rows,
        "generated_coordinates": {
            "00": "additive inverse projection",
            "01": "additive quotient projection",
            "10": "multiplicative inverse projection",
            "11": "multiplicative quotient projection",
        },
        "runtime_text_name_dispatch": False,
        "d5_d6_allocations": 0,
        "instruction_counts": perf_rows,
        "semantic_fact_accounting": fact_rows,
        "instruction_ratio_factorized_over_flat": factor_ir / flat_ir,
        "non_conclusions": [
            "lower instruction count does not confer semantic authority",
            "factorized model does not currently reduce the raw charged fact count",
            "the source envelope is a research lowering path, not a new production builtin",
            "no D5/D6 occupancy or Core ratification is inferred",
            "historical Lisp 1.5 RECIP remains a different law from exact-Q reciprocal",
        ],
    }
    (args.out / "result.json").write_text(
        json.dumps(artifact, indent=2, sort_keys=True) + "
",
        encoding="utf-8",
    )

    report = [
        "# Core-Math arithmetic live — #2698",
        "",
        "Semantic parity: **PASS**",
        "",
        "Required exact-Q corpus:",
    ]
    report.extend(f"- {row}" for row in factor_rows)
    report += [
        "",
        "Architecture:",
        "- real SENS reader parses the exact rational source values;",
        "- lowering removes the source operation projection before execution;",
        "- runtime semantic input is QGroupFactor domain + exact binary coordinate;",
        "- factorized execution uses two family roots + generic inverse/quotient role law;",
        "- zero per-result runtime lookup rows;",
        "- D5/D6 allocations: 0.",
        "",
        "Semantic-fact accounting:",
        "- factorized: 7 explicitly charged facts under the #2494 accounting discipline;",
        "- six-independent control: 6 direct operation-law rows;",
        "- therefore **no raw semantic-fact-count win is claimed**;",
        "- the factorized benefit is generativity/reuse and removal of per-result runtime rows.",
        "",
        "Cachegrind I-ref evidence:",
        f"- factorized: {factor_ir}",
        f"- six-table control: {flat_ir}",
        f"- factorized/control ratio: {factor_ir / flat_ir:.6f}",
        "",
        "Performance is evidence only, never semantic authority.",
        "",
    ]
    text = "
".join(report)
    (args.out / "report.md").write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
