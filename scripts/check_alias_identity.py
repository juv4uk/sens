#!/usr/bin/env python3
"""Українські викличні назви повинні мати однозначну точнодоменну адресу.

Читаємо тільки ратифіковані D1–D10. D7 — текстова клавіатура, не функції.
«en», «san» і «sym» — людські / історичні проєкції; їхні повтори
не дають права вибирати першу відповідну функцію (fail closed у reader).
Цей інструмент перевіряє таблиці, але не виконує програму SENS.
"""
from __future__ import annotations

import argparse
import importlib.util
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "scripts/check_semantic_registry.py"
NAMESPACES = ("ук", "укр")


def load_audit():
    spec = importlib.util.spec_from_file_location("sens_domain_registry_audit", AUDIT)
    if spec is None or spec.loader is None:
        raise ValueError("неможливо завантажити перевірку точних доменів")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def check(root: Path) -> list[str]:
    audit = load_audit()
    owners: dict[tuple[str, str], list[str]] = defaultdict(list)
    problems = []
    for width in range(1, 11):
        path = root / f"lib/domains/d{width}.lisp"
        try:
            forms = audit.parse_all(audit.tokens(path.read_text(encoding="utf-8")))
            if len(forms) != 1:
                raise ValueError("рівно одна таблиця на домен")
            table = forms[0]
            audit.check(table, width)
        except (OSError, ValueError) as error:
            problems.append(f"D{width}: {error}")
            continue
        if width == 7:
            continue  # Сім бітів — текст, а не функціональний код.
        for record in table[1:]:
            identity = f"D{width}:{record[0]}"
            for namespace in NAMESPACES:
                field = next((v for v in record[1:] if v[0] == namespace), None)
                if field is None:
                    problems.append(f"{identity}: відсутня {namespace}")
                    continue
                name = field[1]
                if name != []:
                    owners[(namespace, name)].append(identity)
    for (namespace, name), identities in sorted(owners.items()):
        if len(identities) > 1:
            problems.append(
                f"АЛІАС-НЕОДНОЗНАЧНИЙ ({namespace} {name}): "
                + ", ".join(identities)
            )
    return problems


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", default=str(ROOT))
    args = parser.parse_args()
    issues = check(Path(args.root).resolve())
    if issues:
        print(f"ALIAS_AMBIGUOUS count={len(issues)}")
        for issue in issues:
            print(" -", issue)
        return 1
    print("ALIAS_IDENTITY_OK ук/укр → єдина точна (домен, біти) з D1–D10")
    print("en/san/sym не використовуються як неявні викличні ідентичності")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
