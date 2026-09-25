#!/usr/bin/env python3
"""#1433: порівняння «було / стало» двох прогонів ci_bench.sh.

Пише markdown-таблицю (у $GITHUB_STEP_SUMMARY, якщо задано) і повертає
код 1, якщо будь-яке навантаження стало дорожчим більше ніж на поріг.
Інструкції рахуються без вартості порожньої сесії (рядок `empty`).

  python3 ci_compare.py BASE.tsv HEAD.tsv [--fail-above 3.0]
"""
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


def main():
    base, head = load(sys.argv[1]), load(sys.argv[2])
    threshold = 3.0
    if "--fail-above" in sys.argv:
        threshold = float(sys.argv[sys.argv.index("--fail-above") + 1])
    base_empty, head_empty = base[("empty", "-")], head[("empty", "-")]

    lines = [
        "## Бенчмарк мови: інструкції процесора (valgrind), було → стало",
        "",
        f"Поріг регресу: +{threshold:.1f}%. Вартість порожньої сесії віднято "
        f"(було {base_empty:,}, стало {head_empty:,}).",
        "",
        "| навантаження | форма | було | стало | Δ | en/sens стало |",
        "|---|---|---:|---:|---:|---:|",
    ]
    regressions, improvements = [], []
    names = sorted({name for name, form in head if name != "empty"})
    for name in names:
        for form in ("en", "sens"):
            if (name, form) not in head:
                continue
            now = head[(name, form)] - head_empty
            was = base.get((name, form))
            ratio = ""
            if form == "en" and (name, "sens") in head:
                ratio = f"{now / (head[(name, 'sens')] - head_empty):.3f}"
            if was is None:
                lines.append(f"| {name} | {form} | нове | {now:,} | — | {ratio} |")
                continue
            was -= base_empty
            delta = (now - was) / was * 100 if was else 0.0
            mark = ""
            if delta > threshold:
                mark = " 🔴"
                regressions.append(f"{name}/{form} {delta:+.2f}%")
            elif delta < -threshold:
                mark = " 🟢"
                improvements.append(f"{name}/{form} {delta:+.2f}%")
            lines.append(
                f"| {name} | {form} | {was:,} | {now:,} | {delta:+.2f}%{mark} | {ratio} |")
    lines += ["", f"**Прогрес:** {', '.join(improvements) or 'немає'}",
              f"**Регрес:** {', '.join(regressions) or 'немає'}"]
    report = "\n".join(lines) + "\n"
    print(report)
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as fh:
            fh.write(report)
    sys.exit(1 if regressions else 0)


if __name__ == "__main__":
    main()
