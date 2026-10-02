#!/usr/bin/env python3
"""Discover top-level Lisp definitions without assigning API visibility.

This is a discovery tool, not semantic authority.  It observes canonical
``lib/**/*.lisp`` source and reports top-level DEFINE/``def`` / ``defmacro``
forms. DEFINE's byte-SID spellings come from the Lisp-owned function table
(`(form define)` rows of lib/surface/function-signatures.lisp).
Visibility (public/internal/compatibility) is a separate governance decision.
Surface spellings remain owned exclusively by ``lib/surface/semantic-registry.lisp``.
Machine/ISA exclusion is read from the Lisp-owned machine authority contract;
Python transports that classification but does not own it.  The generated
report is review input only until visibility is explicitly ratified.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import re
import sys

REPO_ROOT = Path(__file__).resolve().parent.parent
LIB_ROOT = REPO_ROOT / "lib"
REPORT = REPO_ROOT / "docs" / "generated" / "public-api-discovery.md"
MACHINE_AUTHORITY = LIB_ROOT / "machine" / "authority-boundary.lisp"
FUNCTION_SIGNATURES = LIB_ROOT / "surface" / "function-signatures.lisp"
CORE_PROFILE_AUTHORITY = REPO_ROOT / "contracts" / "core-profile-contract.lisp"
STATIC_EXCLUDED_TOP_LEVEL_DIRS = {"generated", "surface"}
PUBLIC_API_EXCLUDED_ROOT = re.compile(
    r"^\s*\(public-api-excluded-root\s+lib/([^/\s()]+)\)\s*$"
)
DEFINE_SIGNATURE_ROW = re.compile(r"^\s*\(([01]{8})\s+\(kind syntax\)\s+\(form define\)")
DEFMACRO_SIGNATURE_ROW = re.compile(r"^\s*\(([01]{8})\s+\(kind macro\).*\(sig \"\(defmacro ")
PUBLIC_API_NONCURRENT_SOURCE = re.compile(
    r'^\s*\((?:historical-source|laboratory-source|former-source)\s+\.\s+"([^"]+)"\)+\s*(frozen=True, order=True)
class Definition:
    source: str
    line: int
    kind: str
    name: str


def _mask_strings_and_comments(source: str) -> str:
    """Replace string/comment contents with spaces while preserving newlines."""
    out: list[str] = []
    in_string = False
    escaped = False
    in_comment = False

    for char in source:
        if in_comment:
            if char == "\n":
                in_comment = False
                out.append(char)
            else:
                out.append(" ")
            continue

        if in_string:
            if escaped:
                escaped = False
                out.append(" ")
            elif char == "\\":
                escaped = True
                out.append(" ")
            elif char == '"':
                in_string = False
                out.append(" ")
            elif char == "\n":
                out.append("\n")
            else:
                out.append(" ")
            continue

        if char == ";":
            in_comment = True
            out.append(" ")
        elif char == '"':
            in_string = True
            out.append(" ")
        else:
            out.append(char)

    if in_string:
        raise ValueError("unterminated string literal while scanning Lisp source")
    return "".join(out)


def _atom(text: str, index: int) -> tuple[str | None, int]:
    length = len(text)
    while index < length and text[index].isspace():
        index += 1
    if index >= length or text[index] in "()":
        return None, index
    start = index
    while index < length and not text[index].isspace() and text[index] not in "()":
        index += 1
    return text[start:index], index


def define_operators() -> set[str]:
    """Read DEFINE's byte spellings from the Lisp-owned function table."""
    operators = {
        match.group(1)
        for line in FUNCTION_SIGNATURES.read_text(encoding="utf-8").splitlines()
        if (match := DEFINE_SIGNATURE_ROW.match(line)) is not None
    }
    if not operators:
        raise ValueError(f"{FUNCTION_SIGNATURES.relative_to(REPO_ROOT)} has no (form define) rows")
    return operators


def defmacro_operators() -> set[str]:
    """Read DEFMACRO's byte spelling from the Lisp-owned function table."""
    operators = {
        match.group(1)
        for line in FUNCTION_SIGNATURES.read_text(encoding="utf-8").splitlines()
        if (match := DEFMACRO_SIGNATURE_ROW.match(line)) is not None
    }
    if not operators:
        raise ValueError(f"{FUNCTION_SIGNATURES.relative_to(REPO_ROOT)} has no defmacro row")
    return operators


