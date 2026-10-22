#!/usr/bin/env python3
"""Principle-force guard: every project principle is EVIDENCED, not just declared.

The axioms rest on the project principles P1-P5 (docs/language-core-axioms.md).
This guard restores their force: a principle that is only a sentence has no force,
so every principle must be declared in the doc AND in the constitution, and carry
at least one machine-checkable piece of evidence (research/principle-evidence.json):

  artifact      -- the named file exists;
  fixture       -- the expression is present in tests/fixtures/conformance.lisp;
  doc-reference -- the text is present in docs/language-core-axioms.md.

Principle 5 is the focus: its old-technology half (lib/clips-import.lisp) had no
evidence at all before this guard.

Fail-closed. Exit 0 = PRINCIPLE_FORCE_OK; exit 1 = PRINCIPLE_FORCE_BLOCKED.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REGISTRY = "research/principle-evidence.json"
PRINCIPLE_RANGE = range(1, 6)


def check(root: Path) -> list[str]:
    problems: list[str] = []
    registry_path = root / REGISTRY
    if not registry_path.exists():
        return [f"registry `{REGISTRY}` is missing"]
    data = json.loads(registry_path.read_text(encoding="utf-8"))

    doc = (root / data["principles_doc"]).read_text(encoding="utf-8")
    const = (root / data["constitution_script"]).read_text(encoding="utf-8")
    conf = (root / data["conformance"]).read_text(encoding="utf-8")

    doc_principles = {int(m) for m in re.findall(r"(?m)^\*\*(\d)\.\s", doc)}
    const_principles = {int(m) for m in re.findall(r"\(як-є principle\)\s*(\d)", const)}
    for n in PRINCIPLE_RANGE:
        if n not in doc_principles:
            problems.append(f"principle {n} is not declared in {data['principles_doc']}")
        if n not in const_principles:
            problems.append(f"principle {n} is not declared in {data['constitution_script']}")

    bindings = data.get("bindings", [])
    bound = {b.get("principle") for b in bindings}
    for n in PRINCIPLE_RANGE:
        if n not in bound:
            problems.append(f"principle {n} has no evidence binding (force not restored)")

    # Принцип 5 мусить мати не лише декларацію, а й ВИКОНУВАНИЙ доказ та
    # ОБОРОТНУ пару — інакше він лишається гаслом без сили.
    p5 = next((b for b in bindings if b.get("principle") == 5), {})
    kinds5 = {item.get("kind") for item in p5.get("evidence", [])}
    if "executable" not in kinds5:
        problems.append("principle 5 lacks executable evidence (force not restored)")
    if "reversible" not in kinds5:
        problems.append("principle 5 lacks a reversible evidence pair (force not restored)")

    for b in bindings:
        n = b.get("principle")
        evidence = b.get("evidence", [])
        if not evidence:
            problems.append(f"principle {n} has no evidence")
            continue
        for item in evidence:
            kind = item.get("kind")
            if kind == "artifact":
                if not (root / item["path"]).exists():
                    problems.append(f"principle {n} evidence artifact missing: {item['path']}")
            elif kind == "fixture":
                if item["expr"] not in conf:
                    problems.append(f"principle {n} evidence fixture not in conformance.lisp: {item['expr']}")
            elif kind == "executable":
                # Доказ мусить бути виконуваною програмою, не лише наявним файлом.
                artifact = root / item["path"]
                if not artifact.exists():
                    problems.append(f"principle {n} executable artifact missing: {item['path']}")
                elif "(визначити " not in artifact.read_text(encoding="utf-8"):
                    problems.append(
                        f"principle {n} executable artifact defines nothing: {item['path']}"
                    )
            elif kind == "reversible":
                # Оборотна пара: обидві половини мусять бути визначені.
                artifact = root / item["path"]
                if not artifact.exists():
                    problems.append(f"principle {n} reversible artifact missing: {item['path']}")
                else:
                    body = artifact.read_text(encoding="utf-8")
                    for half in (item["forward"], item["inverse"]):
                        if f"(визначити {half}" not in body:
                            problems.append(
                                f"principle {n} reversible half missing: {half} in {item['path']}"
                            )
            elif kind == "doc-reference":
                if item["text"] not in doc:
                    problems.append(f"principle {n} evidence doc-reference missing: {item['text']}")
            else:
                problems.append(f"principle {n} has an unknown evidence kind: {kind}")
    return problems


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", default=str(Path(__file__).resolve().parents[1]))
    ns = parser.parse_args()
    root = Path(ns.root).resolve()
    try:
        problems = check(root)
    except FileNotFoundError as exc:
        print(f"PRINCIPLE_FORCE_BLOCKED missing file: {exc}", flush=True)
        return 1
    if problems:
        print("PRINCIPLE_FORCE_BLOCKED a project principle is declared but not evidenced:", flush=True)
        for problem in problems:
            print(" -", problem, flush=True)
        return 1
    print(
        "PRINCIPLE_FORCE_OK every project principle (P1-P5) is declared and evidenced "
        "(artifacts, conformance fixtures, doc references)",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
