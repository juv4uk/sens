#!/usr/bin/env python3
"""Summarize one exact-SHA run of every registered benchmark stand.

The audit is intentionally fail-closed: missing, duplicate, extra, hash-drifting,
failed, timed-out, or unknown statuses never become a suite-wide PASS.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BENCHMARKS = ROOT / "benchmarks"
SCHEMA = "sens-benchmark-manifest/v1"


def registered_stands() -> list[str]:
    stands: list[str] = []
    seen: set[str] = set()
    for path in sorted(BENCHMARKS.glob("*/bench.json")):
        try:
            manifest = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError(f"{path.relative_to(ROOT)}: invalid manifest: {exc}") from exc
        if not isinstance(manifest, dict) or manifest.get("schema") != SCHEMA:
            raise ValueError(f"{path.relative_to(ROOT)}: invalid schema")
        stand = manifest.get("stand")
        if not isinstance(stand, str) or stand != path.parent.name:
            raise ValueError(f"{path.relative_to(ROOT)}: stand/path mismatch")
        if stand in seen:
            raise ValueError(f"duplicate registered stand: {stand}")
        seen.add(stand)
        stands.append(stand)
    if not stands:
        raise ValueError("no registered benchmarks found")
    return stands


def read_results(directory: Path) -> tuple[list[dict], list[str]]:
    rows: list[dict] = []
    errors: list[str] = []
    for path in sorted(directory.rglob("result.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"{path}: cannot read result.json: {exc}")
            continue
        if not isinstance(data, dict) or not isinstance(data.get("stand"), str):
            errors.append(f"{path}: missing object/stand field")
            continue
        rows.append(data)
    return rows, errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-dir", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--expected-sha", default=os.environ.get("EXPECTED_SHA", ""))
    args = parser.parse_args()

    try:
        expected = registered_stands()
    except ValueError as exc:
        print(f"SWEEP AUDIT: BLOCKED: {exc}", file=sys.stderr)
        return 2
    rows, errors = read_results(args.results_dir)
    names = [row["stand"] for row in rows]
    counts = Counter(names)
    duplicates = sorted(name for name, count in counts.items() if count != 1)
    actual = set(names)
    expected_set = set(expected)
    missing = sorted(expected_set - actual)
    extra = sorted(actual - expected_set)
    shas = sorted({str(row.get("git_sha", "")) for row in rows})
    statuses = Counter(str(row.get("status", "UNKNOWN")).lower() for row in rows)

    if not args.expected_sha:
        errors.append("expected SHA was not supplied")
    for row in rows:
        if row.get("git_sha") != args.expected_sha:
            errors.append(
                f"{row.get('stand')}: sha={row.get('git_sha')!r}, expected={args.expected_sha!r}"
            )
        if row.get("status") not in {"passed", "failed", "timeout", "blocked"}:
            errors.append(f"{row.get('stand')}: unknown result status {row.get('status')!r}")

    complete = (
        not errors
        and not missing
        and not extra
        and not duplicates
        and len(rows) == len(expected)
        and statuses["passed"] == len(expected)
        and len(shas) == 1
    )
    audit = {
        "schema": "sens-benchmark-sweep-audit/v1",
        "expected_sha": args.expected_sha,
        "registered": len(expected),
        "observed_results": len(rows),
        "shas": shas,
        "counts": {key: statuses.get(key, 0) for key in ("passed", "failed", "blocked", "timeout", "unknown")},
        "missing": missing,
        "extra": extra,
        "duplicates": duplicates,
        "errors": errors,
        "complete_green": complete,
        "results": sorted(rows, key=lambda row: str(row.get("stand", ""))),
    }
    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "summary.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    lines = [
        "# Full registered benchmark sweep",
        "",
        f"- Exact SHA: `{args.expected_sha or 'MISSING'}`",
        f"- Expected / observed: **{len(expected)} / {len(rows)}**",
        f"- Counts: PASS={statuses.get('passed', 0)}, FAIL={statuses.get('failed', 0)}, "
        f"BLOCKED={statuses.get('blocked', 0)}, TIMEOUT={statuses.get('timeout', 0)}, "
        f"UNKNOWN={statuses.get('unknown', 0)}",
        f"- Missing: {missing or 'none'}",
        f"- Extra: {extra or 'none'}",
        f"- Duplicate result names: {duplicates or 'none'}",
        f"- SHA set: {shas}",
        f"- Complete green: **{'YES' if complete else 'NO'}**",
        "",
        "| Stand | Status | Exit | Seconds | SHA |",
        "|---|---|---:|---:|---|",
    ]
    for row in sorted(rows, key=lambda item: str(item.get("stand", ""))):
        lines.append(
            f"| `{row.get('stand', '')}` | {row.get('status', 'UNKNOWN')} | "
            f"{row.get('return_code', '')} | {row.get('duration_seconds', '')} | "
            f"`{row.get('git_sha', '')}` |"
        )
    if errors:
        lines.extend(["", "## Audit errors", ""])
        lines.extend(f"- {error}" for error in errors)
    markdown = "\n".join(lines) + "\n"
    (args.out_dir / "summary.md").write_text(markdown, encoding="utf-8")
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        with open(summary_path, "a", encoding="utf-8") as handle:
            handle.write(markdown)
    print(markdown)
    return 0 if complete else 1


if __name__ == "__main__":
    raise SystemExit(main())
