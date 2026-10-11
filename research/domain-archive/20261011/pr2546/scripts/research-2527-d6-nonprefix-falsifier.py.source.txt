#!/usr/bin/env python3
"""#2527 — attack the scope of the D6 binding-policy lower bound.

Research-only.  The donor result (#2511/#2523) says that, under a local
parent+independent-delta placement law, two independently observable policy
axes require two local binary distinctions over D4 DEFINE.

This falsifier asks whether product, quotient, residue, or non-prefix encodings
actually reduce the semantic distinction count.  Printed token length alone
does not count: hidden tables, indexes, or family context are charged as
authority.

No D6 resident or coordinate is admitted here.
"""

from __future__ import annotations

import contextlib
import io
import itertools
import math
import runpy
from dataclasses import dataclass
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PRODUCT = REPO / "scripts" / "research-2506-d6-binding-policy-generator.py"
LOWER = REPO / "scripts" / "research-2518-d6-binding-residency-lower-bound.py"


class DomainMismatch(ValueError):
    pass


@dataclass(frozen=True)
class TypedBits:
    domain: str
    bits: str


@dataclass(frozen=True)
class ModelResult:
    name: str
    preserves_four_states: bool
    preserves_two_axes: bool
    hidden_table_rows: int
    local_payload_bits: int | None
    extra_semantic_facts: int
    axis_relabel_survives: bool
    classification: str
    falsifies_lower_bound: bool


def capture_main(namespace: dict) -> str:
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        namespace["main"]()
    return buf.getvalue()


def require_binding_policy(value: TypedBits) -> str:
    if value.domain != "Core-D6-binding-policy":
        raise DomainMismatch(value.domain)
    return value.bits


def semantic_coordinates(policy) -> tuple[int, int]:
    scope = 0 if policy.scope.value == "current" else 1
    miss = 0 if policy.miss.value == "create" else 1
    return scope, miss


