#!/usr/bin/env python3
"""Перехідна файлова гвардія SENS (#5398); замінити фізичним SENS-оракулом.

Немає assert, eval, прихованих дефолтів або керування PASS через -O.
Перевіряється повний поточний Git-індекс, не вибірка змінених файлів.
"""
from __future__ import annotations

import csv
import os
import subprocess
import sys
from pathlib import Path

BASELINE = "e2c049e30e2c442c3814d01106ca4c13f0effaf4"
CENSUS = Path("tools/foreign-census.tsv")
PROTECTED = ("lib/", "knowledge/", "witnesses/")
SELF = "tools/check_source_policy.py"
HEADER = ["path", "independence_status", "migration_plan"]


class PolicyError(Exception):
    pass


def git_paths(*args: str) -> set[str]:
    result = subprocess.run(
        ["git", *args],
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise PolicyError(
            "GIT_EVIDENCE_UNAVAILABLE: " +
            result.stderr.decode("utf-8", errors="replace").strip()
        )
    try:
        paths = [part.decode("utf-8") for part in result.stdout.split(b"\0") if part]
    except UnicodeError as error:
        raise PolicyError("PATH_ENCODING_INVALID: " + str(error)) from error
    if len(paths) != len(set(paths)):
        raise PolicyError("DUPLICATE_GIT_PATH")
    return set(paths)


def read_census(path: Path) -> dict[str, tuple[str, str]]:
    if not path.is_file():
        raise PolicyError("CENSUS_MISSING: " + str(path))
    result: dict[str, tuple[str, str]] = {}
    try:
        with path.open("r", encoding="utf-8", newline="") as stream:
            reader = csv.reader(stream, delimiter="\t", quoting=csv.QUOTE_NONE)
            first = next(reader, None)
            if first != HEADER:
                raise PolicyError("CENSUS_HEADER_INVALID")
            for number, row in enumerate(reader, start=2):
                if len(row) != 3:
                    raise PolicyError(f"CENSUS_ROW_INVALID: line={number}")
                name, status, plan = row
                if (not name or name.startswith("/") or
                    "\\" in name or ".." in name.split("/") or
                    name in result):
                    raise PolicyError(f"CENSUS_PATH_INVALID: line={number} path={name!r}")
                if status != "foreign" or not plan.strip() or "мігра" not in plan.lower():
                    raise PolicyError(f"CENSUS_PLAN_MISSING: line={number} path={name}")
                result[name] = (status, plan)
    except (OSError, UnicodeError, csv.Error) as error:
        raise PolicyError("CENSUS_UNREADABLE: " + str(error)) from error
    return result


def important(path: str) -> bool:
    return any(path.startswith(prefix) for prefix in PROTECTED)


def permitted_important(path: str) -> bool:
    return path.endswith(".lisp") or path.endswith(".sens")


def problems(
    tracked: set[str],
    baseline: set[str],
    census: dict[str, tuple[str, str]],
) -> list[str]:
    errors: list[str] = []
    for name in sorted(tracked):
        legacy = name in baseline
        if important(name) and not permitted_important(name) and not legacy:
            errors.append("IMPORTANT_FOREIGN_NEW: " + name)
        if name.endswith(".py") and not name.startswith("tools/") and not legacy:
            errors.append("PY_OUTSIDE_TOOLS: " + name)
        needs_census = (
            name.endswith(".py") or
            (important(name) and not permitted_important(name))
        )
        if needs_census and name not in census:
            errors.append("FOREIGN_WITHOUT_CENSUS: " + name)
    for name in sorted(census):
        if name in baseline:
            if not (name.endswith(".py") or (important(name) and not permitted_important(name))):
                errors.append("CENSUS_UNNEEDED_LEGACY: " + name)
        elif name not in tracked or not (name.startswith("tools/") and name.endswith(".py")):
            errors.append("CENSUS_CANNOT_AUTHORIZE_NEW_EXCEPTION: " + name)
    if SELF not in tracked or SELF not in census:
        errors.append("GUARD_NOT_REGISTERED: " + SELF)
    if CENSUS.as_posix() not in tracked:
        errors.append("CENSUS_NOT_TRACKED: " + CENSUS.as_posix())
    return errors


def self_test() -> None:
    prior = {
        "lib/core4.lisp.fasl",
        "knowledge/existing.json",
        "scripts/existing.py",
    }
    census = {
        "lib/core4.lisp.fasl": ("foreign", "міграція-після-паритету"),
        "knowledge/existing.json": ("foreign", "міграція-після-паритету"),
        "scripts/existing.py": ("foreign", "міграція-після-паритету"),
        SELF: ("foreign", "міграція-в-SENS"),
    }
    mandatory = {SELF, CENSUS.as_posix()}
    cases = [
        ("дозволені вихідні файли",
         prior | mandatory | {"lib/new.lisp", "knowledge/new.sens"},
         census, None),
        ("новий JSON заборонено",
         prior | mandatory | {"knowledge/new.json"},
         census, "IMPORTANT_FOREIGN_NEW"),
        ("новий Python заборонено",
         prior | mandatory | {"tests/new.py"},
         census, "PY_OUTSIDE_TOOLS"),
        ("невідомий інструмент заборонено",
         prior | mandatory | {"tools/new.py"},
         census, "FOREIGN_WITHOUT_CENSUS"),
        ("зареєстрований тимчасовий інструмент",
         prior | mandatory | {"tools/new.py"},
         {**census, "tools/new.py": ("foreign", "міграція-в-SENS")},
         None),
        ("запис census не обходить заборону",
         prior | mandatory | {"knowledge/new.json"},
         {**census, "knowledge/new.json": ("foreign", "міграція-в-SENS")},
         "IMPORTANT_FOREIGN_NEW"),
        ("виключений census обов'язково падає",
         prior | mandatory,
         {name: value for name, value in census.items() if name != "scripts/existing.py"},
         "FOREIGN_WITHOUT_CENSUS"),
    ]
    for label, tracked, data, expected in cases:
        errors = problems(tracked, prior, data)
        if expected is None and errors:
            raise PolicyError("SELF_TEST_UNEXPECTED_FAIL: " + label + " " + str(errors))
        if expected is not None and not any(expected in error for error in errors):
            raise PolicyError("SELF_TEST_UNEXPECTED_PASS: " + label + " " + str(errors))
    print("OK: 7/7 негативних і позитивних сценаріїв (без assert)")


def main() -> int:
    try:
        if sys.argv[1:] == ["--self-test"]:
            self_test()
            return 0
        if len(sys.argv) != 1:
            raise PolicyError("UNKNOWN_OPTION: допустимо лише --self-test")
        # Чужий перевірювач є тимчасовим. Не довіряємо silent defaults.
        census = read_census(CENSUS)
        baseline = git_paths("ls-tree", "-r", "--name-only", "-z", BASELINE)
        tracked = git_paths("ls-files", "-z", "--cached", "--others", "--exclude-standard")
        if not baseline:
            raise PolicyError("BASELINE_EMPTY")
        if not tracked:
            raise PolicyError("TRACKED_TREE_EMPTY")
        errors = problems(tracked, baseline, census)
        for name in sorted(tracked):
            if (important(name) or name.endswith(".py")) and not Path(name).is_file():
                errors.append("TRACKED_FILE_MISSING: " + name)
        if errors:
            for error in errors:
                print("SENS_FILE_POLICY_FAIL: " + error, file=sys.stderr)
            return 1
        print(
            "SENS_FILE_POLICY_PASS: поточні файли=%d, успадковані=%d, foreign census=%d" %
            (len(tracked), len(baseline), len(census))
        )
        return 0
    except PolicyError as error:
        print("SENS_FILE_POLICY_FAIL: " + str(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
