#!/usr/bin/env python3
"""#2383 — відтворюваний census машинних encoder-залежностей.

Цей інструмент є лише research-observer. Він не визначає ISA, не змінює
admission і не проголошує структурну схожість семантичною/машинною владою.

Мета: побудувати детермінований граф x86-encode-* -> x86-encode-* і дати
консервативну попередню класифікацію. Усе, що не доведене структурою графа,
лишається UNKNOWN.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = REPO_ROOT / "lib/machine/encoding/x86-64.lisp"
DEF_RE = re.compile(r"^\(00001001\s+(x86-encode-[^\s()]+)")
REF_RE = re.compile(r"\b(x86-encode-[A-Za-z0-9?+*/<>=!._:-]+)")
LOW_LEVEL = {
    "x86-encode-rex",
    "x86-encode-modrm",
    "x86-encode-sib",
}


def top_level_forms(text: str):
    """Виділяє верхньорівневі форми, не рахуючи дужки в рядках/коментарях."""
    start = None
    depth = 0
    in_string = False
    escaped = False
    in_comment = False

    for index, ch in enumerate(text):
        if in_comment:
            if ch == "\n":
                in_comment = False
            continue

        if in_string:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_string = False
            continue

        if ch == ";":
            in_comment = True
            continue
        if ch == '"':
            in_string = True
            continue
        if ch == "(":
            if depth == 0:
                start = index
            depth += 1
            continue
        if ch == ")":
            depth -= 1
            if depth < 0:
                raise ValueError("unbalanced closing parenthesis")
            if depth == 0 and start is not None:
                yield text[start:index + 1]
                start = None

    if depth != 0 or in_string:
        raise ValueError("unterminated form or string")


def encoder_definitions(text: str):
    rows = []
    for form in top_level_forms(text):
        match = DEF_RE.match(form)
        if not match:
            continue
        name = match.group(1)
        refs = sorted({
            ref
            for ref in REF_RE.findall(form)
            if ref != name
        })
        rows.append({
            "name": name,
            "form": form,
            "refs": refs,
            "direct_byte_list": "(00100111" in form,
            "uses_rex": "x86-encode-rex" in form,
            "uses_modrm": "x86-encode-modrm" in form,
            "uses_sib": "x86-encode-sib" in form,
        })
    return rows


def build_report(text: str):
    rows = encoder_definitions(text)
    names = {row["name"] for row in rows}

    # Лише внутрішні залежності цього encoder-модуля можуть бути ребрами графа.
    for row in rows:
        row["refs"] = [ref for ref in row["refs"] if ref in names]

    callers = Counter()
    for row in rows:
        for ref in row["refs"]:
            callers[ref] += 1

    reusable = set()
    for row in rows:
        name = row["name"]
        if name in LOW_LEVEL:
            reusable.add(name)
        elif callers[name] >= 2 and (
            row["direct_byte_list"]
            or row["uses_rex"]
            or row["uses_modrm"]
            or row["uses_sib"]
        ):
            reusable.add(name)

    definitions = []
    for row in rows:
        name = row["name"]
        refs = row["refs"]
        binds_only_reusable = bool(refs) and all(ref in reusable for ref in refs)
        owns_low_level_shape = (
            row["direct_byte_list"]
            or row["uses_rex"]
            or row["uses_modrm"]
            or row["uses_sib"]
        )

        if name in LOW_LEVEL:
            cls = "encoding-root-candidate"
        elif name in reusable:
            cls = "reused-generator-candidate"
        elif binds_only_reusable and not owns_low_level_shape:
            cls = "derived-wrapper-candidate"
        else:
            cls = "UNKNOWN"

        definitions.append({
            "name": name,
            "classification": cls,
            "calls": refs,
            "caller_count": callers[name],
            "evidence": {
                "direct_byte_list": row["direct_byte_list"],
                "uses_rex": row["uses_rex"],
                "uses_modrm": row["uses_modrm"],
                "uses_sib": row["uses_sib"],
            },
        })

    definitions.sort(key=lambda row: row["name"])
    class_counts = Counter(row["classification"] for row in definitions)

    return {
        "schema": 1,
        "authority": "research-observer-only",
        "source": "lib/machine/encoding/x86-64.lisp",
        "counts": {
            "encoder_definitions": len(definitions),
            "dependency_edges": sum(len(row["calls"]) for row in definitions),
            "encoding_root_candidates": class_counts["encoding-root-candidate"],
            "reused_generator_candidates": class_counts["reused-generator-candidate"],
            "derived_wrapper_candidates": class_counts["derived-wrapper-candidate"],
            "unknown": class_counts["UNKNOWN"],
        },
        "definitions": definitions,
    }


def self_test():
    sample = r"""
(00001001 x86-encode-rex
  (00001000 (w r x b) (+ w r x b)))
(00001001 x86-encode-modrm
  (00001000 (m r x) (+ m r x)))
(00001001 x86-encode-family
  (00001000 (opcode dst src)
    (00100111
      (x86-encode-rex 1 0 0 0)
      opcode
      (x86-encode-modrm 3 dst src))))
(00001001 x86-encode-a
  (00001000 (dst src)
    (x86-encode-family 1 dst src)))
(00001001 x86-encode-b
  (00001000 (dst src)
    (x86-encode-family 2 dst src)))
; Цей вузол викликає helper, але сам матеріалізує байти: wrapper-ом не є.
(00001001 x86-encode-not-a-wrapper
  (00001000 (dst src)
    (00100111 9 (x86-encode-family 3 dst src))))
"""
    report = build_report(sample)
    by_name = {row["name"]: row for row in report["definitions"]}

    checks = [
        by_name["x86-encode-rex"]["classification"] == "encoding-root-candidate",
        by_name["x86-encode-modrm"]["classification"] == "encoding-root-candidate",
        by_name["x86-encode-family"]["classification"] == "reused-generator-candidate",
        by_name["x86-encode-a"]["classification"] == "derived-wrapper-candidate",
        by_name["x86-encode-b"]["classification"] == "derived-wrapper-candidate",
        by_name["x86-encode-not-a-wrapper"]["classification"] == "UNKNOWN",
    ]
    if not all(checks):
        raise SystemExit("machine-law-census self-test: FAIL")
    print("machine-law-census self-test: PASS")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        self_test()
        return

    report = build_report(args.source.read_text(encoding="utf-8"))
    json.dump(
        report,
        fp=__import__("sys").stdout,
        ensure_ascii=False,
        indent=2 if args.pretty else None,
        sort_keys=True,
    )
    print()


if __name__ == "__main__":
    main()
