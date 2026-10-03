#!/usr/bin/env python3
"""#2632 — root-min R5: expansion timing as phase policy vs semantic root.

Research-only bounded witness.

We compare two semantics using the same transformer law:
1. definition-time expansion stores the expanded form in the definition payload;
2. evaluation-time expansion stores the source form and transforms it on invoke.

The OLD/NEW trace is observable, but the question is whether timing itself
requires a new semantic root or is a scheduling policy over already-admitted
transformation + ordinary stored definition data.

No width, coordinate, D5/D6 placement, or resident is inferred.
"""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable


@dataclass(frozen=True)
class Transformer:
    version: str

    def expand(self, source_form: str, call_env: dict[str, Any] | None = None) -> str:
        # Same transform capability in both policies.
        if source_form == "EMIT-VERSION":
            return self.version
        if source_form == "EMIT-RUNTIME-X":
            if call_env is None or "x" not in call_env:
                return "NO-RUNTIME-X"
            return f"X={call_env['x']}"
        return f"{self.version}:{source_form}"


@dataclass(frozen=True)
class DefinitionTimeArtifact:
    expanded_form: str


@dataclass(frozen=True)
class EvaluationTimeArtifact:
    source_form: str


def define_definition_time(
    transformer: Transformer,
    source_form: str,
) -> DefinitionTimeArtifact:
    # Expansion happens now; the result is stored explicitly as definition data.
    return DefinitionTimeArtifact(transformer.expand(source_form, call_env=None))


def define_evaluation_time(source_form: str) -> EvaluationTimeArtifact:
    # Source syntax is stored explicitly; expansion is deferred.
    return EvaluationTimeArtifact(source_form)


def invoke_definition_time(
    artifact: DefinitionTimeArtifact,
    current_transformer: Transformer,
    call_env: dict[str, Any],
) -> str:
    # Current transformer is intentionally irrelevant: expansion already happened.
    _ = current_transformer
    _ = call_env
    return artifact.expanded_form


def invoke_evaluation_time(
    artifact: EvaluationTimeArtifact,
    current_transformer: Transformer,
    call_env: dict[str, Any],
) -> str:
    return current_transformer.expand(artifact.source_form, call_env=call_env)


def hidden_cache_model(
    source_form: str,
    hidden_cache: dict[str, str],
    current_transformer: Transformer,
) -> str:
    # Control only: reproducing OLD via hidden cache is imported state.
    if source_form in hidden_cache:
        return hidden_cache[source_form]
    value = current_transformer.expand(source_form, call_env=None)
    hidden_cache[source_form] = value
    return value


def old_new_trace() -> dict[str, Any]:
    old = Transformer("OLD")
    new = Transformer("NEW")
    source = "EMIT-VERSION"

    def_artifact = define_definition_time(old, source)
    eval_artifact = define_evaluation_time(source)

    definition_time_result = invoke_definition_time(
        def_artifact,
        new,
        call_env={},
    )
    evaluation_time_result = invoke_evaluation_time(
        eval_artifact,
        new,
        call_env={},
    )

    assert definition_time_result == "OLD"
    assert evaluation_time_result == "NEW"

    return {
        "source": source,
        "definition_time_stored": def_artifact.expanded_form,
        "evaluation_time_stored": eval_artifact.source_form,
        "definition_time_result_after_redefine": definition_time_result,
        "evaluation_time_result_after_redefine": evaluation_time_result,
        "observable_difference": definition_time_result != evaluation_time_result,
    }


def runtime_binding_trace() -> dict[str, Any]:
    old = Transformer("OLD")
    new = Transformer("NEW")
    source = "EMIT-RUNTIME-X"

    def_artifact = define_definition_time(old, source)
    eval_artifact = define_evaluation_time(source)

    call_env = {"x": 42}
    definition_time_result = invoke_definition_time(
        def_artifact,
        new,
        call_env=call_env,
    )
    evaluation_time_result = invoke_evaluation_time(
        eval_artifact,
        new,
        call_env=call_env,
    )

    assert definition_time_result == "NO-RUNTIME-X"
    assert evaluation_time_result == "X=42"

    return {
        "source": source,
        "definition_time_result": definition_time_result,
        "evaluation_time_result": evaluation_time_result,
        "runtime_binding_visible_only_when_expansion_deferred": True,
    }


def scheduling_reconstruction() -> dict[str, Any]:
    old = Transformer("OLD")
    new = Transformer("NEW")
    source = "EMIT-VERSION"

    # One transform law; only explicit scheduling differs.
    policies: dict[str, Callable[[], str]] = {
        "definition-time": lambda: invoke_definition_time(
            define_definition_time(old, source),
            new,
            {},
        ),
        "evaluation-time": lambda: invoke_evaluation_time(
            define_evaluation_time(source),
            new,
            {},
        ),
    }
    outputs = {name: thunk() for name, thunk in policies.items()}

    assert outputs == {
        "definition-time": "OLD",
        "evaluation-time": "NEW",
    }

    return {
        "same_transformer_interface": True,
        "policy_outputs": outputs,
        "definition_payloads_are_explicit_data": True,
        "hidden_phase_tag_required": False,
        "hidden_version_table_required": False,
    }


