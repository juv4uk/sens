#!/usr/bin/env python3
"""Перекладає D1-D4 human surfaces через exact domain-qualified projection."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "lib/surface/domain-surfaces-d1-d4.lisp"
ROW = re.compile(
    r'^\s*\(row\s+(D[1-4])\s+"([01]+)"\s+(\S+)\s+'
    r'"([^"]+)"\s+"([^"]+)"\s+"([^"]+)"\s+(\S+)\s+(\S+)\)\s*$'
)
LANGUAGES = ("en", "uk", "sa")


def rows() -> list[dict[str, str]]:
    result: list[dict[str, str]] = []
    for line_number, line in enumerate(REGISTRY.read_text(encoding="utf-8").splitlines(), 1):
        if not line.lstrip().startswith("(row "):
            continue
        match = ROW.match(line)
        if not match:
            raise ValueError(f"line {line_number}: malformed D1-D4 surface row")
        domain, bits, role, en, uk, sa, uk_status, sa_status = match.groups()
        result.append(
            {
                "domain": domain,
                "bits": bits,
                "role": role,
                "en": en,
                "uk": uk,
                "sa": sa,
                "uk_status": uk_status,
                "sa_status": sa_status,
            }
        )
    if len(result) != 30:
        raise ValueError(f"expected 30 exact-domain rows, found {len(result)}")
    return result


def translation_map(source_language: str, target_language: str) -> dict[str, str]:
    if source_language not in LANGUAGES or target_language not in LANGUAGES:
        raise ValueError("languages must be one of: en, uk, sa")
    if source_language == target_language:
        raise ValueError("source and target surfaces must differ")

    translations: dict[str, str] = {}
    for row in rows():
        # D2 labels and D3 EMPTY are descriptive only. Canonical structure stays punctuation/bits.
        if row["role"] == "display":
            continue
        source = row[source_language]
        target = row[target_language]
        previous = translations.get(source)
        if previous is not None and previous != target:
            raise ValueError(
                f"ambiguous {source_language} spelling {source!r}: "
                f"{previous!r} or {target!r}"
            )
        translations[source] = target
    return translations


def translate_program(source: str, translations: dict[str, str]) -> str:
    """Rewrite registered symbols; preserve comments, strings, layout and user names."""
    output: list[str] = []
    index = 0

    while index < len(source):
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
            while index < len(source):
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
            while index < len(source):
                current = source[index]
                if current.isspace() or current in "();\"":
                    break
                index += 1
            token = source[start:index]
            output.append(translations.get(token, token))

    return "".join(output)


def self_test() -> None:
    en = "(define f (lambda (x) (car x)))"
    uk = "(визначити f (функція (x) (перше x)))"
    sa = "(nirvacana f (phalana (x) (ādi x)))"

    assert translate_program(en, translation_map("en", "uk")) == uk
    assert translate_program(uk, translation_map("uk", "sa")) == sa
    assert translate_program(sa, translation_map("sa", "en")) == en

    protected = '; car перше ādi\n("car перше ādi" car user-name)'
    expected = '; car перше ādi\n("car перше ādi" перше user-name)'
    assert translate_program(protected, translation_map("en", "uk")) == expected

    # Structural labels are documentation only, never token rewrites.
    assert "відкрити" not in translation_map("en", "uk")
    assert "open" not in translation_map("en", "uk")

    print("D1-D4-SURFACE-TRANSLATOR: PASS")


def arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", nargs="?", type=Path, help="source file, or - for stdin")
    parser.add_argument("--from", dest="source_language")
    parser.add_argument("--to", dest="target_language")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("-o", "--output", type=Path)
    return parser.parse_args()


def main() -> int:
    args = arguments()
    if args.self_test:
        self_test()
        return 0

    if args.input is None or args.source_language is None or args.target_language is None:
        print("input, --from and --to are required unless --self-test is used", file=sys.stderr)
        return 2

    try:
        translations = translation_map(args.source_language, args.target_language)
    except (OSError, ValueError) as error:
        print(f"translation registry error: {error}", file=sys.stderr)
        return 2

    source = sys.stdin.read() if str(args.input) == "-" else args.input.read_text(encoding="utf-8")
    translated = translate_program(source, translations)
    if args.output:
        args.output.write_text(translated, encoding="utf-8")
    else:
        sys.stdout.write(translated)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
