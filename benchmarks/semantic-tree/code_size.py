#!/usr/bin/env python3
"""#3582: mode-specialized D6 selector code-size accounting.

This is benchmark-only. It compiles the same fixed 16-selector corpus into
three separate binaries so executable/data footprint is not hidden inside one
shared multi-mode executable.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import platform
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = Path(__file__).with_name("code_size.rs")
LANES = {
    "flat16": "lane_flat",
    "generator-direct": "lane_generator",
    "generator-compiled": "lane_compiled",
}


def sh(args, *, cwd=ROOT):
    return subprocess.run(args, cwd=cwd, check=True, text=True, capture_output=True)


def section_sizes(binary: Path) -> dict[str, int]:
    proc = sh(["size", "-A", "-d", str(binary)])
    sections: dict[str, int] = {}
    for line in proc.stdout.splitlines():
        parts = line.split()
        if len(parts) < 2:
            continue
        try:
            size = int(parts[1])
        except ValueError:
            continue
        sections[parts[0]] = size

    def sum_prefix(prefix: str) -> int:
        return sum(v for k, v in sections.items() if k == prefix or k.startswith(prefix + "."))

    return {
        "text_bytes": sum_prefix(".text"),
        "rodata_bytes": sum_prefix(".rodata"),
        "data_bytes": sum_prefix(".data"),
        "bss_bytes": sum_prefix(".bss"),
    }


def parse_run(binary: Path, calls: int) -> dict[str, int | str]:
    proc = sh([str(binary), str(calls)])
    out: dict[str, int | str] = {}
    for line in proc.stdout.splitlines():
        if "\t" not in line:
            continue
        key, value = line.split("\t", 1)
        out[key.lower()] = value if key == "LANE" else int(value)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--calls", type=int, default=100_000)
    ap.add_argument("--out", default="")
    args = ap.parse_args()
    if args.calls <= 0:
        raise SystemExit("--calls must be positive")

    if shutil.which("rustc") is None or shutil.which("size") is None or shutil.which("strip") is None:
        raise SystemExit("rustc, GNU size and strip are required")

    out_dir = Path(args.out) if args.out else ROOT / "benchmarks/semantic-tree/results/code-size"
    out_dir.mkdir(parents=True, exist_ok=True)

    rows = []
    checksums = set()

    with tempfile.TemporaryDirectory(prefix="sens-3582-") as td:
        td_path = Path(td)
        for lane, cfg in LANES.items():
            binary = td_path / lane
            sh([
                "rustc", "-O", "-C", "debuginfo=0", "-C", "panic=abort",
                "--cfg", cfg, str(SOURCE), "-o", str(binary),
            ])
            run = parse_run(binary, args.calls)
            if run.get("lane") != lane:
                raise RuntimeError(f"lane mismatch: expected {lane}, got {run!r}")
            checksums.add(int(run["checksum"]))

            stripped = td_path / f"{lane}.stripped"
            shutil.copy2(binary, stripped)
            sh(["strip", "--strip-all", str(stripped)])

            row = {
                "lane": lane,
                "calls": args.calls,
                "checksum": int(run["checksum"]),
                "prepared_bytes": int(run["prepared_bytes"]),
                "exec_path_bytes": int(run["exec_path_bytes"]),
                "file_bytes": binary.stat().st_size,
                "stripped_file_bytes": stripped.stat().st_size,
            }
            row.update(section_sizes(binary))
            rows.append(row)

    if len(checksums) != 1:
        raise RuntimeError(f"semantic parity failed: checksums={sorted(checksums)}")

    fieldnames = list(rows[0].keys())
    with (out_dir / "code_size.tsv").open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    env = {
        "schema": "sens-d6-selector-code-size/v1",
        "issue": "#3582",
        "parent_benchmark": "#3597 / #1988",
        "authority": "#3393 / Contract 11.5",
        "runtime_mechanism": "#3588 / #3394",
        "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        "git_sha": sh(["git", "rev-parse", "HEAD"]).stdout.strip(),
        "rustc": sh(["rustc", "--version"]).stdout.strip(),
        "size": sh(["size", "--version"]).stdout.splitlines()[0],
        "strip": sh(["strip", "--version"]).stdout.splitlines()[0],
        "python": platform.python_version(),
        "machine": platform.machine(),
        "semantic_rule": "same checksum first; code size has no semantic authority",
    }
    (out_dir / "environment.json").write_text(
        json.dumps(env, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print("semantic parity: PASS")
    for row in rows:
        print(
            f"{row['lane']:18s} text={row['text_bytes']:6d} "
            f"rodata={row['rodata_bytes']:6d} stripped={row['stripped_file_bytes']:7d} "
            f"prepared={row['prepared_bytes']:7d}"
        )
    print(f"wrote {out_dir / 'code_size.tsv'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
