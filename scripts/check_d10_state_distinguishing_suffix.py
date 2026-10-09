#!/usr/bin/env python3
"""D10 RESEARCH/HOLD: shortest canonical binary DFA state distinguishing word.

Pure finite mathematical query, not a runtime/FPGA opcode or SENS D2 decoder.
Two *independently expressed* exact algorithms: reachable-product BFS and
Moore-like finite iterative distinguishability recurrence. All inputs must be
fully specified; epsilon ("") differs from equivalent (None).
Reference: Hopcroft (1971), https://doi.org/10.1016/B978-0-12-417750-5.50022-1
"""
from __future__ import annotations

from collections import deque
import hashlib
import itertools
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOSSIER = ROOT / "knowledge/d10-finite-state-distinguishing-suffix-research-v1.json"
INVENTORY = ROOT / "knowledge/d10-v1-semantic-inventory.json"
MAX_STATES = 10


class Blocked(ValueError):
    pass


def validate(transitions: object, accepting: object, p: object, q: object):
    if not isinstance(transitions, (list, tuple)):
        raise Blocked("DFA: nonempty state table required")
    n = len(transitions)
    if not 1 <= n <= MAX_STATES:
        raise Blocked("DFA: bounded finite number of states 1..10 required")
    if not isinstance(accepting, (list, tuple)) or len(accepting) != n:
        raise Blocked("DFA: accepting vector must have exactly n entries")
    if any(type(v) is not int or v not in (0, 1) for v in accepting):
        raise Blocked("DFA: D1 acceptance values must be exactly 0 or 1")
    if any(type(v) is not int or not (0 <= v < n) for v in (p, q)):
        raise Blocked("DFA: p and q must be in-range integer state indices")
    table = []
    for row in transitions:
        if not isinstance(row, (list, tuple)) or len(row) != 2:
            raise Blocked("DFA: every state requires exact D1 input 0 and 1")
        if any(type(v) is not int or not (0 <= v < n) for v in row):
            raise Blocked("DFA: total two-bit transition targets must be valid states")
        table.append((row[0], row[1]))
    return tuple(table), tuple(accepting), p, q


def result(word: str | None) -> dict:
    return {
        "status": "EQUIVALENT" if word is None else "DISTINGUISHED",
        "word": word,
    }


def product_bfs(transitions, accepting, p, q) -> dict:
    """Shortest then 0-before-1 word over product graph; no input I/O effects."""
    delta, final, p, q = validate(transitions, accepting, p, q)
    queue = deque([(p, q, "")])
    seen = {(p, q)}
    while queue:
        u, v, word = queue.popleft()
        if final[u] != final[v]:
            return result(word)
        for bit in (0, 1):
            other = (delta[u][bit], delta[v][bit])
            if other not in seen:
                seen.add(other)
                queue.append((other[0], other[1], word + str(bit)))
    return result(None)


def _smaller(a: str | None, b: str | None) -> str | None:
    if a is None:
        return b
    if b is None:
        return a
    return min(a, b, key=lambda x: (len(x), x))


def independent_refinement(transitions, accepting, p, q) -> dict:
    """Fixed-point recurrence, not BFS; all state-pair suffixes simultaneously.

    W_0(i,j) = epsilon if accepts differ; otherwise no witness.
    W_(k+1)(i,j) = min W_k(i,j), 0+W_k(d(i,0),d(j,0)),
                                  1+W_k(d(i,1),d(j,1)).
    A new pair can be separated after at most n^2-1 product transitions.
    """
    delta, final, p, q = validate(transitions, accepting, p, q)
    n = len(delta)
    previous = [[("" if final[i] != final[j] else None)
                 for j in range(n)] for i in range(n)]
    for _ in range(n * n):
        following = [[previous[i][j] for j in range(n)] for i in range(n)]
        for i in range(n):
            for j in range(n):
                for bit in (0, 1):
                    tail = previous[delta[i][bit]][delta[j][bit]]
                    if tail is not None:
                        following[i][j] = _smaller(following[i][j], str(bit) + tail)
        if following == previous:
            break
        previous = following
    return result(previous[p][q])


def accepts_after(transitions, accepting, state, word):
    delta, final, start, _ = validate(transitions, accepting, state, state)
    for bit in word:
        if bit not in "01":
            raise Blocked("DFA: suffix must contain only D1 bits")
        start = delta[start][int(bit)]
    return final[start]


def independent_exhaustive_tiny(transitions, accepting, p, q) -> dict:
    """Truth oracle by literal enumeration: bounded <=3 states only."""
    delta, final, p, q = validate(transitions, accepting, p, q)
    n = len(delta)
    if n > 3:
        raise Blocked("ORACLE: exhaustive reference limited to <=3 states")
    for size in range(n * n):
        for symbols in itertools.product("01", repeat=size):
            word = "".join(symbols)
            if accepts_after(delta, final, p, word) != accepts_after(delta, final, q, word):
                return result(word)
    return result(None)


