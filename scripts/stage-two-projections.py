#!/usr/bin/env python3
"""Stage only TWO canonical SENS projections; no physical codec invocation.

For each explicitly named .lisp input, create in an OUTSIDE-repo mirror:
  name.lisp  canonical Ukrainian source (ук)
  name       exact-width 0/1 word view, single spaces and final LF

Physical name.sens is deliberately NOT created here. The current carrier is
T5M, but this two-projection step does NOT run Zig/T5M, SENS evaluation or a
semantic oracle. Source files remain unchanged; no new surface law is defined.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from verify_uk_t5_t5m_triplet import (  # noqa: E402
    ProjectionBlocked, canonical_uk_from_words, project_current_uk, three_pass,
)

# D11 — каталог пропозицій, а не виконуваний код. Відкидаємо також
# довільні "D24+" бітності (25, 32, 49...), яких власник не ратифікував.
# Список числових ширин читаємо з єдиного чинного джерела, не дублюємо.
def _current_word_pattern() -> re.Pattern[str]:
    policy = json.loads(
        (ROOT / "knowledge/number-width-ratified.json").read_text(encoding="utf-8")
    )
    widths = policy.get("ratified_prefix_bits")
    if (policy.get("status") != "owner-ratified"
            or not isinstance(widths, list)
            or widths[:3] != [24, 48, 96]
            or any(type(width) is not int or width <= 10 for width in widths)
            or any(next_width != width * 2
                   for width, next_width in zip(widths, widths[1:]))):
        raise ProjectionBlocked("Числова драбина D24+ не відповідає чинній ратифікації")
    choices = "|".join(f"[01]{{{width}}}" for width in widths)
    # Це тільки лексична межа: ширина не доводить функцію чи семантику.
    return re.compile(rf"(?:[01]{{1,10}}|{choices})\Z")


BITS = _current_word_pattern()


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def source_path(root: Path, supplied: str) -> tuple[Path, Path]:
    rel = Path(supplied)
    if (not supplied or "\\" in supplied or rel.is_absolute()
            or rel.as_posix() != supplied or rel.suffix != ".lisp"
            or any(part in (".", "..") for part in supplied.split("/"))):
        raise ProjectionBlocked(f"unsafe source .lisp path: {supplied!r}")
    path = root
    for component in rel.parts:
        path = path / component
        if path.is_symlink():
            raise ProjectionBlocked(f"symlink source path: {supplied}")
    if not path.is_file() or not path.resolve().is_relative_to(root):
        raise ProjectionBlocked(f"missing/escaping source: {supplied}")
    return rel, path


def migration_maps():
    data = three_pass.load_foundation(ROOT / "knowledge/d1-d11-foundation.json")
    my, upper, _retired_provenance = three_pass.build_three_pass_maps(
        data,
        ROOT / "crates/sens/src/domain_surface_registry_generated.rs",
        ROOT / "crates/sens/src/semantic_registry_generated.rs",
        ROOT / "crates/sens/src/semantic_registry.rs",
        ROOT / "crates/sens/src/eval/necessary_forms_generated.rs",
    )
    # Ratified D7 keyboard/v2 (width 7, occupancy 128/128) is the current Text7
    # authority. The retired crates/sens/src/text7_projection_generated.rs donor
    # has no executable mapping and is never silently substituted.
    text7 = three_pass.build_text7(
        data, ROOT / "knowledge/d7-keyboard-v2-ratified.json"
    )
    return data, my, upper, text7


def prepare(root: Path, supplied: str, source_era: str, maps: tuple) -> dict:
    rel, path = source_path(root, supplied)
    original = path.read_bytes()
    data, my, upper, text7 = maps
    if source_era == "legacy":
        raise ProjectionBlocked("HISTORICAL_SOURCE_ERA_DISABLED: no SID8 execution path")
    resolver = three_pass.Resolver(
        my, upper,
        d9_residents=set(data["domains"].get("D9", {}).get("residents", {})),
    )
    try:
        source = original.decode("utf-8")
        projection = three_pass.migrate_file(
            source, resolver, text7, source_surface="укр"
        )
        words = projection.split()
        if not words or any(BITS.fullmatch(word) is None for word in words):
            raise ProjectionBlocked("not a complete exact-width binary-word projection")
        # The existing bounded canonical UK renderer is independent of the
        # physical packing choice: no Zig/T5M encode or decode happens here.
        canonical_uk = canonical_uk_from_words(words)
        # Доказ двосторонній: не можна реконструювати довільно
        # іншу програму і називати її зворотністю первісного Lisp.
        # Коментарі й пробіли не є частиною програмної тотожності.
        if (project_current_uk(source) != words
                or project_current_uk(canonical_uk) != words):
            raise ProjectionBlocked("Український Lisp не тотожний точним словам")
        uk = canonical_uk.encode("utf-8")
        view = (" ".join(words) + "\n").encode("ascii")
    except (UnicodeError, ValueError, RecursionError, three_pass.MigrationError) as exc:
        raise ProjectionBlocked(f"{supplied}: unproved source projection: {exc}") from exc
    if path.read_bytes() != original:
        raise ProjectionBlocked(f"source changed during conversion: {supplied}")
    return {
        "rel": rel, "path": path, "original": original,
        "uk": uk, "view": view,
        "record": {
            "source": supplied,
            "source_sha256": digest(original),
            "uk_lisp_sha256": digest(uk),
            "typed_view_sha256": digest(view),
            "word_count": len(words),
            "resolved_heads": dict(resolver.counts),
            "source_era": source_era,
            "status": "WOULD_STAGE_TWO_NOT_SEMANTICALLY_ADMITTED",
        },
    }


def safe_mirror(root: Path, mirror: Path) -> Path:
    if any(p.is_symlink() for p in (mirror, *mirror.parents)):
        raise ProjectionBlocked("mirror symlink ancestor forbidden")
    real = mirror.resolve(strict=False)
    if real == root or real.is_relative_to(root):
        raise ProjectionBlocked("mirror must be OUTSIDE repository")
    if mirror.exists() and not mirror.is_dir():
        raise ProjectionBlocked("mirror is not a directory")
    return real


def destination(mirror: Path, rel: Path) -> tuple[Path, Path]:
    uk = mirror / rel
    view = uk.with_suffix("")
    for path in (uk, view):
        if path.exists() or path.is_symlink():
            raise ProjectionBlocked(f"existing output, never overwrite: {path}")
        if not path.resolve(strict=False).is_relative_to(mirror):
            raise ProjectionBlocked(f"destination escapes mirror: {path}")
        if any(p.is_symlink() for p in (path.parent, *path.parent.parents)):
            raise ProjectionBlocked(f"destination symlink ancestor: {path}")
    return uk, view


def publish_new(target: Path, content: bytes) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() or target.is_symlink():
        raise ProjectionBlocked(f"destination already exists: {target}")
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            dir=target.parent, prefix=".sens-two-", suffix=".tmp",
            mode="wb", delete=False,
        ) as stream:
            temporary = Path(stream.name)
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.link(temporary, target)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def stage(root: Path, mirror: Path, sources: list[str],
          source_era: str, write: bool) -> dict:
    root = root.resolve(strict=True)
    mirror = safe_mirror(root, mirror)
    if len(set(sources)) != len(sources):
        raise ProjectionBlocked("duplicate source path")
    maps = migration_maps()
    planned = [prepare(root, name, source_era, maps) for name in sources]
    outputs = []
    for entry in planned:
        uk, view = destination(mirror, entry["rel"])
        outputs.extend(((uk, entry["uk"]), (view, entry["view"])))
    if len({p for p, _ in outputs}) != len(outputs):
        raise ProjectionBlocked("destination collision")
    if write:
        # A cohort is all-or-none. The source is pinned again before EACH write.
        created = []
        created_dirs = []
        try:
            for entry in planned:
                if entry["path"].read_bytes() != entry["original"]:
                    raise ProjectionBlocked(f"source changed: {entry['rel']}")
            for path, data in outputs:
                if any(p.is_symlink() for p in (path.parent, *path.parent.parents)):
                    raise ProjectionBlocked("destination symlink ancestor changed")
                # Каталоги є частиною транзакції: зберігаємо лише
                # власні створення, щоб не зачепити попередні дані.
                missing_dirs = []
                ancestor = path.parent
                while not ancestor.exists() and not ancestor.is_symlink():
                    missing_dirs.append(ancestor)
                    ancestor = ancestor.parent
                for directory in reversed(missing_dirs):
                    directory.mkdir()
                    created_dirs.append(directory)
                publish_new(path, data)
                created.append(path)
        except Exception:
            for path in reversed(created):
                path.unlink(missing_ok=True)
            for directory in reversed(created_dirs):
                try:
                    directory.rmdir()
                except OSError:
                    # Не видаляти каталоги, які заповнив інший процес.
                    pass
            raise
        for entry in planned:
            entry["record"]["status"] = "TWO_STAGED_PHYSICAL_AND_ORACLE_PENDING"
    return {
        "schema": "sens-two-projections-no-physical-codec/v1",
        "mode": "write-two" if write else "preview",
        "third_file": "name.sens PENDING verified Zig/T5M physical encoding",
        "physical_codec_invoked": False,
        "semantic_oracle": "NOT_VERIFIED",
        "release_admitted": False,
        "summary": {"sources": len(planned),
                    "files_created": len(outputs) if write else 0,
                    "would_create": len(outputs) if not write else 0,
                    "blocked": 0},
        "files": [entry["record"] for entry in planned],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sources", nargs="+", help="explicit repository-relative .lisp paths")
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--mirror", type=Path, required=True, help="new output location outside repository")
    parser.add_argument("--source-era", choices=("auto", "legacy", "current"), default="auto")
    parser.add_argument("--write", action="store_true", help="create exactly two projections per source")
    args = parser.parse_args()
    try:
        result = stage(args.root, args.mirror, args.sources, args.source_era, args.write)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, ProjectionBlocked, three_pass.MigrationError) as exc:
        print(json.dumps({
            "schema": "sens-two-projections-no-physical-codec/v1",
            "status": "BLOCKED", "reason": str(exc),
            "files_created": 0, "semantic_oracle": "NOT_VERIFIED",
        }, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
