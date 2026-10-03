#!/usr/bin/env python3
"""#2527 — non-prefix/product/quotient attack on the local D6 lower bound.

Consumes the merged #2511 donor model instead of redefining binding-policy
semantics. No Core residency and no D6 map mutation.

Question:
Does the semantic product square force the *D4-prefix -> D6* representation,
or only two independent semantic distinctions?

Classification vocabulary:
- SEMANTIC-LAW
- CANONICAL-FACTOR-COORDINATE-LAW
- ACCIDENTAL
"""

from __future__ import annotations

import importlib.util
from dataclasses import dataclass
from itertools import permutations, product
from pathlib import Path
from typing import Callable

ROOT = Path(__file__).resolve().parents[2]
DONOR = ROOT / "scripts" / "research-2506-d6-binding-policy-generator.py"


def load_donor():
    spec = importlib.util.spec_from_file_location("d6_donor_2506", DONOR)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


D = load_donor()

POLICIES = (
    D.DEFINE,
    D.CURRENT_FAIL,
    D.NEAREST_CREATE,
    D.SETQ_CORE,
)
BY_PAIR = {
    (0, 0): D.DEFINE,
    (0, 1): D.CURRENT_FAIL,
    (1, 0): D.NEAREST_CREATE,
    (1, 1): D.SETQ_CORE,
}
PAIR_OF = {policy: pair for pair, policy in BY_PAIR.items()}


def semantically_distinct() -> None:
    signatures = [D.signature(policy) for policy in POLICIES]
    assert len(set(signatures)) == 4


def action_s(policy):
    return D.scope_refine(policy)


def action_m(policy):
    return D.miss_refine(policy)


ACTIONS: dict[str, Callable] = {
    "S": action_s,
    "M": action_m,
}


def replay_path(path: str):
    state = D.DEFINE
    for symbol in path:
        state = ACTIONS[symbol](state)
    return state


def canonicalize_path(path: str) -> tuple[int, int]:
    """Quotient words by S^2=S, M^2=M, SM=MS."""
    state = replay_path(path)
    return PAIR_OF[state]


def all_words(max_len: int = 5) -> tuple[str, ...]:
    out = [""]
    for length in range(1, max_len + 1):
        for symbols in product("SM", repeat=length):
            out.append("".join(symbols))
    return tuple(out)


@dataclass(frozen=True)
class ModelReport:
    name: str
    semantic_axes: int
    semantic_states: int
    printed_payload_bits: int | None
    external_domain_or_parent_required: bool
    mapping_table_rows: int
    replay_rule_facts: int
    axis_relabel_survives: bool
    classification: str
    conclusion: str


def canonical_prefix_model() -> ModelReport:
    words = {
        (0, 0): "001100",
        (0, 1): "001101",
        (1, 0): "001110",
        (1, 1): "001111",
    }
    assert len(set(words.values())) == 4
    assert all(len(word) == 6 for word in words.values())

    swap = lambda pair: (pair[1], pair[0])
    assert words[(0, 0)] == words[swap((0, 0))]
    assert words[(1, 1)] == words[swap((1, 1))]
    assert words[(0, 1)] != words[swap((0, 1))]

    return ModelReport(
        name="canonical-parent-prefix",
        semantic_axes=2,
        semantic_states=4,
        printed_payload_bits=6,
        external_domain_or_parent_required=False,
        mapping_table_rows=0,
        replay_rule_facts=2,
        axis_relabel_survives=True,
        classification="CANONICAL-FACTOR-COORDINATE-LAW",
        conclusion="sufficient-local-D6-coordinate-not-globally-forced",
    )


def factor_coordinate_model() -> ModelReport:
    for pair, policy in BY_PAIR.items():
        assert PAIR_OF[policy] == pair

    def set_s(pair): return (1, pair[1])
    def set_m(pair): return (pair[0], 1)

    for pair in BY_PAIR:
        assert set_s(set_m(pair)) == set_m(set_s(pair))
        assert set_s(set_s(pair)) == set_s(pair)
        assert set_m(set_m(pair)) == set_m(pair)

    return ModelReport(
        name="typed-factor-coordinate",
        semantic_axes=2,
        semantic_states=4,
        printed_payload_bits=2,
        external_domain_or_parent_required=True,
        mapping_table_rows=0,
        replay_rule_facts=2,
        axis_relabel_survives=True,
        classification="SEMANTIC-LAW",
        conclusion="falsifies-global-six-bit-necessity-not-two-axis-lower-bound",
    )


