#!/usr/bin/env python3
"""Перекладає my-lisp між людськими поверхнями через byte SIDs.

Джерело словника — `lib/surface/semantic-registry.lisp`. Жодна людська мова не
є мостом до іншої. `sym` — спільна немовна нотація, а `compat` — службовий
простір compatibility-імен; вони не є людськими поверхнями для CLI-перекладу.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
REGISTRY = REPO_ROOT / "lib" / "surface" / "semantic-registry.lisp"
ENTRY = re.compile(r'^\s*\("([01]{8})"\s+(.*)\)\s*$')
SURFACE = re.compile(r"\(([A-Za-z][A-Za-z0-9-]*)\s+(\(\)|[^\s()]+)\)")
NON_HUMAN = {"sym", "compat"}


def decode_surface_token(token: str) -> str:
    if len(token) >= 2 and token[0] == token[-1] == '"':
        return token[1:-1]
    return token


def registry_rows() -> list[dict[str, str]]:
    rows = []
    for line_number, line in enumerate(
        REGISTRY.read_text(encoding="utf-8").splitlines(), 1
    ):
        match = ENTRY.match(line)
        if not match:
            continue
        identity, body = match.groups()
        if identity == "00000000":
            continue

        matches = list(SURFACE.finditer(body))
        residue = SURFACE.sub("", body).strip()
        if not matches or residue:
            raise ValueError(
                f"line {line_number}: malformed sr/2 row for SID {identity}"
            )

        surfaces: dict[str, str] = {}
        for surface in matches:
            language, raw_name = surface.groups()
            name = decode_surface_token(raw_name)
            if language in surfaces:
                raise ValueError(
                    f"line {line_number}: duplicate {language} surface for {identity}"
                )
            if name not in ("()", "—"):
                surfaces[language] = name
        rows.append(surfaces)

    if not rows:
        raise ValueError("byte-SID semantic registry has no entries")
    return rows


def human_languages(rows: list[dict[str, str]]) -> set[str]:
    return {
        language
        for row in rows
        for language in row
        if language not in NON_HUMAN
    }


def translation_map(source_language: str, target_language: str) -> dict[str, str]:
    translations: dict[str, str] = {}
    for row in registry_rows():
        source_name = row.get(source_language)
        target_name = row.get(target_language)
        if source_name is None or target_name is None:
            continue
        previous = translations.get(source_name)
        if previous is not None and previous != target_name:
            raise ValueError(
                f"ambiguous {source_language} surface {source_name!r}: "
                f"{previous!r} or {target_name!r}"
            )
        translations[source_name] = target_name
    return translations


def translate_program(source: str, translations: dict[str, str]) -> str:
    """Rewrite symbols while preserving layout, comments, strings and shared symbols."""
    output: list[str] = []
    index = 0
    length = len(source)

    while index < length:
        character = source[index]
        if character == ";":
            end = source.find("\n", index)
            if end == -1:
                output.append(source[index:])
                break
            output.append(source[index : end + 1])
            index = end + 1
        elif character == '"':
            start = index
            index += 1
            while index < length:
                if source[index] == "\\":
                    index += 2
                elif source[index] == '"':
                    index += 1
                    break
                else:
                    index += 1
            output.append(source[start:index])
        elif character.isspace() or character in "()":
            output.append(character)
            index += 1
        elif character == "'":
            output.append(character)
            index += 1
        else:
            start = index
            while index < length:
                current = source[index]
                if current.isspace() or current in "();\"":
                    break
                index += 1
            token = source[start:index]
            output.append(translations.get(token, token))

    return "".join(output)


def arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="source program, or - for stdin")
    parser.add_argument("--from", dest="source_language", required=True)
    parser.add_argument("--to", dest="target_language", required=True)
    parser.add_argument("-o", "--output", type=Path, help="write here instead of stdout")
    return parser.parse_args()


def main() -> int:
    args = arguments()
    try:
        rows = registry_rows()
        languages = human_languages(rows)
        unknown = {args.source_language, args.target_language} - languages
        if unknown:
            raise ValueError(
                "unknown human surface(s): " + ", ".join(sorted(unknown))
            )
        if args.source_language == args.target_language:
            raise ValueError("source and target surfaces must differ")
        translations = translation_map(args.source_language, args.target_language)
    except (OSError, ValueError) as error:
        print(f"translation registry error: {error}", file=sys.stderr)
        return 2

    source = (
        sys.stdin.read()
        if str(args.input) == "-"
        else args.input.read_text(encoding="utf-8")
    )
    translated = translate_program(source, translations)
    if args.output:
        args.output.write_text(translated, encoding="utf-8")
    else:
        sys.stdout.write(translated)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
