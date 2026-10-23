#!/usr/bin/env python3
"""Structural release preflight; NEVER a full release GO certificate (#4196).

The release stays NO-GO until a set of gates pass on ONE SHA (RELEASE.md). This
script does not *assert* GO -- it RUNS the gates that are executable here and
reports, per gate, GO / NO-GO with the reason, then an overall verdict. Each gate
is tied to the language-core axioms it enforces; the project principles P1-P5 are
included (P5 is the one about modern technologies: the corridor and the migration
must carry NEW technology, never legacy SID8/Sens8 contamination).

Gates (each is a script; missing scripts are reported UNVERIFIED, never PASS):
  corridor-sterile     scripts/check_sterile_zig_corridor.py      (G1,G5,S1-S4)
  corridor-structural  scripts/check_rust_sens_zig_corridor.py   (G6,G7,S2)
  corridor-only-path   scripts/check_migration_zig_only_path.py  (G6,G7,S2)
  corridor-coverage    scripts/check_rust_sens_corridor_coverage.py (G6,G7,S2)
  axiom-binding        scripts/check_corridor_axiom_binding.py   (G1,G5,G6,G7,S2)
  axiom-coverage       scripts/check_axiom_coverage.py           (G1-G8,S1-S3)
  principle-force      scripts/check_principle_force.py          (P1-P5)
  numeric-domain       scripts/check_numeric_domain_exclusive.py (G1,G5)
  rust-isolated        scripts/check_rust_isolated_only_zig.sh   (G6,S2, Zig-owned)
  rust-lisp-sens-io    scripts/check_rust_lisp_sens_io.py        (G1,S2)

Exit 0 when and ONLY when these ten structural checks pass.
This is not a release certificate: exact-SHA CI, native SENS oracles, T5
triples, and owner GO are separate publication requirements.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

GATES = [
    ("corridor-sterile", "scripts/check_sterile_zig_corridor.py", "G1,G5,S1-S4"),
    ("corridor-structural", "scripts/check_rust_sens_zig_corridor.py", "G6,G7,S2"),
    ("corridor-only-path", "scripts/check_migration_zig_only_path.py", "G6,G7,S2"),
    ("corridor-coverage", "scripts/check_rust_sens_corridor_coverage.py", "G6,G7,S2"),
    ("axiom-binding", "scripts/check_corridor_axiom_binding.py", "G1,G5,G6,G7,S2"),
    ("axiom-coverage", "scripts/check_axiom_coverage.py", "G1-G8,S1-S3"),
    ("principle-force", "scripts/check_principle_force.py", "P1-P5"),
    ("numeric-domain", "scripts/check_numeric_domain_exclusive.py", "G1,G5"),
    ("rust-isolated", "scripts/check_rust_isolated_only_zig.sh", "G6,S2"),
    ("rust-lisp-sens-io", "scripts/check_rust_lisp_sens_io.py", "G1,S2"),
]


# Existing positive terminal receipts emitted by the actual source checkers.
# Exit 0 alone (empty stub, wrong checker, symlinked replacement) is NOT
# evidence that the Rust -> Zig -> SENS structural migration guard ran.
# These are transport/provenance guards, not SENS semantic verdicts.
SUCCESS_MARKERS = {
    "scripts/check_sterile_zig_corridor.py": "STERILE_ZIG_CORRIDOR_PASS",
    "scripts/check_rust_sens_zig_corridor.py": "CORRIDOR_OK",
    "scripts/check_migration_zig_only_path.py": "MIGRATION_ZIG_ONLY_PATH_OK",
    "scripts/check_rust_sens_corridor_coverage.py": "COVERAGE_OK",
    "scripts/check_corridor_axiom_binding.py": "AXIOM_BINDING_OK",
    "scripts/check_axiom_coverage.py": "AXIOM_COVERAGE_OK",
    "scripts/check_principle_force.py": "PRINCIPLE_FORCE_OK",
    "scripts/check_numeric_domain_exclusive.py": "NUMERIC_DOMAIN_EXCLUSIVE_OK",
    "scripts/check_rust_isolated_only_zig.sh": "RUST_ISOLATED_ONLY_ZIG_OK",
    "scripts/check_rust_lisp_sens_io.py": "RUST_LISP_SENS_IO_OK",
}


def _positive_receipt(output: str, required: str) -> str | None:
    """Exactly one live terminal token; no blank, duplicate or earlier echo."""
    lines = [line.strip() for line in output.splitlines() if line.strip()]
    matching = [line for line in lines if line.split(maxsplit=1)[0] == required]
    if len(matching) != 1 or not lines or lines[-1] != matching[0]:
        return None
    return matching[0]


def run_gate(root: Path, script: str) -> tuple[str, str]:
    path = root / script
    # A link to an unreviewed program is not the canonical checked-in guard.
    if (root / "scripts").is_symlink() or path.is_symlink() or not path.is_file():
        return "UNVERIFIED", "missing regular checker script"
    marker = SUCCESS_MARKERS[script]
    try:
        proc = subprocess.run([sys.executable, str(path), str(root)],
                              capture_output=True, text=True, timeout=120)
    except (OSError, subprocess.TimeoutExpired, UnicodeError) as exc:
        return "UNVERIFIED", f"could not run: {exc}"
    lines = [line.strip() for line in proc.stdout.splitlines() if line.strip()]
    if proc.returncode != 0:
        details = lines or [line.strip() for line in proc.stderr.splitlines()
                            if line.strip()]
        return "NO-GO", (details[0] if details else f"exit={proc.returncode}")[:90]
    receipt = _positive_receipt(proc.stdout, marker)
    if receipt is None:
        return "UNVERIFIED", f"required terminal receipt absent: {marker}"
    return "GO", receipt[:90]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--json", default="")
    parser.add_argument(
        "--structural-only", action="store_true",
        help="check corridor/axioms only; never imply release publication GO",
    )
    ns = parser.parse_args()
    root = Path(ns.root).resolve()

    rows = []
    for name, script, axioms in GATES:
        verdict, note = run_gate(root, script)
        rows.append({"gate": name, "verdict": verdict, "axioms": axioms,
                     "script": script, "note": note})

    width = max(len(r["gate"]) for r in rows)
    print("RELEASE GO-GATE (per gate, from executable checks)")
    for r in rows:
        print(f"  {r['verdict']:<10} {r['gate']:<{width}}  [{r['axioms']}]  {r['note']}")

    go = sum(1 for r in rows if r["verdict"] == "GO")
    no_go = [r for r in rows if r["verdict"] == "NO-GO"]
    unver = [r for r in rows if r["verdict"] == "UNVERIFIED"]
    print(f"\nGO={go}/{len(rows)}  NO-GO={len(no_go)}  UNVERIFIED={len(unver)}")
    for r in no_go:
        print(f"  NO-GO: {r['gate']} -- {r['note']}")

    if ns.json:
        import json
        Path(ns.json).write_text(json.dumps({"schema": "sens-release-go-gate/v1",
                                             "gates": rows, "go": go, "total": len(rows),
                                             "release_go": False,
                                             "release_admission": "NOT_VERIFIED"},
                                            ensure_ascii=False, indent=2) + "\n",
                                 encoding="utf-8")

    if no_go:
        print("\nRELEASE_GATE_NO_GO (red is red -- fix the gate, do not greenwash)")
        return 1
    if unver:
        print("\nRELEASE_GATE_PARTIAL (some structural gates UNVERIFIED; release NO-GO)")
        return 1
    print("\nRELEASE_STRUCTURAL_GATES_GO 10/10 (NOT release admission)")
    print("RELEASE_STRUCTURAL_ONLY_PASS: physical/semantic release admission NOT_VERIFIED")
    print("RELEASE_ADMISSION_UNVERIFIED: exact SHA, full T5M triplets, native "
          "SENS oracles, independent CI and owner authorization belong to "
          "the separate publication gate")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