def assert_exact_witness(transitions, accepting, p, q, claimed: dict) -> None:
    """Compare against structurally independent refinement + canonical order."""
    if not isinstance(claimed, dict) or set(claimed) != {"status", "word"}:
        raise Blocked("WITNESS: exact tagged result fields required")
    expected = independent_refinement(transitions, accepting, p, q)
    if claimed != expected:
        raise Blocked("WITNESS: not shortest canonical binary distinguishing suffix")


def validate_dossier() -> dict:
    data = json.loads(DOSSIER.read_text(encoding="utf-8"))
    machine = json.loads(INVENTORY.read_text(encoding="utf-8"))
    row = data["candidate"]
    if (data["schema"] != "d10-state-distinguishing-suffix-research/v1"
        or data["status"] != "RESEARCH-HOLD-NOT-SELECTED"
        or row["width"] != "D10"
        or row["semantic_name"] != "FINITE-STATE-SHORTEST-DISTINGUISHER"
        or row["coordinate"] is not None
        or row["selected"] is not False
        or row["ratified"] is not False
        or data["physical_sens_files_created"] != 0
        or data["original_executable_migrations_admitted"] != 0
        or data["independent_external_runtime_oracle"] != "NOT_EXECUTED"
        or data["D1_D9_behavioral_dedup"] != "REVIEW_REQUIRED"):
        raise Blocked("DOSSIER: research-only, unsigned non-admission invariants changed")
    if machine["accounting"]["ratified_d10_residents"] != 0:
        raise Blocked("MACHINE: current D10 unexpectedly ratified")
    names = {r.get("semantic_name") for r in machine["rows"]}
    if row["semantic_name"] in names:
        raise Blocked("MACHINE: DUPLICATE selected D10 semantics, owner must reconcile")
    return data


def evidence() -> dict:
    data = validate_dossier()
    examined = 0
    # Exhaust ALL 2-state binary total transition tables and accepting masks:
    # 2^4 * 2^2 * 2^2 = 256 (including unreachable and equivalent states).
    for raw in itertools.product(range(2), repeat=4):
        delta = ((raw[0], raw[1]), (raw[2], raw[3]))
        for finals in itertools.product((0, 1), repeat=2):
            for p in range(2):
                for q in range(2):
                    x = product_bfs(delta, finals, p, q)
                    if x != independent_refinement(delta, finals, p, q):
                        raise Blocked("ORACLE: product vs refinement mismatch")
                    if x != independent_exhaustive_tiny(delta, finals, p, q):
                        raise Blocked("ORACLE: exhaustive 2-state mismatch")
                    examined += 1

    # 3-state known complete finite automata, seeded deterministic variation.
    import random
    rng = random.Random(20261009)
    three = 0
    for _ in range(128):
        delta = tuple((rng.randrange(3), rng.randrange(3)) for _ in range(3))
        finals = tuple(rng.randrange(2) for _ in range(3))
        p, q = rng.randrange(3), rng.randrange(3)
        expected = independent_exhaustive_tiny(delta, finals, p, q)
        if product_bfs(delta, finals, p, q) != expected:
            raise Blocked("ORACLE: 3-state exact discrepancy")
        if independent_refinement(delta, finals, p, q) != expected:
            raise Blocked("ORACLE: 3-state recurrence discrepancy")
        three += 1

    cases = data["witnesses"]
    for test in cases:
        actual = product_bfs(test["transitions"], test["accepting"], test["p"], test["q"])
        assert_exact_witness(test["transitions"], test["accepting"], test["p"], test["q"], test["expected"])
        if actual != test["expected"]:
            raise Blocked("DOSSIER: named witness falsified")
    return {
        "status": "RESEARCH-VALIDATED-HOLD-NOT-SELECTED",
        "semantic_name": data["candidate"]["semantic_name"],
        "exact_exhaustive_2_state_cases": examined,
        "exact_exhaustive_3_state_seeded_cases": three,
        "named_witness_cases": len(cases),
        "independent_oracles": "product-BFS, dynamic-refinement, tiny-exhaustive",
        "independent_external_runtime_oracle": "NOT_EXECUTED",
        "owner_decision": "HOLD_CORE_VS_DERIVED",
        "D1_D9_behavioral_dedup": "REVIEW_REQUIRED",
        "selected_delta": 0,
        "coordinates_assigned": 0,
        "ratified": 0,
        "original_executable_migrations_admitted": 0,
        "physical_sens_files_created": 0,
        "current_machine_d10_selected": json.loads(INVENTORY.read_text())["accounting"]["selected_semantic_candidates"],
        "dossier_sha256": hashlib.sha256(DOSSIER.read_bytes()).hexdigest(),
    }


if __name__ == "__main__":
    print(json.dumps(evidence(), sort_keys=True, ensure_ascii=False))