def scan_source(source: str, source_name: str) -> list[Definition]:
    masked = _mask_strings_and_comments(source)
    definitions: list[Definition] = []
    function_operators = {"def"} | define_operators()
    macro_operators = {"defmacro"} | defmacro_operators()
    depth = 0
    line = 1
    index = 0

    while index < len(masked):
        char = masked[index]
        if char == "\n":
            line += 1
            index += 1
            continue

        if char == "(":
            if depth == 0:
                operator, after_operator = _atom(masked, index + 1)
                if operator in function_operators | macro_operators:
                    name, _after_name = _atom(masked, after_operator)
                    if name is not None:
                        definitions.append(
                            Definition(
                                source=source_name,
                                line=line,
                                kind="macro" if operator in macro_operators else "function",
                                name=name,
                            )
                        )
            depth += 1
        elif char == ")":
            depth -= 1
            if depth < 0:
                raise ValueError(f"unmatched ')' at {source_name}:{line}")
        index += 1

    if depth != 0:
        raise ValueError(f"unbalanced parentheses in {source_name}: depth={depth}")
    return definitions


def scan_file(path: Path, *, display_name: str | None = None) -> list[Definition]:
    return scan_source(
        path.read_text(encoding="utf-8"),
        display_name if display_name is not None else path.as_posix(),
    )


def classified_excluded_top_level_dirs() -> set[str]:
    """Read explicit public-API exclusions from Lisp-owned authority data."""
    source = MACHINE_AUTHORITY.read_text(encoding="utf-8")
    classified = {
        match.group(1)
        for line in source.splitlines()
        if (match := PUBLIC_API_EXCLUDED_ROOT.match(line)) is not None
    }
    if not classified:
        raise ValueError(
            f"{MACHINE_AUTHORITY.relative_to(REPO_ROOT)} has no "
            "public-api-excluded-root classification"
        )
    return STATIC_EXCLUDED_TOP_LEVEL_DIRS | classified


def classified_excluded_source_files() -> set[str]:
    """Exclude only sources explicitly classified non-current by SENS authority."""
    source = CORE_PROFILE_AUTHORITY.read_text(encoding="utf-8")
    excluded = {
        match.group(1)
        for line in source.splitlines()
        if (match := PUBLIC_API_NONCURRENT_SOURCE.match(line)) is not None
    }
    if not excluded:
        raise ValueError(
            f"{CORE_PROFILE_AUTHORITY.relative_to(REPO_ROOT)} has no "
            "historical/laboratory/former source classification"
        )
    return excluded


def library_files() -> list[Path]:
    excluded_top_level_dirs = classified_excluded_top_level_dirs()
    excluded_source_files = classified_excluded_source_files()
    files = []
    for path in LIB_ROOT.rglob("*.lisp"):
        relative = path.relative_to(LIB_ROOT)
        repo_relative = path.relative_to(REPO_ROOT).as_posix()
        if relative.parts and relative.parts[0] in excluded_top_level_dirs:
            continue
        if repo_relative in excluded_source_files:
            continue
        files.append(path)
    return sorted(files, key=lambda path: path.relative_to(REPO_ROOT).as_posix())


def discover() -> tuple[list[Path], list[Definition]]:
    files = library_files()
    definitions: list[Definition] = []
    for path in files:
        relative = path.relative_to(REPO_ROOT).as_posix()
        definitions.extend(scan_file(path, display_name=relative))
    definitions.sort()
    return files, definitions


def render_report(files: list[Path], definitions: list[Definition]) -> str:
    functions = sum(item.kind == "function" for item in definitions)
    macros = sum(item.kind == "macro" for item in definitions)
    lines = [
        "# Живе виявлення кандидатів публічного API",
        "",
        "> Згенеровано `scripts/public_api_inventory.py`. Цей звіт знаходить",
        "> top-level визначення, але **не** оголошує їх публічним API.",
        "",
        f"- проскановано бібліотечних файлів: {len(files)}",
        f"- top-level функцій: {functions}",
        f"- top-level макросів: {macros}",
        f"- усього визначень: {len(definitions)}",
        "- класифікація: `unreviewed`",
        "",
        "| джерело | вид | ім'я | класифікація |",
        "|---|---|---|---|",
    ]
    lines.extend(
        f"| `{item.source}` | {item.kind} | `{item.name}` | unreviewed |"
        for item in definitions
    )
    lines.append("")
    return "\n".join(lines)


