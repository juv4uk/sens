#!/usr/bin/env python3
"""Точнодоменний свідок для всіх 2046 координат D1–D10.

Бітність адреси є частиною identity: D3:001 ≠ D4:0001.
Перевірки: повнота 2**n, унікальність, ширина, Hamming-1 сусіди,
оборотність побітового пакування та ін'єктивність людських поверхонь.
Це доказ структури кодової книги, НЕ доказ виконуваності резидентів.

Запуск:
    python3 scripts/check-domain-bitness-witness.py
    python3 scripts/check-domain-bitness-witness.py --self-test
"""
from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
SURFACES = ("uk", "ukr", "san", "en", "sym")


def bit_pack_roundtrip(words: list[str], width: int) -> tuple[int, bool]:
    """Відтворити корисні біти щільного потоку; межі задає відомий Dn."""
    stream = "".join(words)
    length = len(stream)
    if not length:
        return 0, True
    pad = (-length) % 8
    data = int(stream + "0" * pad, 2).to_bytes((length + pad) // 8, "big")
    restored = "".join(f"{byte:08b}" for byte in data)[:length]
    slices = [restored[i:i + width] for i in range(0, length, width)]
    return len(data), slices == words


def check_rows(width: int, rows: list) -> dict:
    """Чиста перевірка: мутовані fixtures не залежать від файлового reader."""
    if not 1 <= width <= 10:
        raise ValueError(f"недопустима ширина D{width}")
    expected = 1 << width
    words = [row.bits for row in rows]
    valid = [b for b in words if len(b) == width and set(b) <= {"0", "1"}]
    seen = set(valid)
    bad_width = [f"{b!r} (очікується {width} біт)" for b in words if b not in valid]
    duplicates = sorted({b for b in valid if valid.count(b) > 1})
    missing = sorted({f"{i:0{width}b}" for i in range(expected)} - seen)

    # len(flipped) == n є тавтологією; потрібен інший НАЯВНИЙ резидент.
    bad_bit: list[str] = []
    bit_checks = 0
    for bits in valid:
        for i in range(width):
            flipped = bits[:i] + ("1" if bits[i] == "0" else "0") + bits[i + 1:]
            bit_checks += 1
            if flipped == bits or flipped not in seen:
                bad_bit.append(f"{bits} → {flipped} (відсутній/тотожний сусід)")

    collisions: list[str] = []
    surfaces: dict[str, dict[str, str]] = {s: {} for s in SURFACES}
    for row in rows:
        for name in SURFACES:
            value = getattr(row, name)
            if not value:
                continue
            previous = surfaces[name].setdefault(value, row.bits)
            if previous != row.bits:
                collisions.append(f"{name}:{value!r} у {previous} і {row.bits}")

    pack_bytes, pack_ok = bit_pack_roundtrip(valid, width)
    return {
        "domain": f"D{width}",
        "width": width,
        "residents": len(rows),
        "expected": expected,
        "word_checks": len(words),
        "bit_checks": bit_checks,
        "bad_width": bad_width,
        "bad_bit": bad_bit,
        "duplicates": duplicates,
        "missing": missing,
        "collisions": collisions,
        "pack_bytes": pack_bytes,
        "pack_ok": pack_ok,
    }


def check_domain(path: Path) -> dict:
    """Побудувати свідок для актуальної канонічної таблиці Dn."""
    sys.path.insert(0, str(ROOT / "scripts"))
    from domain_tables import read_domain_table  # noqa: PLC0415
    return check_rows(int(path.stem.removeprefix("d")), read_domain_table(path))


def problems(result: dict) -> list[str]:
    errors = [
        f"кількість: {result['residents']} замість {result['expected']}"
    ] if result["residents"] != result["expected"] else []
    for name in ("bad_width", "bad_bit", "duplicates", "missing", "collisions"):
        errors.extend(f"{name}: {s}" for s in result[name][:3])
    if not result["pack_ok"]:
        errors.append("побітове пакування втратило ідентичність")
    return errors


def self_test() -> int:
    """Негативний контроль самого перевіряльника, без assert/-O обходу."""
    rows = [SimpleNamespace(bits=f"{i:03b}", uk=f"слово-{i}",
                            ukr=None, san=None, en=None, sym=None)
            for i in range(8)]
    cases = {
        "канонічний D3": (rows, False),
        "втрачений сусід": (rows[:-1], True),
        "подвійна координата": (rows[:1] + [SimpleNamespace(**{**vars(rows[1]), "bits": "000"})] + rows[2:], True),
        "неправильна ширина": ([SimpleNamespace(**{**vars(rows[0]), "bits": "0000"})] + rows[1:], True),
        "колізія поверхонь": ([rows[0], SimpleNamespace(**{**vars(rows[1]), "uk": rows[0].uk})] + rows[2:], True),
    }
    for label, (test_rows, should_fail) in cases.items():
        failed = bool(problems(check_rows(3, test_rows)))
        if failed != should_fail:
            print(f"SELF-TEST FAIL: {label} (очікувався fail={should_fail})")
            return 1
        print(f"SELF-TEST PASS: {label}")
    if ("D3", "001") == ("D4", "0001"):
        print("SELF-TEST FAIL: домен загублено у identity")
        return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args == ["--self-test"]:
        return self_test()
    if args:
        print("Невідомі аргументи; допустимо лише --self-test", file=sys.stderr)
        return 2

    sys.path.insert(0, str(ROOT / "scripts"))
    from domain_tables import CURRENT_HUMAN_TABLES  # noqa: PLC0415
    results = []
    for path in CURRENT_HUMAN_TABLES:
        try:
            results.append(check_domain(path))
        except (OSError, ValueError) as exc:
            print(f"DOMAIN-BITNESS: FAIL-CLOSED {path}: {exc}")
            return 1

    print("домен | ширина | позицій | сусідів Hamming-1 | щільно, байтів | стан")
    print("-" * 76)
    failed = 0
    for r in results:
        errors = problems(r)
        failed += bool(errors)
        print(f"{r['domain']:>5} | {r['width']:>6} | {r['residents']:>7} | "
              f"{r['bit_checks']:>17} | {r['pack_bytes']:>14} | "
              f"{'FAIL' if errors else 'PASS'}")
        for issue in errors:
            print(f"      {issue}")
    print("-" * 76)
    print(f"разом: координат={sum(r['residents'] for r in results)}, "
          f"Hamming-1={sum(r['bit_checks'] for r in results)}, "
          f"щільних байтів={sum(r['pack_bytes'] for r in results)}; "
          f"доменів із помилками={failed}")
    if failed:
        print("DOMAIN-BITNESS: FAIL")
        return 1
    print("DOMAIN-BITNESS: PASS — структурний доказ, НЕ допуск до виконання")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
