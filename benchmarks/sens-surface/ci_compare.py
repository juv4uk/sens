#!/usr/bin/env python3
"""#1433: бенчмарк мови — як мова прогресує в швидкості.

Мірило — кількість інструкцій процесора під valgrind: на відміну від часу,
вона відтворювана на спільній машині. Швидкість = 1 / інструкції, тож
«швидкість ×1.20» означає, що програма виконує в 1.20 раза менше інструкцій.

Три сторони:
  old-English  — англійський Lisp до таблиці функцій (b4f75d2f, 2026-09-08),
                 форма `legacy-en`; його швидкість — точка відліку ×1.00;
  new-English  — ця зміна, англійські імена (форма `en`);
  new-SENS     — ця зміна, коди СЕНС (форма `sens`).

new-English і new-SENS — той самий бінарник і ті самі програми (токен у
токен), тож SENS проти EN — контрольований експеримент. Проти old-English —
історичний шлях мови: між комітами змінювалося й інше.

Прогрес коміту — швидкість цієї зміни проти попереднього коміту; уповільнення
понад поріг — код 1. Сирі інструкції — у згорнутому блоці звіту.

  python3 ci_compare.py BASE.tsv HEAD.tsv [--legacy LEGACY.tsv] [--fail-above 3.0]
"""
import math
import os
import sys


def load(path):
    rows = {}
    with open(path, encoding="utf-8") as fh:
        next(fh)
        for line in fh:
            name, form, count = line.rstrip("\n").split("\t")
            rows[(name, form)] = int(count)
    return rows


def option(name, default=None):
    if name in sys.argv:
        return sys.argv[sys.argv.index(name) + 1]
    return default


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
    base_empty, head_empty = base[("empty", "-")], head[("empty", "-")]
    legacy_empty = legacy.get(("empty", "-"))
    names = sorted({name for name, form in head if name != "empty"})

    def net(rows, empty, name, form):
        return rows[(name, form)] - empty

    lines = [
        "## Швидкість мови",
        "",
        "Мірило — інструкції процесора (valgrind), відтворювані на спільній машині. "
        "**«+» / ×більше 1 — швидше, «−» / ×менше 1 — повільніше.** "
        "Вартість порожньої сесії віднято.",
        "",
    ]

    have_legacy = legacy_empty is not None
    if have_legacy:
        lines += [
            "### Шлях мови від англійського Lisp (`b4f75d2f`, 2026-09-08 = ×1.00)",
            "",
            "SENS проти англійської — той самий бінарник, ті самі програми: чистий внесок коду замість імені.",
            "",
            "| навантаження | англійський Lisp зараз | SENS зараз | SENS проти англійської зараз |",
            "|---|---:|---:|---:|",
        ]
        en_hist, sens_hist, sens_vs_en = [], [], []
        for name in names:
            old = net(legacy, legacy_empty, name, "legacy-en")
            en = net(head, head_empty, name, "en")
            sens = net(head, head_empty, name, "sens")
            a, b, c = speedup(en, old), speedup(sens, old), speedup(sens, en)
            en_hist.append(a)
            sens_hist.append(b)
            sens_vs_en.append(c)
            lines.append(f"| {name} | ×{a:.3f} ({pct(a)}) | ×{b:.3f} ({pct(b)}) | ×{c:.3f} ({pct(c)}) |")
        ge, gs, gc = geomean(en_hist), geomean(sens_hist), geomean(sens_vs_en)
        lines += [
            f"| **геометричне середнє** | **×{ge:.3f} ({pct(ge)})** | **×{gs:.3f} ({pct(gs)})** "
            f"| **×{gc:.3f} ({pct(gc)})** |",
            "",
        ]
    else:
        lines += ["Стара англійська база не виміряна.", ""]

    lines += [
        f"### Прогрес цього коміту (проти попереднього; уповільнення гірше ніж −{threshold:.1f}% — червоне)",
        "",
        "| навантаження | SENS | англійський Lisp |",
        "|---|---:|---:|",
    ]
    regressions, improvements = [], []
    for name in names:
        cells = [name]
        for form in ("sens", "en"):
            if (name, form) not in base:
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
        "<details><summary>Сирі інструкції</summary>",
        "",
        "Порожня сесія: "
        + (f"old {legacy_empty:,}, " if have_legacy else "")
        + f"попередній коміт {base_empty:,}, зараз {head_empty:,}.",
        "",
        "| навантаження | old EN сирі | old EN чисті | EN сирі | EN чисті | SENS сирі | SENS чисті |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for name in names:
        old_raw = legacy.get((name, "legacy-en"))
        old_cells = (f"{old_raw:,} | {old_raw - legacy_empty:,}" if old_raw is not None
                     else "— | —")
        en_raw, sens_raw = head[(name, "en")], head[(name, "sens")]
        lines.append(
            f"| {name} | {old_cells} | {en_raw:,} | {en_raw - head_empty:,} | "
            f"{sens_raw:,} | {sens_raw - head_empty:,} |")
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
