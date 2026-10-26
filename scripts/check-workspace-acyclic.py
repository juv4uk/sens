#!/usr/bin/env python3
"""Гейт ациклічності workspace-залежностей.

Навіщо: цикл `sens ↔ sens-cli` (dev-залежність) зайшов у main і виліз як
`error[E0308]` — Cargo будував ДВІ копії крейта `sens`, і `BinarySourceWord`
ставав двома різними типами. Ловилось це руками, коштувало перекарбовування
F6 і двох діб розбирання.

Такий цикл мусить падати в CI за секунди, а не після карбування.

Джерело істини — `cargo metadata` (Cargo сам знає свій граф). Тут лише
DAG-перевірка: жодного власного парсера маніфестів.

Режими:
  --check         перевірити (типово; код 1 при циклі)
  --self-test     самоперевірка детектора на синтетичних графах
  --allow A>B     дозволити конкретне ребро (повторюване), напр. sens>sens-cli
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def load_graph(allow: set[tuple[str, str]]) -> tuple[dict[str, set[str]], set[str]]:
    """Граф локальних (path-) залежностей між членами workspace."""
    try:
        raw = subprocess.run(
            ["cargo", "metadata", "--format-version", "1", "--no-deps"],
            cwd=ROOT, capture_output=True, text=True, timeout=120,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise SystemExit(f"ACYCLIC_UNVERIFIED: cargo недоступний ({exc}). Це НЕ «все чисто».")
    if raw.returncode != 0:
        raise SystemExit(
            "ACYCLIC_UNVERIFIED: cargo metadata не вдався.\n"
            + (raw.stderr or "").strip()[:800]
        )

    data = json.loads(raw.stdout)
    members = {p["name"] for p in data.get("packages", [])}
    graph: dict[str, set[str]] = {name: set() for name in members}
    for pkg in data.get("packages", []):
        for dep in pkg.get("dependencies", []):
            name = dep.get("name")
            if name not in members or name == pkg["name"]:
                continue
            if (pkg["name"], name) in allow:
                continue
            # лише шлях-залежності: зовнішні крейти циклів у workspace не роблять
            if dep.get("path") or dep.get("source") is None:
                graph[pkg["name"]].add(name)
    return graph, members


def find_cycle(graph: dict[str, set[str]]) -> list[str] | None:
    """Перший знайдений цикл як список вершин, або None."""
    WHITE, GREY, BLACK = 0, 1, 2
    colour = {node: WHITE for node in graph}
    stack: list[str] = []

    def visit(node: str) -> list[str] | None:
        colour[node] = GREY
        stack.append(node)
        for nxt in sorted(graph.get(node, ())):
            if colour.get(nxt, BLACK) == GREY:
                return stack[stack.index(nxt):] + [nxt]
            if colour.get(nxt, BLACK) == WHITE:
                found = visit(nxt)
                if found:
                    return found
        stack.pop()
        colour[node] = BLACK
        return None

    for node in sorted(graph):
        if colour[node] == WHITE:
            found = visit(node)
            if found:
                return found
    return None


def self_test() -> int:
    ok = True
    cases = [
        ("ациклічний граф", {"a": {"b"}, "b": {"c"}, "c": set()}, None),
        ("простий цикл a→b→a", {"a": {"b"}, "b": {"a"}}, ["a", "b", "a"]),
        ("довгий цикл a→b→c→a", {"a": {"b"}, "b": {"c"}, "c": {"a"}}, ["a", "b", "c", "a"]),
        ("самопосилання a→a", {"a": {"a"}}, ["a", "a"]),
        ("два компоненти, цикл у другому",
         {"a": set(), "b": {"c"}, "c": {"b"}}, ["b", "c", "b"]),
    ]
    for label, graph, expected in cases:
        got = find_cycle(graph)
        good = (got is None) if expected is None else (got == expected)
        print(("OK    " if good else "ЗБІЙ  ") + label + ("" if good else f"  → {got!r}"))
        ok = ok and good
    print("SELF-TEST:", "OK" if ok else "FAILED")
    return 0 if ok else 1


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--allow", action="append", default=[], metavar="A>B")
    args = ap.parse_args(argv)

    if args.self_test:
        return self_test()

    allow: set[tuple[str, str]] = set()
    for spec in args.allow:
        if ">" not in spec:
            print(f"погане --allow: {spec!r} (очікую A>B)", file=sys.stderr)
            return 2
        a, b = spec.split(">", 1)
        allow.add((a.strip(), b.strip()))

    graph, members = load_graph(allow)
    edges = sum(len(v) for v in graph.values())
    cycle = find_cycle(graph)

    if cycle:
        print("::error::WORKSPACE_DEPENDENCY_CYCLE " + " → ".join(cycle), file=sys.stderr)
        print(
            "\nЦикл у workspace-залежностях. Cargo збудує дві копії крейта, і типи "
            "з них стануть РІЗНИМИ (error[E0308]), навіть якщо імена збігаються.\n"
            "Латай першопричину: прибери ВИКЛИК, а не залежність, або перенеси код "
            "в той крейт, де він природно живе.",
            file=sys.stderr,
        )
        return 1

    print(f"ACYCLIC_OK members={len(members)} edges={edges}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
