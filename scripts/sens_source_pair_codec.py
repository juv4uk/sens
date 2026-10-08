#!/usr/bin/env python3
"""Canonical Ukrainian <-> packed exact-width SENS source bridge.

Semantic migration is delegated to the existing migrate-to-sens-codes.py.
Physical framing is delegated to domain_word_carrier.py. This module adds no
semantic residents and invents no numeric value layout.
"""

from __future__ import annotations

import ast
import importlib.util
from pathlib import Path
import re
import unicodedata

from domain_tables import read_domain_table
from domain_word_carrier import CarrierError, DomainWord, decode as unpack, encode as pack

ROOT = Path(__file__).resolve().parents[1]
MIGRATOR_PATH = ROOT / "scripts" / "migrate-to-sens-codes.py"
FOUNDATION = ROOT / "knowledge" / "d1-d9-foundation.json"
TEXT7 = ROOT / "crates" / "sens" / "src" / "text7_projection_generated.rs"
REGISTRY = ROOT / "lib" / "surface" / "semantic-registry.lisp"
HISTORICAL = ROOT / "contracts" / "core1-historical-sid-map.lisp"
DOMAIN_SURFACES = [
    ROOT / "lib" / "domains" / f"d{width}.lisp"
    for width in range(1, 10)
]

UKRAINIAN_LETTERS = frozenset(
    "абвгґдеєжзиіїйклмнопрстуфхцчшщьюя"
    "АБВГҐДЕЄЖЗИІЇЙКЛМНОПРСТУФХЦЧШЩЬЮЯ"
)
CANONICAL_PUNCTUATION = frozenset(
    " ()[]{}.,;:!?'-+*/=<>%_\\\"№₴"
)


