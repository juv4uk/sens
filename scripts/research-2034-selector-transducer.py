#!/usr/bin/env python3
"""#2034 research-only selector transducer countermodel.

Compares:
  A. current root+suffix interpretation of the proven selector family;
  B. a minimal deterministic subsequential transducer over the whole bounded word.

No human operation names participate in the executable witness.
Semantic outputs are exact binary identities only:
  101
  110

This is not production language/runtime code.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import product

MAX_WIDTH = 12

# Control states are host-only mechanism states, not SENS semantic identities.
START = 0
AFTER_1 = 1
AFTER_10 = 2
AFTER_11 = 3
CONT = 4
DEAD = 5

STATES = (START, AFTER_1, AFTER_10, AFTER_11, CONT, DEAD)
ACCEPTING = {CONT}

# (state, bit) -> (next_state, tuple(binary semantic outputs))
TRANSITIONS = {
    (START, 0): (DEAD, ()),
    (START, 1): (AFTER_1, ()),

    (AFTER_1, 0): (AFTER_10, ()),
    (AFTER_1, 1): (AFTER_11, ()),

    (AFTER_10, 0): (DEAD, ()),
    (AFTER_10, 1): (CONT, ("101",)),

    (AFTER_11, 0): (CONT, ("110",)),
    (AFTER_11, 1): (DEAD, ()),

    (CONT, 0): (CONT, ("101",)),
    (CONT, 1): (CONT, ("110",)),

    (DEAD, 0): (DEAD, ()),
    (DEAD, 1): (DEAD, ()),
}


@dataclass(frozen=True)
class Result:
    accepted: bool
    schedule: tuple[str, ...]


def root_suffix_oracle(word: str) -> Result:
    if word.startswith("101"):
        root = "101"
    elif word.startswith("110"):
        root = "110"
    else:
        return Result(False, ())

    suffix = word[3:]
    schedule = [root]
    schedule.extend("101" if bit == "0" else "110" for bit in suffix)
    return Result(True, tuple(schedule))


def transduce(word: str) -> Result:
    state = START
    out: list[str] = []

    for ch in word:
        bit = 1 if ch == "1" else 0
        state, emitted = TRANSITIONS[(state, bit)]
        out.extend(emitted)

    return Result(state in ACCEPTING, tuple(out) if state in ACCEPTING else ())


def all_words(width: int):
    for bits in product("01", repeat=width):
        yield "".join(bits)


def minimize_dfa() -> list[set[int]]:
    """Partition refinement for the recognizer part of the transducer.

    Output labels are deliberately ignored here. This asks only whether control
    prefixes have distinguishable accepted continuations (Myhill-Nerode style).
    """
    partitions = [set(ACCEPTING), set(STATES) - set(ACCEPTING)]

    while True:
        owner = {}
        for i, part in enumerate(partitions):
            for state in part:
                owner[state] = i

        refined: list[set[int]] = []
        changed = False

        for part in partitions:
            buckets: dict[tuple[int, int], set[int]] = {}
            for state in sorted(part):
                sig = (
                    owner[TRANSITIONS[(state, 0)][0]],
                    owner[TRANSITIONS[(state, 1)][0]],
                )
                buckets.setdefault(sig, set()).add(state)

            refined.extend(buckets.values())
            if len(buckets) > 1:
                changed = True

        partitions = refined
        if not changed:
            return partitions


def conceptual_trie_prefix_count(max_width: int) -> int:
    prefixes = {""}
    for width in range(1, max_width + 1):
        for word in all_words(width):
            if root_suffix_oracle(word).accepted:
                for i in range(1, len(word) + 1):
                    prefixes.add(word[:i])
    return len(prefixes)


def main() -> None:
    checked = 0
    accepted = 0
    schedule_steps = 0

    for width in range(1, MAX_WIDTH + 1):
        for word in all_words(width):
            a = root_suffix_oracle(word)
            b = transduce(word)
            assert a == b, (word, a, b)

            checked += 1
            if a.accepted:
                accepted += 1
                schedule_steps += len(a.schedule)

                # Name-erased output discipline.
                assert all(step in {"101", "110"} for step in a.schedule)

    partitions = minimize_dfa()
    assert len(partitions) == 6, partitions

    # Strong positive controls.
    assert transduce("101") == Result(True, ("101",))
    assert transduce("110") == Result(True, ("110",))
    assert transduce("1011") == Result(True, ("101", "110"))
    assert transduce("1100") == Result(True, ("110", "101"))
    assert transduce("10111") == Result(True, ("101", "110", "110"))

    # Invalid/out-of-family controls.
    for word in ("", "0", "1", "10", "11", "100", "111", "00101"):
        assert not transduce(word).accepted

    trie_prefixes = conceptual_trie_prefix_count(MAX_WIDTH)

    print(f"max width: {MAX_WIDTH}")
    print(f"all bounded binary words checked: {checked}")
    print(f"accepted selector identities: {accepted}")
    print(f"emitted primitive schedule steps: {schedule_steps}")
    print(f"conceptual accepted-prefix trie nodes: {trie_prefixes}")
    print(f"minimal recognizer control states: {len(partitions)}")
    print(f"transition entries: {len(TRANSITIONS)}")
    print()
    print("partition classes:")
    for i, part in enumerate(sorted(partitions, key=lambda p: min(p))):
        print(f"  P{i}: {sorted(part)}")
    print()
    print("RESULT: exhaustive parity PASS")
    print("RESULT: no human operation names used by the executable witness")
    print("RESULT: selector execution control compresses to a constant-size automaton")
    print("NON-CONCLUSION: semantic identities are NOT collapsed")
    print("NON-CONCLUSION: automaton execution does NOT yet provide typed graph self-description")
    print("HYPOTHESIS: graph/proof and execution-machine representations may be intentionally different")


if __name__ == "__main__":
    main()
