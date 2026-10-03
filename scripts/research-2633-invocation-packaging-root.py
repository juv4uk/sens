#!/usr/bin/env python3
"""#2633 — minimize invocation packaging against explicit call data."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Call:
    head: str
    operands: tuple[str, ...]


def operands_only(call: Call):
    return call.operands


def explicit_call_data(head: str, operands: tuple[str, ...]):
    return (head, *operands)


def main() -> None:
    a = Call("macro-a", ("payload",))
    b = Call("macro-b", ("payload",))

    # Mandatory #2580/#2588 collision control.
    assert a.head != b.head
    assert a.operands == b.operands
    assert operands_only(a) == operands_only(b)

    # Once head is explicitly supplied as ordinary data, construction is trivial.
    whole_a = explicit_call_data(a.head, a.operands)
    whole_b = explicit_call_data(b.head, b.operands)
    assert whole_a != whole_b
    assert whole_a == ("macro-a", "payload")
    assert whole_b == ("macro-b", "payload")

    # But no function of the operands-only payload can reconstruct two different heads.
    payload = operands_only(a)
    assert payload == operands_only(b)
    possible_heads = {a.head, b.head}
    assert len(possible_heads) == 2

    # Therefore whole-call construction is derived *given* a head carrier, while
    # automatic head acquisition is not derived from the operands-only channel.
    root_status = "CARRIER-PREMISE"

    print("ROOT-MIN-R6=PASS")
    print("FACTOR=invocation-packaging")
    print("OPERANDS-ONLY-COLLISION=PROVEN")
    print("EXPLICIT-CALL-DATA-CONSTRUCTION=DERIVED-GIVEN-HEAD")
    print("HEAD-ACQUISITION-FROM-OPERANDS=IMPOSSIBLE-UNDER-COLLISION")
    print(f"ROOT-STATUS={root_status}")
    print("HIDDEN-DISPATCH-METADATA=REJECTED-AS-DERIVATION")
    print("WIDTH=UNKNOWN")
    print("COORDINATE=UNPLACED")
    print("NEW-RESIDENTS=0")


if __name__ == "__main__":
    main()