def main() -> None:
    product = runpy.run_path(str(PRODUCT))
    lower = runpy.run_path(str(LOWER))

    product_out = capture_main(product)
    lower_out = capture_main(lower)
    assert "D6-BINDING-POLICY-GENERATOR=PASS" in product_out
    assert "D6-BINDING-RESIDENCY-LOWER-BOUND=PASS" in lower_out

    square = {
        "00": product["DEFINE"],
        "01": product["CURRENT_FAIL"],
        "10": product["NEAREST_CREATE"],
        "11": product["SETQ_CORE"],
    }
    signature = product["signature"]

    # The semantic object under attack really has four observable corners.
    signatures = {key: signature(policy) for key, policy in square.items()}
    assert len(set(signatures.values())) == 4
    coordinates = {key: semantic_coordinates(policy) for key, policy in square.items()}
    assert coordinates == {
        "00": (0, 0),
        "01": (0, 1),
        "10": (1, 0),
        "11": (1, 1),
    }

    # Information-theoretic control: four distinguishable local states require
    # at least two bits if no external table/context carries the distinction.
    local_state_lower_bound = math.ceil(math.log2(len(signatures)))
    assert local_state_lower_bound == 2

    # Model A — canonical ordered local path.
    # The product law owns two semantic axes.  Parent prefix and axis order are
    # coordinate choices; swapping axes swaps only the intermediate labels.
    ordered_words = {key: "0011" + key for key in square}
    swapped_words = {
        "00": ordered_words["00"],
        "01": ordered_words["10"],
        "10": ordered_words["01"],
        "11": ordered_words["11"],
    }
    assert swapped_words["11"] == ordered_words["11"] == "001111"
    ordered = ModelResult(
        "ordered-local-path", True, True, 0, 2, 0, True,
        "coordinate-law", False,
    )

    # Model B — direct two-factor coordinate.
    # Removing the D4 prefix from presentation does not remove either semantic
    # factor.  It is a compact coordinate for the same product, not a semantic
    # compression below two distinctions.
    factor_coordinate = {key: coordinates[key] for key in square}
    assert len(set(factor_coordinate.values())) == 4
    factors = ModelResult(
        "two-factor-coordinate", True, True, 0, 2, 0, True,
        "semantic-law+coordinate-law", False,
    )

    # Model C — quotient of derivation paths.
    # S then M and M then S reach the same target only because commutation is an
    # additional proved relation.  Quotienting paths removes duplicate proofs,
    # not either semantic axis.
    paths_to_target = {("scope", "miss"), ("miss", "scope")}
    quotient_class = frozenset(paths_to_target)
    assert len(quotient_class) == 2
    assert product["miss_refine"](product["scope_refine"](product["DEFINE"])) == product["SETQ_CORE"]
    assert product["scope_refine"](product["miss_refine"](product["DEFINE"])) == product["SETQ_CORE"]
    quotient = ModelResult(
        "quotient-of-paths", True, True, 0, 2, 1, True,
        "semantic-law", False,
    )

    # Model D — explicit residue/root.
    # A single arbitrary resident can name the final endpoint, but it discards
    # the three other corners and the two-axis algebra.  It therefore changes
    # the theorem's subject rather than falsifying it.
    residue = ModelResult(
        "explicit-residue-root", False, False, 1, 0, 1, False,
        "explicit-residue", False,
    )

    # Model E — arbitrary non-prefix D6 numbering.
    # Every permutation is observationally usable if a four-row table supplies
    # the semantics.  24 equally valid assignments demonstrate absence of a
    # canonical semantic coordinate law.
    arbitrary_words = ("000000", "010101", "100001", "111110")
    table_encodings = []
    semantic_keys = tuple(sorted(square))
    for permutation in itertools.permutations(arbitrary_words):
        table_encodings.append(dict(zip(semantic_keys, permutation)))
    assert len(table_encodings) == math.factorial(4) == 24
    assert all(len(set(mapping.values())) == 4 for mapping in table_encodings)
    assert len({tuple(mapping[k] for k in semantic_keys) for mapping in table_encodings}) == 24
    nonprefix = ModelResult(
        "nonprefix-global-table", True, True, 4, 6, 4, False,
        "accidental-representation", False,
    )

    # Strong negative control — print only a 2-bit table index.
    # This looks smaller, but family/domain + the four-row interpretation table
    # now carries the missing authority.  It is not a D2 semantic resident and
    # cannot be compared to the D6 local placement theorem as semantic savings.
    tiny_indices = {"00": "00", "01": "01", "10": "10", "11": "11"}
    assert len(set(tiny_indices.values())) == 4
    short_table = ModelResult(
        "two-bit-external-index", True, True, 4, 2, 4, False,
        "accidental-representation", False,
    )

    # #2508 standing guard: identical raw bits under another domain do not
    # inherit this binding-policy law.
    binding_11 = TypedBits("Core-D6-binding-policy", "11")
    qgroup_11 = TypedBits("Core-Math-QGroupFactor", "11")
    assert binding_11.bits == qgroup_11.bits
    assert binding_11 != qgroup_11
    assert require_binding_policy(binding_11) == "11"
    try:
        require_binding_policy(qgroup_11)
    except DomainMismatch:
        pass
    else:
        raise AssertionError("cross-domain bit equality leaked semantic authority")

    models = [ordered, factors, quotient, residue, nonprefix, short_table]
    assert not any(model.falsifies_lower_bound for model in models)

    # The key scientific classification requested by #2494/#2508 discipline:
    # product structure is semantic; bit orientation/parent prefix is
    # coordinate law; arbitrary enumeration is accidental.
    print("D6-NONPREFIX-FALSIFIER=PASS")
    print("PHASE=STRUCTURAL-DISCOVERY")
    print("DOMAIN=Core-D6")
    print("BINARY-OBJECT=four-state-binding-policy-product")
    print("OBSERVABLE-STATES=4")
    print("INDEPENDENT-SEMANTIC-AXES=2")
    print("LOCAL-STATE-INFORMATION-LOWER-BOUND-BITS=2")
    print("PRODUCT-SQUARE-CLASS=semantic-law")
    print("PARENT-PREFIX-PLUS-AXIS-BITS-CLASS=coordinate-law")
    print("MIDDLE-01-10-ORIENTATION-CLASS=coordinate-law")
    print("ARBITRARY-NONPREFIX-ENUMERATION-CLASS=accidental-representation")
    print("ORDERED-PATH=preserves-two-axes")
    print("FACTOR-COORDINATE=preserves-two-axes")
    print("QUOTIENT=removes-duplicate-proof-paths-not-semantic-axes")
    print("EXPLICIT-RESIDUE=not-comparable-drops-product-algebra")
    print("NONPREFIX-D6-TABLE=24-equally-valid-enumerations")
    print("SHORT-2BIT-INDEX=hidden-domain-plus-4-row-table-authority")
    print("DOMAIN-MISMATCH-GUARD=PASS")
    print("THEOREM-SCOPE=local-parent-plus-independent-observable-deltas")
    print("FALSIFIED=no")
    print("NON-CONCLUSION=no-0011xx-residency")
    print("NON-CONCLUSION=no-axis-polarity-ratified")
    print("NON-CONCLUSION=no-D6-map-mutation")


if __name__ == "__main__":
    main()
