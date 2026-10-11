#!/usr/bin/env python3
"""Вичерпний скінченний свідок Рамки-3: усі 3^0 ... 3^12 потоки.

Перевіряє фізичне ранжування і синтаксичне прийняття без семантичної
ратифікації D1–D9; не змінює канонічний фізичний .sens (T5).
"""
from __future__ import annotations

import argparse
import itertools
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import носій as р

ДОКАЗ = Path(__file__).with_name("свідчення12.json")
ПОЧАТОК = (1, 0, 2)
КІНЕЦЬ = (2, 0, 1)


def носій_допускає(рядок):
    n = len(рядок)
    if n == 5:
        return рядок == (1, 0, 2, 0, 1)
    return (n >= 7 and рядок[:3] == ПОЧАТОК and рядок[-3:] == КІНЕЦЬ
            and not any(a == b == 2 for a, b in zip(рядок, рядок[1:])))


def доказ():
    рядки = []
    всього = 0
    for n in range(13):
        місткість = 0
        синтаксично_прийнято = 0
        синтаксично_відхилено = 0
        ранги = set()
        for трити in itertools.product((0, 1, 2), repeat=n):
            всього += 1
            if not носій_допускає(трити):
                continue
            місткість += 1
            число = р.ранг(трити)
            if число in ранги or р.за_рангом(n, число) != трити:
                raise AssertionError(f"Неоднозначний ранг: {n=} {число=}")
            ранги.add(число)
            слова = "".join(str(x) for x in трити).split("2")
            try:
                перевірено = р.трити_форми(слова)
            except ValueError:
                синтаксично_відхилено += 1
            else:
                if перевірено != трити:
                    raise AssertionError(f"Розбіжність фізичних слів: {n=}")
                дані = р.упакувати(слова)
                if р.розпакувати(дані) != слова:
                    raise AssertionError(f"Порушення roundtrip: {n=}")
                синтаксично_прийнято += 1
        if місткість != р.місткість(n) or ранги != set(range(місткість)):
            raise AssertionError(f"Розбіжність незалежного перебору: {n=}")
        рядки.append({
            "тритів": n, "усіх_потоків": 3 ** n,
            "допустимо_носієм": місткість,
            "синтаксично_прийнято": синтаксично_прийнято,
            "синтаксично_відхилено": синтаксично_відхилено,
        })
    return {
        "схема": "sens-ramka3-exhaustive-12/v1",
        "область": "тритові потоки 0..12; фізика та обмежена D2-рамка, не семантика",
        "перевірено_всього_потоків": всього, "рядки": рядки,
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    modes = p.add_mutually_exclusive_group(required=True)
    modes.add_argument("--check", action="store_true")
    modes.add_argument("--write", action="store_true")
    a = p.parse_args()
    звіт = json.dumps(доказ(), ensure_ascii=False, indent=2) + "\n"
    if a.write:
        ДОКАЗ.write_text(звіт, encoding="utf-8")
    elif ДОКАЗ.read_text(encoding="utf-8") != звіт:
        raise SystemExit("BLOCKED: свідчення12.json не відповідає вичерпному перебору")
    print("PASS: вичерпний перебір 0..12 тритів; звіт збігається")


if __name__ == "__main__":
    main()
