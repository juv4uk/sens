#!/usr/bin/env python3
"""Semantic identity stability benchmark.

Reads the canonical Lisp registry, never the generated Rust projection.  It
measures representation cost and runs a deterministic source-level
rename-perturbation oracle: surface spellings may change, while the canonical
binary identity must remain the same.  This is not a runtime performance
claim and does not prove evaluator behavior.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REGISTRY = ROOT / "lib/surface/semantic-registry.lisp"
ROW_RE = re.compile(r"^\s*\(([01]{8})\s+(.*)\)\s*$")
SLOT_RE = re.compile(r"\((en|ук|укр|sa|sym)\s+(?:\(\)|([^()]*))\)")
NAMESPACES = ("en", "ук", "укр", "sa", "sym")


def parse_registry(path: Path) -> list[dict]:
    rows: list[dict] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        match = ROW_RE.match(line)
        if not match:
            continue
        bits, body = match.groups()
        slots = dict(SLOT_RE.findall(body))
        if set(slots) != set(NAMESPACES):
            raise SystemExit(f"line {line_no}: expected exactly {NAMESPACES}, got {sorted(slots)}")
        rows.append({"bits": bits, "value": int(bits, 2), "surfaces": {
            ns: (None if slots[ns] == "" else slots[ns]) for ns in NAMESPACES
        }})
    if not rows:
        raise SystemExit(f"no canonical registry rows found in {path}")
    return rows


def surface_bytes(rows: list[dict]) -> int:
    return sum(len(value.encode("utf-8")) for row in rows for value in row["surfaces"].values() if value is not None)


def rename_rows(rows: list[dict]) -> list[dict]:
    renamed = []
    for index, row in enumerate(rows):
        surfaces = {
            ns: (None if value is None else f"r{index:03d}-{ns}-{index:04d}")
            for ns, value in row["surfaces"].items()
        }
        renamed.append({"bits": row["bits"], "value": row["value"], "surfaces": surfaces})
    return renamed


def lookup(rows: list[dict]) -> dict[tuple[str, str], int]:
    result: dict[tuple[str, str], int] = {}
    for row in rows:
        for ns, value in row["surfaces"].items():
            if value is None:
                continue
            key = (ns, value)
            if key in result:
                raise SystemExit(f"surface collision: {key}")
            result[key] = row["value"]
    return result


def run(registry: Path) -> dict:
    raw = registry.read_bytes()
    rows = parse_registry(registry)
    identity_values = [row["value"] for row in rows]
    if len(identity_values) != len(set(identity_values)):
        raise SystemExit("duplicate canonical identity")
    base_lookup = lookup(rows)
    renamed = rename_rows(rows)
    renamed_lookup = lookup(renamed)
    expected_renamed = {
        (ns, f"r{index:03d}-{ns}-{index:04d}"): row["value"]
        for index, row in enumerate(rows)
        for ns, value in row["surfaces"].items()
        if value is not None
    }
    if renamed_lookup != expected_renamed:
        raise SystemExit("rename perturbation changed identity mapping")
    complete = sum(all(row["surfaces"][ns] is not None for ns in ("en", "укр", "sa")) for row in rows)
    surface_count = len(base_lookup)
    source_bytes = len(raw)
    id_payload_bytes = (len(rows) * 8 + 7) // 8
    result = {
        "schema": "sens-semantic-identity-stability/v1",
        "authority": "lib/surface/semantic-registry.lisp",
        "authority_sha256": hashlib.sha256(raw).hexdigest(),
        "rows": len(rows),
        "unique_identity_count": len(set(identity_values)),
        "surface_count": surface_count,
        "complete_en_ukr_sa_rows": complete,
        "canonical_source_bytes": source_bytes,
        "identity_payload_bytes_lower_bound": id_payload_bytes,
        "surface_utf8_bytes": surface_bytes(rows),
        "surface_to_identity_entries": surface_count,
        "rename_cases": surface_count,
        "rename_identity_parity": True,
        "surface_collision_count": 0,
        "oracle": "canonical identity unchanged under deterministic surface rename",
        "scope": "source-level representation invariant; not evaluator/runtime proof",
    }
    return result


def report(result: dict) -> str:
    return "\n".join([
        "# Semantic identity stability",
        "",
        f"- Canonical rows: **{result['rows']}**; unique identities: **{result['unique_identity_count']}**.",
        f"- Surface entries: **{result['surface_count']}**; complete EN/UKR/SA rows: **{result['complete_en_ukr_sa_rows']}**.",
        f"- Canonical source: **{result['canonical_source_bytes']} B**; identity payload lower bound: **{result['identity_payload_bytes_lower_bound']} B**.",
        f"- Surface UTF-8 bytes: **{result['surface_utf8_bytes']} B**.",
        f"- Rename perturbation: **{result['rename_identity_parity']}** across {result['rename_cases']} surfaces; collisions: **{result['surface_collision_count']}**.",
        "",
        "> The rename result is a source-level identity invariant. It does not claim that every runtime loader or evaluator already accepts every renamed surface.",
        "",
        f"Authority SHA-256: `{result['authority_sha256']}`",
        "",
    ])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.registry)
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (args.out / "report.md").write_text(report(result), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
