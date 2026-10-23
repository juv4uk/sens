#!/usr/bin/env python3
"""Пакетне перетворення .lisp у поточний фізичний T5M .sens.

Це пакетний оркестратор, а не альтернативна реалізація семантики SENS.
Перетворення джерела виконує migrate-three-pass.py; Zig записує фізичні
байти T5M, а Python є лише незалежним еталоном транспортної оберненості.
Нові файли не записуються без --write та --zig-codec. Вхідні .lisp
залишаються незмінними; доказ виконання програми SENS потрібен окремо.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile

import zig_codec_bridge
import migration_publish_pair

ROOT = Path(__file__).resolve().parents[1]
MIGRATOR = ROOT / "scripts/migrate-three-pass.py"

spec = importlib.util.spec_from_file_location("sens_migration_batch_impl", MIGRATOR)
if spec is None or spec.loader is None:
    raise RuntimeError("cannot load ratified SENS three-pass migrator")
mig = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mig
spec.loader.exec_module(mig)

INPUTS = {
    "foundation": ROOT / "knowledge/d1-d11-foundation.json",
    "domain_surfaces": ROOT / "crates/sens/src/domain_surface_registry_generated.rs",
    "semantic_generated": ROOT / "crates/sens/src/semantic_registry_generated.rs",
    "semantic_registry": ROOT / "crates/sens/src/semantic_registry.rs",
    "necessary_forms": ROOT / "crates/sens/src/eval/necessary_forms_generated.rs",
    "text7": ROOT / "knowledge/d7-keyboard-v2-ratified.json",
}
EXCLUDE = set(mig.SKIP_DIRS)
SCHEMA = "sens-t5-safe-batch/v1"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def forbidden_components(path: Path) -> bool:
    # «.» означає корінь репозиторію і є безпечним явним запитом.
    # Батьківські переходи та виключені каталоги залишаються забороненими.
    return path.is_absolute() or ".." in path.parts or any(
        p in EXCLUDE for p in path.parts
    )


def resolve_without_links(path: Path, role: str) -> Path:
    """Відхилити symlink та '..' у ЗАДАНОМУ шляху ДО Path.resolve()."""
    if ".." in path.parts:
        raise ValueError(f"{role}: parent traversal forbidden")
    absolute = path.absolute()
    for component in (absolute, *absolute.parents):
        if component.is_symlink():
            raise ValueError(f"{role}: symlink path component forbidden: {component}")
    return absolute.resolve()


def verify_pinned_paths(args: argparse.Namespace, repo: Path, out: Path, report: Path) -> None:
    """Перед публікацією підтвердити ті самі початкові адреси, без alias."""
    for role, original, pinned in (
        ("source repository", args.root, repo),
        ("output mirror", args.out, out),
        ("report", args.report, report),
    ):
        if resolve_without_links(original, role) != pinned:
            raise ValueError(f"{role}: path changed during migration")


def assert_no_links(base: Path, relative: Path) -> None:
    current = base
    if current.is_symlink():
        raise ValueError("symlink repository/mirror root forbidden")
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise ValueError(f"symlink input/target component forbidden: {relative}")


def discover(repo: Path, requested: list[str]) -> tuple[list[Path], list[dict]]:
    found: set[Path] = set()
    failures: list[dict] = []
    for item in requested:
        relative = Path(item)
        if not item or forbidden_components(relative):
            failures.append({"path": item, "status": "blocked",
                             "reason": "unsafe/excluded input path"})
            continue
        try:
            assert_no_links(repo, relative)
            path = repo / relative
            if path.is_dir():
                for child in sorted(path.rglob("*")):
                    rel = child.relative_to(repo)
                    if any(p in EXCLUDE for p in rel.parts):
                        continue
                    if child.is_symlink():
                        failures.append({"path": str(rel), "status": "blocked",
                                         "reason": "symlink in input tree"})
                    elif child.is_file() and child.suffix == ".lisp":
                        assert_no_links(repo, rel)
                        found.add(rel)
            elif path.is_file() and relative.suffix == ".lisp":
                found.add(relative)
            else:
                failures.append({"path": item, "status": "blocked",
                                 "reason": "expected existing .lisp source or directory"})
        except (ValueError, OSError) as exc:
            failures.append({"path": item, "status": "blocked", "reason": str(exc)})
    return sorted(found, key=lambda p: p.as_posix()), failures


def run(args: argparse.Namespace) -> dict:
    # Protect direct Python imports as well as the regular CLI entry point.
    if args.write and not args.zig_codec:
        raise ValueError("ZIG_CARRY_REQUIRED_FOR_PUBLICATION")
    # Важливо: Path.resolve() приховує symlink в аргументі користувача.
    # Перевіряємо усі компоненти до нормалізації, включно з відносними.
    repo = resolve_without_links(args.root, "source repository")
    out = resolve_without_links(args.out, "output mirror")
    report = resolve_without_links(args.report, "report")
    if not repo.is_dir():
        raise ValueError("source repository must exist")
    # Власник дозволив створювати точні .sens безпосередньо поруч із .lisp.
    # Захист від перезапису й Zig-перевірка діють також для out == repo.
    # Незмінний JSON-звіт завжди поза репозиторієм джерел.
    if report.is_relative_to(repo):
        raise ValueError("report must be OUTSIDE source root")
    # The JSON receipt must NOT be anywhere in the binary output mirror.
    # Otherwise the later atomic stage.replace(report) can overwrite a .sens
    # just published by Zig, destroying physical exact-width bytes after
    # their SHA was already recorded in the ledger.
    if report.is_relative_to(out):
        raise ValueError(
            "ZIG_REPORT_OUTPUT_COLLISION layer=transport: "
            "--report must be OUTSIDE the physical .sens output mirror"
        )
    if report.is_dir():
        raise ValueError("--report must name a JSON file, not a directory")
    if out.is_symlink() or report.is_symlink():
        raise ValueError("symlink output/report is forbidden")
    paths, failures = discover(repo, args.paths)

    data = mig.load_foundation(INPUTS["foundation"])
    source_era = args.source_era
    # Historical сід8 and its optional registry are retired. A source-era
    # switch cannot revive identity re-interpretation; current D8 is exact.
    if source_era == "legacy":
        raise ValueError("RETIRED_SID8_SOURCE_ERA: use current ratified domain identities")
    d9_residents = set(data["domains"].get("D9", {}).get("residents", {}))
    if source_era == "current" and "D8" not in data.get("current_domains", ()):
        raise ValueError("current D8 source requires owner-ratified D8 foundation")
    # Резолвер отримує лише чинні таблиці кодів і поверхонь.
    # Третій результат — не виконавчий інтерфейс і не використовується.
    my, upper, _ = mig.build_three_pass_maps(
        data, INPUTS["domain_surfaces"], INPUTS["semantic_generated"],
        INPUTS["semantic_registry"], INPUTS["necessary_forms"]
    )
    text7 = mig.build_text7(data, INPUTS["text7"])
    ledger = sorted(failures, key=lambda e: e["path"])
    # A cohort is all-or-none: retain physical candidates in memory until
    # every requested original has passed conversion and final source checks.
    staged: list[tuple[Path, Path, bytes, bytes, dict]] = []
    # Explicit cross-implementation verification; no semantic authority or
    # silent fallback. Compile once for this batch, outside the source tree.
    zig_temp = tempfile.TemporaryDirectory(prefix="sens-zig-batch-") if args.zig_codec else None
    zig_binary = (zig_codec_bridge.build_transport(Path(zig_temp.name))
                  if zig_temp is not None else None)
    for rel in paths:
        source = repo / rel
        destination = mig.sens_destination(rel)
        target = out / destination
        row = {"path": rel.as_posix(), "output": destination.as_posix()}
        resolver = mig.Resolver(my, upper, d9_residents=d9_residents)
        readable = ""  # never inherit another source on per-file error
        try:
            assert_no_links(repo, rel)
            assert_no_links(out, destination)
            # Reviewed data may not masquerade as a runnable .sens even in
            # bulk migration. Synthetic external corpora have no such authority.
            if (repo / mig.NONPROGRAM_MANIFESTS[0][1]).exists():
                mig.reject_reviewed_nonprogram_source(source, repo)
            if target.exists() or target.is_symlink():
                raise ValueError("existing .sens output: overwrite forbidden")
            original = source.read_bytes()
            row["source_sha256"] = digest(original)
            readable = original.decode("utf-8")
            projection = mig.migrate_file(readable, resolver, text7, codec="t5m")
            words = mig.parse_words(projection)
            # Python is an independent reference, NOT the published byte producer.
            reference_bytes = mig.encode_t5m_projection(projection)
            if mig.decode_t5m_bytes(reference_bytes) != words:
                raise ValueError("exact typed T5M word roundtrip failed")
            if zig_binary is not None:
                packed = zig_codec_bridge.carry_t5(
                    zig_binary, projection,
                    codec="t5m",
                    trusted_source_sha256=digest(reference_bytes),
                )
                if packed != reference_bytes:
                    difference = next(
                        (i for i, (a, b) in enumerate(zip(reference_bytes, packed))
                         if a != b), min(len(reference_bytes), len(packed))
                    )
                    raise ValueError(
                        "ZIG_CARRY_REFERENCE_MISMATCH layer=transport "
                        f"expected_sha256={digest(reference_bytes)} "
                        f"actual_sha256={digest(packed)} first_byte={difference}"
                    )
                evidence = zig_codec_bridge.verify_t5(
                    zig_binary, packed,
                    codec="t5m",
                    trusted_source_sha256=digest(reference_bytes),
                )
                row["zig_transport"] = evidence
            else:
                # Preview only; --write without Zig fails at both entry points.
                packed = reference_bytes
            # Disallow use of generated textual bytes as a misleading .sens file.
            if packed == projection.encode("ascii"):
                raise ValueError("invalid text disguised as physical .sens")
            row.update({
                "status": "would-write",
                "physical_bytes": len(packed),
                "source_words": len(words),
                "physical_sha256": digest(packed),
                "typed_word_sha256": mig.typed_sha256(words),
                "passes": dict(resolver.counts),
                "source_era": source_era,
            })
            if args.write:
                staged.append((rel, destination, original, packed, row))
        except (mig.MigrationError, mig.SensT5Error, UnicodeError,
                ValueError, OSError) as exc:
            row.update({"status": "blocked", "reason": str(exc),
                        "passes": dict(resolver.counts), "source_era": source_era})
            tok = getattr(exc, "tok", None)
            if tok is not None:
                row["token"] = tok.text
                row["line"], row["column"] = mig.line_col(readable, tok.offset)
        ledger.append(row)
    ledger.sort(key=lambda e: e["path"])

    # Per-file publication: a blocked file blocks only itself. Every
    # mechanically feasible candidate is published independently, so one
    # unproven source can never hold back the rest of the batch. Safety is
    # enforced per file: no clobber, no symlink, source unchanged, atomic write.
    if args.write:
        verify_pinned_paths(args, repo, out, report)
        for rel, destination, original, packed, row in staged:
            try:
                assert_no_links(repo, rel)
                assert_no_links(out, destination)
                if (out / destination).exists() or (out / destination).is_symlink():
                    raise ValueError("existing .sens output: overwrite forbidden")
                if (repo / rel).read_bytes() != original:
                    raise ValueError("source changed during migration")
                # The binary and exact-bit text view form one publication unit.
                # An existing view must not strand an orphan .sens; a failed view
                # write rolls back only the bytes this candidate just created.
                # T5M bytes have already passed the pinned Zig corridor above.
                view_bytes = (" ".join(mig.decode_t5m_bytes(packed)) + "\n").encode("ascii")
                view_path = out / destination.with_suffix("")
                migration_publish_pair.publish_pair(
                    mig.write_atomic_no_clobber,
                    out / destination, packed, view_path, view_bytes,
                )
                row["view_bytes"] = len(view_bytes)
            except (ValueError, OSError, mig.SensT5Error) as exc:
                row.update(status="blocked", reason=str(exc))
            else:
                row["status"] = "written"

    admitted = sum(e["status"] in ("would-write", "written") for e in ledger)
    blocked = sum(e["status"] == "blocked" for e in ledger)
    written = sum(e["status"] == "written" for e in ledger)
    candidates = sum(e["status"] == "would-write" for e in ledger)
    result = {
        "schema": SCHEMA, "mode": "write-new-only" if args.write else "dry-run",
        "root": str(repo), "output_mirror": str(out),
        "authority": {"foundation_sha256": digest(INPUTS["foundation"].read_bytes()),
                      "codec": "physical-T5M-5-trits-per-byte",
                      "source_era": source_era,
                      "w8_policy": "SID8 retired; auto/current preserve only ratified D8; no historical remapping"},
        "semantic_runtime_verified_by_this_tool": False,
        "release_admitted_by_this_tool": False,
        "mechanical_only": True,
        "summary": {"files_seen": len(ledger), "files_admitted": admitted,
                    "mechanically_packable_files": admitted,
                    "files_written": written,
                    "files_would_write": candidates,
                    "files_blocked": blocked},
        "files": ledger,
    }
    verify_pinned_paths(args, repo, out, report)
    report.parent.mkdir(parents=True, exist_ok=True)
    verify_pinned_paths(args, repo, out, report)
    stage = report.with_name(report.name + ".tmp")
    if stage.exists() or report.is_symlink():
        raise ValueError("report staging target already exists or is symlink")
    try:
        stage.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                         encoding="utf-8")
        stage.replace(report)
    finally:
        stage.unlink(missing_ok=True)
    if zig_temp is not None:
        zig_temp.cleanup()
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+",
                        help="явні шляхи .lisp або каталоги відносно кореня репозиторію")
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--out", type=Path, required=True,
                        help="каталог для нових .sens: дозволено і корінь джерел; без перезапису; --report поза обома деревами")
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--source-era", choices=("auto", "legacy", "current"),
                        default="auto",
                        help="auto/current — лише чинні ратифіковані домени; legacy скасовано")
    parser.add_argument("--zig-codec", action="store_true",
                        help="вимагати фізичну перевірку T5M через закріплений Zig 0.16")
    parser.add_argument("--write", action="store_true",
                        help="створювати лише нові фізичні .sens без перезапису")
    args = parser.parse_args()
    # New reality (#5777/#5779): the Rust<->SENS link crosses ONLY the sterile Zig
    # corridor. Publishing physical .sens without the pinned-Zig cross-check is a
    # silent bypass, so --write REQUIRES --zig-codec and fails closed without it.
    if args.write and not args.zig_codec:
        print("FATAL migration setup: --write requires --zig-codec "
              "(physical .sens may not be published without the sterile Zig corridor)",
              file=sys.stderr)
        return 3
    try:
        result = run(args)
    except (OSError, ValueError, mig.MigrationError) as exc:
        print(f"FATAL migration setup: {exc}", file=sys.stderr)
        return 3
    print(json.dumps(result["summary"], ensure_ascii=False))
    return 0 if result["summary"]["files_admitted"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