def check() -> int:
    first_files, first = discover()
    second_files, second = discover()
    if [path.as_posix() for path in first_files] != [path.as_posix() for path in second_files]:
        print("ERROR: library file discovery is not deterministic", file=sys.stderr)
        return 1
    if first != second:
        print("ERROR: definition discovery is not deterministic", file=sys.stderr)
        return 1

    expected = render_report(first_files, first)
    if REPORT.exists() and REPORT.read_text(encoding="utf-8") != expected:
        print(
            "ERROR: docs/generated/public-api-discovery.md is stale; "
            "run --write-report",
            file=sys.stderr,
        )
        return 1

    functions = sum(item.kind == "function" for item in first)
    macros = sum(item.kind == "macro" for item in first)
    print(f"library files scanned: {len(first_files)}")
    print(f"top-level functions: {functions}")
    print(f"top-level macros: {macros}")
    print(f"top-level definitions: {len(first)}")
    print("classification: unreviewed")
    return 0


def write_report() -> int:
    files, definitions = discover()
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(render_report(files, definitions), encoding="utf-8")
    print(f"wrote {REPORT.relative_to(REPO_ROOT)}")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--write-report", action="store_true")
    mode.add_argument("--scan-file", type=Path, metavar="PATH")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        if args.scan_file is not None:
            for item in scan_file(args.scan_file, display_name=args.scan_file.name):
                print(f"{item.source}\t{item.kind}\t{item.name}")
            return 0
        if args.write_report:
            return write_report()
        return check()
    except (OSError, UnicodeError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

)


@dataclass(frozen=True, order=True)
class Definition:
    source: str
    line: int
    kind: str
    name: str


def _mask_strings_and_comments(source: str) -> str:
    """Replace string/comment contents with spaces while preserving newlines."""
    out: list[str] = []
    in_string = False
    escaped = False
    in_comment = False

    for char in source:
        if in_comment:
            if char == "\n":
                in_comment = False
                out.append(char)
            else:
                out.append(" ")
            continue

        if in_string:
            if escaped:
                escaped = False
                out.append(" ")
            elif char == "\\":
                escaped = True
                out.append(" ")
            elif char == '"':
                in_string = False
                out.append(" ")
            elif char == "\n":
                out.append("\n")
            else:
                out.append(" ")
            continue

        if char == ";":
            in_comment = True
            out.append(" ")
        elif char == '"':
            in_string = True
            out.append(" ")
        else:
            out.append(char)

    if in_string:
        raise ValueError("unterminated string literal while scanning Lisp source")
    return "".join(out)


def _atom(text: str, index: int) -> tuple[str | None, int]:
    length = len(text)
    while index < length and text[index].isspace():
        index += 1
    if index >= length or text[index] in "()":
        return None, index
    start = index
    while index < length and not text[index].isspace() and text[index] not in "()":
        index += 1
    return text[start:index], index


def define_operators() -> set[str]:
    """Read DEFINE's byte spellings from the Lisp-owned function table."""
    operators = {
        match.group(1)
        for line in FUNCTION_SIGNATURES.read_text(encoding="utf-8").splitlines()
        if (match := DEFINE_SIGNATURE_ROW.match(line)) is not None
    }
    if not operators:
        raise ValueError(f"{FUNCTION_SIGNATURES.relative_to(REPO_ROOT)} has no (form define) rows")
    return operators


def defmacro_operators() -> set[str]:
    """Read DEFMACRO's byte spelling from the Lisp-owned function table."""
    operators = {
        match.group(1)
        for line in FUNCTION_SIGNATURES.read_text(encoding="utf-8").splitlines()
        if (match := DEFMACRO_SIGNATURE_ROW.match(line)) is not None
    }
    if not operators:
        raise ValueError(f"{FUNCTION_SIGNATURES.relative_to(REPO_ROOT)} has no defmacro row")
    return operators


