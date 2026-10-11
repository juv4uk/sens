"""Емісія детермінованих векторів для диференційного тесту Rust<->Python."""
import itertools
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import research_codec as rc
import tb33_tail_research as tb
import adaptive_encoder as A

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
    return "\t".join([" ".join(ws), t5.hex(), frh, tbh, prof, chos])


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
