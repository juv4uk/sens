#!/usr/bin/env python3
"""Суцільний облік .lisp -> .sens -> двійкового перегляду.

Усі каталоги входять до знаменника, зокрема історичні та тестові.
Наявність файлів НЕ є доказом зворотності. --verify-bounded запускає
справжній обмежений перевірник трійок (D1/D2/D3 та доведений D4);
непідтримувані форми залишаються BLOCKED, а не PASS.
Навіть 100% обмеженої зворотності не доводять виконання SENS.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from report_ukr_projection_progress import examine_file

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "sens-all-lisp-reversibility-census/v1"


def scan(root: Path, *, verify_bounded: bool = False, validator=None, limit: int = 20) -> dict:
    if not root.is_dir():
        raise NotADirectoryError(root)
    if limit < 0:
        raise ValueError("limit має бути невід'ємним")
    root = root.resolve()
    sources = sorted(
        (p for p in root.rglob("*.lisp") if ".git" not in p.relative_to(root).parts),
        key=lambda p: p.relative_to(root).as_posix(),
    )
    if verify_bounded and validator is None:
        from verify_uk_t5_triplet import verify
        validator = verify

    counts = dict(ukrainian_keyboard=0, with_sens=0, with_view=0,
                  complete_triplets=0, bounded_verified=0)
    blocked: list[dict[str, str]] = []

    def reject(path: str, reason: str) -> None:
        blocked.append({"path": path, "reason": reason})

    for source in sources:
        relative = source.relative_to(root).as_posix()
        # Never follow a symlink, even when its target looks valid.
        if source.is_symlink() or not source.is_file():
            reject(relative, "не звичайний файл Lisp")
            continue
        keyboard_problem = examine_file(source)
        if keyboard_problem is None:
            counts["ukrainian_keyboard"] += 1
        else:
            reject(relative, "не повністю українська розкладка: " + keyboard_problem)
        physical = source.with_suffix(".sens")
        view = source.with_suffix("")
        has_sens = physical.is_file() and not physical.is_symlink()
        has_view = view.is_file() and not view.is_symlink()
        counts["with_sens"] += int(has_sens)
        counts["with_view"] += int(has_view)
        if not has_sens:
            reject(relative, "немає звичайного однойменного .sens")
            continue
        if not has_view:
            reject(relative, "немає звичайного двійкового перегляду")
            continue
        counts["complete_triplets"] += 1
        if verify_bounded:
            try:
                witness = validator(source, physical, view)
                if not isinstance(witness, dict) or not witness.get("canonical_uk_roundtrip"):
                    raise ValueError("перевірник не підтвердив канонічний оберт")
            except (OSError, ValueError, UnicodeError) as exc:
                reject(relative, "обмежена зворотність BLOCKED: " + str(exc))
            else:
                counts["bounded_verified"] += 1

    all_verified = bool(sources) and (
        counts["bounded_verified"] == len(sources)
        and counts["ukrainian_keyboard"] == len(sources)
        and verify_bounded
    )
    return {
        "schema": SCHEMA,
        "total_lisp_files": len(sources),
        **counts,
        "missing_sens": len(sources) - counts["with_sens"],
        "missing_complete_triplet": len(sources) - counts["complete_triplets"],
        "unverified_triplets": counts["complete_triplets"] - counts["bounded_verified"],
        "verification_requested": verify_bounded,
        "all_bounded_reverse_verified": all_verified,
        "semantic_runtime_proven": False,
        "release_ready": False,
        "release_decision": "NO-GO: потрібні докази виконання SENS та повної семантики",
        "blocked_count": len(blocked),
        "blocked_sample": blocked[:limit],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--json", type=Path)
    parser.add_argument("--verify-bounded", action="store_true")
    parser.add_argument("--require-reversible", action="store_true",
                        help="відмова, якщо хоч один Lisp-файл не має підтвердженої обмеженої зворотності")
    args = parser.parse_args(argv)
    try:
        result = scan(args.root, verify_bounded=args.verify_bounded, limit=args.limit)
    except (OSError, ValueError) as exc:
        print("CENSUS_BLOCKED: " + str(exc), file=sys.stderr)
        return 2
    text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    print(text, end="")
    if args.json:
        args.json.write_text(text, encoding="utf-8")
    if args.require_reversible and not result["all_bounded_reverse_verified"]:
        print("REVERSE_BLOCKED: неповне або недоведене покриття", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
