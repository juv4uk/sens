#!/usr/bin/env python3
"""Generate a provenance-bound structural projection of ratified D3 L1-L5 law.

This generator intentionally emits no compiler execution-role table. It only
materializes structural facts already ratified in #3202 so SENS code can derive
roles without treating host code or a generated table as semantic authority.
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
AUTHORITY = ROOT / "contracts/bija3-l1-l5-ratification.lisp"
OUTPUT = ROOT / "knowledge/bija3-l1-l5-structure-projection.json"


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
    block = one(
        r"\(bīja3\s*\.\s*\((.*?)\)\)\s*\n\s*\(d2-prefix-fibres",
        text,
        "bīja3 resident block",
    )
    residents = {
        bits: name
        for bits, name in re.findall(r"\(D3:([01]{3})\s+([A-Z][A-Z0-9-]*)\)", block)
    }
    if len(residents) != 8:
        raise SystemExit(f"expected 8 D3 residents, got {len(residents)}")

    by_name = {name: bits for bits, name in residents.items()}
    if len(by_name) != 8:
        raise SystemExit("D3 resident names must be unique")

    l1_empty = one(
        r'\(L1\s*\.\s*"([01]{3}) is structural empty \(\)"\)',
        text,
        "L1 empty root",
    )
    l4_mask = one(
        r'\(L4\s*\.\s*"dual3\(x\)=x XOR ([01]{3});',
        text,
        "L4 dual mask",
    )
    l5_names = one(
        r'\(L5\s*\.\s*"suffix-0 is the evaluator/metalinguistic spine:\s*([^"]+)"\)',
        text,
        "L5 spine",
    ).split(" -> ")
    l5_names = [name.strip() for name in l5_names]
    try:
        l5_spine = [by_name[name] for name in l5_names]
    except KeyError as error:
        raise SystemExit(f"L5 resident absent from D3 authority: {error.args[0]}") from error

    owner = one(r"\(owner-ratification\s*\.\s*#([0-9]+)\)", text, "owner ratification")
    schema = one(r"\(schema\s*\.\s*([^\s\)]+)\)", text, "schema")

    if l1_empty != by_name.get("EMPTY"):
        raise SystemExit("L1 empty root disagrees with ratified D3 resident map")
    if l4_mask != "111":
        raise SystemExit(f"unexpected current L4 dual mask: {l4_mask}")
    if len(l5_spine) != 4:
        raise SystemExit(f"expected four L5 spine nodes, got {len(l5_spine)}")
    if any(bits[-1] != "0" for bits in l5_spine):
        raise SystemExit("L5 spine must remain suffix-0 under the ratified law")

    mask = int(l4_mask, 2)
    for bits in residents:
        dual = f"{int(bits, 2) ^ mask:03b}"
        if dual not in residents:
            raise SystemExit(f"L4 dual escaped D3: {bits} -> {dual}")

    return {
        "schema": "bija3-l1-l5-structure-projection/1",
        "status": "generated-projection-only",
        "semantic_authority": {
            "path": "contracts/bija3-l1-l5-ratification.lisp",
            "schema": schema,
            "owner_ratification": f"#{owner}",
            "git_blob_sha1": git_blob(AUTHORITY),
            "sha256": sha256(AUTHORITY),
        },
        "domain": {
            "name": "D3",
            "width": 3,
        },
        "laws": {
            "L1_empty": l1_empty,
            "L4_dual_xor_mask": l4_mask,
            "L5_spine": l5_spine,
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
            print("D3 L1-L5 structural projection is stale; regenerate it.", file=sys.stderr)
            return 1
        return 0

    OUTPUT.write_text(generated, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
