#!/usr/bin/env python3
"""#1433: бенчмарк мови — три сторони, інструкції процесора (valgrind).

  old-English  — англійський Lisp до таблиці функцій (b4f75d2f, 2026-09-08),
                 форма `legacy-en`;
  new-English  — ця зміна, англійські імена (форма `en`);
  new-SENS     — ця зміна, коди СЕНС (форма `sens`).

Головний контрольований експеримент — new-English проти new-SENS: той самий
бінарник, ті самі програми (токен у токен після заміни імені на код), різниця
лише в записі функціональної ідентичності. old-English проти new-SENS —
окреме історичне end-to-end порівняння: між цими комітами змінювалося й
інше, тож це не причинний доказ переваги SENS.

Для кожного навантаження — сирі інструкції, вартість порожньої сесії, чисті
інструкції, заощаджені інструкції й виграш у відсотках; потім геометричне
середнє. Знак: «+» — менше інструкцій (краще), «−» — більше (гірше).

Страховка від регресу: SENS і англійська форма бази (попередній коміт)
проти зміни; регрес понад поріг — код 1.

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


def gain(now, was):
    """Виграш у відсотках: «+» — менше інструкцій (краще), «−» — більше (гірше)."""
    return (was - now) / was * 100 if was else 0.0


def geomean(ratios):
    return math.exp(sum(math.log(r) for r in ratios) / len(ratios)) if ratios else float("nan")


def main():
    base, head = load(sys.argv[1]), load(sys.argv[2])
    legacy_path = option("--legacy")
    legacy = load(legacy_path) if legacy_path else {}
    threshold = float(option("--fail-above", "3.0"))
    base_empty, head_empty = base[("empty", "-")], head[("empty", "-")]
    legacy_empty = legacy.get(("empty", "-"))
    names = sorted({name for name, form in head if name != "empty"})

    lines = [
        "## Бенчмарк мови: інструкції процесора (valgrind), три сторони",
        "",
        "- **old-English** — англійський Lisp до таблиці функцій (`b4f75d2f`, 2026-09-08);",
        "- **new-English**, **new-SENS** — ця зміна, той самий бінарник; програми однакові "
        "токен у токен, відрізняється лише запис ідентичності функції (ім'я чи 8-бітний код).",
        "",
        "Знак: **«+» — менше інструкцій (краще), «−» — більше (гірше)**.",
        "",
        "Порожня сесія (віднімається): "
        + (f"old {legacy_empty:,}, " if legacy_empty is not None else "")
        + f"new {head_empty:,}.",
        "",
        "### Контрольований експеримент: new-English → new-SENS",
        "",
        "| навантаження | EN сирі | SENS сирі | EN чисті | SENS чисті | заощаджено інструкцій | виграш SENS |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    controlled = []
    for name in names:
        en_raw, sens_raw = head[(name, "en")], head[(name, "sens")]
        en_net, sens_net = en_raw - head_empty, sens_raw - head_empty
        controlled.append(sens_net / en_net)
        lines.append(
            f"| {name} | {en_raw:,} | {sens_raw:,} | {en_net:,} | {sens_net:,} | "
            f"{en_net - sens_net:+,} | {gain(sens_net, en_net):+.2f}% |")
    g = geomean(controlled)
    lines += ["", f"Геометричне середнє: SENS/EN **{g:.4f}**, виграш SENS **{(1 - g) * 100:+.2f}%**.", ""]

    if legacy_empty is not None:
        lines += [
            "### Історичне end-to-end: old-English (b4f75d2f) → new-English / new-SENS",
            "",
            "Не причинний доказ: між комітами змінювалися й ядро, і логіка (`cond`/`atom?`/`eq?`).",
            "",
            "| навантаження | old сирі | old чисті | new-EN чисті | виграш EN | new-SENS чисті | заощаджено | виграш SENS |",
            "|---|---:|---:|---:|---:|---:|---:|---:|",
        ]
        hist_en, hist_sens = [], []
        for name in names:
            if (name, "legacy-en") not in legacy:
                continue
            old_raw = legacy[(name, "legacy-en")]
            old_net = old_raw - legacy_empty
            en_net = head[(name, "en")] - head_empty
            sens_net = head[(name, "sens")] - head_empty
            hist_en.append(en_net / old_net)
            hist_sens.append(sens_net / old_net)
            lines.append(
                f"| {name} | {old_raw:,} | {old_net:,} | {en_net:,} | {gain(en_net, old_net):+.1f}% | "
                f"{sens_net:,} | {old_net - sens_net:+,} | {gain(sens_net, old_net):+.1f}% |")
        ge, gs = geomean(hist_en), geomean(hist_sens)
        lines += ["", f"Геометричне середнє відносно old: new-EN **{(1 - ge) * 100:+.1f}%**, "
                  f"new-SENS **{(1 - gs) * 100:+.1f}%**.", ""]

    lines += [
        f"### Страховка: попередній коміт → ця зміна (регрес — гірше ніж −{threshold:.1f}%)",
        "",
        "| навантаження | зміна SENS | зміна EN |",
        "|---|---:|---:|",
    ]
    regressions, improvements = [], []
    for name in names:
        cells = [name]
        for form in ("sens", "en"):
            if (name, form) not in base:
                cells.append("нове")
                continue
            delta = gain(head[(name, form)] - head_empty, base[(name, form)] - base_empty)
            mark = ""
            if delta < -threshold:
                mark = " 🔴"
                regressions.append(f"{name}/{form} {delta:+.2f}%")
            elif delta > threshold:
                mark = " 🟢"
                improvements.append(f"{name}/{form} {delta:+.2f}%")
            cells.append(f"{delta:+.2f}%{mark}")
        lines.append("| " + " | ".join(cells) + " |")
    lines += ["", f"**Прогрес між комітами:** {', '.join(improvements) or 'немає'}",
              f"**Регрес між комітами:** {', '.join(regressions) or 'немає'}"]
    report = "\n".join(lines) + "\n"
    print(report)
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as fh:
            fh.write(report)
    sys.exit(1 if regressions else 0)


if __name__ == "__main__":
    main()
