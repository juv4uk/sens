#!/usr/bin/env python3
"""Карта тестів: якою мовою написаний і ЩО перевіряє.

Правило власника (23.10.2026):
  механізм Rust  → Rust-тест
  механізм Zig   → Zig-тест
  мова/семантика/логіка → Lisp-тест (який кодек перетворює в SENS)
  інструменти (чекери, аудити, приводи) → лишаються Python-обслугою

Цей скрипт НЕ блокує нічого. Він дає числа: скільки тестів якою мовою, і де
мова перевіряється не тою мовою, якою мусить. Мета — не новий блокер, а карта,
за якою видно, куди рухатись.

    python3 scripts/audit-test-languages.py
    python3 scripts/audit-test-languages.py --json
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Голови мови (укр-проєкція) — якщо вони є в хостовому тесті, тест несе САМУ МОВУ
LANG_HEADS = ("визначити", "функція", "за-умовою", "як-є", "сполучити", "перше", "решта")
LANG_RE = re.compile(r"\((?:%s)\b" % "|".join(LANG_HEADS))
# ознаки, що тест стосується МЕХАНІЗМУ, а не мови
MECH_RUST = re.compile(r"rust|cargo|corridor|arena|ffi|abi", re.I)
MECH_ZIG = re.compile(r"zig|t5m|codec|трит|трійков", re.I)


def tracked(pattern: str) -> list[str]:
    out = subprocess.run(["git", "-c", "core.quotepath=false", "ls-files", pattern],
                         cwd=ROOT, capture_output=True, text=True).stdout
    return [ln.strip() for ln in out.splitlines() if ln.strip()]


def classify(path: str) -> str:
    """Куди тест мусить належати за правилом власника."""
    low = path.lower()
    if MECH_ZIG.search(low):
        return "механізм-Zig→Zig"
    if MECH_RUST.search(low):
        return "механізм-Rust→Rust"
    if "semantic" in low or "law" in low or "logic" in low:
        return "мова→Lisp"
    return "інструмент→Python (обслуга)"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="карта тестів за мовою")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    rust = [p for p in tracked("crates/*/tests/*.rs") + tracked("tests/*.rs")]
    zig = [p for p in tracked("*.zig") if "test" in p.lower()]
    lisp = tracked("tests/semantic/*.lisp")
    py = tracked("tests/*.py")

    # верхня межа: скільки Python-тестів ЗГАДУЮТЬ голови мови (більшість — чекери,
    # що шукають ці голови; це НЕ доказ, що мова живе в хості)
    py_with_lang = []
    for p in py:
        f = ROOT / p
        try:
            t = f.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        if LANG_RE.search(t):
            py_with_lang.append(p)

    counts = {
        "rust": len(rust), "zig": len(zig), "lisp": len(lisp),
        "python": len(py), "python_згадує_голови": len(py_with_lang),
    }
    if args.json:
        print(json.dumps({"counts": counts, "python_that_carry_language": py_with_lang},
                         ensure_ascii=False, indent=1))
        return 0

    print("КАРТА ТЕСТІВ ЗА МОВОЮ")
    print(f"  Rust (механізм):            {counts['rust']}")
    print(f"  Zig (механізм):             {counts['zig']}")
    print(f"  Lisp (мова/семантика):      {counts['lisp']}")
    print(f"  Python (обслуга):           {counts['python']}")
    print()
    print(f"Python-тести, що ЗГАДУЮТЬ голови мови (шаблони/дані — НЕ обов'язково несуть мову): {len(py_with_lang)}")
    print("  (це ВЕРХНЯ межа: більшість — чекери, що шукають ці голови; справжніх «мова в хості» менше)")
    for p in py_with_lang[:12]:
        print(f"  {p}  →  {classify(p)}")
    if len(py_with_lang) > 12:
        print(f"  … ще {len(py_with_lang) - 12}")
    print()
    print("Правило: механізм Rust→Rust, механізм Zig→Zig, мова→Lisp, інструменти→Python.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
