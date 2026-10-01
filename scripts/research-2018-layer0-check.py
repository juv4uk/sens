#!/usr/bin/env python3
"""Layer-0 research invariants under #2018 premises (not production reader)."""

from __future__ import annotations

import sys

# --- D1: predicate answers -----------------------------------------------
D1 = {"0": "NO", "1": "YES"}


def check_d1() -> None:
    assert set(D1) == {"0", "1"}, "D1 domain must be exactly two bits"
    assert D1["0"] != D1["1"], "NO and YES must differ"
    # Structural empty is NOT predicate 0 (H-NIL / PredicateBit discipline)
    structural_empty = "()"
    assert structural_empty not in D1, "() is data, not a D1 code"
    print("D1 OK: 0=NO 1=YES; () not in predicate domain")


# --- racanā2: structural words -------------------------------------------
RACANA2 = {
    "00": "SEP",
    "10": "OPEN",
    "01": "CLOSE",
    "11": "DOT",
}


def check_racana2() -> None:
    assert len(RACANA2) == 4
    assert len(set(RACANA2)) == 4
    # All width-2; exhaust {0,1}^2
    assert set(RACANA2) == {"00", "01", "10", "11"}
    # Operator bīja3 seeds are width-3 — no code collision in the research model
    bija3 = {"000", "001", "010", "011", "100", "101", "110", "111"}
    assert set(RACANA2).isdisjoint(bija3), "racanā2 width-2 must not equal width-3 seeds"
    print("racanā2 OK: four width-2 structural words; disjoint from bīja3 width-3")


# --- explicit word boundaries --------------------------------------------
def check_word_boundaries() -> None:
    """Source is a sequence of already-bounded words; payload bits do not re-split."""

    def pack(words: list[str]) -> str:
        return "".join(words)

    def unpack(stream: str, widths: list[int]) -> list[str]:
        out, i = [], 0
        for w in widths:
            out.append(stream[i : i + w])
            i += w
        assert i == len(stream)
        return out

    # Example from #1961: 10 001 01 = OPEN, QUOTE, CLOSE
    words = ["10", "001", "01"]
    widths = [len(w) for w in words]
    stream = pack(words)
    assert unpack(stream, widths) == words

    # Internal 00 inside a width-3 seed must NOT become a separator
    seed_with_00 = "100"  # CONS — contains bits 1,0,0 but is ONE word
    assert "00" in seed_with_00[1:] or seed_with_00.endswith("00") or "00" in seed_with_00
    # The point: without external widths, naive split on 00 is wrong
    naive = seed_with_00.split("00")  # would destroy the word
    assert naive != [seed_with_00], "sanity: naive 00-split alters stream"
    # With explicit boundary, word is preserved
    assert unpack(seed_with_00, [3]) == ["100"]

    # Zero-pad EOS is not a boundary law (#1980 falsified) — we only check
    # that Layer-0 does not treat trailing zeros as implicit end without widths.
    padded = "001" + "0000"
    # Without widths, cannot recover; with widths [3] only first word is defined
    assert unpack(padded[:3], [3]) == ["001"]

    print("word-boundaries OK: explicit widths; internal 00 does not split")


def main() -> int:
    try:
        check_d1()
        check_racana2()
        check_word_boundaries()
    except AssertionError as e:
        print(f"FAIL: {e}", file=sys.stderr)
        return 1
    print("Layer-0 invariants: all passed (research model)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