def scan_source(source: str, source_name: str) -> list[Definition]:
    masked = _mask_strings_and_comments(source)
    definitions: list[Definition] = []
    function_operators = {"def"} | define_operators()
    macro_operators = {"defmacro"} | defmacro_operators()
    depth = 0
    line = 1
    index = 0

    while index < len(masked):
        char = masked[index]
        if char == "\n":
            line += 1
            index += 1
            continue

        if char == "(":
            if depth == 0:
                operator, after_operator = _atom(masked, index + 1)
                if operator in function_operators | macro_operators:
                    name, _after_name = _atom(masked, after_operator)
                    if name is not None:
                        definitions.append(
                            Definition(
                                source=source_name,
                                line=line,
                                kind="macro" if operator in macro_operators else "function",
                                name=name,
                            )
                        )
            depth += 1
        elif char == ")":
            depth -= 1
            if depth < 0:
                raise ValueError(f"unmatched ')' at {source_name}:{line}")
        index += 1

    if depth != 0:
        raise ValueError(f"unbalanced parentheses in {source_name}: depth={depth}")
    return definitions


def scan_file(path: Path, *, display_name: str | None = None) -> list[Definition]:
    return scan_source(
        path.read_text(encoding="utf-8"),
        display_name if display_name is not None else path.as_posix(),
    )


def classified_excluded_top_level_dirs() -> set[str]:
    """Read explicit public-API exclusions from Lisp-owned authority data."""
    source = MACHINE_AUTHORITY.read_text(encoding="utf-8")
    classified = {
        match.group(1)
        for line in source.splitlines()
        if (match := PUBLIC_API_EXCLUDED_ROOT.match(line)) is not None
    }
    if not classified:
        raise ValueError(
            f"{MACHINE_AUTHORITY.relative_to(REPO_ROOT)} has no "
            "public-api-excluded-root classification"
        )
    return STATIC_EXCLUDED_TOP_LEVEL_DIRS | classified


def classified_excluded_source_files() -> set[str]:
    """Read profile-source exclusions from the Lisp-owned four-core contract."""
    source = CORE_PROFILE_AUTHORITY.read_text(encoding="utf-8")
    excluded = {
        match.group(1)
        for line in source.splitlines()
        if (match := PUBLIC_API_EXCLUDED_SOURCE.match(line)) is not None
    }
    if not excluded:
        raise ValueError(
            f"{CORE_PROFILE_AUTHORITY.relative_to(REPO_ROOT)} has no "
            "public-api-excluded-source classification"
        )
    return excluded


def library_files() -> list[Path]:
    excluded_top_level_dirs = classified_excluded_top_level_dirs()
    excluded_source_files = classified_excluded_source_files()
    files = []
    for path in LIB_ROOT.rglob("*.lisp"):
        relative = path.relative_to(LIB_ROOT)
        repo_relative = path.relative_to(REPO_ROOT).as_posix()
        if relative.parts and relative.parts[0] in excluded_top_level_dirs:
            continue
        if repo_relative in excluded_source_files:
            continue
        files.append(path)
    return sorted(files, key=lambda path: path.relative_to(REPO_ROOT).as_posix())


def discover() -> tuple[list[Path], list[Definition]]:
    files = library_files()
    definitions: list[Definition] = []
    for path in files:
        relative = path.relative_to(REPO_ROOT).as_posix()
        definitions.extend(scan_file(path, display_name=relative))
    definitions.sort()
    return files, definitions


def render_report(files: list[Path], definitions: list[Definition]) -> str:
    functions = sum(item.kind == "function" for item in definitions)
    macros = sum(item.kind == "macro" for item in definitions)
    lines = [
        "# Живе виявлення кандидатів публічного API",
        "",
        "> Згенеровано `scripts/public_api_inventory.py`. Цей звіт знаходить",
        "> top-level визначення, але **не** оголошує їх публічним API.",
        "",
        f"- проскановано бібліотечних файлів: {len(files)}",
        f"- top-level функцій: {functions}",
        f"- top-level макросів: {macros}",
        f"- усього визначень: {len(definitions)}",
        "- класифікація: `unreviewed`",
        "",
        "| джерело | вид | ім'я | класифікація |",
        "|---|---|---|---|",
    ]
    lines.extend(
        f"| `{item.source}` | {item.kind} | `{item.name}` | unreviewed |"
        for item in definitions
    )
    lines.append("")
    return "\n".join(lines)


def check() -> int:
    first_files, first = discover()
    second_files, second = discover()
    if [path.as_posix() for path in first_files] != [path.as_posix() for path in second_files]:
        print("ERROR: library file discovery is not deterministic", file=sys.stderr)
        return 1
    if first != second:
        print("ERROR: definition discovery is not deterministic", file=sys.stderr)
        return 1

    expected = render_report(first_files, first)
    if REPORT.exists() and REPORT.read_text(encoding="utf-8") != expected:
        print(
            "ERROR: docs/generated/public-api-discovery.md is stale; "
            "run --write-report",
            file=sys.stderr,
        )
        return 1

    functions = sum(item.kind == "function" for item in first)
    macros = sum(item.kind == "macro" for item in first)
    print(f"library files scanned: {len(first_files)}")
    print(f"top-level functions: {functions}")
    print(f"top-level macros: {macros}")
    print(f"top-level definitions: {len(first)}")
    print("classification: unreviewed")
    return 0


