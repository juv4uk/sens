#!/usr/bin/env python3
"""Read-only, fail-closed inventory of real SENS .lisp/.sens/view triplets.

IMPORTANT: a successful mechanical migration or a correct physical view is
NOT semantic admission, original-source credit, or a release authorization.
This inventory never guesses historical W8 era and NEVER runs a migrator.
Use the separate proof-gated original-source publisher for admitted migrations.

Example:
    python3 scripts/sens_inventory.py lib tests/fixtures --json /tmp/sens-inventory.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from sens_spaced_view import ViewError, check_or_stage  # noqa: E402
from sens_t5_codec import SensT5Error  # noqa: E402
from verify_uk_t5_triplet import ProjectionBlocked, verify as prove_bounded_uk  # noqa: E402

SCHEMA = "sens-triple-inventory-failclosed/v2"
SCHEMA_HEAD = re.compile(r"^[A-Za-z][\w./-]*/\d+$")
KNOWN_DECL = {"schema", "token"}
SAFE_ROOT = re.compile(r"^[A-Za-z0-9_./-]+$")
GOOD_UK = "BOUNDED_UK_PROVEN_ORACLE_PENDING"
PHYSICAL_ONLY = "PHYSICAL_VIEW_ONLY_UK_PENDING"
MISSING = "MISSING_TRIPLET"
NONPROGRAM = "NONPROGRAM_CANDIDATE"
BLOCKED = "BLOCKED_INVALID_TRIPLET"


class InventoryBlocked(ValueError):
    pass


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def safe_scope(root: Path, raw: str) -> Path:
    """Do not search outside root or traverse symlinked directories."""
    if not isinstance(raw, str) or not raw or not SAFE_ROOT.fullmatch(raw) or "\\" in raw:
        raise InventoryBlocked("unsafe scope")
    rel = PurePosixPath(raw)
    if rel.is_absolute() or any(part in ("", ".", "..") for part in raw.split("/")):
        raise InventoryBlocked("scope must be repo-relative with no traversal")
    target = root.joinpath(*rel.parts)
    node = root
    for part in rel.parts:
        node = node / part
        if node.is_symlink():
            raise InventoryBlocked("symlinked scope forbidden")
    if not target.resolve().is_relative_to(root.resolve()):
        raise InventoryBlocked("scope escaped repository")
    if not target.is_dir():
        raise InventoryBlocked("scope directory missing")
    return target


def head_of(source: str) -> str | None:
    """Heuristic only! A Lisp datum's apparent head is NOT an executable proof."""
    for line in source.splitlines():
        line = line.split(";", 1)[0].strip()
        if line.startswith("("):
            m = re.match(r"\(\s*([^\s()]+)", line)
            if m:
                return m.group(1)
    return None


def classify(source: bytes) -> str:
    try:
        head = head_of(source.decode("utf-8", errors="strict"))
    except UnicodeError:
        return "unknown"
    if head and (SCHEMA_HEAD.fullmatch(head) or head in KNOWN_DECL):
        return "declarative_candidate"  # NOT an authoritative nonprogram finding
    return "unknown_executable_candidate"  # never automatically executable


