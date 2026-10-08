#!/usr/bin/env python3
"""Мігрує рівно один .lisp у фізичний same-stem T5 .sens."""
from __future__ import annotations
import argparse
import importlib.util
import json
from hashlib import sha256
import os
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
MIGRATOR = ROOT / "scripts" / "migrate-to-sens-codes.py"
spec = importlib.util.spec_from_file_location("sens_bulk_migrator", MIGRATOR)
if spec is None or spec.loader is None:
    raise SystemExit(f"cannot load {MIGRATOR}")
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)

FOUNDATION = ROOT / "knowledge" / "d1-d7-foundation.json"
TEXT7 = ROOT / "crates/sens/src/text7_projection_generated.rs"
REGISTRY = ROOT / "lib/surface/semantic-registry.lisp"
HISTORICAL = ROOT / "contracts/core1-historical-sid-map.lisp"
DOMAINS = [ROOT / "lib" / "domains" / f"d{n}.lisp" for n in range(1, 7)]

def atomic_no_clobber(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    staged = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb", prefix=".sens-one-", suffix=".tmp",
            dir=path.parent, delete=False,
        ) as handle:
            staged = Path(handle.name)
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.link(staged, path)
    finally:
        if staged is not None:
            staged.unlink(missing_ok=True)

def migrate_one(source: Path, target: Path, check_only: bool) -> dict:
    source = source.resolve()
    target = target.resolve()
    if source.suffix.lower() != ".lisp":
        raise SystemExit("source must have .lisp extension")
    if target.suffix.lower() != ".sens":
        raise SystemExit("target must have .sens extension")
    if target.name != source.with_suffix(".sens").name:
        raise SystemExit("target basename must match source basename")
    if target.exists() or target.is_symlink():
        raise SystemExit(f"target exists; refusing overwrite: {target}")

    foundation, foundation_sha = mod.load_foundation(FOUNDATION)
    code_map = mod.build_map(foundation, ["D3", "D4", "D5", "D6"])
    code_map = mod.augment_code_map_with_domain_surfaces(code_map, DOMAINS)
    code_map = mod.augment_code_map_with_registry_aliases(code_map, REGISTRY)
    text7 = mod.build_text7_encoder(foundation, TEXT7)
    resolver = mod.build_resolver(
        historical_map=HISTORICAL,
        foundation=FOUNDATION,
        registry=REGISTRY,
        domain_surfaces=DOMAINS,
    )
    source_text = source.read_text(encoding="utf-8")
    visible, hits, shadowed = mod.binary_rewrite(
        source_text, code_map, text7, resolver=resolver
    )
    words = mod.parse_words(visible)
    physical = mod.encode_projection(visible)
    if mod.decode_bytes(physical) != words:
        raise SystemExit("physical T5 round-trip changed exact words")

    result = {
        "status": "check" if check_only else "written",
        "source": str(source.relative_to(ROOT)) if source.is_relative_to(ROOT) else str(source),
        "target": str(target.relative_to(ROOT)) if target.is_relative_to(ROOT) else str(target),
        "source_sha256": sha256(source.read_bytes()).hexdigest(),
        "foundation_sha256": foundation_sha,
        "semantic_word_count": len(words),
        "semantic_bits": sum(len(w) for w in words),
        "transport_trits": sum(len(w) for w in words) + len(words) - 1,
        "physical_bytes": len(physical),
        "physical_sha256": sha256(physical).hexdigest(),
        "typed_word_sha256": mod.typed_sha256(words),
        "resolved_heads": [h.label for h in hits],
        "shadowed_labels": shadowed,
    }
    if not check_only:
        atomic_no_clobber(target, physical)
    return result

def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("source", type=Path)
    p.add_argument("--output", type=Path)
    p.add_argument("--check", action="store_true")
    args = p.parse_args()
    target = args.output or args.source.with_suffix(".sens")
    print(json.dumps(migrate_one(args.source, target, args.check), ensure_ascii=False, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