def write_report() -> int:
    files, definitions = discover()
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(render_report(files, definitions), encoding="utf-8")
    print(f"wrote {REPORT.relative_to(REPO_ROOT)}")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--write-report", action="store_true")
    mode.add_argument("--scan-file", type=Path, metavar="PATH")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        if args.scan_file is not None:
            for item in scan_file(args.scan_file, display_name=args.scan_file.name):
                print(f"{item.source}\t{item.kind}\t{item.name}")
            return 0
        if args.write_report:
            return write_report()
        return check()
    except (OSError, UnicodeError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

)


@dataclass(frozen=True, order=True)
class Definition:
    source: str
    line: int
    kind: str
    name: str


def _mask_strings_and_comments(source: str) -> str:
    """Replace string/comment contents with spaces while preserving newlines."""
    out: list[str] = []
    in_string = False
    escaped = False
    in_comment = False

    for char in source:
        if in_comment:
            if char == "\n":
                in_comment = False
                out.append(char)
            else:
                out.append(" ")
            continue

        if in_string:
            if escaped:
                escaped = False
                out.append(" ")
            elif char == "\\":
                escaped = True
                out.append(" ")
            elif char == '"':
                in_string = False
                out.append(" ")
            elif char == "\n":
                out.append("\n")
            else:
                out.append(" ")
            continue

        if char == ";":
            in_comment = True
            out.append(" ")
        elif char == '"':
            in_string = True
            out.append(" ")
        else:
            out.append(char)

    if in_string:
        raise ValueError("unterminated string literal while scanning Lisp source")
    return "".join(out)


def _atom(text: str, index: int) -> tuple[str | None, int]:
    length = len(text)
    while index < length and text[index].isspace():
        index += 1
    if index >= length or text[index] in "()":
        return None, index
    start = index
    while index < length and not text[index].isspace() and text[index] not in "()":
        index += 1
    return text[start:index], index


def define_operators() -> set[str]:
    """Read DEFINE's byte spellings from the Lisp-owned function table."""
    operators = {
        match.group(1)
        for line in FUNCTION_SIGNATURES.read_text(encoding="utf-8").splitlines()
        if (match := DEFINE_SIGNATURE_ROW.match(line)) is not None
    }
    if not operators:
        raise ValueError(f"{FUNCTION_SIGNATURES.relative_to(REPO_ROOT)} has no (form define) rows")
    return operators


def defmacro_operators() -> set[str]:
    """Read DEFMACRO's byte spelling from the Lisp-owned function table."""
    operators = {
        match.group(1)
        for line in FUNCTION_SIGNATURES.read_text(encoding="utf-8").splitlines()
        if (match := DEFMACRO_SIGNATURE_ROW.match(line)) is not None
    }
    if not operators:
        raise ValueError(f"{FUNCTION_SIGNATURES.relative_to(REPO_ROOT)} has no defmacro row")
    return operators


def scan_source(source: str, source_name: str) -> list[Definition]:
    masked = _mask_strings_and_comments(source)
    definitions: list[Definition] = []
    function_operators = {"def"} | define_operators()
    macro_operators = {"defmacro"} | defmacro_operators()
    depth = 0
    line = 1
    index = 0

    while index < len(masked):
        char = masked[index]
        if char == "\n":
            line += 1
            index += 1
            continue

        if char == "(":
            if depth == 0:
                operator, after_operator = _atom(masked, index + 1)
                if operator in function_operators | macro_operators:
                    name, _after_name = _atom(masked, after_operator)
                    if name is not None:
                        definitions.append(
                            Definition(
                                source=source_name,
                                line=line,
                                kind="macro" if operator in macro_operators else "function",
                                name=name,
                            )
                        )
            depth += 1
        elif char == ")":
            depth -= 1
            if depth < 0:
                raise ValueError(f"unmatched ')' at {source_name}:{line}")
        index += 1

    if depth != 0:
        raise ValueError(f"unbalanced parentheses in {source_name}: depth={depth}")
    return definitions


