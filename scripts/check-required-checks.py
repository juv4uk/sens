#!/usr/bin/env python3
"""Fail-closed: every release-gate REQUIRED_CHECK must map to a real workflow job.

scripts/verify_release_ci.py requires a fixed set of exact-SHA check names. A
GitHub check-run name is a job's ``name:`` when set, otherwise the job id. If a
job is renamed or removed, the release gate silently blocks with a confusing
"missing exact-SHA check" only at tag time. This guard catches that drift early.

It grants no admission and does not run the release. A required name that
resolves to no job fails closed.
"""
from __future__ import annotations

import importlib.util
import sys
from collections import Counter
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def required_checks(root: Path = ROOT) -> tuple[str, ...]:
    spec = importlib.util.spec_from_file_location("sens_verify_release_ci", root / "scripts" / "verify_release_ci.py")
    if spec is None or spec.loader is None:
        raise ValueError("cannot load scripts/verify_release_ci.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return tuple(module.REQUIRED_CHECKS)


def job_check_names(root: Path = ROOT) -> tuple[list[tuple[str, str]], list[str]]:
    names: list[tuple[str, str]] = []
    warnings: list[str] = []
    for path in sorted(p for p in (root / ".github" / "workflows").iterdir()
                       if p.suffix in {".yml", ".yaml"}):
        try:
            document = yaml.safe_load(path.read_text(encoding="utf-8"))
        except yaml.YAMLError as exc:
            warnings.append(f"{path.name}: YAML parse failed ({exc})")
            continue
        if not isinstance(document, dict):
            warnings.append(f"{path.name}: YAML root must be a mapping")
            continue
        jobs = document.get("jobs")
        if not isinstance(jobs, dict):
            continue
        for job_id, job in jobs.items():
            if not isinstance(job, dict):
                continue
            name = job.get("name")
            check = name.strip() if isinstance(name, str) and name.strip() else str(job_id)
            names.append((check, path.name))
    return names, warnings


def check(root: Path = ROOT) -> tuple[tuple[str, ...], list[str], list[str]]:
    required = required_checks(root)
    names, warnings = job_check_names(root)
    counts = Counter(check_name for check_name, _ in names)
    problems: list[str] = []
    for req in required:
        count = counts.get(req, 0)
        if count == 0:
            problems.append(f"REQUIRED check {req!r} resolves to no workflow job")
        elif count > 1:
            problems.append(f"REQUIRED check {req!r} is ambiguous: {count} jobs share the name")
    return required, problems, warnings


def main(argv: list[str] | None = None) -> int:
    try:
        required, problems, warnings = check()
    except (ValueError, OSError) as exc:
        print(f"REQUIRED_CHECKS_BLOCKED: {exc}", file=sys.stderr)
        return 2
    for warning in warnings:
        print(f"REQUIRED_CHECKS_BLOCKED: {warning}", file=sys.stderr)
    if problems or warnings:
        for problem in problems:
            print(f"REQUIRED_CHECKS_BLOCKED: {problem}", file=sys.stderr)
        return 1
    print(f"REQUIRED_CHECKS_PASS {len(required)}/{len(required)} required checks resolve to a job")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
