#!/usr/bin/env python3
"""#2630 — root-min R3: explicit caller environment vs environment reification.

Research-only bounded witness.

Question:
Can caller-only bindings be reconstructed using ordinary explicit data passed
to a D4-style function, or does transparent access to the *current* caller
environment require a new semantic carrier/channel?

Three modes:
1. ordinary callee with no environment argument;
2. ordinary callee receiving an explicit environment-as-data chain;
3. hidden evaluator reflection that injects the current environment.

No width, coordinate, D5/D6 placement, or resident is inferred.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


class LookupErrorSemantic(RuntimeError):
    pass


def frame(**bindings: Any) -> dict[str, Any]:
    return dict(bindings)


def env_chain(*frames: dict[str, Any]) -> list[dict[str, Any]]:
    # nearest frame first
    return list(frames)


def lookup_explicit_env(env: list[dict[str, Any]], name: str) -> Any:
    for fr in env:
        if name in fr:
            return fr[name]
    raise LookupErrorSemantic(f"UNBOUND:{name}")


def ordinary_callee_no_env(local_frame: dict[str, Any], name: str) -> Any:
    # Deliberately only the callee's own admitted local bindings.
    if name in local_frame:
        return local_frame[name]
    raise LookupErrorSemantic(f"UNBOUND:{name}")


def ordinary_callee_explicit_env(
    local_frame: dict[str, Any],
    explicit_env: list[dict[str, Any]],
    name: str,
) -> Any:
    # Environment is ordinary explicit data; querying it is distinct from
    # ordinary lookup in the callee's own lexical frame.
    _ = local_frame
    return lookup_explicit_env(explicit_env, name)


def hidden_reflection_callee(
    local_frame: dict[str, Any],
    evaluator_current_caller_env: list[dict[str, Any]],
    name: str,
) -> Any:
    # This mode is a control: it succeeds by importing evaluator state.
    # The caller environment remains a distinct object from the callee frame.
    _ = local_frame
    return lookup_explicit_env(evaluator_current_caller_env, name)


def caller_constructs_explicit_env(
    nearest: dict[str, Any],
    outer: dict[str, Any],
) -> list[dict[str, Any]]:
    # Construction uses ordinary explicit data only. This is not generic
    # reflection over hidden evaluator state; the caller provides the bindings.
    return env_chain(nearest, outer)


def run_case(
    case_id: str,
    local_frame: dict[str, Any],
    caller_env: list[dict[str, Any]],
    explicit_env: list[dict[str, Any]],
    name: str,
) -> dict[str, Any]:
    expected = lookup_explicit_env(caller_env, name)

    no_env_error = ""
    no_env_result = None
    try:
        no_env_result = ordinary_callee_no_env(local_frame, name)
    except LookupErrorSemantic as exc:
        no_env_error = str(exc)

    explicit_result = ordinary_callee_explicit_env(
        local_frame,
        explicit_env,
        name,
    )
    reflected_result = hidden_reflection_callee(
        local_frame,
        caller_env,
        name,
    )

    return {
        "case": case_id,
        "name": name,
        "expected_caller_observation": expected,
        "no_env_result": no_env_result,
        "no_env_error": no_env_error,
        "no_env_matches": no_env_result == expected,
        "explicit_env_result": explicit_result,
        "explicit_env_matches": explicit_result == expected,
        "hidden_reflection_result": reflected_result,
        "hidden_reflection_matches": reflected_result == expected,
        "hidden_reflection_imports_channel": True,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    outer = frame(x="OUTER-X", only_outer="OUTER-ONLY")
    nearest = frame(x="NEAREST-X", caller_only="CALLER-ONLY")
    caller_env = env_chain(nearest, outer)
    explicit_env = caller_constructs_explicit_env(nearest, outer)

    local_empty = frame()
    local_shadow = frame(x="CALLEE-X")

    rows = [
        run_case(
            "caller-only-binding",
            local_empty,
            caller_env,
            explicit_env,
            "caller_only",
        ),
        run_case(
            "nearest-caller-shadowing",
            local_empty,
            caller_env,
            explicit_env,
            "x",
        ),
        run_case(
            "outer-fallback",
            local_empty,
            caller_env,
            explicit_env,
            "only_outer",
        ),
        run_case(
            "callee-local-does-not-substitute-caller-env",
            local_shadow,
            caller_env,
            explicit_env,
            "x",
        ),
    ]

    # Caller-only/outer bindings are not visible without an environment input.
    assert rows[0]["no_env_matches"] is False
    assert rows[2]["no_env_matches"] is False

    # Explicit ordinary data reproduces caller lookup semantics for every case.
    assert all(row["explicit_env_matches"] for row in rows)

    # Hidden evaluator reflection also works, but only by importing a channel.
    assert all(row["hidden_reflection_matches"] for row in rows)

    # Nearest caller binding remains observable even when the callee happens
    # to have a local binding with the same spelling: the explicit caller-env
    # is a separate semantic input.
    assert rows[1]["explicit_env_result"] == "NEAREST-X"
    assert rows[3]["explicit_env_result"] == "NEAREST-X"
    assert rows[3]["no_env_result"] == "CALLEE-X"

    classification = "CARRIER-PREMISE"

    tsv_rows = []
    for row in rows:
        tsv_rows.append({
            "case": row["case"],
            "name": row["name"],
            "expected_caller_observation": row["expected_caller_observation"],
            "no_env_matches": row["no_env_matches"],
            "no_env_error": row["no_env_error"],
            "explicit_env_matches": row["explicit_env_matches"],
            "hidden_reflection_matches": row["hidden_reflection_matches"],
            "hidden_reflection_imports_channel": row[
                "hidden_reflection_imports_channel"
            ],
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
        "schema": "post-d4-root-min-r3/v1",
        "authority": "research-only",
        "factor": "explicit-caller-env",
        "bounded_independent": True,
        "derivable_from_basis": False,
        "hidden_capability_needed_for_transparent_current_env": True,
        "basis_dependencies": [
            "ordinary explicit data",
            "association-list/environment chain representation",
            "explicit caller construction/provision of that environment value",
        ],
        "root_status": classification,
        "width": "UNKNOWN",
        "coordinate": "UNPLACED",
        "new_residents": 0,
        "observations": rows,
        "result": {
            "ordinary_callee_without_env_sees_caller_only_binding": False,
            "explicit_environment_data_reconstructs_lookup": True,
            "nearest_binding_order_preserved": True,
            "caller_env_remains_distinct_from_callee_local_frame": True,
            "transparent_current_env_access_requires_reification_channel": True,
            "host_reflection_counts_as_imported_authority": True,
        },
        "interpretation": (
            "Caller-environment behavior is reconstructible once an environment "
            "chain is explicitly represented and supplied as ordinary data. "
            "However, obtaining the current caller environment transparently is "
            "not provided by ordinary call semantics; reflection/evaluator-state "
            "injection is a separate carrier/protocol premise."
        ),
        "falsifier": (
            "Reclassify DERIVED only if ordinary admitted D1-D4 semantics can "
            "construct and supply the current caller environment generically "
            "without host reflection, hidden evaluator state, or explicit extra "
            "input. Reclassify PROVEN-ROOT only if explicit environment-as-data "
            "cannot reproduce the required lookup observations."
        ),
        "non_conclusions": [
            "environment-as-data representation does not allocate a semantic root coordinate",
            "explicitly supplied alist/chain is not transparent current-environment reflection",
            "host reflection/evaluator state is semantic authority when required",
            "no D5/D6 width or placement follows",
        ],
    }

    (args.out / "result.json").write_text(
        json.dumps(artifact, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    report = [
        "# Root minimization R3 — explicit caller environment",
        "",
        "Bounded result: **CARRIER-PREMISE**",
        "",
        "| control | result |",
        "|---|---|",
        "| caller-only binding visible without env input | NO |",
        "| explicit environment-as-data reconstructs lookup | YES |",
        "| nearest caller binding preserved | YES |",
        "| caller-env remains distinct from callee-local frame | YES |",
        "| hidden evaluator reflection reconstructs lookup | YES, but imports a channel |",
        "",
        "Interpretation:",
        "environment lookup is expressible once the environment is explicit ordinary data,",
        "but transparent access to the current caller environment requires a reification/input channel.",
        "That is a carrier premise, not a proved standalone root.",
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
