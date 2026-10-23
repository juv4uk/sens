#!/usr/bin/env python3
"""Guard: програма мусить спиратися на драбини D1–D10, а не винаходити наново.

Правило (AGENTS.md): при написанні програм функції беруться з D1–D10.
  • наявне — вжити (дубль заборонено);
  • немає в програмі — визначити;
  • немає в жодній драбині — кандидат D11 (далі D12…), а не локальний дубль.

ЄДИНИЙ механізм. Цей охоронець НЕ читає драбини сам і НЕ має власної логіки
розпізнавання поверхонь — він ІМПОРТУЄ наявний
`scripts/discover_domain_function_candidates.py` (load_domain_tables + aliases)
і користується ним. Так само має робити будь-який новий інструмент: спершу
шукай наявний механізм, а не плоди дубль.

Статика, fail-closed:
  • нове `(визначити <ім'я> …)` у зміненому .lisp, чиє ім'я збігається з
    ратифікованою поверхнею D1–D10 → BLOCKED (це дубль);
  • нові імена, яких немає в драбинах → КАНДИДАТИ D11 (інформативно).

Використання:
  python3 scripts/guard-domain-function-reuse.py --staged
  python3 scripts/guard-domain-function-reuse.py --paths-from FILE
  python3 scripts/guard-domain-function-reuse.py --file lib/x.lisp
  python3 scripts/guard-domain-function-reuse.py --self-test

Код виходу: 0 — дублів немає; 1 — знайдено дубль (BLOCKED); 2 — помилка вживання.
"""
from __future__ import annotations

import argparse
import importlib.util
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DISCOVER = ROOT / "scripts" / "discover_domain_function_candidates.py"

EXCLUDED_PREFIXES = (
    "lib/generated/", "lib/surface/", "lib/domains/", "lib/machine/",
    "vendor/", "benchmarks/", "tests/",
)
DEF = re.compile(r"\(визначити\s+([^\s()]+)")


def _load_discover():
    """Імпорт ЄДИНОГО механізму виявлення поверхонь — без власної копії логіки."""
    spec = importlib.util.spec_from_file_location("discover_domain_function_candidates", DISCOVER)
    if spec is None or spec.loader is None:
        raise SystemExit("GUARD-DOMAIN-REUSE: не вдалося завантажити discover_domain_function_candidates.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def ladder_names(root: Path) -> set[str]:
    """Усі людські назви поверхонь драбин — через наявний механізм."""
    discover = _load_discover()
    names: set[str] = set()
    for _domain, rows in discover.load_domain_tables(root).items():
        for row in rows:
            names.update(discover.aliases(row))
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

    ladder = ladder_names(ROOT)

    if args.self_test:
        ok = len(ladder) > 1000
        print(f"GUARD-DOMAIN-REUSE self-test: {'OK' if ok else 'FAIL'} (поверхонь у драбинах: {len(ladder)}, джерело: discover_domain_function_candidates)")
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
            (blocked if name in ladder else candidates).append((rel, name))

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
