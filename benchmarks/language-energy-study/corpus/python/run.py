#!/usr/bin/env python3
"""Python-реалізація задачі корпусу, запущена як ОКРЕМИЙ процес.

Вхід через середовище (TASK_ID, TASK_*), як у JS-реалізацій — щоб раннер
не мав двох різних способів передавати параметри.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import parity_check as p  # noqa: E402

task_id = os.environ["TASK_ID"]
fn = getattr(p, p.PY_MODULES[task_id]) if hasattr(p, "PY_MODULES") else None
if fn is None:
    fn = getattr(p, "ref_" + task_id.split("-")[0])
print(fn(**p.VERIFY_SIZE[task_id]))
