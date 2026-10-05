#!/usr/bin/env python3
"""Generate a provenance-bound structural projection of the ratified D4 bootstrap fibre.

The output deliberately contains no compiler execution-role names and no backend
mechanism mapping. It materializes only the owner-ratified QUOTE-parent fibre
that contains the two irreducible bootstrap children, so executable SENS code
can assign compiler roles without host-owned meaning.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUTHORITY = ROOT / "contracts/d4-bootstrap-ratification.lisp"
OUTPUT = ROOT / "knowledge/d4-bootstrap-compiler-structure-projection.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_blob(path: Path) -> str:
    result = subprocess.run(
        ["git", "-C", str(ROOT), "hash-object", str(path)],
        check=True,
        capture_output=True,
        text=True,
    )
    value = result.stdout.strip()
    if not re.fullmatch(r"[0-9a-f]{40}", value):
        raise SystemExit(f"invalid git blob id for {path}: {value!r}")
    return value


def one(pattern: str, text: str, label: str) -> str:
    match = re.search(pattern, text, re.MULTILINE | re.DOTALL)
    if not match:
        raise SystemExit(f"missing {label} in {AUTHORITY}")
    return match.group(1)


def parse_authority(text: str) -> dict[str, object]:
    resident_block = one(
        r"\(residents\s*\.\s*\((.*?)\)\)\s*\n\s*\(d3-fibres",
        text,
        "D4 resident block",
    )
    residents = {
        bits: name
        for bits, name in re.findall(
            r"\(D4:([01]{4})\s+([A-Z][A-Z0-9-]*)\)", resident_block
        )
    }
    if len(residents) != 16:
        raise SystemExit(f"expected 16 D4 residents, got {len(residents)}")
    by_name = {name: bits for bits, name in residents.items()}
    if len(by_name) != 16:
        raise SystemExit("D4 resident names must be unique")

    fibre_block = one(
        r"\(d3-fibres\s*\.\s*\((.*?)\)\)\s*\n\s*\(classification",
        text,
        "D3 fibre block",
    )
    fibres = [
        (parent, left, right)
        for parent, left, right in re.findall(
            r"\(D3:([01]{3})\s+([A-Z][A-Z0-9-]*)\s+([A-Z][A-Z0-9-]*)\)",
            fibre_block,
        )
    ]
    if len(fibres) != 8:
        raise SystemExit(f"expected 8 D3->D4 fibres, got {len(fibres)}")

    quote_fibre = [
        (parent, left, right)
        for parent, left, right in fibres
        if left == "LAMBDA" and right == "DEFINE"
    ]
    if len(quote_fibre) != 1:
        raise SystemExit("expected exactly one ratified LAMBDA/DEFINE fibre")
    parent_bits, left_name, right_name = quote_fibre[0]
    children = [by_name[left_name], by_name[right_name]]

    # The ratified D4 coordinates must preserve the D3 parent as the first
    # three bits. This verifies structure; it does not assign compiler roles.
    if children != [parent_bits + "0", parent_bits + "1"]:
        raise SystemExit(
            f"D4 irreducible bootstrap fibre is not an exact D3 prefix fibre: "
            f"{parent_bits} -> {children}"
        )

    classification = one(
        r"\(irreducible-bootstrap\s+([^\)]+)\)",
        text,
        "irreducible bootstrap classification",
    ).split()
    if classification != ["LAMBDA", "DEFINE"]:
        raise SystemExit(
            f"unexpected irreducible bootstrap classification: {classification}"
        )

    owner = one(r"\(owner-ratification\s*\.\s*#([0-9]+)\)", text, "owner ratification")
    schema = one(r"\(schema\s*\.\s*([^\s\)]+)\)", text, "schema")

    return {
        "schema": "d4-bootstrap-compiler-structure-projection/1",
        "status": "generated-projection-only",
        "semantic_authority": {
            "path": "contracts/d4-bootstrap-ratification.lisp",
            "schema": schema,
            "owner_ratification": f"#{owner}",
            "git_blob_sha1": git_blob(AUTHORITY),
            "sha256": sha256(AUTHORITY),
        },
        "domain": {
            "name": "D4",
            "width": 4,
        },
        "irreducible_bootstrap_fibre": {
            "parent_domain": "D3",
            "parent_bits": parent_bits,
            "children": children,
        },
        "non_authority": {
            "compiler_role_table": False,
            "backend_mechanism_table": False,
            "human_name_routing": False,
            "d8_admission": False,
        },
    }


def render() -> str:
    data = parse_authority(AUTHORITY.read_text(encoding="utf-8"))
    canonical = json.dumps(
        data,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    data["projection_sha256"] = hashlib.sha256(canonical).hexdigest()
    return json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    generated = render()
    if args.check:
        if not OUTPUT.is_file():
            print(f"missing generated projection: {OUTPUT}", file=sys.stderr)
            return 1
        if OUTPUT.read_text(encoding="utf-8") != generated:
            print("D4 bootstrap structural projection is stale; regenerate it.", file=sys.stderr)
            return 1
        return 0

    OUTPUT.write_text(generated, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
