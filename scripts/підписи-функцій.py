#!/usr/bin/env python3
"""Підписи функцій — контракт, який агент може прочитати до того, як писати.

Лікує хворобу калькулятора: слово «тест» без ЦІЛІ розв'язується в найближчий
канонічний приклад, бо агент не бачить, ЩО в проєкті вже є і з якими
аргументами. Підпис робить ціль видимою: `(текст-у-символ текст)` каже
більше, ніж будь-який опис.

Джерело істини — згенерована таблиця сигнатур (не власний парсер мови):
  crates/sens/src/function_signatures_generated.rs
    FunctionSignature { semantic_id: …, kind: …, arity: …,
                        signature: "(текст-у-символ текст)",
                        documentation: "Створити символ із текстового рядка" }

Режими:
  --list [N]      перші N підписів
  --find ЗАПИТ    пошук за іменем або описом
  --stats         скільки сигнатур, скільки з описом
  --self-test     самоперевірка розбору
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TABLE = ROOT / "crates" / "sens" / "src" / "function_signatures_generated.rs"

ROW = re.compile(
    r"FunctionSignature\s*\{[^}]*?"
    r'signature:\s*"(?P<sig>(?:[^"\\]|\\.)*)"\s*,\s*'
    r'documentation:\s*"(?P<doc>(?:[^"\\]|\\.)*)"',
    re.S,
)


def load() -> list[tuple[str, str]]:
    """[(підпис, опис)] із згенерованої таблиці."""
    if not TABLE.exists():
        raise SystemExit(f"НЕ ВИМІРЯНО: немає {TABLE.relative_to(ROOT)}")
    text = TABLE.read_text(encoding="utf-8", errors="ignore")
    out = []
    for row in ROW.finditer(text):
        sig = row.group("sig").replace('\\"', '"')
        doc = row.group("doc").replace('\\"', '"')
        out.append((sig, doc))
    return out


def split_signature(sig: str) -> tuple[str, list[str]]:
    """`(текст-у-символ текст)` → («текст-у-символ», [«текст»])."""
    inner = sig.strip()
    if inner.startswith("(") and inner.endswith(")"):
        inner = inner[1:-1]
    parts = inner.split()
    if not parts:
        return ("", [])
    return (parts[0], parts[1:])


def self_test() -> int:
    ok = True
    cases = [
        ("(текст-у-символ текст)", ("текст-у-символ", ["текст"])),
        ("(eq a b)", ("eq", ["a", "b"])),
        ("(порожній?)", ("порожній?", [])),
        ("()", ("", [])),
    ]
    for sig, expected in cases:
        got = split_signature(sig)
        good = got == expected
        print(("OK    " if good else "ЗБІЙ  ") + f"{sig} → {got}")
        ok = ok and good
    print("SELF-TEST:", "OK" if ok else "FAILED")
    return 0 if ok else 1


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--list", nargs="?", const=25, type=int, default=None, metavar="N")
    ap.add_argument("--find", metavar="ЗАПИТ")
    ap.add_argument("--stats", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args(argv)

    if args.self_test:
        return self_test()
    if args.list is None and not args.find and not args.stats:
        ap.print_help()
        return 2

    rows = load()
    if not rows:
        print("НЕ ВИМІРЯНО: таблиця сигнатур порожня")
        return 2

    if args.stats:
        with_doc = sum(1 for _, doc in rows if doc.strip())
        print("ПІДПИСИ ФУНКЦІЙ")
        print(f"  усього:        {len(rows)}")
        print(f"  з описом:      {with_doc}  ({100 * with_doc / len(rows):.1f}%)")
        print(f"  без опису:     {len(rows) - with_doc}")
        return 0

    if args.find:
        q = args.find.lower()
        hits = [(s, d) for s, d in rows if q in s.lower() or q in d.lower()]
        print(f"ПІДПИСИ за запитом «{args.find}» — знайдено {len(hits)}:")
        for sig, doc in hits[:40]:
            name, args_ = split_signature(sig)
            print(f"  {name} ({' '.join(args_)})" + (f"  — {doc}" if doc else ""))
        return 0

    print(f"ПІДПИСИ (перші {min(args.list, len(rows))}):")
    for sig, doc in rows[: args.list]:
        name, args_ = split_signature(sig)
        print(f"  {name} ({' '.join(args_)})" + (f"  — {doc}" if doc else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
