#!/usr/bin/env python3
"""Executable finite witnesses for #3970 D9 local-law mining.

Це дослідницькі моделі семантичних відношень. Вони не ратифікують D9
і навмисно не використовують host file descriptors, pointers або ABI.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Callable, Hashable

ROOT = Path(__file__).resolve().parents[1]
LAWS = ROOT / "knowledge" / "d9-laws-v1.json"
INVENTORY = ROOT / "knowledge" / "d9-v1-semantic-inventory.json"


@dataclass(frozen=True)
class ResourceState:
    next_handle: int
    live: frozenset[int]


def open_abstract(state: ResourceState) -> tuple[ResourceState, int]:
    handle = state.next_handle
    return replace(state, next_handle=handle + 1, live=state.live | {handle}), handle


def close_abstract(state: ResourceState, handle: int) -> ResourceState:
    assert handle in state.live
    return replace(state, live=state.live - {handle})


def with_open_file_abstract(
    state: ResourceState,
    body: Callable[[int, ResourceState], tuple[ResourceState, Hashable]],
) -> tuple[ResourceState, Hashable]:
    opened, handle = open_abstract(state)
    after_body, result = body(handle, opened)
    return close_abstract(after_body, handle), result


def witness_stream_family() -> None:
    start = ResourceState(next_handle=7, live=frozenset())

    def body(handle: int, state: ResourceState):
        assert state.live == {handle}
        return state, ("body-result", handle)

    scoped_state, scoped_result = with_open_file_abstract(start, body)

    explicit_open, handle = open_abstract(start)
    explicit_body, explicit_result = body(handle, explicit_open)
    explicit_closed = close_abstract(explicit_body, handle)

    assert scoped_state == explicit_closed
    assert scoped_result == explicit_result
    assert scoped_state.live == frozenset()

    # Remove-one falsifier: без CLOSE ресурс лишається живим.
    assert explicit_body.live != explicit_closed.live


def define_descriptor(
    registry: dict[tuple[str, str], str],
    kind: str,
    name: str,
    payload: str,
) -> dict[tuple[str, str], str]:
    out = dict(registry)
    out[(kind, name)] = payload
    return out


def witness_descriptor_family() -> None:
    registry: dict[tuple[str, str], str] = {}
    registry = define_descriptor(registry, "structure", "node", "slots:left,right")
    registry = define_descriptor(registry, "type", "node", "predicate:nodep")
    registry = define_descriptor(registry, "condition", "node", "severity:error")

    assert registry[("structure", "node")] == "slots:left,right"
    assert registry[("type", "node")] == "predicate:nodep"
    assert registry[("condition", "node")] == "severity:error"
    assert len(registry) == 3

    # Falsifier: без kind-axis однакове name колапсує до одного payload.
    collapsed = {
        "node": "slots:left,right",
        "node": "predicate:nodep",
        "node": "severity:error",
    }
    assert len(collapsed) == 1


def row_major_multi_index(shape: tuple[int, ...], linear: int) -> tuple[int, ...]:
    assert shape and all(n > 0 for n in shape)
    total = 1
    for n in shape:
        total *= n
    assert 0 <= linear < total

    out = [0] * len(shape)
    rem = linear
    for i in range(len(shape) - 1, -1, -1):
        out[i] = rem % shape[i]
        rem //= shape[i]
    return tuple(out)


def witness_row_major_aref() -> None:
    one_dim = ("a", "b", "c", "d")
    for i, value in enumerate(one_dim):
        assert row_major_multi_index((len(one_dim),), i) == (i,)
        assert one_dim[i] == value

    array2 = (("a", "b", "c"), ("d", "e", "f"))
    idx = row_major_multi_index((2, 3), 4)
    assert idx == (1, 1)
    assert array2[idx[0]][idx[1]] == "e"

    # Falsifier: трактувати 4 лише як first-dimension AREF неможливо для shape 2x3.
    assert 4 >= len(array2)


def pure_union(xs: list[int], ys: list[int]) -> list[int]:
    out = list(xs)
    for y in ys:
        if y not in out:
            out.append(y)
    return out


def destructive_union(xs: list[int], ys: list[int]) -> list[int]:
    for y in ys:
        if y not in xs:
            xs.append(y)
    return xs


def witness_nunion_distinction() -> None:
    first = [1, 2]
    alias = first
    pure_result = pure_union(first, [2, 3])
    assert pure_result == [1, 2, 3]
    assert alias == [1, 2]

    destructive_result = destructive_union(first, [2, 3])
    assert destructive_result is first
    assert alias == [1, 2, 3]

    # Falsifier boundary: якщо aliases не спостерігаються, content-result однаковий.
    assert pure_result == destructive_result


def main() -> int:
    laws = json.loads(LAWS.read_text(encoding="utf-8"))
    inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))

    witness_stream_family()
    witness_descriptor_family()
    witness_row_major_aref()
    witness_nunion_distinction()

    reviewed = (
        sum((family["members"] for family in laws["proved_families"]), [])
        + [row["semantic_name"] for row in laws["proved_distinctions"]]
        + [row["semantic_name"] for row in laws["underdetermined"]]
    )
    selected = {
        row["semantic_name"]
        for row in inventory["rows"]
        if row["source_class"] == "D8-OVERFLOW-RECOVERY"
    }

    assert len(reviewed) == 20
    assert len(set(reviewed)) == 20
    assert set(reviewed) == selected
    assert laws["accounting"] == {
        "candidates_reviewed": 20,
        "proved_family_members": 7,
        "proved_distinct_independent": 1,
        "underdetermined": 12,
        "fixed_coordinates": 0,
        "orbit_coordinates": 0,
        "ratified_d9_residents": 0,
    }

    print("D9-LAWS-1=PASS")
    print("proved-family-members=7")
    print("proved-distinct-independent=1")
    print("underdetermined=12")
    print("coordinates-assigned=0")
    print("ratified-d9=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
