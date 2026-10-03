#!/usr/bin/env python3
"""#2593 — compose existing protocol witnesses into one factor-independence matrix.

This script does not recreate #2522 or #2568. It imports their live research
witnesses, reuses their probes/source guards, and emits a conservative matrix
for the four protocol factors from #2583:

F3 raw-form-input
F4 explicit-caller-env
F5 returned-form-protocol
F6 expansion-timing

Result class is only "independent-bounded-axis". It is not a root theorem and
has no placement implication.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
CUBE_PATH = ROOT / "scripts" / "research-2522-fexpr-protocol-cube.py"
TIMING_PATH = ROOT / "scripts" / "research-2568-macro-timing.py"
OUT = ROOT / "benchmarks" / "d5-structural-discovery" / "protocol-independence.json"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module



def canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def axis_pairs(cube, axis: str) -> list[dict[str, Any]]:
    protocols = cube.all_protocols()
    pairs: list[dict[str, Any]] = []

    if axis == "raw-form-input":
        for env in (0, 1):
            for result in (0, 1):
                left_bits = f"0{env}{result}"
                right_bits = f"1{env}{result}"
                left = protocols[left_bits]
                right = protocols[right_bits]
                assert left.env == right.env
                assert left.result == right.result
                before = cube.raw_operand_probe(left)
                after = cube.raw_operand_probe(right)
                assert before != after
                assert cube.caller_env_probe(left) == cube.caller_env_probe(right)
                assert cube.result_protocol_probe(left) == cube.result_protocol_probe(right)
                pairs.append({
                    "left": left_bits,
                    "right": right_bits,
                    "held_constant": ["explicit-caller-env", "returned-form-protocol"],
                    "observable_before": list(before),
                    "observable_after": list(after),
                })
        return pairs

    if axis == "explicit-caller-env":
        for raw in (0, 1):
            for result in (0, 1):
                left_bits = f"{raw}0{result}"
                right_bits = f"{raw}1{result}"
                left = protocols[left_bits]
                right = protocols[right_bits]
                assert left.operand == right.operand
                assert left.result == right.result
                before = cube.caller_env_probe(left)
                after = cube.caller_env_probe(right)
                assert before != after
                assert cube.raw_operand_probe(left) == cube.raw_operand_probe(right)
                assert cube.result_protocol_probe(left) == cube.result_protocol_probe(right)
                pairs.append({
                    "left": left_bits,
                    "right": right_bits,
                    "held_constant": ["raw-form-input", "returned-form-protocol"],
                    "observable_before": list(before),
                    "observable_after": list(after),
                })
        return pairs

    if axis == "returned-form-protocol":
        for raw in (0, 1):
            for env in (0, 1):
                left_bits = f"{raw}{env}0"
                right_bits = f"{raw}{env}1"
                left = protocols[left_bits]
                right = protocols[right_bits]
                assert left.operand == right.operand
                assert left.env == right.env
                before = cube.result_protocol_probe(left)
                after = cube.result_protocol_probe(right)
                assert before != after
                assert cube.raw_operand_probe(left) == cube.raw_operand_probe(right)
                assert cube.caller_env_probe(left) == cube.caller_env_probe(right)
                pairs.append({
                    "left": left_bits,
                    "right": right_bits,
                    "held_constant": ["raw-form-input", "explicit-caller-env"],
                    "observable_before": list(before),
                    "observable_after": list(after),
                })
        return pairs

    raise AssertionError(axis)


def build_matrix() -> dict[str, Any]:
    cube = load_module(CUBE_PATH, "sens_research_2522")
    timing = load_module(TIMING_PATH, "sens_research_2568")

    # Reuse the live source guards from the original witnesses.
    cube.source_classify_current_transformer()
    timing.source_controls()

    rows = []

    for factor, probe in (
        ("raw-form-input", "raw_operand_probe"),
        ("explicit-caller-env", "caller_env_probe"),
        ("returned-form-protocol", "result_protocol_probe"),
    ):
        pairs = axis_pairs(cube, factor)
        assert len(pairs) == 4
        rows.append({
            "factor": factor,
            "positive_witness": "#2522/#2530",
            "held_constant_factors": pairs[0]["held_constant"],
            "changed_factor": factor,
            "observable_discriminator": probe,
            "witness_pair_count": len(pairs),
            "witness_pairs": pairs,
            "remove_one_result": "observation-changes-when-factor-changes",
            "alternative_parent_result": "not-tested-by-this-slice",
            "independence_status": "independent-bounded-axis",
            "root_status": "not-proven",
            "placement_implication": "NONE",
        })

    # Timing is independent of the already-aligned A/B/C form protocol.
    hart_protocol = cube.Protocol(
        cube.OperandMode.RAW,
        cube.EnvMode.NONE,
        cube.ResultMode.REEVAL,
    )
    current_protocol = cube.CURRENT_TRANSFORMER
    assert cube.signature(hart_protocol) == cube.signature(current_protocol)

    trace = timing.Trace(macro_at_definition="OLD", macro_at_call="NEW")
    definition_time = timing.hart_define_time(trace)
    evaluation_time = timing.sens_evaluation_time(trace)
    assert definition_time == "OLD"
    assert evaluation_time == "NEW"
    assert definition_time != evaluation_time

    rows.append({
        "factor": "expansion-timing",
        "positive_witness": "#2568/#2569",
        "held_constant_factors": [
            "raw-form-input",
            "explicit-caller-env",
            "returned-form-protocol",
        ],
        "changed_factor": "expansion-timing",
        "observable_discriminator": "macro-redefinition-after-containing-definition",
        "witness_pair_count": 1,
        "witness_pairs": [{
            "left": "definition-time",
            "right": "evaluation-time",
            "held_constant": [
                "raw-form-input=1",
                "explicit-caller-env=0",
                "returned-form-protocol=1",
            ],
            "observable_before": definition_time,
            "observable_after": evaluation_time,
        }],
        "remove_one_result": "observation-changes-when-expansion-locus-changes",
        "alternative_parent_result": "not-tested-by-this-slice",
        "independence_status": "independent-bounded-axis",
        "root_status": "not-proven",
        "placement_implication": "NONE",
    })

    return {
        "schema": "d5-factor-independence-protocol/1",
        "authority": "research-only-no-placement",
        "source_witnesses": [
            {"path": str(CUBE_PATH.relative_to(ROOT)), "issues": ["#2522", "#2530"]},
            {"path": str(TIMING_PATH.relative_to(ROOT)), "issues": ["#2568", "#2569"]},
        ],
        "rows": rows,
        "summary": {
            "protocol_factors_tested": 4,
            "independent_bounded_axes": 4,
            "proven_roots": 0,
            "new_d5_residents": 0,
            "placement_implication": "NONE",
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    matrix = build_matrix()
    text = canonical(matrix)

    if args.write:
        OUT.write_text(text, encoding="utf-8")
    if args.check:
        assert OUT.exists(), "protocol-independence artifact missing"
        assert OUT.read_text(encoding="utf-8") == text, "protocol-independence artifact stale"

    summary = matrix["summary"]
    print("D5-PROTOCOL-INDEPENDENCE=PASS")
    print("protocol-factors-tested=4")
    print("independent-bounded-axes=4")
    print("proven-roots=0")
    print("new-d5-residents=0")
    print("placement-implication=NONE")
    print("RULE=independent-bounded-axis-is-not-root")
    print("RULE=protocol-axis-is-not-domain-bit")


if __name__ == "__main__":
    main()
