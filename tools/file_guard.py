#!/usr/bin/env python3
"""Тимчасова зовнішня гвардія нових файлів SENS; семантика належить SENS.

Жодного assert: навіть python -O не вимикає охорону.
Міграційний контракт: tools/foreign-census.json, задача #5396.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import PurePosixPath
from typing import Any

CENSUS = "tools/foreign-census.json"
IMPORTANT = ("lib/", "knowledge/", "witnesses/")
ALLOWED = {".lisp", ".sens"}
BLOCKED = "SENS-FILE-GUARD: BLOCKED"
ISSUE = re.compile(r"^#[0-9]+$")


def fail(message: str) -> None:
    raise ValueError(message)


def command(*args: str) -> bytes:
    proc = subprocess.run(
        ["git", *args], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False
    )
    if proc.returncode:
        fail(f"Git завершився {proc.returncode}: {' '.join(args)}: "
             f"{proc.stderr.decode('utf-8', 'replace')}")
    return proc.stdout


def paths_nul(raw: bytes) -> list[str]:
    # Порожній Git diff допустимий; кожний непорожній запис з -z завершується NUL.
    if not raw:
        return []
    if not raw.endswith(b"\x00"):
        fail("Обірваний Git NUL-перелік: немає кінцевого NUL")
    parts = raw[:-1].split(b"\x00")
    if any(not part for part in parts):
        fail("Порожнє поле у Git NUL-переліку")
    try:
        return [value.decode("utf-8") for value in parts]
    except UnicodeDecodeError as exc:
        fail(f"Некоректний UTF-8 у Git-шляху: {exc}")


def path_valid(path: str) -> bool:
    return bool(path) and not path.startswith("/") and "\\" not in path and all(
        section not in ("", ".", "..") for section in path.split("/")
    )


def census_entries(data: Any) -> dict[str, dict[str, str]]:
    if not isinstance(data, dict) or data.get("schema") != "sens-foreign-tool-census/1":
        fail("Немає чинної схеми реєстру foreign-інструментів")
    entries = data.get("tools")
    if not isinstance(entries, list):
        fail("Поле tools має бути списком")
    results: dict[str, dict[str, str]] = {}
    for entry in entries:
        if not isinstance(entry, dict):
            fail("Запис foreign-інструмента має бути об'єктом")
        path = entry.get("path")
        status = entry.get("independence_status")
        plan = entry.get("migration_plan")
        purpose = entry.get("purpose")
        issue = entry.get("owner_issue")
        if not isinstance(path, str) or not path_valid(path) or not (
            path.startswith("tools/") and path.endswith(".py")
        ):
            fail(f"Недопустимий шлях foreign-інструмента: {path!r}")
        if path in results:
            fail(f"Дубль foreign-запису: {path}")
        if status != "foreign":
            fail(f"{path}: independence_status мусить бути foreign")
        if not isinstance(plan, str) or len(plan.strip()) < 60:
            fail(f"{path}: потрібен конкретний план міграції до SENS")
        if not isinstance(purpose, str) or len(purpose.strip()) < 20:
            fail(f"{path}: відсутня роль зовнішнього механізму")
        if not isinstance(issue, str) or not ISSUE.fullmatch(issue):
            fail(f"{path}: потрібна точна задача GitHub #NNN")
        results[path] = entry
    return results


def violations(added: list[str], tracked_python: list[str],
               census: dict[str, dict[str, str]]) -> list[str]:
    errors: list[str] = []
    for path in added:
        if not path_valid(path):
            errors.append(f"неканонічний Git-шлях: {path!r}")
            continue
        if path.startswith(IMPORTANT) and PurePosixPath(path).suffix not in ALLOWED:
            errors.append(f"{path}: нове важливе джерело дозволено лише .lisp/.sens")
        if path.endswith(".py") and not path.startswith("tools/"):
            errors.append(f"{path}: новий Python дозволено лише у tools/")
        if path.startswith("tools/") and path.endswith(".py") and path not in census:
            errors.append(f"{path}: немає foreign-запису та плану міграції")
    for path in tracked_python:
        if not path_valid(path) or not path.startswith("tools/") or not path.endswith(".py"):
            errors.append(f"неочікуваний шлях Python-інструмента: {path!r}")
        elif path not in census:
            errors.append(f"{path}: чинний tools/*.py не внесено до foreign-census")
    for path in census:
        if path not in tracked_python:
            errors.append(f"{path}: запис census без фактичного tools/*.py")
    return errors


def self_test() -> None:
    # Іспит NUL-транспорту: жодне обрізання чи порожнє поле не є PASS.
    if paths_nul(b"") != []:
        fail("Порожній Git NUL-перелік спотворено")
    valid_path = "witnesses/доказ.lisp"
    if paths_nul(valid_path.encode("utf-8") + b"\x00") != [valid_path]:
        fail("Коректний UTF-8 Git NUL-шлях відхилено")
    for malformed in (
        b"knowledge/broken.json",
        b"lib/ok.lisp\x00\x00",
        b"\x00",
        b"lib/ok.lisp\x00\x00tools/uncensused.py\x00",
        b"\xff\x00",
    ):
        try:
            paths_nul(malformed)
        except ValueError:
            continue
        fail(f"Пошкоджений Git NUL-перелік допущено: {malformed!r}")
    entry = {
        "path": "tools/check.py", "independence_status": "foreign",
        "purpose": "Тимчасова незалежна від семантики гвардія Git",
        "migration_plan": "Замінити логіку на SENS .sens, атестувати позитивні "
                          "та негативні свідки на реальному оракулі.",
        "owner_issue": "#5396",
    }
    admitted = census_entries({"schema": "sens-foreign-tool-census/1", "tools": [entry]})
    samples = [
        (["lib/нове.lisp", "knowledge/закон.sens", "witnesses/доказ.lisp"],
         ["tools/check.py"], []),
        (["lib/new.json"], ["tools/check.py"], ["lib/new.json"]),
        (["knowledge/new.tsv"], ["tools/check.py"], ["knowledge/new.tsv"]),
        (["witnesses/new.py"], ["tools/check.py"], ["нове важливе джерело", "новий Python"]),
        (["scripts/new.py"], ["tools/check.py"], ["scripts/new.py"]),
        (["tools/unknown.py"], ["tools/check.py"], ["tools/unknown.py"]),
        ([], ["tools/check.py", "tools/unknown.py"], ["tools/unknown.py"]),
        (["lib/../escape.lisp"], ["tools/check.py"], ["lib/../escape.lisp"]),
    ]
    for added, tracked, expected in samples:
        actual = violations(added, tracked, admitted)
        if len(actual) != len(expected) or any(
            not any(want in error for error in actual) for want in expected
        ):
            fail(f"Негативний тест гвардії не пройшов: {added!r}: {actual!r}")
    for invalid in (
        {**entry, "independence_status": "own"},
        {**entry, "migration_plan": ""},
        {**entry, "owner_issue": ""},
    ):
        try:
            census_entries({"schema": "sens-foreign-tool-census/1", "tools": [invalid]})
        except ValueError:
            continue
        fail("Неправильний foreign-запис несподівано допущено")
    print("SENS-FILE-GUARD: 11 негативних/позитивних сценаріїв PASS")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", help="Git commit до зміни (PR base або push before)")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    if not args.base or not re.fullmatch(r"[0-9a-fA-F]{40}", args.base) or set(args.base) == {"0"}:
        fail("Потрібен непорожній точний 40-символьний Git SHA бази")
    command("rev-parse", "--verify", f"{args.base}^{{commit}}")
    command("merge-base", "--is-ancestor", args.base, "HEAD")
    added = paths_nul(command(
        "diff", "--no-renames", "--diff-filter=A", "--name-only", "-z", args.base, "HEAD"
    ))
    tracked = [p for p in paths_nul(command("ls-files", "-z", "--", "tools/"))
               if p.endswith(".py")]
    try:
        with open(CENSUS, encoding="utf-8") as source:
            census = census_entries(json.load(source))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        fail(f"Не можна прочитати обов'язковий foreign census: {exc}")
    errors = violations(added, tracked, census)
    if errors:
        for error in errors:
            print(f"{BLOCKED} — {error}", file=sys.stderr)
        return 1
    print(f"SENS-FILE-GUARD: PASS (нових файлів: {len(added)}, "
          f"облікованих foreign Python: {len(tracked)})")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError) as exc:
        print(f"{BLOCKED} — {exc}", file=sys.stderr)
        raise SystemExit(2)
