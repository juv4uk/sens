#!/usr/bin/env python3
"""Перевірка координаційних незмінностей енкодера SENS; не мовна семантика."""
from __future__ import annotations

import argparse
from pathlib import Path
import sys


BEGIN = "<!-- SENS-ENCODER-SWARM-2026-10-10:BEGIN -->"
END = "<!-- SENS-ENCODER-SWARM-2026-10-10:END -->"

# Це тільки контроль протоколу рою. Авторитет D1–D9 лишається в SENS.
REQUIRED = (
    "**Канонічний файловий вихід:** `.sens` = **T5**",
    "**Окремий експеримент:** `.senc` = **F3/F4 тільки за явним opt-in**",
    "жодного автоматичного визначення",
    "**Три проєкції #4449:**",
    "D1–D9; D10 залишається дослідженням",
    "фізичний T5/F3/Tb-33 ≠ x86-64 ISA-кодувальник",
    "спочатку [М0 #5444]",
    "[#5439](https://github.com/juv4uk/sens/issues/5439)",
    "[#5442](https://github.com/juv4uk/sens/issues/5442)",
    "[М1 #5445]",
    "[М2 #5446]",
    "М3 [#5447]",
    "[#5443](https://github.com/juv4uk/sens/issues/5443)",
    "[епік #5438]",
    "[координатор #5440]",
    "[дослідний PR #5429]",
    "агент/напрям; issue→батько; repo+точний main SHA",
    "незалежний негативний контроль",
    "жодного прямого запису в `main`",
    "[#5041](https://github.com/juv4uk/sens/issues/5041)",
    "[#5224](https://github.com/juv4uk/sens/issues/5224)",
    "SEE_LOCAL_FIX_",
    "LOAD_FROM_FILE:",
    "RESTORED_FULL_FILE",
    "GPU/FPGA без реального пристрою = `UNVERIFIED`",
)


def errors(text: str) -> list[str]:
    problems: list[str] = []
    if text.count(BEGIN) != 1 or text.count(END) != 1:
        return ["потрібно рівно по одному початковому і кінцевому маркеру"]
    start = text.index(BEGIN) + len(BEGIN)
    stop = text.index(END)
    if start >= stop:
        return ["неправильний порядок маркерів"]
    fragment = text[start:stop]
    for anchor in REQUIRED:
        if anchor not in fragment:
            problems.append(f"відсутній обов'язковий контракт: {anchor}")
    return problems


def self_test(source: str) -> list[str]:
    failures: list[str] = []
    baseline = errors(source)
    if baseline:
        return ["позитивний документ не пройшов контроль: " + "; ".join(baseline)]
    mutations = (
        ("підміна T5", "**Канонічний файловий вихід:** `.sens` = **T5**",
         "**Канонічний файловий вихід:** `.sens` = **F3**"),
        ("втрачений явний opt-in", "**Окремий експеримент:** `.senc` = **F3/F4 тільки за явним opt-in**",
         "**Окремий експеримент:** `.senc` = **F3/F4 автоматично**"),
        ("втрачений М0", "спочатку [М0 #5444]", "спочатку [М1 #5445]"),
        ("втрачений кінцевий маркер", END, "<!-- закінчено -->"),
        ("втрачений основний епік", "[епік #5438]", "[епік невідомий]"),
    )
    for name, old, new in mutations:
        if old not in source:
            failures.append(f"некоректний негативний зразок: {name}")
            continue
        candidate = source.replace(old, new, 1)
        if not errors(candidate):
            failures.append(f"негативний зразок помилково допущено: {name}")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description="Перевірка AGENTS.md за #5443")
    parser.add_argument("--file", default="AGENTS.md")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    path = Path(args.file)
    if not path.is_file():
        print(f"BLOCKED: немає {path}", file=sys.stderr)
        return 2
    try:
        source = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        print(f"BLOCKED: неможливо прочитати {path}: {exc}", file=sys.stderr)
        return 2
    failures = errors(source)
    if args.self_test:
        failures.extend(self_test(source))
    if failures:
        for failure in failures:
            print("FAIL:", failure, file=sys.stderr)
        return 1
    print("PASS: контракт рою #5443" +
          (" і незалежні негативні мутації" if args.self_test else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
