#!/usr/bin/env python3
"""#1433: бенчмарк мови — англійський Lisp проти SENS на одному коміті.

Той самий бінарник, ті самі програми, дві форми:
  англійська — текст, імена; виконується як є, ім'я розв'язується під час
               виконання (без попереднього зведення до кодів);
  SENS       — двійковий вигляд (fasl), функція = 1 байт; виконується як є.

Мірило — кількість інструкцій процесора під valgrind (відтворювана на
спільній машині), медіана повторів; швидкість = 1 / інструкції. Вартість
створення сесії віднято. «×1.40» — SENS у 1.40 раза швидший.

Прогрес коміту — швидкість цієї зміни проти попереднього коміту для обох
форм; уповільнення понад поріг — код 1.

  python3 ci_compare.py BASE.tsv HEAD.tsv [--fail-above 3.0] [--skip-base-regression]
"""
import math
import os
import statistics
import sys
from collections import defaultdict


def load(path):
    """(workload, form, mode) -> список інструкцій по повторах; params —
    розмір навантаження на кожне ім'я (#1587). Стара п'ятиколонкова схема
    (без params) приймається: параметр стає "-", а не мовчазною втратою."""
    rows = defaultdict(list)
    params = {}
    with open(path, encoding="utf-8") as fh:
        next(fh)
        for line in fh:
            parts = line.rstrip("\n").split("\t")
            if len(parts) == 6:
                name, param, form, mode, _rep, count = parts
            else:
                name, form, mode, _rep, count = parts
                param = "-"
            rows[(name, form, mode)].append(int(count))
            params.setdefault(name, param)
    return rows, params


def option(name, default=None):
    if name in sys.argv:
        return sys.argv[sys.argv.index(name) + 1]
    return default


def median(rows, key):
    return statistics.median(rows[key])


def spread(rows, key):
    values = rows[key]
    mid = statistics.median(values)
    return (max(values) - min(values)) / mid * 100 if mid else 0.0


def geomean(ratios):
    return math.exp(sum(math.log(r) for r in ratios) / len(ratios)) if ratios else float("nan")


def main():
    (base, base_params), (head, head_params) = load(sys.argv[1]), load(sys.argv[2])
    params = {**base_params, **head_params}
    threshold = float(option("--fail-above", "3.0"))
    skip_base_regression = "--skip-base-regression" in sys.argv
    empty = ("empty", "-", "full")
    head_empty, base_empty = median(head, empty), median(base, empty)
    names = sorted({name for name, form, mode in head if name != "empty"})

    def net(rows, empty_cost, name, form, mode):
        return median(rows, (name, form, mode)) - empty_cost

    lines = [
        "## Англійський Lisp проти SENS — той самий коміт, ті самі програми",
        "",
        "Англійська — текст, імена розв'язуються під час виконання; SENS — двійковий вигляд, "
        "функція = 1 байт. Інструкції процесора (valgrind), медіана 3 повторів, "
        "вартість створення сесії віднято. **×більше 1 — SENS швидший.**",
        "",
        "#1587: кожен рядок несе свій розмір (params). Порівняння «×N швидше» —",
        "лише в межах одного розміру; крос-розмірних висновків цей звіт не робить.",
        "",
    ]
    for mode, title in (("full", "Виконання програми"), ("load", "Завантаження програми")):
        lines += [
            f"### {title}",
            "",
            "| навантаження · розмір | англійська | SENS | SENS швидший |",
            "|---|---:|---:|---:|",
        ]
        ratios = []
        for name in names:
            en = net(head, head_empty, name, "en", mode)
            sens = net(head, head_empty, name, "sens", mode)
            ratios.append(en / sens)
            lines.append(f"| {name} · {params.get(name, '-')} | {en:,.0f} | {sens:,.0f} | ×{en / sens:.3f} |")
        g = geomean(ratios)
        lines += [f"| **геометричне середнє** (усереднено по навантаженнях, не по розмірах) | | | **×{g:.3f}** |", ""]

    regressions, improvements = [], []
    if skip_base_regression:
        lines += [
            "### Прогрес base → head — не оцінюється",
            "",
            "Контрольоване benchmark-навантаження або harness змінено в цьому PR. "
            "Крос-комітне порівняння не виконується, бо програма вже не є тією самою. "
            "Порівняння English ↔ SENS вище лишається чинним: обидві форми виміряні "
            "на одному HEAD-бінарнику й з одного шаблону.",
            "",
        ]
    else:
        lines += [
            f"### Прогрес цього коміту — виконання (проти попереднього; уповільнення гірше ніж −{threshold:.1f}% — червоне)",
            "",
            "| навантаження · розмір | SENS | англійська |",
            "|---|---:|---:|",
        ]
        for name in names:
            cells = [f"{name} · {params.get(name, '-')}"]
            for form in ("sens", "en"):
                if (name, form, "full") not in base:
                    cells.append("нове")
                    continue
                was = net(base, base_empty, name, form, "full")
                now = net(head, head_empty, name, form, "full")
                change = (was / now - 1) * 100
                mark = ""
                if change < -threshold:
                    mark = " 🔴"
                    regressions.append(f"{name}/{form} {change:+.2f}%")
                elif change > threshold:
                    mark = " 🟢"
                    improvements.append(f"{name}/{form} {change:+.2f}%")
                cells.append(f"{change:+.2f}%{mark}")
            lines.append("| " + " | ".join(cells) + " |")
        lines += [
            "",
            f"**Швидше:** {', '.join(improvements) or 'немає'}",
            f"**Повільніше:** {', '.join(regressions) or 'немає'}",
            "",
        ]

    lines += [
        "<details><summary>Сирі інструкції (медіана, розкид повторів)</summary>",
        "",
        (f"Створення сесії: зараз {head_empty:,.0f} (base не порівнюється — workload змінено)."
         if skip_base_regression
         else f"Створення сесії: попередній коміт {base_empty:,.0f}, зараз {head_empty:,.0f}."),
        "",
        "| навантаження · розмір | режим | англійська | SENS |",
        "|---|---|---:|---:|",
    ]
    for name in names:
        for mode in ("load", "full"):
            cells = []
            for form in ("en", "sens"):
                key = (name, form, mode)
                cells.append(f"{median(head, key):,.0f} (±{spread(head, key):.2f}%)")
            lines.append(f"| {name} · {params.get(name, '-')} | {mode} | {cells[0]} | {cells[1]} |")
    lines += ["", "</details>"]

    report = "\n".join(lines) + "\n"
    print(report)
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as fh:
            fh.write(report)
    sys.exit(1 if regressions else 0)


if __name__ == "__main__":
    main()
