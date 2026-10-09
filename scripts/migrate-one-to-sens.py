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
- --dry-run нічого не записує;
- джерело обробляє ТІЛЬКИ scripts/migrate-three-pass.py (D1–D9);
- невизначені символи/рядки не перетворюються в неструктуровані D7 комірки;
- без незалежного D2+oracle-доказу у git-репозиторій нічого не публікуємо.
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
MIGRATOR = ROOT / "scripts" / "migrate-three-pass.py"
CODEC = ROOT / "scripts" / "sens_t5_codec.py"

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
    parser.add_argument("--source-era", choices=("auto", "legacy", "current"), default="auto",
                        help="auto блокує двозначні W8; legacy = історичний SID8, current = D8")
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
    if (output.exists() or output.is_symlink()) and not args.dry_run:
        display = str(output.relative_to(ROOT)) if output.is_relative_to(ROOT) else str(output)
        raise SystemExit(f"BLOCK: target already exists; refusing overwrite: {display}")
    if not args.dry_run and output.is_relative_to(ROOT):
        raise SystemExit(
            "BLOCK: in-repository publication needs independent Rust D2/oracle proof; "
            "use scripts/admit-t5-migration.py or --output /tmp/your-file.sens for physical staging"
        )

    missing = [str(p.relative_to(ROOT)) for p in [MIGRATOR, CODEC] if not p.exists()]
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
            sys.executable, str(MIGRATOR), str(staged_source),
            "--out", str(stage_out),
            "--source-era", args.source_era,
            "--report", str(report),
        ]
        completed = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
        state = json.loads(report.read_text(encoding="utf-8")) if report.exists() else None
        expected_rel = str(rel.with_suffix(".sens"))

        if completed.returncode != 0:
            file_rows = (state or {}).get("files") or [{}]
            print(json.dumps({
                "status": "blocked",
                "source": str(rel),
                "output": expected_rel,
                "source_era": args.source_era,
                "reason": file_rows[0].get(
                    "reason", completed.stderr.strip() or "canonical three-pass migrator blocked"
                ),
            }, ensure_ascii=False, indent=2))
            return 2

        generated = stage_out / staged_source.with_suffix(".sens").name
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
            "source_era": args.source_era,
            "semantic_parity": "NOT_VERIFIED",
            "three_pass": (state or {}).get("files", [{}])[0].get("passes", {}),
        }

        if sha256_file(source) != source_hash_before:
            raise SystemExit("BLOCK: source changed during migration")
        if not args.dry_run:
            atomic_no_clobber(generated, output)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
