#!/usr/bin/env python3
"""Вивести D11-координату й готовий рядок для нової функції за законом домену.

Навіщо: закон D11 (selector-suffix-extension) був лише коментарем. Агент, якому
потрібна функція, якої немає в D1–D10, мусив вручну склеювати 10 біт батька з
одним бітом суфікса, сам вигадувати назви в усіх колонках і сам збирати рядок.
Це тертя. Тут — простий механізм: дай батька (координату або назву) і суфікс,
отримай координату, назви та готовий рядок для lib/domains/d11.lisp.

Закон (knowledge/d11-selector-seed.json):
    суфікс 0: батьківський селектор застосовується до голови аргументу
    суфікс 1: батьківський селектор застосовується до хвоста аргументу
    координата = 10 біт батька || 1 біт

Приклади:
    derive-d11-coordinate.py 0110000000 0
    derive-d11-coordinate.py --name решта-від-перше 1
    derive-d11-coordinate.py --from-lisp CDAAAAAAAAR 1
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEED = ROOT / "knowledge" / "d11-selector-seed.json"


def _rows() -> dict[str, str]:
    doc = json.loads(SEED.read_text(encoding="utf-8"))
    return {bits: lisp for bits, lisp in doc["rows"]}


def _d10_by_lisp() -> dict[str, str]:
    """LISP-ім'я → 10-бітна координата батька (з D10)."""
    out: dict[str, str] = {}
    path = ROOT / "lib" / "domains" / "d10.lisp"
    for line in path.read_text(encoding="utf-8").splitlines():
        m = re.match(r"\s*\(([01]{10})\s", line)
        if not m:
            continue
        bits = m.group(1)
        lm = re.search(r"\(LISP\s+([^()\s]+)\)", line)
        if lm:
            out[lm.group(1)] = bits
    return out


def _ukr(lisp: str) -> str:
    steps = lisp[1:-1]
    return "-від-".join("перше" if c == "A" else "решта" for c in steps)


def _san(lisp: str) -> str:
    steps = lisp[1:-1]
    return "-".join("ādi" if c == "A" else "śeṣa" for c in steps)


def derive(parent_bits: str, suffix: str, parent_lisp: str | None) -> dict[str, str]:
    if not re.fullmatch(r"[01]{10}", parent_bits):
        raise SystemExit(f"батько мусить бути 10 біт (D10), отримано {parent_bits!r}")
    if suffix not in ("0", "1"):
        raise SystemExit("суфікс мусить бути 0 або 1")
    coord = parent_bits + suffix
    letter = "A" if suffix == "0" else "D"  # 0 → перше(CAR), 1 → решта(CDR)
    if parent_lisp and parent_lisp.startswith("C") and parent_lisp.endswith("R"):
        lisp = "C" + letter + parent_lisp[1:]  # батько застосований до перше/решта
    else:
        lisp = (parent_lisp or "?") + ("-ПЕРШЕ" if suffix == "0" else "-РЕШТА")
    return {
        "coordinate": coord,
        "parent": parent_bits,
        "suffix": suffix,
        "lisp": lisp,
        "ukr": _ukr(lisp),
        "san": _san(lisp),
        "en": lisp.lower(),
    }


def row_line(d: dict[str, str]) -> str:
    u = d["ukr"]
    return (f'  ({d["coordinate"]} (ук {u}) (укр {u}) (san {d["san"]}) '
            f'(en {d["en"]}) (LISP {d["lisp"]}) (sym ()))')


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="вивести D11-координату за законом")
    ap.add_argument("parent", nargs="?", help="10-бітна координата батька з D10")
    ap.add_argument("suffix", nargs="?", help="0 (перше) або 1 (решта)")
    ap.add_argument("--name", help="укр-назва батька (шукається в D10)")
    ap.add_argument("--from-lisp", help="LISP-ім'я батька (напр. CDAAAAAAAAR)")
    ap.add_argument("--check", action="store_true", help="звірити з сідом, якщо координата вже є")
    args = ap.parse_args(argv)

    rows = _rows()
    by_lisp = _d10_by_lisp()
    lisp_by_bits = {b: l for l, b in by_lisp.items()}

    parent_bits = args.parent
    parent_lisp = lisp_by_bits.get(parent_bits) if parent_bits else None
    if args.from_lisp:
        parent_lisp = args.from_lisp.upper()
        parent_bits = by_lisp.get(parent_lisp)
        if parent_bits is None:
            # можливо, це вже 11-бітна похідна — тоді віднімаємо суфікс
            if len(parent_lisp) >= 3 and parent_lisp in rows.values():
                for bits, lisp in rows.items():
                    if lisp == parent_lisp:
                        parent_bits, sfx = bits[:-1], bits[-1]
                        print(f"УВАГА: {parent_lisp} — уже похідна; батько {parent_bits}, суфікс {sfx}")
                        args.suffix = args.suffix or sfx
                        break
        if parent_bits is None:
            raise SystemExit(f"батька {parent_lisp!r} немає серед D10")
    if args.name and parent_bits is None:
        for bits, line in ((b, l) for b, l in by_lisp.items()):
            pass
        # шукаємо укр-назву серед D10
        path = ROOT / "lib" / "domains" / "d10.lisp"
        for line in path.read_text(encoding="utf-8").splitlines():
            m = re.match(r"\s*\(([01]{10})\s", line)
            if m and re.search(r"\(ук\s+" + re.escape(args.name) + r"\)", line):
                parent_bits = m.group(1)
                lm = re.search(r"\(LISP\s+([^()\s]+)\)", line)
                parent_lisp = lm.group(1) if lm else None
                break
        if parent_bits is None:
            raise SystemExit(f"батька з укр-назвою {args.name!r} немає в D10")

    if not parent_bits or not args.suffix:
        ap.error("потрібні батько (координата/--name/--from-lisp) і суфікс 0|1")

    d = derive(parent_bits, args.suffix, parent_lisp)
    # Сід — авторитет назв: якщо координата вже там, беремо його LISP і перекладаємо.
    if d["coordinate"] in rows:
        d["lisp"] = rows[d["coordinate"]]
        d["ukr"] = _ukr(d["lisp"]); d["san"] = _san(d["lisp"]); d["en"] = d["lisp"].lower()
    print("D11-КООРДИНАТА:", d["coordinate"])
    print("  батько:", d["parent"], " суфікс:", d["suffix"])
    print("  назви:  ук/укр =", d["ukr"], "| san =", d["san"], "| en =", d["en"], "| LISP =", d["lisp"])
    print("  готовий рядок для lib/domains/d11.lisp:")
    print(row_line(d))
    if args.check:
        if d["coordinate"] in rows:
            print("ЗВІРКА: координата вже в сіді →", rows[d["coordinate"]], "(очікувано", d["lisp"] + ")")
        else:
            print("ЗВІРКА: координати ще немає в сіді — це новий рядок за законом")
    return 0


if __name__ == "__main__":
    sys.exit(main())
