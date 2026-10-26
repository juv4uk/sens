#!/usr/bin/env python3
"""Коефіцієнт перевикористання драбини d1–d10.

Питання, на яке відповідає: коли в проєкті з'являється НОВЕ визначення
функції — чи воно бере вже наявну функцію драбини, чи вигадує власну?

Метрика рахується з історії git, а не з поточного знімка, тож показує
ТЕНДЕНЦІЮ, а не лише «зараз».

  reuse rate = (нові визначення, що викликають ≥1 функцію драбини)
               / (усі нові визначення)

Джерело істини для імен драбини — scripts/discover_domain_function_candidates.py
(той самий, що вживає охоронець). Другого сканера драбин тут НЕ заводимо.

Режими:
  --rate [--since REF] [--max N]   коефіцієнт перевикористання за комітами
  --self-test                      самоперевірка метрики на синтетиці
"""

from __future__ import annotations

import argparse
import importlib.util
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DISCOVER = ROOT / "scripts" / "discover_domain_function_candidates.py"

# Голови, які є БУДОВОЮ форми, а не вживанням операції.
# Лише СПРАВЖНЯ будова форми. `перше`, `решта`, `список`, `сполучити` —
# це функції драбини (D3/D4), а не синтаксис; раніше вони стояли тут
# помилково, і самоперевірка це зловила.
STRUCTURAL = {
    "визначити", "функція", "макрос", "як-є", "за-умовою", "нехай",
    "нехай-послідовно",
}

DEFINE_RE = re.compile(r"\(\s*(?:визначити|defmacro|defun)\s+([^\s()]+)")
HEAD_RE = re.compile(r"\(\s*([^\s()]+)")


def load_ladder_names() -> set[str]:
    """Українські імена поверхонь d1–d11 із наявного джерела істини."""
    if not DISCOVER.exists():
        return set()
    spec = importlib.util.spec_from_file_location("discover", DISCOVER)
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)  # type: ignore[union-attr]
    except Exception:
        return set()
    names: set[str] = set()
    for attr in ("load_domain_tables", "domain_tables", "TABLES"):
        obj = getattr(module, attr, None)
        if obj is None:
            continue
        try:
            tables = obj() if callable(obj) else obj
        except Exception:
            continue
        if isinstance(tables, dict):
            for rows in tables.values():
                for row in rows:
                    for key in ("uk", "ук", "en", "LISP", "sym"):
                        value = row.get(key) if isinstance(row, dict) else None
                        if isinstance(value, str) and value:
                            names.add(value)
        if names:
            break
    return names


def ladder_names_fallback() -> set[str]:
    """Запасний шлях: прочитати укр. стовпець таблиць доменів напряму."""
    names: set[str] = set()
    for path in sorted((ROOT / "lib" / "domains").glob("d*.lisp")):
        if not re.fullmatch(r"d\d+\.lisp", path.name):
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        names.update(re.findall(r"\(ук\s+([^\s()]+)", text))
    return names


def added_definitions(patch: str) -> list[tuple[str, list[str]]]:
    """З diff-у витягнути додані визначення та голови їхніх тіл."""
    out: list[tuple[str, list[str]]] = []
    current: str | None = None
    heads: list[str] = []
    for line in patch.splitlines():
        if not line.startswith("+") or line.startswith("+++"):
            continue
        body = line[1:]
        match = DEFINE_RE.search(body)
        if match:
            if current is not None:
                out.append((current, heads))
            current = match.group(1)
            # Голови тіла можуть бути на ТОМУ САМОМУ рядку, що й визначити —
            # саме на цьому самоперевірка й зловила помилку.
            rest = body[match.end():]
            heads = [h for h in HEAD_RE.findall(rest) if h not in STRUCTURAL]
            continue
        if current is not None:
            heads.extend(h for h in HEAD_RE.findall(body) if h not in STRUCTURAL)
    if current is not None:
        out.append((current, heads))
    return out


def measure(since: str, limit: int) -> dict:
    names = load_ladder_names() or ladder_names_fallback()
    if not names:
        return {"error": "не знайдено імен драбини"}
    cmd = [
        "git", "-C", str(ROOT), "log", f"--max-count={limit}", "--no-merges",
        "--unified=0", "--format=%x00%h %s", "-p",
    ]
    if since:
        cmd.append(f"{since}..HEAD")
    try:
        raw = subprocess.run(cmd, capture_output=True, text=True, timeout=180).stdout
    except (OSError, subprocess.SubprocessError) as exc:
        return {"error": f"git недоступний: {exc}"}

    total = reused = 0
    per_commit: list[tuple[str, int, int]] = []
    for chunk in raw.split("\x00"):
        if not chunk.strip():
            continue
        head, _, patch = chunk.partition("\n")
        defs = added_definitions(patch)
        if not defs:
            continue
        c_total = len(defs)
        c_reused = sum(1 for _, heads in defs if any(h in names for h in heads))
        total += c_total
        reused += c_reused
        per_commit.append((head.strip()[:60], c_total, c_reused))

    rate = (reused / total * 100) if total else 0.0
    return {
        "ladder_names": len(names),
        "commits": len(per_commit),
        "definitions": total,
        "reused": reused,
        "rate": rate,
        "worst": sorted(per_commit, key=lambda x: (x[2] / x[1] if x[1] else 0))[:5],
        "best": sorted(per_commit, key=lambda x: -(x[2] / x[1] if x[1] else 0))[:5],
    }


def self_test() -> int:
    """Самоперевірка: метрика мусить рахувати рівно те, що заявлено."""
    ok = True
    names = {"перше", "решта", "довжина"}
    patch = (
        "+ (визначити моя-функція (функція (x) (перше x)))\n"
        "+ (визначити інша (функція (x) (моя-хелпер x)))\n"
        "+ (визначити третя (функція (x) (довжина x)))\n"
    )
    defs = added_definitions(patch)
    reused = sum(1 for _, heads in defs if any(h in names for h in heads))
    checks = [
        ("знайдено 3 визначення", len(defs) == 3),
        ("перевикористано 2 з 3", reused == 2),
        ("структурні голови не рахуються", all("функція" not in h for _, hs in defs for h in hs)),
    ]
    for label, good in checks:
        print(("OK   " if good else "ЗБІЙ ") + label)
        ok = ok and good
    print("SELF-TEST:", "OK" if ok else "FAILED")
    return 0 if ok else 1


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--rate", action="store_true", help="порахувати коефіцієнт перевикористання")
    ap.add_argument("--since", default="", help="від якого REF (типово: уся доступна історія)")
    ap.add_argument("--max", type=int, default=200, help="скільки комітів узяти")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args(argv)

    if args.self_test:
        return self_test()
    if not args.rate:
        ap.print_help()
        return 2

    data = measure(args.since, args.max)
    if "error" in data:
        print(f"НЕ ВДАЛОСЯ: {data['error']}")
        return 2

    print("ПЕРЕВИКОРИСТАННЯ ДРАБИНИ d1–d11")
    print(f"  імен драбини:        {data['ladder_names']}")
    print(f"  комітів із новими:   {data['commits']}")
    print(f"  нових визначень:     {data['definitions']}")
    print(f"  з них узяли драбину: {data['reused']}")
    print(f"  КОЕФІЦІЄНТ:           {data['rate']:.1f}%")
    if data["worst"]:
        print("\n  найгірші коміти (0% = вигадували своє):")
        for head, total, reused in data["worst"]:
            print(f"    {reused}/{total}  {head}")
    if data["best"]:
        print("\n  найкращі коміти (усе з драбини):")
        for head, total, reused in data["best"]:
            print(f"    {reused}/{total}  {head}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