def quotient_model() -> ModelReport:
    words = all_words(5)
    classes: dict[tuple[int, int], list[str]] = {pair: [] for pair in BY_PAIR}
    for word in words:
        classes[canonicalize_path(word)].append(word)

    assert canonicalize_path("SM") == canonicalize_path("MS") == (1, 1)
    assert canonicalize_path("SSM") == (1, 1)
    assert canonicalize_path("MMM") == (0, 1)
    assert all(classes[pair] for pair in classes)

    return ModelReport(
        name="derivation-path-quotient",
        semantic_axes=2,
        semantic_states=4,
        printed_payload_bits=None,
        external_domain_or_parent_required=True,
        mapping_table_rows=0,
        replay_rule_facts=3,
        axis_relabel_survives=True,
        classification="SEMANTIC-LAW",
        conclusion="same-product-structure-without-fixed-prefix-width",
    )


def residue_model() -> ModelReport:
    labels = ("r0", "r1", "r2", "r3")
    table = dict(zip(labels, POLICIES, strict=True))
    assert len({D.signature(p) for p in table.values()}) == 4

    return ModelReport(
        name="explicit-residue-root-table",
        semantic_axes=2,
        semantic_states=4,
        printed_payload_bits=None,
        external_domain_or_parent_required=True,
        mapping_table_rows=4,
        replay_rule_facts=0,
        axis_relabel_survives=False,
        classification="ACCIDENTAL",
        conclusion="represents-states-but-does-not-compress-semantic-law",
    )


def global_numbering_model() -> ModelReport:
    labels = ("00", "01", "10", "11")
    base = dict(zip(labels, POLICIES, strict=True))

    raw_law_survivors = 0
    for perm in permutations(labels):
        relabel = dict(zip(labels, perm, strict=True))

        def raw_pair(label: str) -> tuple[int, int]:
            return (int(label[0]), int(label[1]))

        ok = True
        for label, policy in base.items():
            new_label = relabel[label]
            if raw_pair(new_label) != PAIR_OF[policy]:
                ok = False
                break
        if ok:
            raw_law_survivors += 1

    assert raw_law_survivors == 1

    return ModelReport(
        name="arbitrary-global-two-bit-index",
        semantic_axes=2,
        semantic_states=4,
        printed_payload_bits=2,
        external_domain_or_parent_required=True,
        mapping_table_rows=4,
        replay_rule_facts=0,
        axis_relabel_survives=False,
        classification="ACCIDENTAL",
        conclusion="short-printing-imports-four-row-table-authority",
    )


def semantic_lower_bound() -> None:
    parent = D.signature(D.DEFINE)
    only_s = D.signature(D.NEAREST_CREATE)
    only_m = D.signature(D.CURRENT_FAIL)
    both = D.signature(D.SETQ_CORE)

    assert parent != only_s
    assert parent != only_m
    assert only_s != both
    assert only_m != both
    assert only_s != only_m

    # Any one-axis collapse identifies donor states with distinct signatures.
    assert D.signature(D.DEFINE) != D.signature(D.NEAREST_CREATE)
    assert D.signature(D.DEFINE) != D.signature(D.CURRENT_FAIL)


def main() -> None:
    semantically_distinct()
    semantic_lower_bound()

    reports = (
        canonical_prefix_model(),
        factor_coordinate_model(),
        quotient_model(),
        residue_model(),
        global_numbering_model(),
    )

    assert all(report.semantic_axes == 2 for report in reports)
    assert all(report.semantic_states == 4 for report in reports)

    print("D6-NONPREFIX-FALSIFIER=PASS")
    print("DONOR=#2511-merged-model")
    print("SEMANTIC-DISTINCTION-COUNT=2-independent-axes")
    print("SEMANTIC-STATES=4")
    print("COLLAPSE-EITHER-AXIS=REJECT")
    print("GLOBAL-SIX-BIT-NECESSITY=FALSIFIED")
    print("LOCAL-D4-PARENT-PLUS-DELTA-D6=NOT-FALSIFIED")
    print("D6-RESIDENCY=NONE")

    for report in reports:
        bits = (
            "variable-or-table"
            if report.printed_payload_bits is None
            else str(report.printed_payload_bits)
        )
        print(
            "MODEL "
            f"name={report.name} "
            f"class={report.classification} "
            f"payload_bits={bits} "
            f"external_context={int(report.external_domain_or_parent_required)} "
            f"table_rows={report.mapping_table_rows} "
            f"replay_rule_facts={report.replay_rule_facts} "
            f"axis_relabel_survives={int(report.axis_relabel_survives)} "
            f"conclusion={report.conclusion}"
        )

    print("SEMANTIC-LAW=two-independent-commuting-idempotent-axes")
    print("COORDINATE-LAW=orientation-and-local-prefix-choice-not-semantic")
    print("ACCIDENTAL=arbitrary-global-index-with-table-authority")
    print("PRINCIPLE=representation-can-change-without-reducing-semantic-distinctions")
    print("AUTHORITY=RESEARCH-ONLY")


if __name__ == "__main__":
    main()
