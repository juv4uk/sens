#!/usr/bin/env python3
"""Run SENS-code migration/audit across sibling repositories.

Example:
  python3 scripts/migrate-sens-ecosystem.py ../cml ../wsm-my-lisp ../wsm-graalvm \
    --foundation knowledge/d1-d7-foundation.json --mirror-root ../sens-migrated
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
MIGRATOR = HERE / "migrate-to-sens-codes.py"
AUDITOR = HERE / "audit-sens-name-debt.py"

def run(cmd):
    proc = subprocess.run(cmd, text=True, capture_output=True)
    return {
        "cmd": cmd,
        "returncode": proc.returncode,
        "stdout": proc.stdout.strip(),
        "stderr": proc.stderr.strip(),
    }

def main():
    p = argparse.ArgumentParser()
    p.add_argument("repos", nargs="+", type=Path)
    p.add_argument("--foundation", type=Path, required=True)
    p.add_argument("--mirror-root", type=Path)
    p.add_argument("--apply", action="store_true")
    p.add_argument("--report-dir", type=Path, default=Path("sens-migration-reports"))
    args = p.parse_args()

    if args.apply and args.mirror_root:
        p.error("--apply and --mirror-root are mutually exclusive")

    args.report_dir.mkdir(parents=True, exist_ok=True)
    results = []
    worst = 0

    for repo in args.repos:
        repo = repo.resolve()
        name = repo.name
        audit_report = args.report_dir / f"{name}-name-debt.json"
        migrate_report = args.report_dir / f"{name}-migration.json"

        audit_cmd = [
            sys.executable, str(AUDITOR), str(repo),
            "--foundation", str(args.foundation),
            "--report", str(audit_report),
        ]
        audit = run(audit_cmd)

        migrate_cmd = [
            sys.executable, str(MIGRATOR), str(repo),
            "--foundation", str(args.foundation),
            "--report", str(migrate_report),
        ]
        if args.apply:
            migrate_cmd.append("--apply")
        elif args.mirror_root:
            migrate_cmd += ["--mirror", str(args.mirror_root / name)]
        migrate = run(migrate_cmd)

        worst = max(worst, audit["returncode"], migrate["returncode"])
        results.append({"repo": str(repo), "audit": audit, "migration": migrate})

    aggregate = {
        "foundation": str(args.foundation),
        "mode": "apply" if args.apply else ("mirror" if args.mirror_root else "audit"),
        "results": results,
    }
    aggregate_path = args.report_dir / "ecosystem-summary.json"
    aggregate_path.write_text(json.dumps(aggregate, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(str(aggregate_path))
    return worst

if __name__ == "__main__":
    raise SystemExit(main())
