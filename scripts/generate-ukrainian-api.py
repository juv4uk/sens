#!/usr/bin/env python3
"""Generate human API documentation from exact D1–D10 identities and full укр.

The documentation index contains canonical Dn:bits keys and their explicit
full Ukrainian projection. The ratified domain tables are the only authority.
No historical SID8 / Function8 table participates in the join.
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
API_DOC = ROOT / "docs/ukrainian-api.md"

START = "## Повний довідник"
END = "## Межа довідника"

DOC_RE = re.compile(
    r'^\s*\(doc\s+(\S+)\s+(D(?:[1-9]|10):[01]+)\s+([^\s()]+)\s+(\S+)\s+"((?:\\.|[^"\\])*)"\s+"((?:\\.|[^"\\])*)"\)\s*$'
)
SURFACE_RE = re.compile(r"\((ук|укр|en|sym)\s+(\(\)|[^\s)]+)\)")
ROW_RE = re.compile(r'^\s*\(([01]+)\s')

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
    ukr: str
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
    if "(schema uk-api-docs-4)" not in source:
        raise SystemExit("uk-docs.lisp має використовувати чинну схему uk-api-docs-4")

    rows: list[DocRow] = []
    for line in source.splitlines():
        if not line.lstrip().startswith("(doc "):
            continue
        match = DOC_RE.match(line)
        if not match:
            raise SystemExit(f"cannot parse documentation row: {line}")
        category, identity, ukr, kind, call, description = match.groups()
        domain, bits = identity.split(":", 1)
        if len(bits) != int(domain[1:]):
            raise SystemExit(f"{identity}: невірна бітність точного домену")
        if category not in CATEGORY_TITLES:
            raise SystemExit(f"unknown documentation category {category!r} for {identity}")
        if kind not in KIND_UK:
            raise SystemExit(f"unknown documentation kind {kind!r} for {identity}")
        rows.append(
            DocRow(
                category=category,
                identity=identity,
                ukr=ukr,
                kind=kind,
                call=decode_string(call),
                description=decode_string(description),
            )
        )

    identities = [row.identity for row in rows]
    if len(rows) != 140:
        raise SystemExit(f"очікується 140 чинних точнодоменних описів, знайдено {len(rows)}")
    if len(set(identities)) != len(identities):
        raise SystemExit("у довіднику повторюється точна доменна адреса")
    return rows


def parse_domain_tables() -> dict[str, dict[str, Surface]]:
    """Read D1..D10 by exact width. No historical SID8 donor data."""
    result: dict[str, dict[str, Surface]] = {}
    for width in range(1, 11):
        table = ROOT / "lib" / "domains" / f"d{width}.lisp"
        for line in table.read_text(encoding="utf-8").splitlines():
            match = ROW_RE.match(line)
            if match is None or len(match.group(1)) != width:
                continue
            identity = f"D{width}:{match.group(1)}"
            if identity in result:
                raise SystemExit(f"повторна ратифікована адреса {identity}")
            result[identity] = {
                surface: Surface(word=word.strip('"'))
                for surface, word in SURFACE_RE.findall(line)
            }
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
        "Нижче — проєкція точних доменних ідентичностей D1–D10, а не історичних SID8. Опис береться з `lib/surface/uk-docs.lisp`, а `ук`, `укр` та назва походять безпосередньо з чинних `lib/domains/dN.lisp`. Наявність опису не доводить виконуваність.",
        "",
    ]

    header = "| Домен | `ук` | `укр` | Виклик | Тип | Що робить | Основа |"
    separator = "|---:|---|---|---|---|---|---|"

    for category, category_rows in grouped.items():
        if not category_rows:
            continue
        out.extend([f"### {CATEGORY_TITLES[category]}", "", header, separator])
        for row in category_rows:
            surfaces = table.get(row.identity)
            if surfaces is None:
                raise SystemExit(f"function table missing documented semantic ID {row.identity}")
            uk = surfaces.get("ук")
            ukr = surfaces.get("укр")
            en = surfaces.get("en")
            sym = surfaces.get("sym")
            if uk is None or uk.word == "()" or uk.word == "—":
                raise SystemExit(f"documented semantic ID {row.identity} has no uk surface")
            if ukr is None or ukr.word == "()" or ukr.word == "—":
                raise SystemExit(f"немає повної проєкції укр для {row.identity}")
            if row.ukr != ukr.word:
                raise SystemExit(f"{row.identity}: заявлена укр {row.ukr!r} не збігається з таблицею {ukr.word!r}")
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
    generated = render_reference(parse_docs_index(), parse_domain_tables())
    if start >= 0 and end > start:
        return current[:start] + generated + current[end:]
    if start >= 0 or end >= 0:
        raise SystemExit("неповна пара маркерів детального довідника")
    boundary = current.find("## Історичний Function8/SID8 індекс сумісності")
    if boundary < 0:
        raise SystemExit("немає секції відокремленого архіву сумісності")
    return current[:boundary] + generated + END + "\n\n" + current[boundary:]


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
