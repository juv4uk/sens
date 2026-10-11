#!/usr/bin/env python3
"""Pinned donor Go integer-inequality replay versus independent Python integers.

Proves agreement on a finite adversarial corpus for one D10 meaning. This
does not establish universal semantics or SENS runtime evaluation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DONOR_COMMIT = "f6719457ff38e01fc87c6aea027bedfad1742cdd"
DONOR_SOURCE = "lisp1_5/math.go"
DONOR_BLOB = "724b065b8e4f12eb7c2912e77b949328ec83f409"
SELECTED_BLOB = "4523aad78809da4da9ce37408a676e352b1ec508"
FN = "func ne(a, b *big.Int) bool { return a.Cmp(b) != 0 }"
D10_BITCODE = "0000000111"
D10_ID = "d10.crossrepo.early.c54e7e4316a0f576"


def need(value: bool, explanation: str) -> None:
    if not value:
        raise ValueError("D10_NUMERIC_NE_BLOCK:" + explanation)


def git_blob(raw: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()


def pinned_json(path: Path, expected_sha: str) -> dict:
    raw = path.read_bytes()
    need(git_blob(raw) == expected_sha, "pinned JSON drift " + str(path))
    return json.loads(raw)


def corpus() -> list[tuple[int, int]]:
    small = list(range(-32, 33))
    rows = [(a, b) for a in small for b in small]
    edge = [0, 1, -1, (1 << 127) - 1, 1 << 127,
            (1 << 127) + 1, -((1 << 127) + 1),
            10 ** 80, -(10 ** 80), (1 << 255) - 19]
    rows.extend((a, b) for a in edge for b in edge)
    return rows


def go_executable_source() -> str:
    return """package main
import (
  "bufio"
  "fmt"
  "math/big"
  "os"
  "strings"
)
""" + FN + """
func main() {
  scanner := bufio.NewScanner(os.Stdin)
  for scanner.Scan() {
    parts := strings.Fields(scanner.Text())
    if len(parts) != 2 { panic("expected two exact integer words") }
    a, ok := new(big.Int).SetString(parts[0], 10)
    if !ok { panic("invalid left integer") }
    b, ok := new(big.Int).SetString(parts[1], 10)
    if !ok { panic("invalid right integer") }
    if ne(a, b) { fmt.Println("1") } else { fmt.Println("0") }
  }
  if err := scanner.Err(); err != nil { panic(err) }
}
"""


def witness(root: Path, donor_root: Path, self_test: bool = False) -> dict:
    owner = json.loads((root / "knowledge/d10-owner-whole-domain-ratification-20261012.json").read_text(encoding="utf-8"))
    ptr = json.loads((root / "knowledge/d10-current-inventory.json").read_text(encoding="utf-8"))
    need(owner["ratified"] is True and
         owner["inventory"]["git_blob"] == ptr["canonical_current"]["git_blob"],
         "whole-domain owner decision or inventory pin")
    inv = pinned_json(root / owner["inventory"]["path"], owner["inventory"]["git_blob"])
    selected = pinned_json(root / "knowledge/d10-crossrepo-early-lisp-v1.json", SELECTED_BLOB)
    matches = [r for r in inv["rows"] if r["coordinate"] == D10_BITCODE]
    need(len(matches) == 1 and matches[0]["stable_id"] == D10_ID and
         matches[0]["semantic_name"] == "NUMERIC-NOT-EQUAL", "D10 code identity")
    claims = [r for r in selected["selected_rows"] if r["stable_id"] == D10_ID]
    need(len(claims) == 1 and claims[0]["donor_repo"] == "juv4uk/lisp-1" and
         claims[0]["source_file"] == DONOR_SOURCE, "selected source mismatch")

    source = (donor_root / DONOR_SOURCE).resolve()
    need(source.is_relative_to(donor_root.resolve()) and source.is_file(),
         "pinned donor source not checked out")
    raw = source.read_bytes()
    need(git_blob(raw) == DONOR_BLOB, "donor must match pinned exact Go blob")
    code = raw.decode("utf-8")
    need(code.count(FN) == 1 and
         bool(re.search(r"func \(c \*Context\) neFunc\([^\n]*", code)),
         "ne leaf function or entry point missing")
    pairs = corpus()
    stdin = "".join(f"{a} {b}\n" for a, b in pairs)
    with tempfile.TemporaryDirectory(prefix="d10-ne-") as temp:
        program = Path(temp) / "main.go"
        program.write_text(go_executable_source(), encoding="utf-8")
        result = subprocess.run(
            ["go", "run", str(program)], input=stdin, text=True,
            capture_output=True, timeout=120, check=False)
    need(result.returncode == 0, "Go donor leaf replay failed: " + result.stderr[-1200:])
    outputs = result.stdout.splitlines()
    need(len(outputs) == len(pairs), "Go replay omitted cases")
    expected = [str(int(a != b)) for a, b in pairs]
    need(all(g in ("0", "1") and g == e for g, e in zip(outputs, expected)),
         "Go math/big versus independent Python integer inequality mismatch")
    if self_test:
        need("0" in outputs and "1" in outputs, "non-discriminating corpus")
        wrong = [str(int(a == b)) for a, b in pairs]
        need(any(x != y for x, y in zip(outputs, wrong)),
             "negative control (inverted comparison) went undetected")
        need(any(a.bit_length() > 128 for a, _ in pairs),
             "large-integer edge case absent")
    return {
        "schema": "d10-numeric-ne-pinned-donor-leaf-replay/v1",
        "D10": D10_BITCODE,
        "donor_repo": "juv4uk/lisp-1",
        "donor_commit": DONOR_COMMIT,
        "donor_blob": DONOR_BLOB,
        "exact_integer_pairs": len(pairs),
        "mismatches": 0,
        "negative_comparison_control_rejected": self_test,
        "F1_pinned_donor_leaf": True,
        "F2_cross_language_integer_leaf_cases_replayed": True,
        "F2_full_SENS_oracle_or_evaluator_verified": False,
        "F3_global_semantic_distinctness_verified": False,
        "F4_native_T5_runtime_admitted": False,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--donor-root", required=True, type=Path)
    parser.add_argument("--self-test", action="store_true")
    options = parser.parse_args()
    print(json.dumps(witness(ROOT, options.donor_root, options.self_test),
                     sort_keys=True))
