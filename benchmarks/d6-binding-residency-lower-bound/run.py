#!/usr/bin/env python3
"""#2518 — D6 binding-policy local-width lower-bound witness.

Research-only. This witness composes already-merged evidence:

- #2492: D4 DEFINE -> shared-location target differs in two independently
  observable binding-policy axes; one D5 delta is insufficient.
- #2511: those two refinements commute, are idempotent, and form a clean
  two-bit product square over D4 0011.

The theorem proved here is deliberately scoped:

    under the local parent + independently-observable-delta placement law,
    D6 is the minimum width for this two-axis extension of D4 0011.

It does NOT ratify any D6 resident or bit-axis orientation.
"""

from __future__ import annotations

import contextlib
import io
import runpy
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
ONE_BIT = REPO / "scripts" / "research-2489-setq-placement.py"
PRODUCT = REPO / "scripts" / "research-2506-d6-binding-policy-generator.py"


def capture_main(ns: dict) -> str:
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        ns["main"]()
    return buf.getvalue()


def main() -> None:
    one = runpy.run_path(str(ONE_BIT))
    product = runpy.run_path(str(PRODUCT))

    # Replay the donor gates, including their internal assertions.
    one_out = capture_main(one)
    product_out = capture_main(product)

    assert "DEFINE-TO-SETQ-DELTA-COUNT=2" in one_out
    assert "DEFINE-PARENT-DECISION=NEEDS-WIDER-WIDTH" in one_out
    assert "LOOKUP-COUNTERPARENT=same-resolution-but-different-base-operation" in one_out
    assert "BIND-COUNTERPARENT=different-base-operation" in one_out

    assert "COMMUTATIVE=yes" in product_out
    assert "IDEMPOTENT=yes" in product_out
    assert "D6-001111=shared-location-two-axis-candidate" in product_out
    assert "D6-SELECTOR-COLLISION=none" in product_out
    assert "BIT-AXIS-ORDER=intermediate-symmetric" in product_out

    DEFINE = one["DEFINE"]
    SETQ_CORE = one["SETQ_CORE"]
    Policy = one["Policy"]
    Scope = one["Scope"]
    Miss = one["Miss"]
    signature = one["signature"]
    hamming_policy_distance = one["hamming_policy_distance"]

    # The two one-axis children are both observably distinct from parent and
    # target. Therefore neither single D5 refinement reaches the target.
    nearest_create = Policy(Scope.NEAREST, Miss.CREATE)
    current_fail = Policy(Scope.CURRENT, Miss.FAIL)

    sig_define = signature(DEFINE)
    sig_nearest_create = signature(nearest_create)
    sig_current_fail = signature(current_fail)
    sig_target = signature(SETQ_CORE)

    assert len({sig_define, sig_nearest_create, sig_current_fail, sig_target}) == 4
    assert hamming_policy_distance(DEFINE, SETQ_CORE) == 2
    assert hamming_policy_distance(DEFINE, nearest_create) == 1
    assert hamming_policy_distance(DEFINE, current_fail) == 1
    assert sig_nearest_create != sig_target
    assert sig_current_fail != sig_target

    # Local width lower bound:
    # D4 parent + one independently-observable binary delta => D5.
    # Target requires two such deltas => D6 under the declared placement law.
    parent_bits = "0011"
    one_axis_words = {parent_bits + "0", parent_bits + "1"}
    assert all(len(word) == 5 for word in one_axis_words)

    d6_square = {
        "00": parent_bits + "00",
        "01": parent_bits + "01",
        "10": parent_bits + "10",
        "11": parent_bits + "11",
    }
    assert all(len(word) == 6 for word in d6_square.values())
    assert d6_square["11"] == "001111"

    # Axis-order swap exchanges only the middle children. The both-deltas
    # endpoint is invariant, so the target suffix 11 does not depend on which
    # semantic axis is named first.
    swapped = {
        "00": d6_square["00"],
        "01": d6_square["10"],
        "10": d6_square["01"],
        "11": d6_square["11"],
    }
    assert swapped["11"] == d6_square["11"]
    assert swapped["01"] == d6_square["10"]
    assert swapped["10"] == d6_square["01"]

    # Reuse #2511's selector closure to prove this local family is disjoint
    # from the 16 already-generated D6 selector descendants.
    selector_closure = product["d6_selector_closure"]()
    assert len(selector_closure) == 16
    assert set(d6_square.values()).isdisjoint(selector_closure)

    # Negative control: if one semantic axis is collapsed, the target differs
    # from DEFINE in only one observable dimension and a D5 local extension
    # would suffice. This prevents width-by-aesthetics reasoning.
    collapsed_target = nearest_create
    assert hamming_policy_distance(DEFINE, collapsed_target) == 1
    assert signature(collapsed_target) != sig_define

    print("D6-BINDING-RESIDENCY-LOWER-BOUND=PASS")
    print("DOMAIN=Core-D6")
    print("PARENT-D4=0011")
    print("OBSERVABLE-INDEPENDENT-DELTA-COUNT=2")
    print("D5-LOCAL-ONE-DELTA-SUFFICIENT=no")
    print("D6-LOCAL-TWO-DELTA-SUFFICIENT=yes")
    print("D6-TARGET-CANDIDATE=001111")
    print("D6-TARGET-AXIS-ORDER-INVARIANT=yes")
    print("D6-MIDDLE-AXIS-ORIENTATION-FORCED=no")
    print("D6-SELECTOR-COLLISION=none")
    print("LOOKUP-COUNTERPARENT=rejected-different-base-operation")
    print("BIND-COUNTERPARENT=rejected-different-base-operation")
    print("NEGATIVE-CONTROL-COLLAPSE-ONE-AXIS=D5-sufficient")
    print("THEOREM-SCOPE=local-parent-plus-independent-observable-deltas")
    print("NON-CONCLUSION=no-D6-resident-ratified")
    print("NON-CONCLUSION=no-bit-axis-polarity-ratified")
    print("NON-CONCLUSION=no-production-core-allocation")


if __name__ == "__main__":
    main()
