#!/usr/bin/env python3
"""Перевірити, що всі воркфлоу GitHub Actions парсяться як YAML і мають непорожній
набір джобів. Це захист від повторного зламу `ci.yml`, коли необережна правка
злипає рядки або дублює блоки — тоді прогін має `jobs: 0`, і весь CI стоїть,
хоч самі тести цілі.

Запуск: python3 scripts/check-workflow-yaml.py
Вихід 0 — усе гаразд; 1 — є файл, що не парситься або без джобів.
"""
from __future__ import annotations

import sys
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    print("CHECK_WORKFLOW_YAML_SKIP: немає PyYAML")
    sys.exit(0)

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"


def main() -> int:
    bad: list[str] = []
    files = sorted(WORKFLOWS.glob("*.y*ml"))
    if not files:
        print("CHECK_WORKFLOW_YAML_FAIL: не знайдено жодного воркфлоу")
        return 1
    for path in files:
        rel = path.relative_to(ROOT)
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
        except yaml.YAMLError as exc:
            bad.append(f"{rel}: YAML не парситься: {str(exc).splitlines()[0]}")
            continue
        if not isinstance(data, dict):
            bad.append(f"{rel}: верхівка не є мапою")
            continue
        jobs = data.get("jobs")
        if not isinstance(jobs, dict) or not jobs:
            bad.append(f"{rel}: немає непорожніх jobs (прогін мав би jobs: 0)")
            continue
        # кожна джоба мусить мати runs-on або uses
        for name, job in jobs.items():
            if not isinstance(job, dict):
                bad.append(f"{rel}: джоба {name!r} не є мапою")
            elif "runs-on" not in job and "uses" not in job:
                bad.append(f"{rel}: джоба {name!r} без runs-on/uses")
    if bad:
        for line in bad:
            print(f"CHECK_WORKFLOW_YAML_FAIL: {line}")
        return 1
    print(f"CHECK_WORKFLOW_YAML_PASS: {len(files)} воркфлоу парсяться, у кожного є джоби")
    return 0


if __name__ == "__main__":
    sys.exit(main())
