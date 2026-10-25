#!/usr/bin/env python3
"""Read-only inventory of same-stem SENS triples: Ukrainian source, T5 and view.

This does not translate Ukrainian, admit semantic parity, or publish programs.
It never creates or modifies source, packed T5 or extensionless view files.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

from audit_t5_t5m_file_pairs import (inspect as inspect_pairs, physical_words, physical_encode, SKIP_DIRS)
from sens_t5_t5m_codec import typed_sha256
from report_ukr_projection_progress import tokenize_lisp
from audit_all_lisp_triplets import git_blob_sha, reviewed_nonprogram_pins

SCHEMA = "sens-t5-triplet-inventory/v1"
GOLDEN = "tests/fixtures/migration-d1-cond-cohort/branch.sens"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_view(words: list[str]) -> bytes:
    """Exactly ONE ASCII space between exact-width bit words and ONE last LF."""
    return (" ".join(words) + "\n").encode("ascii")


def tracked_paths(root: Path) -> set[str]:
    proc = subprocess.run(
        ["git", "-C", str(root), "ls-files", "-z"],
        capture_output=True, check=False,
    )
    if proc.returncode:
        raise ValueError("tracked Git inventory unavailable; use --include-untracked for temporary fixtures")
    return {os.fsdecode(x) for x in proc.stdout.split(b"\0") if x}


def lisp_source_names(root: Path, tracked: set[str] | None) -> list[str]:
    """List all .lisp inputs, not merely sources already paired with .sens."""
    if tracked is not None:
        return sorted(name for name in tracked if name.endswith(".lisp"))
    found: list[str] = []
    for directory, subdirs, files in os.walk(root, followlinks=False):
        subdirs[:] = sorted(
            name for name in subdirs
            if name not in SKIP_DIRS and not (Path(directory) / name).is_symlink()
        )
        found.extend(
            (Path(directory) / name).relative_to(root).as_posix()
            for name in files if name.endswith(".lisp")
        )
    return sorted(found)


def is_comment_only_lisp(root: Path, name: str) -> bool:
    """Коментарі й пробіли не породжують машинної програми для пакування.

    Вкладені #| ... |# та ; розпізнаються чинним Lisp-токенізатором.
    Неправильний UTF-8, обірваний коментар або посилання не звільняються
    від обліку виконуваних кандидатів.
    """
    relative = Path(name)
    path = root / relative
    if (not path.is_file() or path.is_symlink()
            or not no_link_ancestors(root, relative)):
        return False
    try:
        return not tokenize_lisp(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError):
        return False


def safe_relative(name: str) -> Path:
    if not isinstance(name, str) or not name or "\\" in name:
        raise ValueError("invalid relative .sens path")
    path = Path(name)
    if (path.is_absolute() or path.suffix != ".sens" or
            path.as_posix() != name or
            any(x in ("", ".", "..") for x in name.split("/"))):
        raise ValueError("require a safe repo-relative .sens path")
    return path


def no_link_ancestors(root: Path, relative: Path) -> bool:
    """Avoid symlink escapes even where the final view is a regular file."""
    cur = root
    for part in relative.parts:
        cur = cur / part
        if cur.is_symlink():
            return False
    return True


def inspect(root: Path, *, include_untracked: bool = False,
            required: tuple[str, ...] = (), strict: bool = False) -> dict:
    root = root.resolve(strict=True)
    if not root.is_dir():
        raise ValueError("not a directory")
    required_names = {safe_relative(p).as_posix() for p in required}
    # Existing canonical pair auditor supplies the complete physical inventory
    # and source provenance; this report adds VIEW only, not new semantics.
    pairs = inspect_pairs(root, include_untracked=include_untracked)
    tracked = None if include_untracked else tracked_paths(root)
    sources = lisp_source_names(root, tracked)
    records: list[dict] = []
    statuses = {}
    for pair in pairs["files"]:
        name = pair["sens"]
        path = safe_relative(name)
        # Джерело підтвердив фізичний аудитор: це може бути .lisp або .bits.
        source_rel = Path(pair["source"])
        if (source_rel.as_posix() != pair["source"] or
                source_rel not in (path.with_suffix(".lisp"), path.with_suffix(".bits"))):
            raise ValueError(f"invalid same-stem audited source for {name}: {pair['source']}")
        view_rel = path.with_suffix("")
        view_name = view_rel.as_posix()
        row = {
            "sens": name,
            "source": source_rel.as_posix(),
            "view": view_name,
            "physical_status": pair["physical_status"],
            "source_status": pair["source_status"],
            "view_status": "BLOCKED",
            "uk_oracle": "NOT_VERIFIED",
            "release_admitted": False,
            "original_executable_migration_credit": 0,
        }
        records.append(row)
        statuses[name] = row
        if (not no_link_ancestors(root, path) or
                not no_link_ancestors(root, source_rel) or
                not no_link_ancestors(root, view_rel)):
            row["view_status"] = "UNSAFE_LINK"
            row["reason"] = "source, physical binary or extensionless view has a symlink ancestor"
            continue
        if pair["physical_status"] != "PASS":
            row["view_status"] = "PHYSICAL_BLOCKED"
            row["reason"] = pair.get("error", "T5/source pair not validated")
            continue
        row["physical_sha256"] = pair["physical_sha256"]
        row["source_sha256"] = pair["source_sha256"]
        row["typed_word_sha256"] = pair["typed_word_sha256"]
        row["typed_word_count"] = pair["semantic_word_count"]
        try:
            payload = (root / path).read_bytes()
            codec = pair["physical_codec"]
            words = physical_words(payload, codec)
            # The base pair auditor has already checked this, but fail-closed
            # on changes to the physical file between its scan and our scan.
            if physical_encode(words, codec) != payload or sha(payload) != pair["physical_sha256"]:
                raise ValueError("T5 bytes drifted during inventory")
            expected = canonical_view(words)
            row["expected_view_sha256"] = sha(expected)
            file = root / view_rel
            if not file.is_file():
                row["view_status"] = "MISSING_VIEW"
                row["reason"] = "no extensionless text view beside verified .sens"
                continue
            if tracked is not None and view_name not in tracked:
                row["view_status"] = "UNTRACKED_VIEW"
                row["reason"] = "untracked extensionless view cannot prove a Git release candidate"
                continue
            actual = file.read_bytes()
            row["view_sha256"] = sha(actual)
            if actual != expected:
                row["view_status"] = "VIEW_MISMATCH"
                row["reason"] = (
                    "view must be canonical ASCII exact bits, one ordinary space "
                    "between words and one final LF; bytes differ from decoded T5"
                )
                continue
            if physical_encode(actual[:-1].decode("ascii").split(" "), codec) != payload:
                raise ValueError("view to physical T5 byte-roundtrip failed")
            if typed_sha256(actual[:-1].decode("ascii").split(" ")) != pair["typed_word_sha256"]:
                raise ValueError("exact domain word widths drifted")
            row["view_status"] = "PHYSICAL_VIEW_PASS"
        except (OSError, UnicodeError, ValueError) as exc:
            row["view_status"] = "BLOCKED"
            row["reason"] = str(exc)[:320]

    physical_names = set(statuses)
    unpaired_sources = [
        name for name in sources
        if Path(name).with_suffix(".sens").as_posix() not in physical_names
    ]
    # Усі .lisp залишаються в історичному знаменнику, але інертні
    # коментарі не стають недоведеними виконуваними SENS-програмами.
    # Точно SHA-затверджені джерела даних не є виконуваними програмами.
    # Пошкоджений маніфест, дрейф blob або симлінк не дають звільнення.
    reviewed = reviewed_nonprogram_pins(root)

    def is_reviewed_nonprogram(name: str) -> bool:
        pin = reviewed.get(name)
        relative = Path(name)
        path = root / relative
        return bool(pin and no_link_ancestors(root, relative)
                    and path.is_file() and not path.is_symlink()
                    and git_blob_sha(path.read_bytes()) == pin[0])

    unpaired_nonprogram = [
        name for name in unpaired_sources
        if is_comment_only_lisp(root, name) or is_reviewed_nonprogram(name)
    ]
    nonprogram = set(unpaired_nonprogram)
    unpaired_programs = [name for name in unpaired_sources if name not in nonprogram]
    failed_required = sorted(
        name for name in required_names
        if name not in statuses or statuses[name]["view_status"] != "PHYSICAL_VIEW_PASS"
    )
    blocked_physical = sum(r["physical_status"] != "PASS" for r in records)
    ready = sum(r["view_status"] == "PHYSICAL_VIEW_PASS" for r in records)
    missing = sum(r["view_status"] == "MISSING_VIEW" for r in records)
    invalid = sum(r["view_status"] not in ("PHYSICAL_VIEW_PASS", "MISSING_VIEW")
                  for r in records)
    # INCOMPLETE_VIEWS is a debt-bearing informational result, not release GREEN.
    status = ("NO_FILES" if not records else
              "BLOCKED" if blocked_physical or invalid or failed_required or
                          (strict and (ready != len(records) or unpaired_programs)) else
              "INCOMPLETE_VIEWS" if ready != len(records) else
              "INCOMPLETE_SOURCE_PAIRS" if unpaired_programs else
              "PHYSICAL_VIEW_ONLY_UK_PENDING")
    return {
        "schema": SCHEMA,
        "status": status,
        "mode": pairs["mode"],
        "strict": strict,
        "required": sorted(required_names),
        "failed_required": failed_required,
        "unpaired_lisp_sources": unpaired_sources,
        "unpaired_nonprogram_lisp_sources": unpaired_nonprogram,
        "unpaired_program_lisp_sources": unpaired_programs,
        "summary": {
            "lisp_sources_seen": len(sources),
            "lisp_with_physical": len(sources) - len(unpaired_sources),
            "lisp_without_physical": len(unpaired_sources),
            "unpaired_nonprogram_lisp_sources": len(unpaired_nonprogram),
            "unpaired_program_lisp_sources": len(unpaired_programs),
            "physical_pairs_seen": len(records),
            "physical_blocked": blocked_physical,
            "view_present_valid": ready,
            "view_missing": missing,
            "view_invalid_or_unsafe": invalid,
            "uk_oracle_verified": 0,
            "original_executable_migrations_certified": 0,
            "release_admitted": 0,
        },
        "files": records,
        "warning": (
            "All .lisp without .sens are counted; comment-only sources are "
            "reported separately and are not missing machine programs. "
            "T5↔ASCII view identity is mechanical ONLY. Ukrainian uk source "
            "roundtrip, independent runtime semantics and release are NOT_VERIFIED."
        ),
    }



def write_receipt_once(root: Path, destination: Path, report: dict) -> None:
    """Create an immutable JSON evidence file outside the source corpus.

    Hard-linking a flushed temporary file is exclusive; a concurrent write
    cannot replace a source .lisp, physical .sens, human view or earlier report.
    """
    source_root = root.resolve(strict=True)
    if not source_root.is_dir():
        raise ValueError("corpus root must be a directory")
    target = destination.absolute()
    if target.exists() or target.is_symlink():
        raise ValueError("report already exists; no overwrite")
    if target.resolve(strict=False).is_relative_to(source_root):
        raise ValueError("report must be outside original source repository")
    ancestor = target.parent
    while True:
        if ancestor.is_symlink():
            raise ValueError("report path has symlink ancestor")
        if ancestor == ancestor.parent:
            break
        ancestor = ancestor.parent
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.parent.is_symlink() or target.parent.resolve() != target.parent:
        raise ValueError("report parent changed to a symlink during staging")
    staged = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=target.parent,
            prefix=".sens-triplet-receipt-", suffix=".tmp", delete=False,
        ) as stream:
            staged = Path(stream.name)
            json.dump(report, stream, ensure_ascii=False, indent=2, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.link(staged, target)  # atomic create-if-absent
    except FileExistsError as error:
        raise ValueError("report already exists; no overwrite") from error
    finally:
        if staged is not None:
            staged.unlink(missing_ok=True)


def _proof_counts(proof_report):
    """(uk_oracle_verified, certified) зі звіту виконання.

    Відсутній, порожній або НЕВАЛІДНИЙ звіт -> (0, 0): відсутність доказу НЕ
    стає допуском. Невалідний JSON трапляється законно: при провалі
    prove-lisp-language-laws.sh виходить із exit 1 ДО закриття JSON.

    ПОВНИЙ валідний звіт означає, що ВСІ випадки пройшли: скрипт виходить із
    exit 1 на першій розбіжності.
    """
    if proof_report is None or not proof_report.is_file():
        return 0, 0
    try:
        data = json.loads(proof_report.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return 0, 0
    cases = data.get("cases")
    if not isinstance(cases, list) or not cases:
        return 0, 0
    laws = {c.get("test_id") for c in cases if c.get("kind") == "law"}
    mutants = {c.get("test_id") for c in cases if c.get("kind") == "mutant"}
    paired = {x for x in (laws & mutants) if x}
    return len(cases), len(paired)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path, nargs="?", default=Path("."))
    parser.add_argument("--include-untracked", action="store_true",
                        help="test-only: scan an isolated temporary fixture directory")
    parser.add_argument("--require-view", action="append", default=[],
                        help="require exact physical/view parity for named .sens path")
    parser.add_argument("--strict", action="store_true",
                        help="BLOCK if any physical view OR Lisp source pair is missing")
    parser.add_argument("--report", type=Path,
                        help="write JSON audit receipt, never a program or view")
    parser.add_argument("--proof-report", type=Path, default=None,
                        help="звіт scripts/prove-lisp-language-laws.sh: перелік "
                             "випадків, ПРОЙДЕНИХ виконанням. Порожній/невалідний "
                             "= відсутність доказу, а НЕ допуск")
    parser.add_argument("--informational", action="store_true",
                        help="show existing migration debt without stopping unrelated CI; audit errors still fail")
    args = parser.parse_args(argv)
    if args.informational and (args.strict or args.require_view):
        print("TRIPLE INVENTORY BLOCKED: --informational cannot override --strict/--require-view",
              file=sys.stderr)
        return 2
    try:
        report = inspect(
            args.root, include_untracked=args.include_untracked,
            required=tuple(args.require_view), strict=args.strict,
        )
        # Доказ під'єднано: три поля-вердикти стають ВИВЕДЕНИМИ зі звіту
        # виконання. БЕЗ доказу повертається (0, 0) — те саме, що було зашито,
        # тож вердикт НЕ змінюється. status НЕ перераховується: це семантика
        # гейта і рішення власника.
        uk_oracle, certified = _proof_counts(args.proof_report)
        report["summary"]["uk_oracle_verified"] = uk_oracle
        report["summary"]["original_executable_migrations_certified"] = certified
        report["summary"]["release_admitted"] = 1 if certified > 0 else 0
        if args.report:
            write_receipt_once(args.root, args.report, report)
        print(json.dumps({"status": report["status"], **report["summary"],
                          "failed_required": report["failed_required"]},
                         ensure_ascii=False, sort_keys=True))
        if args.informational and report["status"] == "BLOCKED":
            # A successfully computed inventory is not a release gate. Do not
            # swallow exceptions: they still take the error branch below.
            print("::warning::T5_TRIPLET_INVENTORY_DEBT: physical/source debt remains; semantic parity NOT_VERIFIED")
            return 0
        return 2 if report["status"] in ("BLOCKED", "NO_FILES") else 0
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        print("TRIPLE INVENTORY BLOCKED: " + str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