def scan_file(path: Path, *, display_name: str | None = None) -> list[Definition]:
    return scan_source(
        path.read_text(encoding="utf-8"),
        display_name if display_name is not None else path.as_posix(),
    )


def classified_excluded_top_level_dirs() -> set[str]:
    """Read explicit public-API exclusions from Lisp-owned authority data."""
    source = MACHINE_AUTHORITY.read_text(encoding="utf-8")
    classified = {
        match.group(1)
        for line in source.splitlines()
        if (match := PUBLIC_API_EXCLUDED_ROOT.match(line)) is not None
    }
    if not classified:
        raise ValueError(
            f"{MACHINE_AUTHORITY.relative_to(REPO_ROOT)} has no "
            "public-api-excluded-root classification"
        )
    return STATIC_EXCLUDED_TOP_LEVEL_DIRS | classified


def classified_excluded_source_files() -> set[str]:
    """Exclude only sources explicitly classified non-current by SENS authority."""
    source = CORE_PROFILE_AUTHORITY.read_text(encoding="utf-8")
    excluded = {
        match.group(1)
        for line in source.splitlines()
        if (match := PUBLIC_API_NONCURRENT_SOURCE.match(line)) is not None
    }
    if not excluded:
        raise ValueError(
            f"{CORE_PROFILE_AUTHORITY.relative_to(REPO_ROOT)} has no "
            "historical/laboratory/former source classification"
        )
    return excluded


def library_files() -> list[Path]:
    excluded_top_level_dirs = classified_excluded_top_level_dirs()
    excluded_source_files = classified_excluded_source_files()
    files = []
    for path in LIB_ROOT.rglob("*.lisp"):
        relative = path.relative_to(LIB_ROOT)
        repo_relative = path.relative_to(REPO_ROOT).as_posix()
        if relative.parts and relative.parts[0] in excluded_top_level_dirs:
            continue
        if repo_relative in excluded_source_files:
            continue
        files.append(path)
    return sorted(files, key=lambda path: path.relative_to(REPO_ROOT).as_posix())


def discover() -> tuple[list[Path], list[Definition]]:
    files = library_files()
    definitions: list[Definition] = []
    for path in files:
        relative = path.relative_to(REPO_ROOT).as_posix()
        definitions.extend(scan_file(path, display_name=relative))
    definitions.sort()
    return files, definitions


def render_report(files: list[Path], definitions: list[Definition]) -> str:
    functions = sum(item.kind == "function" for item in definitions)
    macros = sum(item.kind == "macro" for item in definitions)
    lines = [
        "# Живе виявлення кандидатів публічного API",
        "",
        "> Згенеровано `scripts/public_api_inventory.py`. Цей звіт знаходить",
        "> top-level визначення, але **не** оголошує їх публічним API.",
        "",
        f"- проскановано бібліотечних файлів: {len(files)}",
        f"- top-level функцій: {functions}",
        f"- top-level макросів: {macros}",
        f"- усього визначень: {len(definitions)}",
        "- класифікація: `unreviewed`",
        "",
        "| джерело | вид | ім'я | класифікація |",
        "|---|---|---|---|",
    ]
    lines.extend(
        f"| `{item.source}` | {item.kind} | `{item.name}` | unreviewed |"
        for item in definitions
    )
    lines.append("")
    return "\n".join(lines)


def check() -> int:
    first_files, first = discover()
    second_files, second = discover()
    if [path.as_posix() for path in first_files] != [path.as_posix() for path in second_files]:
        print("ERROR: library file discovery is not deterministic", file=sys.stderr)
        return 1
    if first != second:
        print("ERROR: definition discovery is not deterministic", file=sys.stderr)
        return 1

    expected = render_report(first_files, first)
    if REPORT.exists() and REPORT.read_text(encoding="utf-8") != expected:
        print(
            "ERROR: docs/generated/public-api-discovery.md is stale; "
            "run --write-report",
            file=sys.stderr,
        )
        return 1

    functions = sum(item.kind == "function" for item in first)
    macros = sum(item.kind == "macro" for item in first)
    print(f"library files scanned: {len(first_files)}")
    print(f"top-level functions: {functions}")
    print(f"top-level macros: {macros}")
    print(f"top-level definitions: {len(first)}")
    print("classification: unreviewed")
    return 0