def inspect(root: Path = ROOT, roots: tuple[str, ...] = ("lib", "tests/fixtures")) -> dict:
    if not root.is_dir() or root.is_symlink():
        raise InventoryBlocked("repository root must be a real directory")
    root = root.resolve()
    paths: set[Path] = set()
    for name in roots:
        directory = safe_scope(root, name)
        for path in directory.rglob("*.lisp"):
            if not path.is_symlink() and path.is_file():
                paths.add(path)
    rows = []
    for src in sorted(paths, key=lambda path: path.relative_to(root).as_posix()):
        rel = src.relative_to(root).as_posix()
        source_data = src.read_bytes()
        kind = classify(source_data)
        sens = src.with_suffix(".sens")
        view = src.with_suffix("")
        row = {
            "path": rel,
            "source_kind": kind,
            "source_sha256": sha(source_data),
            "sens": sens.relative_to(root).as_posix(),
            "view": view.relative_to(root).as_posix(),
            "status": MISSING,
            "release_admitted": False,
            "original_executable_migration_credit": 0,
            "independent_execution_oracle": "NOT_VERIFIED",
            "source_era": "UNKNOWN_NOT_INFERRED",
        }
        # No name-only or width-only inference of an executable from a schema.
        if kind == "declarative_candidate":
            row["status"] = NONPROGRAM
            row["reason"] = "heuristic declarative head; needs independent review"
        elif any(p.is_symlink() for p in (src, sens, view)):
            row["status"] = BLOCKED
            row["reason"] = "symlinked artifact forbidden"
        elif not sens.is_file() or not view.is_file():
            row["status"] = MISSING
            row["reason"] = "physical .sens and spaced view must both exist"
        else:
            try:
                physical = check_or_stage(root, row["sens"])
                row.update({
                    "sens_sha256": physical["sens_sha256"],
                    "view_sha256": physical["view_sha256"],
                    "typed_word_sha256": physical["typed_word_sha256"],
                    "words": physical["words"],
                    "physical_bytes": physical["physical_bytes"],
                })
                row["status"] = PHYSICAL_ONLY
                row["reason"] = "T5/view verified; Ukrainian meaning still unknown"
                try:
                    uk = prove_bounded_uk(src, sens, view)
                    if (uk["typed_word_sha256"] != physical["typed_word_sha256"]
                            or uk["physical_sha256"] != physical["sens_sha256"]
                            or uk["view_sha256"] != physical["view_sha256"]
                            or uk["source_sha256"] != physical["source_sha256"]):
                        raise InventoryBlocked("bounded Ukrainian proof disagrees with T5 receipt")
                    row["status"] = GOOD_UK
                    row["reason"] = "bounded D1/D3 UK parity; runtime and original oracle still pending"
                except ProjectionBlocked as error:
                    row["uk_blocker"] = str(error)
            except (ViewError, SensT5Error, InventoryBlocked, OSError, ValueError) as error:
                row["status"] = BLOCKED
                row["reason"] = str(error)
        rows.append(row)
    statuses = (MISSING, NONPROGRAM, BLOCKED, PHYSICAL_ONLY, GOOD_UK)
    counts = {status: sum(r["status"] == status for r in rows) for status in statuses}
    return {
        "schema": SCHEMA,
        "status": "INVENTORY_ONLY_NO_RELEASE_ADMISSION",
        "summary": {
            "files_seen": len(rows),
            "mechanically_admitted": 0,
            "release_admitted": 0,
            "original_executable_migrations_certified": 0,
            "by_status": counts,
        },
        "files": rows,
    }


def write_receipt(path: Path, report: dict, root: Path) -> None:
    """Separate, new .json only; never clobber sources, T5 or extensionless view."""
    if path.suffix != ".json" or path.is_symlink():
        raise InventoryBlocked("receipt must be a new regular .json file")
    if path.resolve().is_relative_to(root.resolve()):
        raise InventoryBlocked("receipts must be stored outside source repository")
    payload = (json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n")
    with path.open("x", encoding="utf-8", newline="\n") as output:
        output.write(payload)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("roots", nargs="*", default=["lib", "tests/fixtures"],
                   help="scoped repo-relative directories; no implicit original approval")
    p.add_argument("--root", type=Path, default=ROOT)
    p.add_argument("--json", type=Path, help="new report file OUTSIDE repository; no clobber")
    p.add_argument("--require-bounded-uk", action="append", default=[],
                   help="require named existing .lisp to pass bounded UK proof, not oracle")
    args = p.parse_args(argv)
    try:
        data = inspect(args.root, tuple(args.roots))
        found = {row["path"]: row for row in data["files"]}
        missing = [path for path in args.require_bounded_uk
                   if path not in found or found[path]["status"] != GOOD_UK]
        if missing:
            data["status"] = "BLOCKED"
            data["failed_required"] = missing
        if args.json is not None:
            write_receipt(args.json, data, args.root)
        print(json.dumps({
            "status": data["status"],
            "summary": data["summary"],
            "failed_required": data.get("failed_required", []),
        }, ensure_ascii=False, sort_keys=True))
        return 2 if missing else 0
    except (InventoryBlocked, OSError, ValueError, UnicodeError) as error:
        print("INVENTORY BLOCKED: " + str(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
