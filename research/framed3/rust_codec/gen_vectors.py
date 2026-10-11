"""Емісія детермінованих векторів для диференційного тесту Rust<->Python."""
import itertools
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import research_codec as rc
import tb33_tail_research as tb
import adaptive_encoder as A


# Independent Python D3 executable-subprofile oracle. The legacy transport
# oracle accepts many D2-shaped DATA trees; the Rust explicit .senc decoder
# intentionally rejects some of them as executable CODE. They must not be
# mislabeled as Rust/Python transport bit mismatches.
from test_canonical_capacity_research import parse_program, Rejected
from semantic_redundancy_research import Word, FIXED_ARITY


def d3_code_admitted(ws):
    try:
        root = parse_program(tuple(ws))
    except (Rejected, ValueError, IndexError):
        return False

    def legal(node, data=False):
        if isinstance(node, Word):
            return True
        items = node.items
        if not items:
            return data
        if data:
            return all(legal(item, True) for item in items)
        head, *args = items
        if not isinstance(head, Word):
            return False  # No ratified nested-head D3 callable.
        name = head.bits
        if name in FIXED_ARITY:
            return len(args) == FIXED_ARITY[name] and all(
                legal(item, name == "001") for item in args
            )
        if name in ("000", "110"):
            return all(legal(item) for item in args)
        return False

    return legal(root)

PROFILE = {"т5": "T5", "рамка3": "Frame3", "тб33": "Tb33"}


def line(words):
    ws = [str(w) for w in words]
    try:
        t5 = A.кодувати_т5(ws)
    except Exception:
        return None
    try:
        frh = rc.encode(ws).hex()
    except Exception:
        frh = "-"
    try:
        tbh = tb.encode(A.трити(ws)).hex()
    except Exception:
        tbh = "-"
    try:
        chosen = A.найменший_носій(ws)
        prof = PROFILE[chosen.профіль]
        chos = chosen.дані.hex()
    except Exception:
        prof = "-"
        chos = "-"
    return "\t".join([" ".join(ws), t5.hex(), frh, tbh, prof, chos, "D3" if d3_code_admitted(ws) else "REJECT"])


def all_bitstrings(n):
    for bits in itertools.product("01", repeat=n):
        yield "".join(bits)


def balanced_random(rng, depth):
    if depth <= 0 or rng.random() < 0.3:
        return "01"
    inner = [balanced_random(rng, depth - 1) for _ in range(rng.randint(1, 3))]
    return "10 " + " ".join(inner) + " 01"


def main():
    rng = random.Random(20261010)
    cases = []

    cases.append(("10", "01"))
    cases.append(("10", "001", "00", "000", "01"))
    cases.append(tuple("10 100 00 10 111 00 1 00 0 01 01".split()))
    cases.append(())

    for n in range(1, 10):
        for bits in all_bitstrings(n):
            cases.append((bits,))
    for n in range(1, 10):
        cases.append(("0" * n,))
    for n in range(1, 10):
        cases.append(("10", "1" * n, "01"))
    for n in range(1, 10):
        cases.append(("10", "0" * n, "01"))

    for _ in range(300):
        cases.append(tuple(balanced_random(rng, 5).split()))

    for k in range(0, 30):
        cases.append(("10",) + ("1" * 9,) * k + ("01",))
        cases.append(("10",) + ("0" * 9,) * k + ("01",))
        cases.append(("10",) + tuple("10 0 01".split()) * 0 + ("01",))

    for _ in range(400):
        count = rng.randint(2, 12)
        words = [all_bitstrings(rng.randint(1, 9)) and next(iter(all_bitstrings(rng.randint(1, 9)))) for _ in range(count)]
        cases.append(tuple(words))

    seen = set()
    out = []
    for words in cases:
        record = line(words)
        if record is None or record in seen:
            continue
        seen.add(record)
        out.append(record)
    print("\n".join(out))


if __name__ == "__main__":
    main()
