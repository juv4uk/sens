#!/usr/bin/env python3
"""Атомарне створення української трійки .lisp / .sens (T5M) / бітовий перегляд.

.lisp копіюється без змін, але тотожність програми звіряється за точними
словами та структурою, а не за коментарями чи форматуванням тексту.
Фізичне видання .sens виконує лише SHA-атестований Zig 0.16 T5M;
Python T5M є незалежним еталоном для попереднього перегляду та порівняння.
Немає самовільного семантичного допуску, запису в main або перезапису.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from sens_t5_t5m_codec import encode_t5m_projection, decode_t5m_bytes, typed_sha256
import zig_codec_bridge
from verify_uk_t5_t5m_triplet import (
    ProjectionBlocked, canonical_uk_from_words, project_current_uk, verify,
)

SCHEMA = "sens-uk-t5m-three-projection-atomic-preview/v2"
MAX_FILES = 100


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def validate_path(root: Path, value: str) -> tuple[Path, Path]:
    rel = Path(value)
    if (rel.is_absolute() or rel.suffix != ".lisp" or not rel.parts
            or any(p in ("..", ".") for p in rel.parts)
            or "\\" in value or rel.as_posix() != value):
        raise ProjectionBlocked("require safe repository-relative .lisp path")
    curr = root
    if curr.is_symlink():
        raise ProjectionBlocked("source root symlink forbidden")
    for part in rel.parts:
        curr /= part
        if curr.is_symlink():
            raise ProjectionBlocked(f"symlink source component: {rel}")
    if not curr.is_file():
        raise ProjectionBlocked(f"source does not exist: {rel}")
    if not curr.resolve().is_relative_to(root):
        raise ProjectionBlocked("source escaped root")
    return rel, curr


def attest_source(source: bytes) -> tuple[list[str], bytes, bytes]:
    try:
        text = source.decode("utf-8")
        words = project_current_uk(text)
        rendered = canonical_uk_from_words(words)
        if project_current_uk(rendered) != words:
            raise ProjectionBlocked("українська проєкція не зберегла програму")
        physical = encode_t5m_projection(" ".join(words))
        if decode_t5m_bytes(physical) != words:
            raise ProjectionBlocked("T5M не зберіг точні слова програми")
    except (UnicodeError, ValueError, RecursionError) as exc:
        if isinstance(exc, ProjectionBlocked):
            raise
        raise ProjectionBlocked("недоведений вихідний код або некоректний T5M") from exc
    view = (" ".join(words) + "\n").encode("ascii")
    if not view or b"2" in view:
        raise ProjectionBlocked("invalid human binary view")
    return words, physical, view


def mirror_safety(root: Path, mirror: Path, report: Path) -> None:
    # A lexical /tmp/alias/mirror can point back into root when /tmp/alias
    # is a symlink. Resolve containment and ban every symlinked mirror parent
    # BEFORE mkdir/staging; checking descendants of mirror alone is unsafe.
    real_mirror = mirror.resolve(strict=False)
    if (mirror == root or mirror.is_relative_to(root)
            or real_mirror == root or real_mirror.is_relative_to(root)
            or any(parent.is_symlink() for parent in (mirror, *mirror.parents))
            or report == root or report.is_relative_to(root)
            or mirror == report or report.is_symlink()):
        raise ProjectionBlocked("mirror/report must be outside source repository")
    if mirror.exists() and not mirror.is_dir():
        raise ProjectionBlocked("mirror exists and is not a directory")


def destination_paths(mirror: Path, rel: Path) -> list[Path]:
    lisp = mirror / rel
    return [lisp, lisp.with_suffix(".sens"), lisp.with_suffix("")]


def no_symlink_destination(mirror: Path, target: Path) -> None:
    if not target.is_relative_to(mirror):
        raise ProjectionBlocked("target escaped mirror")
    current = mirror
    if current.is_symlink():
        raise ProjectionBlocked("mirror symlink")
    for part in target.relative_to(mirror).parts:
        current /= part
        if current.is_symlink():
            raise ProjectionBlocked(f"symlink destination: {target}")


def publish_no_clobber(paths_data: list[tuple[Path, bytes]],
                       mirror: Path) -> list[Path]:
    """Write ALL files or roll back only our newly created links."""
    created: list[Path] = []
    staging: list[Path] = []
    try:
        # Check all colliding targets BEFORE publication.
        for target, _ in paths_data:
            no_symlink_destination(mirror, target)
            if target.exists() or target.is_symlink():
                raise ProjectionBlocked(f"destination exists; no overwrite: {target}")
        for target, data in paths_data:
            target.parent.mkdir(parents=True, exist_ok=True)
            no_symlink_destination(mirror, target)
            with tempfile.NamedTemporaryFile(
                mode="wb", dir=target.parent, prefix=".t5m-stage-",
                suffix=".tmp", delete=False,
            ) as pending:
                temporary = Path(pending.name)
                staging.append(temporary)
                pending.write(data)
                pending.flush()
                os.fsync(pending.fileno())
        for (target, _), temporary in zip(paths_data, staging):
            no_symlink_destination(mirror, target)
            os.link(temporary, target)  # atomic and fails if target exists
            created.append(target)
    except (OSError, ProjectionBlocked):
        for name in reversed(created):
            name.unlink(missing_ok=True)
        raise
    finally:
        for name in staging:
            name.unlink(missing_ok=True)
    return created


def export(root: Path, mirror: Path, report: Path,
           requested: list[str], write: bool) -> dict:
    root = root.resolve()
    mirror = mirror.absolute()
    report = report.absolute()
    mirror_safety(root, mirror, report)
    if report.exists() or report.is_symlink():
        raise ProjectionBlocked("existing report forbidden (no overwrite)")
    if any(part.is_symlink() for part in report.parents):
        raise ProjectionBlocked("symlink report parent forbidden")
    if not 1 <= len(requested) <= MAX_FILES:
        raise ProjectionBlocked("expected 1..100 explicitly chosen sources")
    seen: set[str] = set()
    candidates: list[tuple[Path, Path, bytes, list[str], bytes, bytes]] = []
    rows: list[dict] = []
    # Entire requested cohort must be admitted: one empty -> no writes.
    for name in requested:
        row: dict = {"source": name}
        try:
            rel, source = validate_path(root, name)
            if name in seen:
                raise ProjectionBlocked(f"duplicate source {name}")
            seen.add(name)
            original = source.read_bytes()
            words, physical, view = attest_source(original)
            paths = destination_paths(mirror, rel)
            for target in paths:
                no_symlink_destination(mirror, target)
                if target.exists() or target.is_symlink():
                    raise ProjectionBlocked(f"destination already exists: {target}")
            candidates.append((rel, source, original, words, physical, view))
            row.update(status="candidate-not-oracle-admitted",
                       target_sens=rel.with_suffix(".sens").as_posix(),
                       target_view=rel.with_suffix("").as_posix(),
                       word_count=len(words), physical_bytes=len(physical),
                       physical_codec="t5m",
                       source_sha256=sha(original), physical_sha256=sha(physical),
                       physical_authority="reference-only-nonpublic",
                       view_sha256=sha(view), typed_word_sha256=typed_sha256(words))
        except (ProjectionBlocked, OSError, ValueError) as exc:
            row.update(status="blocked", reason=str(exc))
        rows.append(row)

    created: list[Path] = []
    if write and all(row["status"] != "blocked" for row in rows):
        # Python transport is a read-only reference; publication is Zig-only.
        # Build once for the cohort, not once per file. Never write a .sens
        # unless the attested Zig physical bytes equal the independent
        # exact-word reference and Zig's own canonical roundtrip succeeds.
        with tempfile.TemporaryDirectory(prefix="sens-uk-zig-t5m-") as tool_dir:
            binary = zig_codec_bridge.build_transport(Path(tool_dir))
            for index, (rel, source, original, words, reference, view) in enumerate(candidates):
                physical = zig_codec_bridge.carry_t5(
                    binary, view.decode("ascii"), codec="t5m",
                )
                receipt = zig_codec_bridge.verify_t5(binary, physical, codec="t5m")
                if physical != reference or decode_t5m_bytes(physical) != words:
                    raise ProjectionBlocked(
                        f"ZIG_T5M_REFERENCE_PARITY_MISMATCH: {rel}"
                    )
                candidates[index] = (rel, source, original, words, physical, view)
                rows[index]["physical_sha256"] = sha(physical)
                rows[index]["physical_bytes"] = len(physical)
                rows[index]["zig_binary_sha256"] = receipt["zig_binary_sha256"]
                rows[index]["physical_authority"] = "zig-attested-t5m"
        paths_data: list[tuple[Path, bytes]] = []
        for rel, source, original, words, physical, view in candidates:
            if source.read_bytes() != original:
                raise ProjectionBlocked(f"source modified during transaction: {rel}")
            paths_data.extend(zip(destination_paths(mirror, rel),
                                  (original, physical, view)))
        try:
            created = publish_no_clobber(paths_data, mirror)
            for rel, source, original, words, physical, view in candidates:
                # Independent existing bounded verifier controls exact 3-way
                # canonical Ukrainian and byte/view roundtrip after publication.
                lisp, sens, human = destination_paths(mirror, rel)
                result = verify(lisp, sens, human, codec="t5m")
                if result["runtime_oracle_admitted_by_this_audit"] is not False:
                    raise ProjectionBlocked("invalid semantic oracle claim")
                if source.read_bytes() != original:
                    raise ProjectionBlocked("source modified during verification")
        except Exception:
            for target in reversed(created):
                target.unlink(missing_ok=True)
            raise
        for row in rows:
            row["status"] = "written-mechanical-only-not-oracle-admitted"
    payload = {
        "schema": SCHEMA, "mode": "write-triple" if write else "preview-only",
        "source_root": str(root), "mirror": str(mirror),
        "truth": "canonical Ukrainian subset only; NO oracle semantic admission",
        "summary": {
            "requested": len(requested),
            "blocked": sum(x["status"] == "blocked" for x in rows),
            "candidates": len(candidates),
            "triplets_written": sum(x["status"].startswith("written") for x in rows),
            "original_executables_oracle_certified": 0,
        },
        "files": rows,
    }
    # The report belongs to the SAME transaction: if it cannot be written,
    # roll back new triplets rather than leave unaccounted orphan .sens files.
    report_created = False
    try:
        report.parent.mkdir(parents=True, exist_ok=True)
        if report.is_symlink() or report.exists():
            raise ProjectionBlocked("existing or symlink report forbidden")
        with report.open("x", encoding="utf-8") as f:
            report_created = True  # ONLY our own created report can be removed
            json.dump(payload, f, ensure_ascii=False, indent=2)
            f.write("\n")
    except (OSError, ValueError, ProjectionBlocked):
        for target in reversed(created):
            target.unlink(missing_ok=True)
        if report_created:
            report.unlink(missing_ok=True)
        raise
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", nargs="+",
                        help="explicit repo-relative canonical Ukrainian .lisp")
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--mirror", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    try:
        out = export(args.root, args.mirror, args.report,
                     args.source, args.write)
        print(json.dumps(out["summary"], ensure_ascii=False))
        return 2 if out["summary"]["blocked"] else 0
    except (OSError, ValueError, ProjectionBlocked) as exc:
        print("BLOCKED: " + str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
