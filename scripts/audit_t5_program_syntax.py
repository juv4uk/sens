#!/usr/bin/env python3
"""Read-only physical T5 -> current Rust D2 grammar admission audit.

Build/read the real SENS `sens-trit` opener; do NOT approximate D2 syntax in
Python or evaluate programs. Complements (does not replace) the independent
physical/source-pair audit #4497.

Syntax PASS != SENS oracle parity or release-certified executable semantics.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from audit_t5_file_pairs import inspect as inspect_physical_pairs
from sens_t5_codec import decode_bytes

SCHEMA = "sens-t5-d2-program-syntax-audit/v1"


def d2_structure_balance_hint(words: list[str]) -> dict:
    """Count only literal D2 OPEN/CLOSE boundaries as a read-only diagnostic.

    This is NOT a grammar parser, callable classifier, or admission law.
    Rust sens-trit decides D2 syntax. This only localizes obvious unmatched
    structural controls in the exact-width T5 word stream for owners.
    """
    opens: list[int] = []
    first_unexpected_close: int | None = None
    opens_total = 0
    closes_total = 0
    for index, word in enumerate(words, 1):
        if word == "10":
            opens_total += 1
            opens.append(index)
        elif word == "01":
            closes_total += 1
            if opens:
                opens.pop()
            elif first_unexpected_close is None:
                first_unexpected_close = index

    sample = []
    for index in opens[-5:]:
        low = max(index - 3, 1)
        high = min(index + 3, len(words))
        sample.append({
            "open_word": index,
            "context_start_word": low,
            "typed_words": words[low - 1:high],
        })
    return {
        "scope": "diagnostic-only; Rust D2 syntax remains authoritative",
        "typed_word_count": len(words),
        "d2_opens": opens_total,
        "d2_closes": closes_total,
        "first_unmatched_close_word": first_unexpected_close,
        "unclosed_open_count": len(opens),
        "first_unclosed_open_word": opens[0] if opens else None,
        "last_unclosed_open_word": opens[-1] if opens else None,
        "unclosed_open_contexts": sample,
    }


def audit(root: Path, *, reader: Path,
          include_untracked: bool = False,
          strict_source: bool = False) -> dict:
    """Mechanically validate packed bytes, provenance and current D2 parser."""
    root = root.resolve(strict=True)
    reader = reader.resolve(strict=True)
    if not root.is_dir() or not reader.is_file():
        raise ValueError("expected a directory and a real sens-trit executable")
    physical = inspect_physical_pairs(root, include_untracked=include_untracked)
    rows: list[dict] = []
    for item in physical["files"]:
        row = dict(item)
        row["syntax_status"] = "BLOCKED"
        row["oracle_status"] = "NOT_VERIFIED"
        rows.append(row)
        if row["physical_status"] != "PASS":
            row["syntax_reason"] = "physical T5 or same-stem source failed"
            continue
        path = root / row["sens"]
        if path.is_symlink():
            row["syntax_reason"] = "symlink not an admitted program file"
            continue
        try:
            # independent physical codec says only that trits/widths survive
            words = decode_bytes(path.read_bytes())
            result = subprocess.run(
                [str(reader), "open", str(path)],
                capture_output=True, check=False,
                timeout=15, text=True, encoding="utf-8",
            )
            if result.returncode != 0:
                row["d2_structure_balance_hint"] = d2_structure_balance_hint(words)
                row["syntax_reason"] = "Rust D2 reader rejected stream: " + (
                    result.stderr.strip()[:300] or f"exit={result.returncode}"
                )
                # A transport-level InvalidProgramSyntax is unhelpfully vague
                # for original-source migration. Ask the SAME Rust reader to
                # explain via its canonical grammar; never infer D2 in Python.
                # Older readers can lack this opt-in command: keep the original
                # BLOCK status and syntax reason in that case.
                explanation = subprocess.run(
                    [str(reader), "explain", str(path)],
                    capture_output=True, check=False,
                    timeout=15, text=True, encoding="utf-8",
                )
                detail = explanation.stderr.strip()
                if explanation.returncode and "D2 grammar rejected" in detail:
                    row["syntax_reason"] += " | " + detail[:1200]
                    row["d2_word_coordinate_diagnostic"] = detail[:1200]
                continue
            expected = " ".join(words) + "\n"
            if result.stdout != expected:
                row["syntax_reason"] = "Rust D2 human projection differs from exact typed words"
                continue
            row["syntax_status"] = "PASS_D2_SYNTAX"
            if row["source_status"] == "PENDING_ORACLE":
                row["syntax_reason"] = (
                    "source is symbolic Lisp: independent translation/oracle proof still required"
                )
            else:
                row["syntax_reason"] = (
                    "structural syntax admitted only; semantic execution not verified"
                )
        except (OSError, UnicodeError, subprocess.TimeoutExpired, ValueError) as exc:
            row["syntax_reason"] = str(exc)[:300]
    n = len(rows)
    passed = sum(row["syntax_status"] == "PASS_D2_SYNTAX" for row in rows)
    blocked = n - passed
    pending = sum(row["source_status"] == "PENDING_ORACLE" for row in rows)
    require_source_block = strict_source and pending != 0
    status = (
        "NO_FILES" if n == 0
        else "BLOCKED" if blocked or require_source_block
        else "SYNTAX_ONLY"
    )
    return {
        "schema": SCHEMA,
        "status": status,
        "source_mode": physical["mode"],
        "strict_source": strict_source,
        "empty_is_not_certification": n == 0,
        "summary": {
            "pairs_seen": n,
            "physical_pass": physical["summary"]["physical_pass"],
            "physical_blocked": physical["summary"]["physical_blocked"],
            "d2_syntax_pass": passed,
            "d2_syntax_blocked": blocked,
            "symbolic_source_pending_oracle": pending,
            "executable_semantics_certified": 0,
        },
        "files": rows,
        "warning": (
            "D2 grammar parse is not execution/oracle parity. "
            "A symbolic .lisp source requires proven historical mapping. "
            "No program is executed, no files are changed."
        ),
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("root", type=Path, nargs="?", default=Path("."))
    p.add_argument("--reader", type=Path, required=True,
                   help="built Rust sens-trit binary (real canonical D2 reader)")
    p.add_argument("--output", type=Path, help="optional read-only JSON audit report")
    p.add_argument("--include-untracked", action="store_true")
    p.add_argument("--strict-source", action="store_true",
                   help="symbolic Lisp without oracle must block release")
    p.add_argument("--require-files", action="store_true",
                   help="empty .sens inventory blocks release")
    args = p.parse_args(argv)
    try:
        report = audit(
            args.root, reader=args.reader, include_untracked=args.include_untracked,
            strict_source=args.strict_source,
        )
        if args.output is not None:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(
                json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
                encoding="utf-8",
            )
        print(json.dumps({"status": report["status"], **report["summary"]},
                         ensure_ascii=False, sort_keys=True))
        return 2 if report["status"] == "BLOCKED" or (
            args.require_files and report["status"] == "NO_FILES"
        ) else 0
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        print(f"SENS T5 D2 SYNTAX AUDIT ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