def hidden_state_attack() -> dict[str, Any]:
    old = Transformer("OLD")
    new = Transformer("NEW")
    source = "EMIT-VERSION"

    # Warm hidden cache under OLD.
    hidden_cache: dict[str, str] = {}
    first = hidden_cache_model(source, hidden_cache, old)
    after_redefine = hidden_cache_model(source, hidden_cache, new)
    assert first == after_redefine == "OLD"

    # Clearing hidden cache flips the result to NEW. Therefore cache content is
    # observable authority if it is not represented as explicit definition data.
    hidden_cache.clear()
    after_clear = hidden_cache_model(source, hidden_cache, new)
    assert after_clear == "NEW"

    return {
        "hidden_cache_can_mimic_definition_time": True,
        "cache_clear_changes_observation": True,
        "classification": "IMPORTED-HIDDEN-STATE",
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    trace = old_new_trace()
    runtime = runtime_binding_trace()
    reconstruction = scheduling_reconstruction()
    hidden = hidden_state_attack()

    classification = "POLICY-OVER-ROOT"

    rows = [
        {
            "model": "definition-time",
            "stored_payload": trace["definition_time_stored"],
            "after_redefine_result": trace["definition_time_result_after_redefine"],
            "runtime_x_result": runtime["definition_time_result"],
            "hidden_state": False,
        },
        {
            "model": "evaluation-time",
            "stored_payload": trace["evaluation_time_stored"],
            "after_redefine_result": trace["evaluation_time_result_after_redefine"],
            "runtime_x_result": runtime["evaluation_time_result"],
            "hidden_state": False,
        },
        {
            "model": "hidden-cache-control",
            "stored_payload": "host-cache",
            "after_redefine_result": "OLD",
            "runtime_x_result": "n/a",
            "hidden_state": True,
        },
    ]

    with (args.out / "results.tsv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=list(rows[0].keys()),
            delimiter="\t",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)

    artifact = {
        "schema": "post-d4-root-min-r5/v1",
        "authority": "research-only",
        "factor": "expansion-timing",
        "bounded_independent": True,
        "derivable_from_basis": True,
        "hidden_capability_needed": False,
        "basis_dependencies": [
            "one admitted transformation capability",
            "ordinary explicit definition payload storage",
            "explicit scheduling policy",
        ],
        "root_status": classification,
        "width": "UNKNOWN",
        "coordinate": "UNPLACED",
        "new_residents": 0,
        "old_new_trace": trace,
        "runtime_binding_trace": runtime,
        "scheduling_reconstruction": reconstruction,
        "hidden_state_attack": hidden,
        "result": {
            "timing_is_observable": True,
            "same_transform_law_used_by_both_models": True,
            "difference_reconstructed_by_explicit_schedule_and_payload": True,
            "hidden_cache_or_version_state_not_required": True,
            "hidden_cache_if_used_is_semantic_authority": True,
        },
        "interpretation": (
            "Expansion timing changes observable behavior, but the bounded model "
            "reconstructs both timing choices using the same transformer law plus "
            "ordinary explicit stored definition payloads and a scheduling policy. "
            "Therefore timing is a policy over an admitted transformation capability, "
            "not a separately proved semantic root."
        ),
        "falsifier": (
            "Reclassify away from POLICY-OVER-ROOT if definition-time vs evaluation-"
            "time observations cannot be reconstructed with one transformation law "
            "and explicit ordinary stored payloads, or if an additional hidden "
            "phase/version channel is provably required."
        ),
        "non_conclusions": [
            "POLICY-OVER-ROOT does not erase the observable OLD/NEW timing axis",
            "this result does not decide macro/transformer placement",
            "hidden compiler/cache state cannot substitute for explicit definition payload",
            "no D5/D6 width or coordinate follows",
        ],
    }

    (args.out / "result.json").write_text(
        json.dumps(artifact, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    report = [
        "# Root minimization R5 — expansion timing",
        "",
        "Bounded result: **POLICY-OVER-ROOT**",
        "",
        "| control | result |",
        "|---|---|",
        "| OLD/NEW timing trace remains observable | PASS |",
        "| runtime-only binding distinguishes deferred expansion | PASS |",
        "| same transformation law used by both timing models | YES |",
        "| explicit scheduling + stored payload reconstructs both | YES |",
        "| hidden phase/version state required | NO |",
        "| hidden cache can mimic OLD | YES, but cache-clear changes observation |",
        "",
        "Interpretation:",
        "timing is a real protocol axis, but in this bounded model it is scheduling policy",
        "over the same transformation capability with explicit definition payload state.",
        "The factor therefore does not earn a standalone semantic root.",
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
