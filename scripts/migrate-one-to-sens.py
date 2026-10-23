#!/usr/bin/env python3
"""Міграція одного .lisp у парні фізичний T5M .sens та двійковий перегляд.

Один вихідний файл -> перевірена Zig/T5M пара .sens + файл без розширення.
Джерело та наявні артефакти не перезаписуються. Історичний T5 — тільки перегляд,
нові фізичні файли випускаються через Zig/T5M.
Цей фізичний доказ сам по собі НЕ засвідчує семантику виконання.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
MIGRATOR = ROOT / "scripts" / "migrate-three-pass.py"
CODEC = ROOT / "scripts" / "sens_t5_t5m_codec.py"
sys.path.insert(0, str(ROOT / "scripts"))
import migration_publish_pair

def load_codec():
    spec = importlib.util.spec_from_file_location("sens_t5_t5m_codec", CODEC)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load codec: {CODEC}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def resolve_without_links(path: Path, role: str) -> Path:
    """Зберегти походження source/output: жодних symlink або '..' до resolve()."""
    if ".." in path.parts:
        raise SystemExit(f"BLOCK: {role} path contains parent traversal")
    absolute = path.absolute()
    for component in (absolute, *absolute.parents):
        if component.is_symlink():
            raise SystemExit(f"BLOCK: {role} path contains symlink: {component}")
    return absolute.resolve()


def atomic_no_clobber(target: Path, data: bytes) -> None:
    """Write a verified carrier or view once, without following target links."""
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="wb", prefix=".sens-one-", suffix=".tmp",
        dir=target.parent, delete=False,
    ) as staged:
        temp = Path(staged.name)
        staged.write(data)
        staged.flush()
        os.fsync(staged.fileno())
    try:
        os.link(temp, target)
    finally:
        temp.unlink(missing_ok=True)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_upstream_t5_witness(report, source_name, words, payload, codec_name, codec):
    """Check actual three-pass/Zig witness; not a semantic approval."""
    if not isinstance(report, dict) or report.get("schema") != "sens-three-pass-t5-migration/v3":
        raise ValueError("THREE_PASS_WITNESS: missing v3 report")
    if (report.get("mode") != "write-new-only-zig-minted" or
            report.get("physical_producer") != "PINNED_ZIG_" + codec_name.upper() + "_CARRY"):
        raise ValueError("THREE_PASS_WITNESS: source not minted by Zig")
    fmt = report.get("file_format")
    if not isinstance(fmt, dict) or not str(fmt.get("physical", "")).startswith("binary-" + codec_name.upper() + "-"):
        raise ValueError("THREE_PASS_WITNESS: physical codec mismatch")
    rows, summary = report.get("files"), report.get("summary")
    if not isinstance(rows, list) or len(rows) != 1 or not isinstance(summary, dict):
        raise ValueError("THREE_PASS_WITNESS: expected exactly one source")
    for key, val in (("files_seen", 1), ("files_written", 1), ("files_blocked", 0)):
        if type(summary.get(key)) is not int or summary[key] != val:
            raise ValueError("THREE_PASS_WITNESS: accounting mismatch: " + key)
    row = rows[0]
    expected = {
        "path": source_name, "output": str(Path(source_name).with_suffix(".sens")),
        "status": "written", "bytes": len(payload),
        "semantic_word_count": len(words), "semantic_bits": sum(map(len, words)),
        "transport_trits": sum(map(len, words)) + len(words) - 1,
        "physical_sha256": hashlib.sha256(payload).hexdigest(),
        "typed_word_sha256": codec.typed_sha256(words),
    }
    for key, val in expected.items():
        if type(row.get(key)) is not type(val) or row[key] != val:
            raise ValueError("THREE_PASS_WITNESS: receipt mismatch " + key)
    receipt = row.get("zig_transport")
    if (not isinstance(row.get("passes"), dict) or row.get("semantic_admitted") is not False or
            not isinstance(receipt, dict) or
            receipt.get("physical_sha256") != expected["physical_sha256"] or
            receipt.get("source_pin_status") != "MATCHED_CALLER_SUPPLIED_SHA256" or
            not receipt.get("zig_binary_sha256")):
        raise ValueError("THREE_PASS_WITNESS: Zig receipt missing/mismatched")
    return expected


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--output", type=Path, help="same-stem .sens by default")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--replace-existing", action="store_true",
                        help="refresh an existing same-stem .sens + extensionless view pair")
    parser.add_argument("--codec", choices=("t5m", "t5"), default="t5m")
    parser.add_argument("--source-surface", choices=("default", "ук", "укр"), default="укр")
    parser.add_argument("--binding-source", action="append", type=Path, default=[],
                        help="явно завантажений Lisp-файл, що визначає зовнішні замикання")
    args = parser.parse_args()
    # Історичний T5 — лише діагностика. Нові фізичні .sens
    # створюються тільки через сучасний Zig/T5M.
    if args.codec == "t5" and not args.dry_run:
        raise SystemExit(
            "LEGACY_T5_PUBLICATION_DISABLED: use Zig/T5M for current .sens; "
            "--codec t5 is read-only with --dry-run"
        )
    source = resolve_without_links(args.source, "source")
    if source.suffix != ".lisp":
        raise SystemExit("BLOCK: source must have .lisp extension")
    if not source.is_file():
        raise SystemExit("BLOCK: source does not exist: " + str(source))
    try:
        rel = source.relative_to(ROOT)
    except ValueError as exc:
        raise SystemExit("BLOCK: source must be inside the repository") from exc
    output = resolve_without_links(args.output or source.with_suffix(".sens"), "output")
    if output.suffix != ".sens":
        raise SystemExit("BLOCK: target must have .sens extension")
    view = resolve_without_links(output.with_suffix(""), "view")
    existing_targets = {}
    for target in (output, view):
        if target.is_symlink():
            raise SystemExit("BLOCK: target path contains symlink: " + str(target))
        if target.exists() and not target.is_file():
            raise SystemExit("BLOCK: target must be a regular file: " + str(target))
        existing_targets[target] = target.is_file()
        if existing_targets[target] and not args.replace_existing and not args.dry_run:
            raise SystemExit("BLOCK: target already exists; refusing overwrite: " + str(target))
    if source in (output, view):
        raise SystemExit("BLOCK: source cannot be the target")
    original = source.read_bytes()
    with tempfile.TemporaryDirectory(prefix="sens-one-stage-") as temp:
        stage = Path(temp) / "out"
        report_path = Path(temp) / "report.json"
        # Do not clone source to /tmp: preserve its Git path for nonprogram
        # classification and historical identity in the shared migrator.
        command = [sys.executable, str(MIGRATOR), str(source),
                   "--out", str(stage), "--report", str(report_path),
                   "--codec", args.codec, "--source-surface", args.source_surface]
        for binding_source in args.binding_source:
            command.extend(["--binding-source", str(binding_source)])
        if args.dry_run:
            command.append("--dry-run")
        process = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
        report = json.loads(report_path.read_text(encoding="utf-8")) if report_path.exists() else None
        if process.returncode:
            row = ((report or {}).get("files") or [{}])[0]
            print(json.dumps({
                "status": "blocked", "source": str(rel),
                "output": str(rel.with_suffix(".sens")), "codec": args.codec,
                "reason": row.get("reason", process.stderr.strip() or "three-pass failed"),
                "token": row.get("token"), "line": row.get("line"), "column": row.get("column"),
            }, ensure_ascii=False, indent=2))
            return 2
        # Dry-run is a read-only preview: the upstream migrator does not
        # publish .sens/view files or mint a Zig receipt in this mode.
        # Report its reference estimate explicitly, without pretending that
        # a physical carrier or executable proof was produced.
        if args.dry_run:
            rows = (report or {}).get("files") or []
            row = rows[0] if len(rows) == 1 else {}
            if ((report or {}).get("mode") != "dry-run"
                    or row.get("status") != "would-write"
                    or (report or {}).get("summary", {}).get("files_would_write") != 1):
                raise SystemExit("BLOCK: inconsistent three-pass dry-run receipt")
            if source.read_bytes() != original:
                raise SystemExit("BLOCK: source changed during dry-run")
            print(json.dumps({
                "status": "would-write", "source": str(rel),
                "output": str(output.relative_to(ROOT)) if output.is_relative_to(ROOT) else str(output),
                "view": str(view.relative_to(ROOT)) if view.is_relative_to(ROOT) else str(view),
                "target_action": ("replace-existing-pair" if args.replace_existing else
                                  "refuse-existing-pair" if any(existing_targets.values()) else
                                  "create-new-pair"),
                "codec": args.codec, "source_surface": args.source_surface,
                "source_sha256": hashlib.sha256(original).hexdigest(),
                "physical_sha256": row["physical_sha256"],
                "typed_word_sha256": row["typed_word_sha256"],
                "bytes": row["bytes"],
                "semantic_bits": row["semantic_bits"],
                "semantic_word_count": row["semantic_word_count"],
                "physical_producer": "PYTHON_REFERENCE_ONLY",
                "zig_transport": None, "semantic_parity": "NOT_VERIFIED",
            }, ensure_ascii=False, indent=2))
            return 0
        physical_path = stage / rel.with_suffix(".sens").name
        view_path = physical_path.with_suffix("")
        if not physical_path.is_file() or not view_path.is_file():
            raise SystemExit("BLOCK: missing .sens or extensionless view from three-pass")
        payload, visible = physical_path.read_bytes(), view_path.read_bytes()
        codec = load_codec()
        words = codec.decode_t5m_bytes(payload) if args.codec == "t5m" else codec.decode_bytes(payload)
        roundtrip = (codec.encode_t5m_projection(" ".join(words)) if args.codec == "t5m"
                     else codec.encode_words(words))
        if payload != roundtrip or visible != (" ".join(words) + "\n").encode("ascii"):
            raise SystemExit("BLOCK: physical/view word identity mismatch")
        try:
            proof = verify_upstream_t5_witness(report, rel.name, words, payload, args.codec, codec)
        except ValueError as exc:
            print(json.dumps({"status": "blocked", "reason": str(exc)}, ensure_ascii=False))
            return 2
        if source.read_bytes() != original:
            raise SystemExit("BLOCK: source changed during conversion")
        if resolve_without_links(args.source, "source") != source:
            raise SystemExit("BLOCK: source path changed during conversion")
        if not args.dry_run:
            if args.replace_existing:
                migration_publish_pair.replace_pair(output, payload, view, visible)
            else:
                migration_publish_pair.publish_pair(atomic_no_clobber, output, payload, view, visible)
        result = {
            "status": ("replaced" if args.replace_existing and any(existing_targets.values()) else "written"),
            "target_action": "replace-existing-pair" if args.replace_existing else "create-new-pair",
            "source": str(rel),
            "output": str(output.relative_to(ROOT)) if output.is_relative_to(ROOT) else str(output),
            "view": str(view.relative_to(ROOT)) if view.is_relative_to(ROOT) else str(view),
            "codec": args.codec,
            "source_surface": args.source_surface,
            "source_sha256": hashlib.sha256(original).hexdigest(),
            "physical_sha256": proof["physical_sha256"],
            "view_sha256": hashlib.sha256(visible).hexdigest(),
            "typed_word_sha256": proof["typed_word_sha256"],
            "words": words,
            "bytes": len(payload), "semantic_bits": proof["semantic_bits"],
            "semantic_word_count": proof["semantic_word_count"],
            "zig_transport": report["files"][0]["zig_transport"],
            "semantic_parity": "NOT_VERIFIED",
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
