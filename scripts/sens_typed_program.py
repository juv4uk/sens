#!/usr/bin/env python3
"""Історичний типізований перегляд, тільки діагностика; Zig/T5M карбує .sens.

Машина читає програму НЕ як текст і не як телеграфний wire-запис, а як
послідовність ЯВНО типізованих доменних слів: кожне слово несе свій домен
(D1..D9) і рівно свою ширину біт. Драбина тут явна в тезі, а не виведена з
ширини. Кодує кодек репо (scripts/sens_t5_t5m_codec.encode_typed_domain_words).

Формат вхідного файлу: по одному слову в рядку, "<Dn> <bits>", напр.:
    D2 10
    D4 1000
    D2 00

Wire-запис ("10 1000 00 ...", слова через пробіл) -- то форма для передачі
по телеграфу; вона читається окремо (sens_view.py / sens-trit open) і не є
машинною формою.

Використання:
    python3 scripts/sens_typed_program.py emit <program.typed> <out.sens>  # заборонено; Zig/T5M
    python3 scripts/sens_typed_program.py wire <out.sens>       # телеграфний запис
    python3 scripts/sens_typed_program.py selftest              # caar == фікстура
"""
from __future__ import annotations
import argparse
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import sens_t5_t5m_codec as C  # noqa: E402

TAG = __import__("re").compile(r"D[1-9]\Z")


def parse_typed(text: str) -> list[tuple[str, str]]:
    """Fail-closed: рівно '<Dn> <bits>', D1..D9, біти точної ширини домену."""
    out: list[tuple[str, str]] = []
    for lineno, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith(";"):
            continue
        parts = line.split()
        if len(parts) != 2:
            raise C.SensT5Error(f"рядок {lineno}: очікую '<Dn> <bits>', маю {line!r}")
        domain, bits = parts
        if not TAG.fullmatch(domain):
            raise C.SensT5Error(f"рядок {lineno}: домен мусить бути D1..D9, маю {domain!r}")
        out.append((domain, bits))
    if not out:
        raise C.SensT5Error("порожня типізована програма")
    return out


def emit(typed_path: pathlib.Path) -> bytes:
    return C.encode_typed_domain_words(parse_typed(typed_path.read_text(encoding="utf-8")))


def selftest() -> None:
    repo = pathlib.Path(__file__).resolve().parents[1]
    fixture = repo / "tests/fixtures/migration-d4-selector-cohort/caar.sens"
    if not fixture.exists():
        print("selftest: фікстуру не знайдено — пропуск")
        return
    ref = fixture.read_bytes()
    # caar у типізованих доменних словах
    typed = [
        ("D2", "10"), ("D4", "1000"), ("D2", "00"),
        ("D2", "10"), ("D3", "111"), ("D2", "00"),
        ("D2", "10"), ("D3", "111"), ("D2", "00"),
        ("D2", "10"), ("D3", "001"), ("D2", "00"), ("D3", "000"), ("D2", "01"),
        ("D2", "00"),
        ("D2", "10"), ("D3", "001"), ("D2", "00"), ("D3", "000"), ("D2", "01"),
        ("D2", "01"), ("D2", "00"),
        ("D2", "10"), ("D3", "001"), ("D2", "00"), ("D3", "000"), ("D2", "01"),
        ("D2", "01"), ("D2", "01"),
    ]
    got = C.encode_typed_domain_words(typed)
    if got != ref:
        raise SystemExit("selftest ПРОВАЛ: typed-caar != фікстура")
    print(f"selftest OK: typed-caar == {fixture.name} ({len(ref)} Б, байт-у-байт)")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    e = sub.add_parser("emit"); e.add_argument("typed"); e.add_argument("out")
    w = sub.add_parser("wire"); w.add_argument("sens")
    sub.add_parser("selftest")
    a = ap.parse_args()
    if a.cmd == "emit":
        # Застарілий Python-кодек може бути лише еталонною перевіркою:
        # він не є власником фізичних файлів сучасної мови.
        print("LEGACY_PYTHON_T5M_PUBLICATION_DISABLED: "
              "use migrate-one-to-sens.py and pinned Zig/T5M", file=sys.stderr)
        return 2
    elif a.cmd == "wire":
        # Чинний фізичний носій — T5M, а не історичний T5.
        print(" ".join(C.decode_t5m_bytes(pathlib.Path(a.sens).read_bytes())))
    else:
        selftest()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
