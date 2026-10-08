#!/usr/bin/env python3
"""Безпечна міграція одного .lisp у same-stem фізичний T5 .sens.

Приклад:
    python3 scripts/migrate-one-to-sens.py tests/fixtures/foo.lisp

Правила:
- працює лише з одним явно названим .lisp;
- використовує існуючий трипрохідний мігратор + T5 codec;
- .lisp ніколи не переписується;
- наявний .sens ніколи не перезаписується;
- невідоме/неоднозначне джерело стає BLOCK, а не псевдо-.sens;
- результат містить source/output SHA256 і typed-word SHA256;
- --dry-run нічого не записує.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
MIGRATOR = ROOT / "scripts" / "migrate-to-sens-codes.py"
CODEC = ROOT / "scripts" / "sens_t5_codec.py"

DEFAULT_ARGS = {
    "foundation": ROOT / "knowledge" / "d1-d7-foundation.json",
    "domain_surfaces": ROOT / "lib" / "domains" / "d3.lisp",
    "semantic_registry": ROOT / "lib" / "surface" / "semantic-registry.lisp",
    "historical_map": ROOT / "contracts" / "core1-historical-sid-map.lisp",
    "text7": ROOT / "crates" / "sens" / "src" / "text7_projection_generated.rs",
}


def load_codec():
    spec = importlib.util.spec_from_file_location("sens_t5_codec", CODEC)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load codec: {CODEC}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def atomic_no_clobber(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="wb", prefix=".sens-one-", suffix=".tmp",
        dir=target.parent, delete=False,
    ) as staged:
        tmp = Path(staged.name)
        with source.open("rb") as src:
            shutil.copyfileobj(src, staged)
        staged.flush()
        os.fsync(staged.fileno())
    try:
        os.link(tmp, target)
    finally:
        tmp.unlink(missing_ok=True)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="один .lisp у поточному репозиторії")
    parser.add_argument("--output", type=Path, help="явний target; default = same-stem .sens")
    parser.add_argument("--dry-run", action="store_true", help="перевірити без запису target")
    args = parser.parse_args()

    source = args.source.resolve()
    if source.suffix.lower() != ".lisp":
        raise SystemExit("BLOCK: source must have .lisp extension")
    try:
        rel = source.relative_to(ROOT)
    except ValueError as exc:
        raise SystemExit("BLOCK: source must be inside the repository") from exc
    if not source.is_file():
        raise SystemExit(f"BLOCK: source does not exist: {rel}")

    output = (args.output or source.with_suffix(".sens")).resolve()
    source_hash_before = sha256_file(source)

    if output == source:
        raise SystemExit("BLOCK: output aliases source")
    if output.exists() and not args.dry_run:
        raise SystemExit(f"BLOCK: target already exists; refusing overwrite: {output.relative_to(ROOT)}")

    missing = [str(p.relative_to(ROOT)) for p in [MIGRATOR, CODEC, *DEFAULT_ARGS.values()] if not p.exists()]
    if missing:
        raise SystemExit("BLOCK: missing migration dependency: " + ", ".join(missing))

    rel_parent = rel.parent
    with tempfile.TemporaryDirectory(prefix="sens-one-stage-") as td:
        stage = Path(td) / "source"
        stage.mkdir(parents=True)
        staged_source = stage / rel_parent / rel.name
        staged_source.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, staged_source)
        stage_out = Path(td) / "out"
        report = Path(td) / "report.json"

        cmd = [
            sys.executable, str(MIGRATOR), str(stage),
            "--foundation", str(DEFAULT_ARGS["foundation"]),
            "--sens-mirror", str(stage_out),
            "--text7-projection", str(DEFAULT_ARGS["text7"]),
            "--historical-map", str(DEFAULT_ARGS["historical_map"]),
            "--semantic-registry", str(DEFAULT_ARGS["semantic_registry"]),
            "--domain-surfaces", str(DEFAULT_ARGS["domain_surfaces"]),
            "--report", str(report),
        ]
        completed = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
        state = json.loads(report.read_text(encoding="utf-8")) if report.exists() else None
        expected_rel = str(rel.with_suffix(".sens"))

        if completed.returncode != 0:
            print(json.dumps({
                "status": "blocked",
                "source": str(rel),
                "output": expected_rel,
                "reason": (state or {}).get("files", [{}])[0].get(
                    "reason", completed.stderr.strip() or "three-pass migrator blocked"
                ),
            }, ensure_ascii=False, indent=2))
            return 2

        generated = stage_out / rel.with_suffix(".sens")
        if not generated.is_file():
            print(json.dumps({
                "status": "blocked",
                "source": str(rel),
                "output": expected_rel,
                "reason": "three-pass migrator produced no same-stem physical .sens",
            }, ensure_ascii=False, indent=2))
            return 2

        codec = load_codec()
        payload = generated.read_bytes()
        words = codec.decode_bytes(payload)
        if codec.encode_words(words) != payload:
            raise SystemExit("BLOCK: generated bytes are not canonical T5")
        typed_hash = codec.typed_sha256(words)
        output_hash = hashlib.sha256(payload).hexdigest()

        result = {
            "status": "would-write" if args.dry_run else "written",
            "source": str(rel),
            "output": str(output.relative_to(ROOT)) if output.is_relative_to(ROOT) else str(output),
            "source_sha256": source_hash_before,
            "physical_sha256": output_hash,
            "typed_word_sha256": typed_hash,
            "bytes": len(payload),
            "words": words,
            "three_pass": (state or {}).get("files", [{}])[0].get("passes", {}),
        }

        if not args.dry_run:
            atomic_no_clobber(generated, output)
            if sha256_file(source) != source_hash_before:
                raise SystemExit("BLOCK: source changed during migration")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