def _load_migrator():
    spec = importlib.util.spec_from_file_location(
        "sens_pair_migrator", MIGRATOR_PATH
    )
    if spec is None or spec.loader is None:
        raise CarrierError(f"cannot load migration library: {MIGRATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def validate_canonical_ukrainian(source: bytes) -> str:
    try:
        text = source.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise CarrierError(f"invalid UTF-8: {exc}") from exc

    if not text or text != unicodedata.normalize("NFC", text):
        raise CarrierError("Ukrainian projection must be nonempty canonical NFC")

    in_string = False
    escaped = False
    previous_space = False

    for index, ch in enumerate(text):
        if in_string:
            if (
                ch not in UKRAINIAN_LETTERS
                and ch not in CANONICAL_PUNCTUATION
                and ch not in "\n\t"
            ):
                raise CarrierError(
                    f"forbidden/non-keyboard character U+{ord(ch):04X} at offset {index}"
                )
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_string = False
            continue

        if ch == '"':
            in_string = True
            previous_space = False
            continue
        if ch in ("'", ",") or ord(ch) == 96:
            raise CarrierError(
                f"reader abbreviation at offset {index}; use explicit canonical QUOTE"
            )
        if ch == ";":
            raise CarrierError(f"comments are not canonical source at offset {index}")
        if ch in "\r\n\t":
            raise CarrierError(
                f"noncanonical whitespace {ch!r} outside strings at offset {index}"
            )
        if ch not in UKRAINIAN_LETTERS and ch not in CANONICAL_PUNCTUATION:
            raise CarrierError(
                f"forbidden/non-keyboard character U+{ord(ch):04X} at offset {index}"
            )
        if ch == " ":
            if previous_space or index == 0:
                raise CarrierError("canonical source uses single interior spaces only")
            previous_space = True
        else:
            previous_space = False

    if in_string:
        raise CarrierError("unterminated string")
    if text.endswith(" "):
        raise CarrierError("canonical source must not end in whitespace")
    return text


def _load_uk_render() -> list[str | None]:
    generated = (
        ROOT / "crates" / "sens" / "src" / "text7_projection_generated.rs"
    ).read_text(encoding="utf-8")
    match = re.search(
        r"pub\(crate\) const UK_RENDER: &\[Option<&str>; 128\] = &\[(.*?)\];",
        generated,
        re.DOTALL,
    )
    if match is None:
        raise CarrierError("UK_RENDER projection table not found")
    values: list[str | None] = []
    pattern = re.compile(r'Some\(("(?:\\.|[^"\\])*")\)|\bNone\b')
    for item in pattern.finditer(match.group(1)):
        values.append(
            ast.literal_eval(item.group(1)) if item.group(1) else None
        )
    if len(values) != 128:
        raise CarrierError(f"UK_RENDER expected 128 cells, found {len(values)}")
    return values


def _semantic_uk_words() -> dict[tuple[int, str], str]:
    result: dict[tuple[int, str], str] = {}
    for width in range(1, 10):
        for row in read_domain_table(
            ROOT / "lib" / "domains" / f"d{width}.lisp"
        ):
            if row.uk and row.uk != "()":
                result[(width, row.bits)] = row.uk
    return result


def _encoder_material():
    migrator = _load_migrator()
    foundation, _digest = migrator.load_foundation(FOUNDATION)
    code_map = migrator.build_map(
        foundation, list(migrator.CALL_DOMAINS)
    )
    code_map = migrator.augment_code_map_with_domain_surfaces(
        code_map, DOMAIN_SURFACES
    )
    code_map = migrator.augment_code_map_with_registry_aliases(
        code_map, REGISTRY
    )
    resolver = migrator.build_resolver(
        historical_map=HISTORICAL,
        foundation=FOUNDATION,
        registry=REGISTRY,
        domain_surfaces=DOMAIN_SURFACES,
    )
    text7 = migrator.build_text7_encoder(foundation, TEXT7)
    legacy_sid_map = migrator.build_legacy_sid_map(REGISTRY, code_map)
    registry_surface_sid_map = migrator.build_registry_surface_sid_map(REGISTRY)
    return (
        migrator,
        code_map,
        resolver,
        text7,
        legacy_sid_map,
        registry_surface_sid_map,
    )


def _visible_binary_words(source: str) -> list[DomainWord]:
    (
        migrator,
        code_map,
        resolver,
        text7,
        legacy_sid_map,
        registry_surface_sid_map,
    ) = _encoder_material()

    converted, _hits, _shadowed = migrator.binary_rewrite(
        source,
        code_map,
        text7,
        legacy_sid_map,
        registry_surface_sid_map,
        resolver,
    )

    words: list[DomainWord] = []
    for token in converted.split():
        if not re.fullmatch(r"[01]{1,9}", token):
            raise CarrierError(
                f"migration emitted invalid exact-domain token {token!r}"
            )
        words.append(DomainWord(len(token), token))

    if not words:
        raise CarrierError("migration produced empty canonical source")
    return words


def encode_ukrainian(source: bytes) -> bytes:
    text = validate_canonical_ukrainian(source)
    return pack(_visible_binary_words(text))


def _render_d7(cells: list[str], render: list[str | None]) -> str:
    out: list[str] = []
    for token in cells:
        spelling = render[int(token, 2)]
        if spelling is None:
            raise CarrierError(
                f"D7 cell {token} has no canonical Ukrainian rendering"
            )
        out.append(spelling)
    return "".join(out)


def decode_words(words: list[DomainWord]) -> str:
    render = _load_uk_render()
    semantic = _semantic_uk_words()
    out: list[str] = []
    d7_buffer: list[str] = []

    def flush_d7() -> None:
        nonlocal d7_buffer
        if d7_buffer:
            out.append(_render_d7(d7_buffer, render))
            d7_buffer = []

    def add_space() -> None:
        if out and out[-1] not in ("(", " ", "."):
            out.append(" ")

    for word in words:
        key = (word.domain, word.bits)

        if word.domain == 2:
            flush_d7()
            if word.bits == "00":
                add_space()
            elif word.bits == "10":
                out.append("(")
            elif word.bits == "01":
                while out and out[-1] == " ":
                    out.pop()
                if not out or out[-1] == "(":
                    raise CarrierError(
                        "invalid empty D2 list; canonical empty is D3:000"
                    )
                out.append(")")
            elif word.bits == "11":
                while out and out[-1] == " ":
                    out.pop()
                if not out or out[-1] == "(":
                    raise CarrierError("invalid D2 dot placement")
                out.append(" .")
            else:
                raise CarrierError(f"invalid D2 source word {word.bits}")
            continue

        if word.domain == 3 and word.bits == "000":
            flush_d7()
            add_space()
            out.append("()")
            continue

        if word.domain == 7:
            d7_buffer.append(word.bits)
            continue

        flush_d7()
        surface = semantic.get(key)
        if surface is None:
            raise CarrierError(
                f"D{word.domain}:{word.bits} has no canonical Ukrainian projection"
            )
        add_space()
        out.append(surface)

    flush_d7()
    result = "".join(out).strip()
    if not result:
        raise CarrierError("decoded canonical source is empty")
    validate_canonical_ukrainian(result.encode("utf-8"))
    return result


def decode_ukrainian(data: bytes) -> bytes:
    return decode_words(unpack(data)).encode("utf-8")