def write_report() -> int:
    files, definitions = discover()
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(render_report(files, definitions), encoding="utf-8")
    print(f"wrote {REPORT.relative_to(REPO_ROOT)}")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--write-report", action="store_true")
    mode.add_argument("--scan-file", type=Path, metavar="PATH")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        if args.scan_file is not None:
            for item in scan_file(args.scan_file, display_name=args.scan_file.name):
                print(f"{item.source}\t{item.kind}\t{item.name}")
            return 0
        if args.write_report:
            return write_report()
        return check()
    except (OSError, UnicodeError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

)


@dataclass(frozen=True, order=True)
class Definition:
    source: str
    line: int
    kind: str
    name: str


def _mask_strings_and_comments(source: str) -> str:
    """Replace string/comment contents with spaces while preserving newlines."""
    out: list[str] = []
    in_string = False
    escaped = False
    in_comment = False

    for char in source:
        if in_comment:
            if char == "\n":
                in_comment = False
                out.append(char)
            else:
                out.append(" ")
            continue

        if in_string:
            if escaped:
                escaped = False
                out.append(" ")
            elif char == "\\":
                escaped = True
                out.append(" ")
            elif char == '"':
                in_string = False
                out.append(" ")
            elif char == "\n":
                out.append("\n")
            else:
                out.append(" ")
            continue

        if char == ";":
            in_comment = True
            out.append(" ")
        elif char == '"':
            in_string = True
            out.append(" ")
        else:
            out.append(char)

    if in_string:
        raise ValueError("unterminated string literal while scanning Lisp source")
    return "".join(out)


def _atom(text: str, index: int) -> tuple[str | None, int]:
    length = len(text)
    while index < length and text[index].isspace():
        index += 1
    if index >= length or text[index] in "()":
        return None, index
    start = index
    while index < length and not text[index].isspace() and text[index] not in "()":
        index += 1
    return text[start:index], index


def define_operators() -> set[str]:
    """Read DEFINE's byte spellings from the Lisp-owned function table."""
    operators = {
        match.group(1)
        for line in FUNCTION_SIGNATURES.read_text(encoding="utf-8").splitlines()
        if (match := DEFINE_SIGNATURE_ROW.match(line)) is not None
    }
    if not operators:
        raise ValueError(f"{FUNCTION_SIGNATURES.relative_to(REPO_ROOT)} has no (form define) rows")
    return operators


def defmacro_operators() -> set[str]:
    """Read DEFMACRO's byte spelling from the Lisp-owned function table."""
    operators = {
        match.group(1)
        for line in FUNCTION_SIGNATURES.read_text(encoding="utf-8").splitlines()
        if (match := DEFMACRO_SIGNATURE_ROW.match(line)) is not None
    }
    if not operators:
        raise ValueError(f"{FUNCTION_SIGNATURES.relative_to(REPO_ROOT)} has no defmacro row")
    return operators


def scan_source(source: str, source_name: str) -> list[Definition]:
    masked = _mask_strings_and_comments(source)
    definitions: list[Definition] = []
    function_operators = {"def"} | define_operators()
    macro_operators = {"defmacro"} | defmacro_operators()
    depth = 0
    line = 1
    index = 0

    while index < len(masked):
        char = masked[index]
        if char == "\n":
            line += 1
            index += 1
            continue

        if char == "(":
            if depth == 0:
                operator, after_operator = _atom(masked, index + 1)
                if operator in function_operators | macro_operators:
                    name, _after_name = _atom(masked, after_operator)
                    if name is not None:
                        definitions.append(
                            Definition(
                                source=source_name,
                                line=line,
                                kind="macro" if operator in macro_operators else "function",
                                name=name,
                            )
                        )
            depth += 1
        elif char == ")":
            depth -= 1
            if depth < 0:
                raise ValueError(f"unmatched ')' at {source_name}:{line}")
        index += 1

    if depth != 0:
        raise ValueError(f"unbalanced parentheses in {source_name}: depth={depth}")
    return definitions


def scan_file(path: Path, *, display_name: str | None = None) -> list[Definition]:
    return scan_source(
        path.read_text(encoding="utf-8"),
        display_name if display_name is not None else path.as_posix(),
    )


