#!/usr/bin/env python3
"""#2629 — root-min R2: raw-form input vs explicit quoted data.

Research-only bounded witness.

Question:
Can the observable payload of a raw-form call be reconstructed using admitted
ordinary eager calls when syntax is supplied explicitly as data?

Three modes are compared:
1. ordinary eager, unchanged source;
2. ordinary eager with explicit caller-written QUOTE/data wrappers;
3. hidden automatic quote/rewrite before the call.

The witness separates:
- syntax-as-data expressibility;
- automatic acquisition of caller syntax.

No width, coordinate, D5/D6 placement, or resident is inferred.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


class EvalError(RuntimeError):
    pass


def sym(name: str) -> tuple[str, str]:
    return ("SYM", name)


def lit(value: str) -> tuple[str, str]:
    return ("LIT", value)


def call(head: str, *args: Any) -> tuple:
    return ("CALL", head, *args)


def quote(expr: Any) -> tuple[str, Any]:
    return ("QUOTE", expr)


def canonical(expr: Any) -> str:
    if not isinstance(expr, tuple):
        return repr(expr)
    tag = expr[0]
    if tag == "SYM":
        return expr[1]
    if tag == "LIT":
        return repr(expr[1])
    if tag == "QUOTE":
        return "(quote " + canonical(expr[1]) + ")"
    if tag == "CALL":
        return "(" + " ".join([expr[1], *(canonical(x) for x in expr[2:])]) + ")"
    raise ValueError(tag)


def evaluate(expr: Any, env: dict[str, Any]) -> Any:
    tag = expr[0]
    if tag == "LIT":
        return ("VALUE", expr[1])
    if tag == "SYM":
        name = expr[1]
        if name not in env:
            raise EvalError(f"UNDEFINED:{name}")
        return env[name]
    if tag == "QUOTE":
        # Syntax-as-data carrier is explicit and ordinary.
        return ("SYNTAX", expr[1])
    if tag == "CALL":
        head = expr[1]
        if head == "pair":
            values = [evaluate(x, env) for x in expr[2:]]
            return ("PAIR", *values)
        raise EvalError(f"UNKNOWN-CALL:{head}")
    raise EvalError(f"UNKNOWN-EXPR:{tag}")


def syntax_payload(value: Any) -> Any:
    if not (isinstance(value, tuple) and len(value) == 2 and value[0] == "SYNTAX"):
        raise EvalError("EXPECTED-SYNTAX-DATA")
    return value[1]


def body_observation(raw_args: list[Any]) -> dict[str, Any]:
    """A body that observes raw structure but intentionally ignores evaluation."""
    first = raw_args[0]
    second = raw_args[1]

    second_head = second[1] if second[0] == "CALL" else second[0]
    nested_shape = (
        [canonical(x) for x in second[2:]]
        if second[0] == "CALL"
        else []
    )
    return {
        "first_form": canonical(first),
        "second_tag": second[0],
        "second_head": second_head,
        "second_children": nested_shape,
    }


def raw_call(source_args: list[Any]) -> dict[str, Any]:
    # Special channel: body receives syntax forms before ordinary evaluation.
    return body_observation(source_args)


def eager_call_unchanged(source_args: list[Any], env: dict[str, Any]) -> dict[str, Any]:
    # Ordinary D4-style control: evaluate every operand before body entry.
    values = [evaluate(expr, env) for expr in source_args]
    # The body needs syntax, but ordinary values do not generally carry it.
    raw = [syntax_payload(value) for value in values]
    return body_observation(raw)


def eager_call_explicit_quote(source_args: list[Any], env: dict[str, Any]) -> dict[str, Any]:
    # Caller explicitly supplies source forms as ordinary syntax data.
    quoted = [quote(expr) for expr in source_args]
    values = [evaluate(expr, env) for expr in quoted]
    raw = [syntax_payload(value) for value in values]
    return body_observation(raw)


def hidden_auto_quote_rewrite(source_args: list[Any], env: dict[str, Any]) -> dict[str, Any]:
    # Mechanically identical payload to explicit QUOTE, but the caller did not
    # write it. Therefore this mode imports a pre-body rewrite channel.
    rewritten = [quote(expr) for expr in source_args]
    values = [evaluate(expr, env) for expr in rewritten]
    return body_observation([syntax_payload(value) for value in values])


def run_case(case_id: str, args: list[Any], env: dict[str, Any]) -> dict[str, Any]:
    expected = raw_call(args)

    eager_error = ""
    eager_result = None
    try:
        eager_result = eager_call_unchanged(args, env)
    except EvalError as exc:
        eager_error = str(exc)

    explicit = eager_call_explicit_quote(args, env)
    hidden = hidden_auto_quote_rewrite(args, env)

    return {
        "case": case_id,
        "source": " ".join(canonical(x) for x in args),
        "raw_observation": expected,
        "unchanged_eager_result": eager_result,
        "unchanged_eager_error": eager_error,
        "unchanged_eager_matches_raw": eager_result == expected,
        "explicit_quote_matches_raw": explicit == expected,
        "hidden_rewrite_matches_raw": hidden == expected,
        "hidden_rewrite_imports_channel": True,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    env = {
        "defined": ("VALUE", "DEFINED"),
    }

    cases = [
        (
            "unused-undefined",
            [
                lit("ok"),
                sym("never_defined"),
            ],
        ),
        (
            "inspect-raw-structure",
            [
                lit("ok"),
                call("pair", sym("never_defined"), lit("tail")),
            ],
        ),
        (
            "nested-raw-shape",
            [
                call("pair", lit("a"), lit("b")),
                call("outer", call("inner", sym("never_defined")), lit("z")),
            ],
        ),
    ]

    rows = [run_case(case_id, exprs, env) for case_id, exprs in cases]

    # Mandatory controls:
    # raw path preserves all syntax without triggering undefined evaluation;
    # explicit caller-written QUOTE reconstructs all body-level observations;
    # unchanged eager calling convention cannot.
    assert all(row["explicit_quote_matches_raw"] for row in rows)
    assert all(row["hidden_rewrite_matches_raw"] for row in rows)
    assert not any(row["unchanged_eager_matches_raw"] for row in rows)
    assert rows[0]["unchanged_eager_error"].startswith("UNDEFINED:")
    assert rows[1]["unchanged_eager_error"].startswith("UNDEFINED:")
    assert rows[2]["unchanged_eager_error"].startswith("UNKNOWN-CALL:")

    # The bounded classification deliberately distinguishes payload
    # expressibility from automatic raw acquisition.
    classification = "CARRIER-PREMISE"

    tsv_rows = []
    for row in rows:
        tsv_rows.append({
            "case": row["case"],
            "source": row["source"],
            "unchanged_eager_matches_raw": row["unchanged_eager_matches_raw"],
            "unchanged_eager_error": row["unchanged_eager_error"],
            "explicit_quote_matches_raw": row["explicit_quote_matches_raw"],
            "hidden_rewrite_matches_raw": row["hidden_rewrite_matches_raw"],
            "hidden_rewrite_imports_channel": row["hidden_rewrite_imports_channel"],
        })

    with (args.out / "results.tsv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=list(tsv_rows[0].keys()),
            delimiter="\t",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(tsv_rows)

    artifact = {
        "schema": "post-d4-root-min-r2/v1",
        "authority": "research-only",
        "factor": "raw-form-input",
        "bounded_independent": True,
        "derivable_from_basis": False,
        "hidden_capability_needed_for_same_source": True,
        "basis_dependencies": [
            "ordinary eager call",
            "QUOTE / syntax-as-data",
            "explicit caller construction of source-form data",
        ],
        "root_status": classification,
        "width": "UNKNOWN",
        "coordinate": "UNPLACED",
        "new_residents": 0,
        "observations": rows,
        "result": {
            "same_source_ordinary_eager_reconstructs_raw": False,
            "explicit_syntax_data_reconstructs_body_observation": True,
            "automatic_raw_acquisition_requires_extra_channel": True,
            "reader_or_compiler_auto_quote_counts_as_imported_channel": True,
        },
        "interpretation": (
            "Raw syntax is not an irreducible new value capability once syntax is "
            "explicitly supplied as admitted data, but ordinary eager call semantics "
            "do not automatically acquire caller syntax. The missing ingredient is "
            "therefore an input-carrier/protocol premise, not a proved standalone root."
        ),
        "falsifier": (
            "Reclassify DERIVED only if unchanged ordinary D1-D4 call semantics can "
            "preserve the same-source raw observations without explicit caller syntax "
            "data or hidden pre-body rewrite. Reclassify PROVEN-ROOT only if syntax-as-"
            "data reconstruction itself is shown impossible from admitted data semantics."
        ),
        "non_conclusions": [
            "CARRIER-PREMISE does not allocate a function or domain coordinate",
            "explicit caller QUOTE is not equivalent to transparent same-source raw calling",
            "hidden reader/compiler auto-quoting is a semantic channel, not free mechanism",
            "no D5/D6 width follows from this result",
        ],
    }

    (args.out / "result.json").write_text(
        json.dumps(artifact, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    report = [
        "# Root minimization R2 — raw-form input",
        "",
        "Bounded result: **CARRIER-PREMISE**",
        "",
        "| control | result |",
        "|---|---|",
        "| raw call keeps unused undefined operand inert | PASS |",
        "| ordinary eager unchanged source reproduces raw observation | NO |",
        "| explicit caller-written syntax/QUOTE data reproduces raw observation | YES |",
        "| hidden automatic quote/rewrite reproduces payload | YES, but imports a channel |",
        "",
        "Interpretation:",
        "raw-form body observations are reproducible once syntax is an explicit data carrier,",
        "but ordinary eager calls cannot transparently acquire that syntax from the same source call.",
        "Therefore this bounded attack does not earn a standalone semantic root;",
        "it exposes a carrier/protocol premise.",
        "",
        "width=UNKNOWN; coordinate=UNPLACED; new residents=0.",
        "",
    ]
    text = "\n".join(report)
    (args.out / "report.md").write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
