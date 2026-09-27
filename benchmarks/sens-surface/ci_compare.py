#!/usr/bin/env python3
"""#1433: бенчмарк мови — як мова прогресує в швидкості.

Мірило — кількість інструкцій процесора під valgrind: на відміну від часу,
вона відтворювана на спільній машині. Швидкість = 1 / інструкції, тож
«×1.20» означає, що програма виконує в 1.20 раза менше інструкцій.

SENS — 8-бітна функція, не текст: форма `sens` виконується з двійкового
вигляду (fasl, функція = 1 байт). Англійська форма — з тексту, своєї людської
поверхні.

Три сторони:
  old-English  — англійський Lisp до таблиці функцій (b4f75d2f, 2026-09-08),
                 форма `legacy-en`; його швидкість — точка відліку ×1.00;
  new-English  — ця зміна, англійські імена (`en`);
  new-SENS     — ця зміна, коди СЕНС у двійковому вигляді (`sens`).

new-English і new-SENS — той самий бінарник і ті самі програми. Проти
old-English — історичний шлях мови: між комітами змінювалося й інше.

Кожен вимір — медіана REPS повторів; розкид — у згорнутому блоці.
Уповільнення виконання між комітами понад поріг — код 1.

  python3 ci_compare.py BASE.tsv HEAD.tsv [--legacy LEGACY.tsv] [--fail-above 3.0]
"""
import math
import os
import statistics
import sys
from collections import defaultdict


def load(path):
    """(workload, form, mode) -> список інструкцій по повторах."""
    rows = defaultdict(list)
    with open(path, encoding="utf-8") as fh:
        next(fh)
        for line in fh:
            name, form, mode, _rep, count = line.rstrip("\n").split("\t")
            rows[(name, form, mode)].append(int(count))
    return rows


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


def speedup(now, was):
    """Скільки разів швидше: більше 1 — швидше, менше 1 — повільніше."""
    return was / now if now else float("nan")


def geomean(ratios):
    return math.exp(sum(math.log(r) for r in ratios) / len(ratios)) if ratios else float("nan")


def pct(factor):
    return f"{(factor - 1) * 100:+.1f}%"


def main():
    base, head = load(sys.argv[1]), load(sys.argv[2])
    legacy_path = option("--legacy")
    legacy = load(legacy_path) if legacy_path else {}
    threshold = float(option("--fail-above", "3.0"))
    empty = ("empty", "-", "full")
    head_empty, base_empty = median(head, empty), median(base, empty)
    legacy_empty = median(legacy, empty) if legacy else None
    names = sorted({name for name, form, mode in head if name != "empty"})

    def net(rows, empty_cost, name, form, mode="full"):
        return median(rows, (name, form, mode)) - empty_cost

    lines = [
        "## Швидкість мови",
        "",
        "Мірило — інструкції процесора (valgrind), медіана 3 повторів. "
        "**«+» / ×більше 1 — швидше, «−» / ×менше 1 — повільніше.** "
        "SENS виконується з двійкового вигляду (функція = 1 байт), англійська — з тексту. "
        "Вартість створення сесії віднято.",
        "",
    ]

    if legacy:
        lines += [
            "### Виконання: шлях мови від англійського Lisp (`b4f75d2f`, 2026-09-08 = ×1.00)",
            "",
            "SENS проти англійської — той самий бінарник, ті самі програми.",
            "",
            "| навантаження | англійський Lisp зараз | SENS зараз | SENS проти англійської зараз |",
            "|---|---:|---:|---:|",
        ]
        cols = ([], [], [])
        for name in names:
            old = net(legacy, legacy_empty, name, "legacy-en")
            en = net(head, head_empty, name, "en")
            sens = net(head, head_empty, name, "sens")
            factors = (speedup(en, old), speedup(sens, old), speedup(sens, en))
            for col, factor in zip(cols, factors):
                col.append(factor)
            lines.append("| " + name + " | " + " | ".join(f"×{f:.3f} ({pct(f)})" for f in factors) + " |")
        means = [geomean(col) for col in cols]
        lines += ["| **геометричне середнє** | "
                  + " | ".join(f"**×{g:.3f} ({pct(g)})**" for g in means) + " |", ""]

    lines += [
        "### Завантаження програми: SENS (двійковий вигляд, функція = 1 байт) проти тексту",
        "",
        "| навантаження | англійська (текст) зараз | SENS (двійковий) зараз | SENS швидше за англійську |"
        + (" SENS швидше за англійський Lisp 8.09 |" if legacy else ""),
        "|---|---:|---:|---:|" + ("---:|" if legacy else ""),
    ]
    load_sens, load_legacy = [], []
    for name in names:
        en = net(head, head_empty, name, "en", "load")
        sens = net(head, head_empty, name, "sens", "load")
        load_sens.append(speedup(sens, en))
        row = f"| {name} | {en:,.0f} | {sens:,.0f} | ×{speedup(sens, en):.2f} |"
        if legacy:
            old = net(legacy, legacy_empty, name, "legacy-en", "load")
            load_legacy.append(speedup(sens, old))
            row += f" ×{speedup(sens, old):.2f} |"
        lines.append(row)
    g = geomean(load_sens)
    lines += ["", f"Геометричне середнє: SENS завантажується в **×{g:.2f}** швидше за англійський текст"
              + (f", в **×{geomean(load_legacy):.2f}** швидше за англійський Lisp 8.09" if legacy else "")
              + ". Завантаження — мала частка часу виконання цих програм.", ""]

    lines += [
        f"### Прогрес цього коміту — виконання (проти попереднього; уповільнення гірше ніж −{threshold:.1f}% — червоне)",
        "",
        "| навантаження | SENS | англійський Lisp |",
        "|---|---:|---:|",
    ]
    regressions, improvements = [], []
    for name in names:
        cells = [name]
        for form in ("sens", "en"):
            if (name, form, "full") not in base:
                cells.append("нове")
                continue
            factor = speedup(net(head, head_empty, name, form), net(base, base_empty, name, form))
            change = (factor - 1) * 100
            mark = ""
            if change < -threshold:
                mark = " 🔴"
                regressions.append(f"{name}/{form} {change:+.2f}%")
            elif change > threshold:
                mark = " 🟢"
                improvements.append(f"{name}/{form} {change:+.2f}%")
            cells.append(f"{change:+.2f}%{mark}")
        lines.append("| " + " | ".join(cells) + " |")
    lines += ["", f"**Швидше:** {', '.join(improvements) or 'немає'}",
              f"**Повільніше:** {', '.join(regressions) or 'немає'}", ""]

    lines += [
        "<details><summary>Сирі інструкції (медіана, розкид повторів)</summary>",
        "",
        "Створення сесії: "
        + (f"old {legacy_empty:,.0f}, " if legacy else "")
        + f"попередній коміт {base_empty:,.0f}, зараз {head_empty:,.0f}.",
        "",
        "| навантаження | режим | англійський Lisp 8.09 | англійська зараз | SENS зараз |",
        "|---|---|---:|---:|---:|",
    ]
    for name in names:
        for mode in ("load", "full"):
            def cell(rows, form):
                key = (name, form, mode)
                if key not in rows:
                    return "—"
                return f"{median(rows, key):,.0f} (±{spread(rows, key):.2f}%)"
            lines.append(f"| {name} | {mode} | {cell(legacy, 'legacy-en')} | "
                         f"{cell(head, 'en')} | {cell(head, 'sens')} |")
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
