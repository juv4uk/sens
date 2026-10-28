#!/usr/bin/env python3
"""Відтворює ПОВНУ таблицю результатів із сирих парних даних.

Критерій приймання #6290: «сирі парні дані і скрипт, який відтворює 100%
таблиць/ДІ з них». Цей файл — той скрипт. Він не містить жодного числа,
вписаного руками: усе рахується з raw/*.json через verdict.py.

Запуск:
  python3 benchmarks/language-energy-study/report_table.py
  python3 benchmarks/language-energy-study/report_table.py --markdown
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RAW = HERE / "raw"
sys.path.insert(0, str(HERE.parent / "measurement-triad"))

from verdict import analyze  # noqa: E402

METRICS = ("wall_time_ns", "peak_rss_kib")


def load_raw() -> dict[str, dict]:
    """Збирає всі задачі з усіх сирих файлів. Пізніші файли не перетирають
    раніші — якщо задача вже є, береться той, де більше пар."""
    tasks: dict[str, dict] = {}
    for path in sorted(RAW.glob("*.json")):
        doc = json.loads(path.read_text(encoding="utf-8"))
        for task_id, data in (doc.get("tasks") or {}).items():
            if task_id not in tasks or len(data["pairs"]) > len(tasks[task_id]["pairs"]):
                tasks[task_id] = data
    return tasks


def rows(tasks: dict[str, dict]) -> list[dict]:
    out = []
    for task_id in sorted(tasks):
        data = tasks[task_id]
        for metric in METRICS:
            # Метрика, якої немає в сирих даних, НЕ вигадується і не падає:
            # старі прогони писалися до появи peak_rss_kib, і чесніше
            # показати рядок як відсутній, ніж підставити нуль.
            field = {"wall_time_ns": "baseline_ns",
                     "peak_rss_kib": "baseline_peak_rss_kib"}[metric]
            if data["pairs"] and field not in data["pairs"][0]:
                continue
            doc = dict(data)
            doc["metric"] = metric
            r = analyze(doc, draws=4000, seed=5227)
            ci = r.get("ci95_ratio")
            out.append({
                "task": task_id,
                "metric": metric,
                "status": r["status"],
                "ratio": r.get("ratio"),
                "ci_low": ci[0] if ci else None,
                "ci_high": ci[1] if ci else None,
                "units": r.get("independent_processes"),
                "pairs": r.get("pairs"),
                "reason": r.get("reason"),
            })
    return out


def render(rows_: list[dict], markdown: bool) -> str:
    if markdown:
        lines = ["| задача | метрика | status | ratio | CI95 | одиниць | пар |",
                 "| --- | --- | --- | --- | --- | --- | --- |"]
        for r in rows_:
            ratio = f"{r['ratio']:.3f}" if r["ratio"] else "—"
            ci = f"[{r['ci_low']:.3f}, {r['ci_high']:.3f}]" if r["ci_low"] else "—"
            lines.append(f"| {r['task']} | {r['metric']} | **{r['status']}** | {ratio} | {ci} | "
                         f"{r['units'] or '—'} | {r['pairs'] or '—'} |")
        return "\n".join(lines)
    lines = []
    for r in rows_:
        ratio = f"{r['ratio']:.4f}" if r["ratio"] else "-"
        ci = f"[{r['ci_low']:.4f}, {r['ci_high']:.4f}]" if r["ci_low"] else "-"
        lines.append(f"{r['task']:28} {r['metric']:14} {r['status']:12} {ratio:>8} {ci:>22} "
                     f"units={r['units'] or '-'} pairs={r['pairs'] or '-'}")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--markdown", action="store_true")
    args = ap.parse_args()
    tasks = load_raw()
    if not tasks:
        print("немає сирих даних у", RAW)
        return 1
    table = rows(tasks)
    print(render(table, args.markdown))
    print()
    decisive = [r for r in table if r["status"] in ("FASTER", "SLOWER")]
    print(f"задач: {len(tasks)} · рядків: {len(table)} · визначених: {len(decisive)} · "
          f"невизначених: {len(table) - len(decisive)}")
    print("енергія: ENERGY_NOT_MEASURED (RAPL недоступний) — джоулі не обчислюються")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
