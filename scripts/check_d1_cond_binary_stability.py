#!/usr/bin/env python3
"""Fail-closed executable D1/COND regression on actual packed T5.

This is a bounded differential against directly evaluated D1 literals, not an
independent Lisp semantic oracle and not a claim of historical migration.
Rust/host records only byte-identical observations. Exact words own the cases.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from sens_t5_codec import decode_bytes, encode_words  # noqa: E402

# Contract 11.8: D1:1 selects, D1:0 skips, D3:110 COND has two-field clauses.
# Every program below contains only exact-width D1/D2/D3 source words.
POSITIVE = (
    ("select-first", "10 110 00 10 1 00 1 01 00 10 0 00 0 01 01", "1"),
    ("skip-first", "10 110 00 10 0 00 1 01 00 10 1 00 0 01 01", "0"),
    ("lazy-false", "10 110 00 10 0 00 10 100 00 000 01 01 00 10 1 00 0 01 01", "0"),
    ("lazy-true", "10 110 00 10 1 00 1 01 00 10 0 00 10 100 00 000 01 01 01", "1"),
)

NEGATIVE = (
    # Three fields in the first D3 clause must be rejected before evaluation.
    ("obsolete-three-field", "10 110 00 10 1 00 0 00 1 01 01", "requires exactly"),
    # Structural D3:000 EMPTY is not a D1 PredicateBit.
    ("structural-empty-test", "10 110 00 10 000 00 1 01 01", "expects exact D1"),
)


def program_file(directory: Path, name: str, visible: str) -> Path:
    words = visible.split(" ")
    physical = encode_words(words)
    if decode_bytes(physical) != words:
        raise AssertionError(f"{name}: physical T5 word identity failed")
    path = directory / (name + ".sens")
    path.write_bytes(physical)
    return path


def execute(cli: Path, file: Path, trit: bool) -> subprocess.CompletedProcess[bytes]:
    cmd = [str(cli), "eval", str(file)] if trit else [str(cli), str(file)]
    return subprocess.run(cmd, cwd=ROOT, capture_output=True, timeout=30, check=False)


def accepted(cli: Path, file: Path, trit: bool) -> bytes:
    result = execute(cli, file, trit)
    if result.returncode != 0 or not result.stdout or result.stderr:
        raise AssertionError(
            f"{cli.name}: {file.name}: expected clean value; "
            f"rc={result.returncode}, stdout={result.stdout!r}, "
            f"stderr={result.stderr[:500]!r}"
        )
    return result.stdout


def rejected(cli: Path, file: Path, trit: bool, needle: str) -> None:
    result = execute(cli, file, trit)
    if result.returncode == 0 or result.stdout:
        raise AssertionError(
            f"{cli.name}: {file.name}: invalid D1/COND program executed; "
            f"rc={result.returncode}, stdout={result.stdout[:200]!r}"
        )
    if needle.encode() not in result.stderr:
        raise AssertionError(
            f"{cli.name}: {file.name}: unexpected rejection; "
            f"expected {needle!r}, stderr={result.stderr[:500]!r}"
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sens", required=True, type=Path)
    parser.add_argument("--sens-trit", required=True, type=Path)
    args = parser.parse_args()
    sens, trit = args.sens.resolve(), args.sens_trit.resolve()
    if not sens.is_file() or not trit.is_file():
        parser.error("actual built sens and sens-trit executables required")

    observations: list[dict[str, object]] = []
    with TemporaryDirectory(prefix="sens-cond-d1-stability-") as temp:
        directory = Path(temp)
        direct: dict[str, bytes] = {}
        for bit in ("0", "1"):
            file = program_file(directory, "literal-d1-" + bit, bit)
            actual = accepted(sens, file, False)
            if actual != accepted(trit, file, True):
                raise AssertionError(f"D1:{bit}: CLIs disagree on direct literal")
            direct[bit] = actual
        if direct["0"] == direct["1"]:
            raise AssertionError("D1:0 and D1:1 are not distinguishable")

        for name, visible, expected_bit in POSITIVE:
            file = program_file(directory, name, visible)
            actual = accepted(sens, file, False)
            if actual != direct[expected_bit]:
                raise AssertionError(
                    f"{name}: expected direct D1:{expected_bit} byte observation; "
                    f"actual={actual!r}, baseline={direct[expected_bit]!r}"
                )
            if actual != accepted(trit, file, True):
                raise AssertionError(f"{name}: pure CLI entrypoints disagree")
            observations.append({
                "name": name,
                "status": "PASS",
                "expected_exact_D1": expected_bit,
                "t5_sha256": hashlib.sha256(file.read_bytes()).hexdigest(),
            })

        for name, visible, diagnostic in NEGATIVE:
            file = program_file(directory, name, visible)
            rejected(sens, file, False, diagnostic)
            rejected(trit, file, True, diagnostic)
            observations.append({
                "name": name,
                "status": "BLOCKED_AS_REQUIRED",
                "t5_sha256": hashlib.sha256(file.read_bytes()).hexdigest(),
            })

    print(json.dumps({
        "schema": "sens-executable-d1-cond-stability/v1",
        "status": "PASS",
        "scope": "physical exact D1/D2/D3; no independent semantics or D10 admission",
        "sens_executable_sha256": hashlib.sha256(sens.read_bytes()).hexdigest(),
        "sens_trit_executable_sha256": hashlib.sha256(trit.read_bytes()).hexdigest(),
        "observations": observations,
    }, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