def classified_excluded_top_level_dirs() -> set[str]:
    """Read explicit public-API exclusions from Lisp-owned authority data."""
    source = MACHINE_AUTHORITY.read_text(encoding="utf-8")
    classified = {
        match.group(1)
        for line in source.splitlines()
        if (match := PUBLIC_API_EXCLUDED_ROOT.match(line)) is not None
    }
    if not classified:
        raise ValueError(
            f"{MACHINE_AUTHORITY.relative_to(REPO_ROOT)} has no "
            "public-api-excluded-root classification"
        )
    return STATIC_EXCLUDED_TOP_LEVEL_DIRS | classified


def classified_excluded_source_files() -> set[str]:
    """Read profile-source exclusions from the Lisp-owned four-core contract."""
    source = CORE_PROFILE_AUTHORITY.read_text(encoding="utf-8")
    excluded = {
        match.group(1)
        for line in source.splitlines()
        if (match := PUBLIC_API_EXCLUDED_SOURCE.match(line)) is not None
    }
    if not excluded:
        raise ValueError(
            f"{CORE_PROFILE_AUTHORITY.relative_to(REPO_ROOT)} has no "
            "public-api-excluded-source classification"
        )
    return excluded


def library_files() -> list[Path]:
    excluded_top_level_dirs = classified_excluded_top_level_dirs()
    excluded_source_files = classified_excluded_source_files()
    files = []
    for path in LIB_ROOT.rglob("*.lisp"):
        relative = path.relative_to(LIB_ROOT)
        repo_relative = path.relative_to(REPO_ROOT).as_posix()
        if relative.parts and relative.parts[0] in excluded_top_level_dirs:
            continue
        if repo_relative in excluded_source_files:
            continue
        files.append(path)
    return sorted(files, key=lambda path: path.relative_to(REPO_ROOT).as_posix())


def discover() -> tuple[list[Path], list[Definition]]:
    files = library_files()
    definitions: list[Definition] = []
    for path in files:
        relative = path.relative_to(REPO_ROOT).as_posix()
        definitions.extend(scan_file(path, display_name=relative))
    definitions.sort()
    return files, definitions


def render_report(files: list[Path], definitions: list[Definition]) -> str:
    functions = sum(item.kind == "function" for item in definitions)
    macros = sum(item.kind == "macro" for item in definitions)
    lines = [
        "# Живе виявлення кандидатів публічного API",
        "",
        "> Згенеровано `scripts/public_api_inventory.py`. Цей звіт знаходить",
        "> top-level визначення, але **не** оголошує їх публічним API.",
        "",
        f"- проскановано бібліотечних файлів: {len(files)}",
        f"- top-level функцій: {functions}",
        f"- top-level макросів: {macros}",
        f"- усього визначень: {len(definitions)}",
        "- класифікація: `unreviewed`",
        "",
        "| джерело | вид | ім'я | класифікація |",
        "|---|---|---|---|",
    ]
    lines.extend(
        f"| `{item.source}` | {item.kind} | `{item.name}` | unreviewed |"
        for item in definitions
    )
    lines.append("")
    return "\n".join(lines)


def check() -> int:
    first_files, first = discover()
    second_files, second = discover()
    if [path.as_posix() for path in first_files] != [path.as_posix() for path in second_files]:
        print("ERROR: library file discovery is not deterministic", file=sys.stderr)
        return 1
    if first != second:
        print("ERROR: definition discovery is not deterministic", file=sys.stderr)
        return 1

    expected = render_report(first_files, first)
    if REPORT.exists() and REPORT.read_text(encoding="utf-8") != expected:
        print(
            "ERROR: docs/generated/public-api-discovery.md is stale; "
            "run --write-report",
            file=sys.stderr,
        )
        return 1

    functions = sum(item.kind == "function" for item in first)
    macros = sum(item.kind == "macro" for item in first)
    print(f"library files scanned: {len(first_files)}")
    print(f"top-level functions: {functions}")
    print(f"top-level macros: {macros}")
    print(f"top-level definitions: {len(first)}")
    print("classification: unreviewed")
    return 0


def write_report() -> int:
    files, definitions = discover()
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(render_report(files, definitions), encoding="utf-8")
    print(f"wrote {REPORT.relative_to(REPO_ROOT)}")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--write-report", action="store_true")
    mode.add_argument("--scan-file", type=Path, metavar="PATH")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        if args.scan_file is not None:
            for item in scan_file(args.scan_file, display_name=args.scan_file.name):
                print(f"{item.source}\t{item.kind}\t{item.name}")
            return 0
        if args.write_report:
            return write_report()
        return check()
    except (OSError, UnicodeError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
