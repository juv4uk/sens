#!/usr/bin/env python3
"""Незалежна fail-closed перевірка агентної політики #5443 (не енкодер)."""
from __future__ import annotations

import argparse
from pathlib import Path

START = "<!-- SENS-ENCODER-SWARM-CONTRACT-2026-10-10:BEGIN -->"
END = "<!-- SENS-ENCODER-SWARM-CONTRACT-2026-10-10:END -->"
REQUIRED = (
    "**Канонічний `.sens` = T5:**",
    "**Дослідний `.senc` = лише F3/F4 за явною згодою:**",
    "**Канонічна `.lisp` = українська людиночитана проєкція:**",
    "**Файл без розширення = читабельна двійкова проєкція:**",
    "**Одна семантика D1–D9, один спільний контракт пакування:**",
    "**Машинний x86-64 ISA-енкодер ≠ фізичний T5-енкодер SENS:**",
    "**Міграція історичних кодів ≠ тріада проєкцій ≠ оптимізація носія:**",
    "**М0 [#5444]",
    "**окремі гілки/PR, без прямої зміни `main`**",
    "**один призначений мерджер, один PR за раз, свіжий HEAD, обов'язкові зелені перевірки**",
    "`SEE_LOCAL_FIX_`", "`LOAD_FROM_FILE:`", "`RESTORED_FULL_FILE`",
    "`PLACEHOLDER`", "`BLOCKED` або `UNVERIFIED`",
    "https://github.com/juv4uk/sens/issues/5438",
    "https://github.com/juv4uk/sens/issues/5440",
    "https://github.com/juv4uk/sens/issues/5439",
    "https://github.com/juv4uk/sens/issues/5442",
    "https://github.com/juv4uk/sens/issues/5443",
    "https://github.com/juv4uk/cml/issues/695",
    "https://github.com/juv4uk/fpga-lisp/issues/85",
    "https://github.com/juv4uk/sens-futhark/issues/132",
    "https://github.com/juv4uk/wsm-graalvm/issues/301",
)
REPORT_FIELDS = (
    "**Агент / напрям:**",
    "**Задача та батьківська задача:**",
    "**Репозиторій і поточний SHA:**",
    "**Що досліджено або змінено:**",
    "**Файли та посилання на PR:**",
    "**Перевірки: PASS / FAIL / BLOCKED / UNVERIFIED:**",
    "**Знайдені блокери й пов'язані задачі:**",
    "**Наступна атомарна дія:**",
    "**Кому передано результат:**",
)


def violations(markdown: str) -> list[str]:
    problems = []
    if markdown.count(START) != 1 or markdown.count(END) != 1:
        return ["відсутні або дубльовані межі нормативного блоку"]
    begin = markdown.index(START) + len(START)
    end = markdown.index(END)
    if begin >= end:
        return ["межі нормативного блоку переплутано"]
    block = markdown[begin:end]
    for text in REQUIRED + REPORT_FIELDS:
        if text not in block:
            problems.append(f"відсутній інваріант або поле: {text}")
    positions = [block.find(name) for name in REPORT_FIELDS]
    if positions != sorted(positions):
        problems.append("порушено порядок полів звіту")
    return problems


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", type=Path, default=Path("AGENTS.md"))
    ap.add_argument("--self-test", action="store_true")
    options = ap.parse_args()
    try:
        text = options.file.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        print(f"АГЕНТНИЙ-КОНТРАКТ: FAIL, не прочитано файл: {exc}")
        return 1
    errors = violations(text)
    if options.self_test and not errors:
        mutations = (
            ("без початку", text.replace(START, "", 1)),
            ("змінено T5", text.replace("**Канонічний `.sens` = T5:**",
                                      "**Канонічний `.senc` = T5:**", 1)),
            ("немає звіту", text.replace("**Кому передано результат:**", "", 1)),
            ("немає single-writer", text.replace(
                "**один призначений мерджер, один PR за раз, свіжий HEAD, обов'язкові зелені перевірки**", "", 1)),
            ("немає батьківської задачі", text.replace(
                "https://github.com/juv4uk/sens/issues/5440", "https://github.com/juv4uk/sens/issues/ЗЛАМАНО")),
        )
        for label, mutant in mutations:
            if not violations(mutant):
                errors.append(f"негативний свідок прийнятий: {label}")
        if not errors:
            print(f"АГЕНТНИЙ-КОНТРАКТ: негативні мутації відхилено {len(mutations)}/{len(mutations)}")
    if errors:
        for e in errors:
            print("АГЕНТНИЙ-КОНТРАКТ: FAIL:", e)
        return 1
    print("АГЕНТНИЙ-КОНТРАКТ: PASS, український фізичний контракт збережено")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
