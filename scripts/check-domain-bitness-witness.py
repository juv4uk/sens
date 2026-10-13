#!/usr/bin/env python3
"""Свідок бітності домену — точковий інформативний тест.

Ми цінуємо кожен біт: домен Dn має бути ТОЧНО n біт, і межа домену
має триматися на рівні біта, а не назви. Наявні стра́жі перевіряють
лічильники й поверхні, але НЕ перевіряють цю структурну властивість.

Три перевірки (fail-closed — будь-яка невдача = ненульовий вихід):

  1. ТОЧНІСТЬ ШИРИНИ — кожне слово таблиці Dn має рівно n біт.
  2. ЗАМКНЕНІСТЬ ЗА ОДНИМ БІТОМ — перевертання ОДНОГО біта слова Dn
     дає слово ТІЄЇ Ж ширини n (межа домену не залежить від вмісту).
  3. ТОЧНІСТЬ ПОВЕРХОНЬ — у межах одного домену кожен непорожній символ
     поверхні (ук/укр/san/en/sym) унікальний (ін'єктивність); колізія = FAIL.

Вивід — інформативна таблиця, а не «ok/fail»:
  домен | ширина | резидентів | слів-перевірок | бітових-перевірок | колізій

Це read-only: жодного файла не змінює. Запуск: python3 scripts/check-domain-bitness-witness.py
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from domain_tables import read_domain_table, CURRENT_HUMAN_TABLES  # noqa: E402

SURFACES = ("uk", "ukr", "san", "en", "sym")


def check_domain(path: Path) -> dict:
    """Повертає один рядок свідчення для одного домену Dn."""
    width = int(path.stem.removeprefix("d"))
    rows = read_domain_table(path)
    word_checks = 0
    bit_checks = 0
    bad_width: list[str] = []
    bad_bit: list[str] = []
    collisions: list[str] = []
    seen: dict[str, dict[str, str]] = {s: {} for s in SURFACES}

    for row in rows:
        bits = row.bits
        # 1. точність ширини
        word_checks += 1
        if len(bits) != width or set(bits) - {"0", "1"}:
            bad_width.append(f"{bits} (очікується {width} біт)")
            continue
        # 2. замкненість за одним бітом
        for i in range(width):
            flipped = bits[:i] + ("1" if bits[i] == "0" else "0") + bits[i + 1:]
            bit_checks += 1
            if len(flipped) != width or set(flipped) - {"0", "1"}:
                bad_bit.append(f"{bits} -> {flipped}")
        # 3. точність поверхонь (ін'єктивність у межах домену)
        for s in SURFACES:
            val = getattr(row, s)
            if not val:
                continue
            if val in seen[s] and seen[s][val] != bits:
                collisions.append(f"{s}:{val!r} у {seen[s][val]} і {bits}")
            else:
                seen[s][val] = bits

    return {
        "domain": f"D{width}",
        "width": width,
        "residents": len(rows),
        "word_checks": word_checks,
        "bit_checks": bit_checks,
        "bad_width": bad_width,
        "bad_bit": bad_bit,
        "collisions": collisions,
    }


def main() -> int:
    results = [check_domain(p) for p in CURRENT_HUMAN_TABLES]
    header = f"{'домен':>6} | {'ширина':>6} | {'резидентів':>10} | {'слів':>5} | {'бітових':>8} | {'колізій':>7} | стан"
    print(header)
    print("-" * len(header))
    failures = 0
    for r in results:
        problems = len(r["bad_width"]) + len(r["bad_bit"]) + len(r["collisions"])
        ok = problems == 0
        failures += 0 if ok else 1
        print(f"{r['domain']:>6} | {r['width']:>6} | {r['residents']:>10} | "
              f"{r['word_checks']:>5} | {r['bit_checks']:>8} | {len(r['collisions']):>7} | "
              f"{'OK' if ok else 'FAIL'}")
        for label, key in (("ширина", "bad_width"), ("біт", "bad_bit"), ("колізія", "collisions")):
            for msg in r[key][:3]:
                print(f"        {label}: {msg}")

    total_words = sum(r["word_checks"] for r in results)
    total_bits = sum(r["bit_checks"] for r in results)
    print("-" * len(header))
    print(f"разом: доменів={len(results)} слів={total_words} бітових-перевірок={total_bits} "
          f"провалів={failures}")
    if failures:
        print("DOMAIN-BITNESS: FAIL")
        return 1
    print("DOMAIN-BITNESS: PASS — кожен домен точної ширини, межа тримається на рівні біта")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
