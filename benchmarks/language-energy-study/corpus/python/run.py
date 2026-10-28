#!/usr/bin/env python3
"""Python baseline: виконує ТІ САМІ TASK_* параметри, що й інші мови.

Жодного fallback з MEASURE_SIZE до VERIFY_SIZE: відмінний вхід
забороняє фізичний висновок, навіть коли вимір часу завершився.
"""
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import parity_check as p  # noqa: E402


def admitted_params(task_id: str) -> dict[str, int]:
    """Дозволені лише зафіксовані VERIFY/MEASURE входи з корпусу."""
    if task_id not in p.PY_MODULES:
        raise ValueError("unknown TASK_ID")
    task = next(
        (t for t in p.load_manifest()["tasks"] if t["id"] == task_id),
        None,
    )
    if task is None:
        raise ValueError("TASK_ID missing from frozen manifest")

    params = {}
    for name in task["input"]:
        raw = os.environ.get("TASK_" + name.upper())
        if raw is None or re.fullmatch(r"[0-9]+", raw, flags=re.ASCII) is None:
            raise ValueError("missing or invalid TASK_" + name.upper())
        value = int(raw)
        if str(value) != raw:
            raise ValueError("noncanonical TASK_" + name.upper())
        params[name] = value

    if params != p.VERIFY_SIZE[task_id] and params != task["input"]:
        raise ValueError("TASK_* is neither frozen VERIFY_SIZE nor MEASURE_SIZE")
    return params


def main() -> int:
    try:
        task_id = os.environ["TASK_ID"]
        params = admitted_params(task_id)
    except (KeyError, ValueError, StopIteration) as exc:
        print(f"INVALID_TASK_INPUT: {exc}", file=sys.stderr)
        return 2

    fn = getattr(p, p.PY_MODULES[task_id])
    print(fn(**params))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
