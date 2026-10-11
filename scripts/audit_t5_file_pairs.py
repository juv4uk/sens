#!/usr/bin/env python3
"""Read-only audit of physical T5 + Ukrainian .lisp + optional spaced-bit view.

Scope: physical file identity and source provenance, NOT oracle certification.
Never creates, deletes, fixes or converts any source or target.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

from sens_t5_codec import SensT5Error, decode_bytes, encode_words, parse_words, typed_sha256

SCHEMA = "sens-t5-file-pair-audit/v1"
SKIP_DIRS = {".git", ".venv", "venv", "node_modules", "target", "__pycache__"}


def candidates(root: Path, include_untracked: bool = False) -> list[Path]:
    """Prefer tracked Git files to avoid generated build/cache artifacts."""
    if not include_untracked:
        proc = subprocess.run(
            ["git", "-C", str(root), "ls-files", "-z", "--", "*.sens"],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False,
        )
        if proc.returncode == 0:
            paths = [root / os.fsdecode(rel) for rel in proc.stdout.split(b"\0") if rel]
            return sorted(paths)
    result: list[Path] = []
    for directory, names, files in os.walk(root, followlinks=False):
        names[:] = sorted(name for name in names if name not in SKIP_DIRS)
        for name in sorted(files):
            if name.endswith(".sens"):
                result.append(Path(directory) / name)
    return sorted(result)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def split_nul_delimited_paths(raw: bytes) -> list[str]:
    """Decode the NUL-terminated path stream emitted by Git's -z options."""
    if not raw:
        return []
    if not raw.endswith(b"\0"):
        raise ValueError("NUL-delimited Git output is missing its final terminator")
    fields = raw[:-1].split(b"\0")
    if any(not field for field in fields):
        raise ValueError("NUL-delimited Git output contains an empty path")
    return [os.fsdecode(field) for field in fields]


def require_changed_views(report: dict, changed_sens: list[str]) -> None:
    """PR/push gate: no NEW/MODIFIED physical .sens without a verified view.

    This does NOT pretend legacy existing files are admitted. Source-to-current
    semantic equivalence needs independent Ukrainian oracle and original SHA.
    """
    if report.get("schema") != SCHEMA:
        raise ValueError("unknown T5 report schema")
    records = {row["sens"]: row for row in report.get("files", ())}
    if len(records) != len(report.get("files", ())):
        raise ValueError("duplicate T5 source pair report rows")
    seen: set[str] = set()
    for path in changed_sens:
        if not isinstance(path, str) or not path.endswith(".sens") or path.startswith("/"):
            raise ValueError(f"invalid changed T5 path: {path!r}")
        posix = Path(path)
        if (posix.as_posix() != path or
                any(part in ("", ".", "..") for part in path.split("/"))):
            raise ValueError(f"unsafe changed T5 path: {path!r}")
        if path in seen:
            raise ValueError(f"duplicate changed T5 path: {path}")
        seen.add(path)
        row = records.get(path)
        if row is None:
            raise ValueError(f"new/modified T5 not included in physical audit: {path}")
        if row.get("physical_status") != "PASS" or row.get("view_status") != "PASS":
            raise ValueError(
                f"new/modified T5 must have same-stem canonical spaced-bit view: {path}; "
                f"physical={row.get('physical_status')} view={row.get('view_status')}"
            )


