#!/usr/bin/env python3
"""Guard: програма мусить спиратися на драбини D1–D10, а не винаходити наново.

Правило (AGENTS.md): при написанні програм функції беруться з D1–D10.
  • якщо потрібна операція вже визначена — вжити наявну (дубль заборонено);
  • якщо функція ще не визначена в програмі — визначити її;
  • якщо такої функції немає в жодній драбині — додати її як кандидата D11
    (а коли з'явиться D12 — як кандидата D12), а не писати локальний дубль.

Що перевіряє цей guard (статика, fail-closed):
  1. Кожне нове top-level визначення `(визначити <ім'я> …)` у змінених .lisp,
     чиє ім'я ЗБІГАЄТЬСЯ з уже ратифікованою поверхнею D1–D10, — це ДУБЛЬ
     (BLOCKED), бо наявне треба вживати, а не перевизначати.
  2. Нові імена, яких немає в драбинах, друкуються як КАНДИДАТИ D11 —
     інформативно, щоб їх було внесено в пропозиції, а не загублено в коді.

Джерело влади над поверхнями: lib/domains/d1.lisp … d10.lisp.

Використання:
  python3 scripts/guard-domain-function-reuse.py --staged
  python3 scripts/guard-domain-function-reuse.py --paths-from FILE
  python3 scripts/guard-domain-function-reuse.py --file lib/x.lisp [--file ...]
  python3 scripts/guard-domain-function-reuse.py --self-test

Код виходу: 0 — дублів немає; 1 — знайдено дубль (BLOCKED); 2 — помилка вживання.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED_PREFIXES = (
    "lib/generated/", "lib/surface/", "lib/domains/", "lib/machine/",
    "vendor/", "benchmarks/", "tests/",
)
ROW = re.compile(r"^\s*\(([01]{3,})\s+(.*)\)\s*$")
COL = re.compile(r"\((ук|укр|san|en|LISP|sym)\s+(.*?)\)")
DEF = re.compile(r"\(визначити\s+([^\s()]+)")


def ladder_names() -> set[str]:
    names: set[str] = set()
    for path in sorted((ROOT / "lib" / "domains").glob("d*.lisp")):
        if not re.fullmatch(r"d\d+", path.stem):
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            m = ROW.match(line)
            if not m:
                continue
            for cm in COL.finditer(m.group(2)):
                v = cm.group(2).strip()
                if re.fullmatch(r"[^()\s]+", v):
                    names.add(v)
    return names


def definitions(text: str) -> list[str]:
    return [m.group(1) for m in DEF.finditer(text)]


def changed_files(args) -> list[str]:
    if args.file:
        return list(args.file)
    if args.paths_from:
        return [ln.strip() for ln in Path(args.paths_from).read_text(encoding="utf-8").splitlines() if ln.strip()]
    if args.staged:
        out = subprocess.run(
            ["git", "-c", "core.quotepath=false", "diff", "--name-only", "--cached"],
            cwd=ROOT, capture_output=True, text=True, check=False,
        ).stdout
        return [ln.strip() for ln in out.splitlines() if ln.strip()]
    return []


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="guard: вживати функції драбин D1–D10")
    ap.add_argument("--staged", action="store_true")
    ap.add_argument("--paths-from")
    ap.add_argument("--file", action="append")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args(argv)

    ladder = ladder_names()

    if args.self_test:
        ok = len(ladder) > 1000  # драбини D1–D10 разом дають тисячі людських назв
        print(f"GUARD-DOMAIN-REUSE self-test: {'OK' if ok else 'FAIL'} (поверхонь у драбинах: {len(ladder)})")
        return 0 if ok else 1

    if not (args.staged or args.paths_from or args.file):
        ap.error("потрібен --staged / --paths-from / --file")

    blocked: list[tuple[str, str]] = []
    candidates: list[tuple[str, str]] = []
    checked = 0
    for rel in changed_files(args):
        if not rel.endswith(".lisp"):
            continue
        if any(rel.startswith(p) for p in EXCLUDED_PREFIXES):
            continue
        path = ROOT / rel
        if not path.is_file():
            continue
        checked += 1
        for name in definitions(path.read_text(encoding="utf-8")):
            if name in ladder:
                blocked.append((rel, name))
            else:
                candidates.append((rel, name))

    for rel, name in candidates:
        print(f"КАНДИДАТ D11: {rel}: {name} — немає в драбинах; внеси в пропозиції D11 (далі D12…), не лишай локальним дублем")

    if blocked:
        for rel, name in blocked:
            print(f"BLOCKED: {rel}: «{name}» вже є ратифікованою поверхнею D1–D10 — вжий наявну, не перевизначай")
        print(f"GUARD-DOMAIN-REUSE: BLOCKED ({len(blocked)} дублів серед {checked} файлів)")
        return 1

    print(f"GUARD-DOMAIN-REUSE: OK ({checked} файлів перевірено, {len(candidates)} кандидатів D11)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
