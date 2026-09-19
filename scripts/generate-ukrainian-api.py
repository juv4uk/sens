#!/usr/bin/env python3
"""Generate the detailed Ukrainian API reference from byte-SID documentation + surface authority.

Behavior prose lives once in lib/surface/uk-docs.lisp, keyed by byte SID.
Surface spellings come from lib/generated/function-table.lisp, itself a projection
of lib/surface/semantic-registry.lisp. This script only joins those two projections.
"""

from __future__ import annotations

import argparse
import difflib
import json
import re
from collections import OrderedDict
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS_INDEX = ROOT / "lib/surface/uk-docs.lisp"
FUNCTION_TABLE = ROOT / "lib/generated/function-table.lisp"
API_DOC = ROOT / "docs/ukrainian-api.md"

START = "## Повний довідник"
END = "## Межа довідника"

DOC_RE = re.compile(
    r'^\s*\(doc\s+(\S+)\s+"([01]{8})"\s+(\S+)\s+"((?:\\.|[^"\\])*)"\s+"((?:\\.|[^"\\])*)"\)\s*$'
)
SURFACE_RE = re.compile(r"\((uk|ukr|en|sym)\s+(\(\)|[^\s)]+)\)")
ROW_RE = re.compile(r'^\s*\("([01]{8})"\s')

CATEGORY_TITLES = OrderedDict(
    [
        ("canon", "Канон 0+7"),
        ("forms", "Форми та макроси визначення"),
        ("arithmetic", "Арифметика"),
        ("comparison", "Порівняння"),
        ("predicate", "Базові предикати"),
        ("list", "Списки"),
        ("higher-order", "Функції вищого порядку"),
        ("string", "Текст і символи"),
        ("io", "Читання, обчислення та вивід"),
        ("vector", "Звичайні вектори"),
        ("time", "Час"),
        ("persistent-map", "Персистентні карти"),
        ("persistent-vector", "Персистентні вектори"),
        ("knowledge", "Знання"),
        ("reasoning", "Логічне міркування"),
        ("unification", "Уніфікація"),
        ("epistemic", "Епістемічні структури"),
        ("other", "Інші базові засоби"),
    ]
)

KIND_UK = {
    "form": "форма",
    "macro": "макрос",
    "function": "функція",
    "predicate": "предикат",
    "mutation": "мутація",
    "value": "значення",
}


@dataclass(frozen=True)
class DocRow:
    category: str
    identity: str
    kind: str
    call: str
    description: str


@dataclass(frozen=True)
class Surface:
    word: str


def decode_string(raw: str) -> str:
    return json.loads(f'"{raw}"')


def parse_docs_index() -> list[DocRow]:
    source = DOCS_INDEX.read_text(encoding="utf-8")
    if "(schema uk-api-docs/3)" not in source:
        raise SystemExit("uk-docs.lisp must use schema uk-api-docs/3 before generation")

    rows: list[DocRow] = []
    for line in source.splitlines():
        if not line.lstrip().startswith("(doc "):
            continue
        match = DOC_RE.match(line)
        if not match:
            raise SystemExit(f"cannot parse documentation row: {line}")
        category, identity, kind, call, description = match.groups()
        if category not in CATEGORY_TITLES:
            raise SystemExit(f"unknown documentation category {category!r} for {identity}")
        if kind not in KIND_UK:
            raise SystemExit(f"unknown documentation kind {kind!r} for {identity}")
        rows.append(
            DocRow(
                category=category,
                identity=identity,
                kind=kind,
                call=decode_string(call),
                description=decode_string(description),
            )
        )

    identities = [row.identity for row in rows]
    if len(rows) != 140:
        raise SystemExit(f"expected 140 documented stable uk identities, found {len(rows)}")
    if len(set(identities)) != len(identities):
        raise SystemExit("documentation index contains duplicate byte SIDs")
    return rows


def parse_function_table() -> dict[str, dict[str, Surface]]:
    result: dict[str, dict[str, Surface]] = {}
    for line in FUNCTION_TABLE.read_text(encoding="utf-8").splitlines():
        row_match = ROW_RE.match(line)
        if not row_match:
            continue
        identity = row_match.group(1)
        surfaces = {
            namespace: Surface(word=word.strip('"'))
            for namespace, word in SURFACE_RE.findall(line)
        }
        result[identity] = surfaces
    return result


def md_text(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


def code(value: str) -> str:
    return f"`{md_text(value)}`"


def render_reference(rows: list[DocRow], table: dict[str, dict[str, Surface]]) -> str:
    grouped: OrderedDict[str, list[DocRow]] = OrderedDict((key, []) for key in CATEGORY_TITLES)
    for row in rows:
        grouped[row.category].append(row)

    out = [
        "## Повний довідник `uk` / `ukr`",
        "",
        "Нижче — згенерований join по **byte SID**. Опис поведінки береться один раз із `lib/surface/uk-docs.lisp`; `uk`, `ukr` та основа беруться з authoritative function-table projection. Ручне редагування рядків цієї секції буде перезаписано генератором.",
        "",
    ]

    header = "| byte SID | `uk` | `ukr` | Виклик | Тип | Що робить | Основа |"
    separator = "|---:|---|---|---|---|---|---|"

    for category, category_rows in grouped.items():
        if not category_rows:
            continue
        out.extend([f"### {CATEGORY_TITLES[category]}", "", header, separator])
        for row in category_rows:
            surfaces = table.get(row.identity)
            if surfaces is None:
                raise SystemExit(f"function table missing documented semantic ID {row.identity}")
            uk = surfaces.get("uk")
            ukr = surfaces.get("ukr")
            en = surfaces.get("en")
            sym = surfaces.get("sym")
            if uk is None or uk.word == "()" or uk.word == "—":
                raise SystemExit(f"documented semantic ID {row.identity} has no uk surface")
            if ukr is None or ukr.word == "()" or ukr.word == "—":
                raise SystemExit(f"function table missing ukr projection for {row.identity}")
            basis = en.word if en is not None and en.word not in ("()", "—") else (
                sym.word if sym is not None and sym.word not in ("()", "—") else "—"
            )
            out.append(
                "| "
                + " | ".join(
                    [
                        code(row.identity),
                        code(uk.word),
                        code(ukr.word),
                        code(row.call),
                        KIND_UK[row.kind],
                        md_text(row.description),
                        code(basis),
                    ]
                )
                + " |"
            )
        out.append("")

    return "\n".join(out).rstrip() + "\n\n"


def desired_document() -> str:
    current = API_DOC.read_text(encoding="utf-8")
    start = current.find(START)
    end = current.find(END)
    if start < 0 or end < 0 or end <= start:
        raise SystemExit("docs/ukrainian-api.md is missing detailed-reference boundaries")
    generated = render_reference(parse_docs_index(), parse_function_table())
    return current[:start] + generated + current[end:]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="fail if committed Markdown differs")
    args = parser.parse_args()

    current = API_DOC.read_text(encoding="utf-8")
    desired = desired_document()
    if args.check:
        if current == desired:
            print("ukrainian-api: in sync")
            return 0
        diff = "".join(
            difflib.unified_diff(
                current.splitlines(keepends=True),
                desired.splitlines(keepends=True),
                fromfile=str(API_DOC),
                tofile="generated",
            )
        )
        print(diff)
        return 1

    API_DOC.write_text(desired, encoding="utf-8")
    print("ukrainian-api: generated 140 documented identities")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