def inspect(root: Path, *, strict_semantic: bool = False,
            include_untracked: bool = False,
            require_spaced_view: bool = False) -> dict:
    root = root.resolve(strict=True)
    if not root.is_dir():
        raise ValueError("root must be directory")
    entries: list[dict] = []
    for file in candidates(root, include_untracked):
        try:
            rel = file.relative_to(root)
        except ValueError:
            raise ValueError("candidate not within root") from None
        row = {
            "sens": rel.as_posix(),
            "source": rel.with_suffix(".lisp").as_posix(),
            "view": rel.with_suffix("").as_posix(),
            "view_status": "NOT_CHECKED",
            "physical_status": "BLOCKED",
            "source_status": "NOT_CHECKED",
        }
        entries.append(row)
        source = root / rel.with_suffix(".lisp")
        try:
            # No link traversal into unrelated user-owned paths.
            if file.is_symlink() or source.is_symlink():
                raise ValueError("symlink source/target forbidden")
            if not file.is_file():
                raise ValueError("physical .sens is not a regular file")
            if not source.is_file():
                raise ValueError("missing same-stem .lisp source")
            data = file.read_bytes()
            words = decode_bytes(data)
            if encode_words(words) != data:
                raise ValueError("T5 canonical re-encode mismatch")
            row.update({
                "physical_status": "PASS",
                "physical_bytes": len(data),
                "physical_sha256": _sha(data),
                "typed_word_sha256": typed_sha256(words),
                "semantic_word_count": len(words),
                "semantic_bits": sum(map(len, words)),
                "interword_trits": len(words) - 1,
            })
            source_bytes = source.read_bytes()
            row["source_sha256"] = _sha(source_bytes)
            try:
                source_text = source_bytes.decode("utf-8")
            except UnicodeError:
                row["source_status"] = "PENDING_ORACLE"
                row["source_reason"] = "source not readable as UTF-8 exact projection"
            else:
                try:
                    source_words = parse_words(source_text)
                except SensT5Error:
                    # Symbolic Lisp may have a VALID conversion, but independent
                    # source→SENS semantics are not established by this audit.
                    row["source_status"] = "PENDING_ORACLE"
                    row["source_reason"] = "nonbinary .lisp requires proven translator + oracle"
                else:
                    if source_words != words:
                        raise ValueError("binary source word identities differ from .sens")
                    row["source_status"] = "EXACT_BINARY_SOURCE"

            # The extensionless third projection is a GENERATED read-only view.
            # Verify exact canonical ASCII bytes from the PHYSICAL .sens, not
            # from a potentially untrusted source or a whitespace-tolerant split().
            # Source→current-SENS semantic parity remains a SEPARATE oracle.
            view = root / rel.with_suffix("")
            if view.is_symlink():
                row["view_status"] = "BLOCKED"
                row["view_reason"] = "symlink extensionless view forbidden"
            elif view.exists():
                if not view.is_file():
                    row["view_status"] = "BLOCKED"
                    row["view_reason"] = "extensionless view must be a regular file"
                else:
                    try:
                        actual_view = view.read_bytes()
                    except OSError as exc:
                        row["view_status"] = "BLOCKED"
                        row["view_reason"] = str(exc)
                    else:
                        canonical_view = (" ".join(words) + "\n").encode("ascii")
                        if actual_view != canonical_view:
                            row["view_status"] = "BLOCKED"
                            row["view_reason"] = (
                                "extensionless spaced-bit view differs from "
                                "canonical T5 typed words or ASCII/LF layout"
                            )
                        else:
                            row["view_status"] = "PASS"
                            row["view_sha256"] = _sha(actual_view)
            else:
                row["view_status"] = "MISSING_NOT_CERTIFIED"
        except (OSError, SensT5Error, ValueError) as exc:
            row["error"] = str(exc)
            row["physical_status"] = "BLOCKED"
            if row["source_status"] == "NOT_CHECKED":
                row["source_status"] = "BLOCKED"
    physical_blockers = sum(row["physical_status"] == "BLOCKED" for row in entries)
    pending_oracle = sum(row["source_status"] == "PENDING_ORACLE" for row in entries)
    exact_binary = sum(row["source_status"] == "EXACT_BINARY_SOURCE" for row in entries)
    view_pass = sum(row["view_status"] == "PASS" for row in entries)
    view_missing = sum(row["view_status"] == "MISSING_NOT_CERTIFIED" for row in entries)
    view_blocked = sum(row["view_status"] == "BLOCKED" for row in entries)
    return {
        "schema": SCHEMA,
        "mode": "tracked-only" if not include_untracked else "all-files",
        "strict_semantic": strict_semantic,
        "require_spaced_view": require_spaced_view,
        "empty_is_not_certification": len(entries) == 0,
        "summary": {
            "sens_files": len(entries),
            "physical_pass": len(entries) - physical_blockers,
            "physical_blocked": physical_blockers,
            "exact_binary_source_pairs": exact_binary,
            "pending_oracle": pending_oracle,
            "spaced_view_pass": view_pass,
            "spaced_view_missing": view_missing,
            "spaced_view_blocked": view_blocked,
            "admitted_executable_semantics": None,
        },
        "status": (
            "BLOCKED" if (physical_blockers or view_blocked
                          or (require_spaced_view and view_missing)
                          or (strict_semantic and pending_oracle))
            else "NO_FILES" if not entries else
            "MECHANICAL_ONLY" if pending_oracle else "EXACT_BINARY_PAIRS"
        ),
        "files": entries,
        "warning": (
            "Physical T5 and a source pair do not prove parser/oracle semantics. "
            "Missing extensionless views are NOT certified unless explicitly "
            "required for a scoped admitted cohort. Symbolic Lisp remains "
            "PENDING_ORACLE; no automatic execution."
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path, nargs="?", default=Path("."))
    parser.add_argument("--output", type=Path, help="JSON report path (not inside .sens)")
    parser.add_argument("--strict-semantic", action="store_true",
                        help="require exact 0/1 source identity; block symbolic .lisp")
    parser.add_argument("--include-untracked", action="store_true",
                        help="scan all .sens files; default scans only git-tracked files")
    parser.add_argument("--require-spaced-view", action="store_true",
                        help="fail if any checked .sens has no canonical same-stem ASCII view; scope to an admitted cohort")
    args = parser.parse_args(argv)
    try:
        report = inspect(args.root, strict_semantic=args.strict_semantic,
                         include_untracked=args.include_untracked,
                         require_spaced_view=args.require_spaced_view)
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(
                json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
        print(json.dumps({"status": report["status"], **report["summary"]},
                         ensure_ascii=False, sort_keys=True))
        return 2 if report["status"] == "BLOCKED" else 0
    except (OSError, ValueError) as exc:
        print(f"T5 FILE-PAIR AUDIT ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
