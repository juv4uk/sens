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

from verdict import analyze, InvalidEvidence  # noqa: E402

METRICS = ("wall_time_ns", "peak_rss_kib")


def load_raw(raw_dir: Path | None = None) -> dict[str, dict]:
    """Retain every source/task record; never select a winner by pair count.

    A file is one provenance-bearing observation, not a replaceable task slot.
    In particular, an incoming SENS T01 must not overwrite historical JS T01
    (or conversely) merely because it has more process pairs.
    """
    directory = RAW if raw_dir is None else raw_dir
    records: dict[str, dict] = {}
    for path in sorted(directory.glob("*.json")):
        doc = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(doc, dict) or not isinstance(doc.get("tasks"), dict):
            raise ValueError(f"{path.name}: tasks object missing")
        for task_id, data in doc["tasks"].items():
            if not isinstance(task_id, str) or not task_id or not isinstance(data, dict):
                raise ValueError(f"{path.name}: malformed task record")
            key = f"{path.name}::{task_id}"
            records[key] = dict(data, _source_file=path.name, _task_id=task_id)
    return records


def candidate_for(task_id: str, data: dict) -> tuple[str, str | None]:
    """Recognize physical candidate from all process IDs, never filename.

    Optional candidate_language is corroborating provenance only; one
    ambiguous/mixed record is blocked rather than silently relabeled.
    """
    pairs = data.get("pairs")
    if not isinstance(pairs, list) or not pairs:
        return "UNKNOWN", "NO_MEASURED_PAIRS"
    found: set[str] = set()
    needle = f"-{task_id}-p"
    for pair in pairs:
        if not isinstance(pair, dict):
            return "UNKNOWN", "MALFORMED_PAIR"
        process_id = pair.get("process_id")
        if not isinstance(process_id, str) or process_id.count(needle) != 1:
            return "UNKNOWN", "UNRECOGNIZED_CANDIDATE_PROCESS_ID"
        prefix, suffix = process_id.split(needle)
        if not prefix or not suffix or not suffix[0].isdigit():
            return "UNKNOWN", "UNRECOGNIZED_CANDIDATE_PROCESS_ID"
        explicit = pair.get("candidate_language")
        if explicit is not None and explicit != prefix:
            return "UNKNOWN", "CONFLICTING_CANDIDATE_METADATA"
        found.add(prefix)
    if len(found) != 1:
        return "UNKNOWN", "MIXED_CANDIDATE_LANGUAGES"
    return next(iter(found)), None


def rows(tasks: dict[str, dict]) -> list[dict]:
    out = []
    for key, data in sorted(tasks.items()):
        task_id = data.get("_task_id", key)
        source = data.get("_source_file", "unknown")
        candidate, identity_error = candidate_for(task_id, data)
        parity = data.get("parity")
        oracle = parity.get("oracle_id") if isinstance(parity, dict) else None
        # Historical parity_check.py --selftest tests the oracle itself;
        # it does not prove that the candidate process produced the result.
        parity_error = None
        if not isinstance(parity, dict) or parity.get("passed") is not True:
            parity_error = "PARITY_NOT_PROVED"
        elif not isinstance(oracle, str) or "selftest" in oracle.lower():
            parity_error = "SELFTEST_IS_NOT_MEASURED_OUTPUT_PARITY"
        elif data.get("rejected"):
            parity_error = "REJECTED_MEASUREMENT_ATTEMPTS"

        mode = parity.get("size_mode") if isinstance(parity, dict) else None
        if mode not in ("verify", "measure"):
            mode = "UNSPECIFIED"

        for metric in METRICS:
            field = {"wall_time_ns": "baseline_ns",
                     "peak_rss_kib": "baseline_peak_rss_kib"}[metric]
            pairs = data.get("pairs")
            error = identity_error or parity_error
            if not error and (not isinstance(pairs, list) or
                              any(field not in p for p in pairs)):
                error = "METRIC_NOT_MEASURED"
            if error:
                result = {"status": "BLOCKED" if error != "METRIC_NOT_MEASURED"
                          else "NOT_MEASURED", "reason": error,
                          "ratio": None, "ci95_ratio": None,
                          "independent_processes": None,
                          "pairs": len(pairs) if isinstance(pairs, list) else 0}
            else:
                doc = dict(data, metric=metric)
                try:
                    result = analyze(doc, draws=4000, seed=5227)
                except (InvalidEvidence, KeyError, TypeError, ValueError) as exc:
                    result = {"status": "BLOCKED", "reason": f"INVALID_EVIDENCE:{exc}",
                              "ratio": None, "ci95_ratio": None}
            ci = result.get("ci95_ratio")
            out.append({
                "task": task_id, "candidate": candidate, "mode": mode,
                "source": source,
                "metric": metric,
                "status": result["status"],
                "ratio": result.get("ratio"),
                "ci_low": ci[0] if ci else None,
                "ci_high": ci[1] if ci else None,
                "units": result.get("independent_processes"),
                "pairs": result.get("pairs"),
                "reason": result.get("reason"),
            })
    return out


def render(rows_: list[dict], markdown: bool) -> str:
    if markdown:
        lines = ["| задача | кандидат | режим | джерело | метрика | status | ratio | CI95 | причина |",
                 "| --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
        for r in rows_:
            ratio = f"{r['ratio']:.3f}" if r["ratio"] is not None else "—"
            ci = (f"[{r['ci_low']:.3f}, {r['ci_high']:.3f}]"
                  if r["ci_low"] is not None else "—")
            lines.append(f"| {r['task']} | {r['candidate']} | {r['mode']} | "
                         f"{r['source']} | {r['metric']} | **{r['status']}** | "
                         f"{ratio} | {ci} | {r['reason'] or '—'} |")
        return "\n".join(lines)
    lines = []
    for r in rows_:
        ratio = f"{r['ratio']:.4f}" if r["ratio"] is not None else "-"
        ci = (f"[{r['ci_low']:.4f}, {r['ci_high']:.4f}]"
              if r["ci_low"] is not None else "-")
        lines.append(f"{r['task']} candidate={r['candidate']} mode={r['mode']} "
                     f"source={r['source']} metric={r['metric']} "
                     f"status={r['status']} ratio={ratio} ci95={ci} "
                     f"units={r['units'] or '-'} pairs={r['pairs'] or '-'} "
                     f"reason={r['reason'] or '-'}")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--markdown", action="store_true")
    args = ap.parse_args()
    try:
        tasks = load_raw()
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        print(f"BLOCKED_RAW_INPUT: {exc}", file=sys.stderr)
        return 2
    if not tasks:
        print("немає сирих даних у", RAW)
        return 1
    table = rows(tasks)
    print(render(table, args.markdown))
    print()
    decisive = [r for r in table if r["status"] in ("FASTER", "SLOWER")]
    print(f"задач: {len({r['task'] for r in table})} · джерел: {len(tasks)} · рядків: {len(table)} · визначених: {len(decisive)} · "
          f"невизначених: {len(table) - len(decisive)}")
    print("енергія: ENERGY_NOT_MEASURED (RAPL недоступний) — джоулі не обчислюються")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
