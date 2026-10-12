#!/usr/bin/env python3
"""D7 Sound/Text: exact 7-bit code <-> glyph of an explicitly selected surface.

Engineering algorithm adapted from juv4uk/shiva-sutras:
prototype/upc7_layouts.py (UPC7Text.encode/render/switch_layout, master).
The SENS owner-ratified knowledge/d7-ratified.json (#3572) is the ONLY source
of admitted coordinates and existing glyph assignments. The donor's old 107-cell
map or later candidate remappings MUST NEVER be imported as D7 identities.

No function is admitted by this text codec. No extra bits or padding are added.
"""
from __future__ import annotations

import argparse
import json
import re
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "knowledge" / "d7-ratified.json"
LAYOUTS = {"ук": "uk", "укр": "uk", "san": "deva", "en": "iast",
           "sym": "iast", "slp1": "slp1"}
BITS7 = re.compile(r"[01]{7}\Z")
DEVA_DIGITS = "०१२३४५६७८९"


class D7CodecError(ValueError):
    """Unadmitted code, absent glyph, ambiguous text, or unsupported surface."""


def _surface_glyph(row: dict, layout: str) -> str | None:
    source = LAYOUTS[layout]
    # Owner ledger contains a historical TAB projection at the *quote* cell.
    # Do not reinterpret TAB as a double quote or silently rewrite authority.
    if row["coordinate"] == "1100101":
        return None
    value = row.get("projection", {}).get(source)
    if not value:
        kind = row["semantic_role"]
        label = row.get("surface_label")
        if kind == "text-digit" and label in "0123456789":
            value = DEVA_DIGITS[int(label)] if layout == "san" else label
        elif kind == "text-punctuation" and label:
            value = label
    if not value:
        return None
    # Some ratified projections use ASCII control escapes in their JSON,
    # not actual control characters. Interpret only documented exact escapes.
    if re.fullmatch(r"\\x[0-9a-fA-F]{2}", value):
        return chr(int(value[2:], 16))
    if value == "\\\\":
        return "\\"
    if any(ch in value for ch in ("\x00",)):
        raise D7CodecError("NUL is not an admitted text glyph")
    return value


class D7SymbolCodec:
    def __init__(self, authority: dict | None = None) -> None:
        doc = authority if authority is not None else json.loads(
            SOURCE.read_text(encoding="utf-8")
        )
        if (doc.get("status"), doc.get("authority"), doc.get("width"),
                doc.get("capacity"), doc.get("occupancy")) != (
                    "owner-ratified", "#3572", 7, 128, 126
                ):
            raise D7CodecError("D7 ratified authority changed")
        admitted = doc["residents"]
        reserved = set(doc["reserved_coordinates"])
        if (len(admitted) != 126 or reserved != {"0100001", "0101010"}
                or set(admitted) & reserved
                or set(admitted) | reserved != {f"{i:07b}" for i in range(128)}):
            raise D7CodecError("D7 occupancy/reservation mismatch")
        rows = {row["coordinate"]: row for row in doc["rows"]}
        if len(rows) != 128:
            raise D7CodecError("D7 row ledger incomplete")
        if any(rows[bits]["status"] != "OWNER-RATIFIED"
               or rows[bits]["report_name"] != role
               for bits, role in admitted.items()):
            raise D7CodecError("D7 semantic role drift")
        if any(rows[bits]["status"] != "OWNER-RESERVED-PINNED" for bits in reserved):
            raise D7CodecError("D7 reserved cell admitted")
        self.roles = dict(admitted)
        self.forward: dict[str, dict[str, str]] = {}
        self.reverse: dict[str, dict[str, str]] = {}
        for layout in LAYOUTS:
            table: dict[str, str] = {}
            inverse: dict[str, str] = {}
            for bits in sorted(admitted):
                glyph = _surface_glyph(rows[bits], layout)
                if glyph is None:
                    continue
                if glyph in inverse and inverse[glyph] != bits:
                    raise D7CodecError(
                        f"{layout}: glyph collision {glyph!r}: "
                        f"{inverse[glyph]} != {bits}"
                    )
                table[bits] = glyph
                inverse[glyph] = bits
            self.forward[layout] = table
            self.reverse[layout] = inverse

    @staticmethod
    def _checked_bits(bits: str) -> None:
        if not isinstance(bits, str) or BITS7.fullmatch(bits) is None:
            raise D7CodecError(f"D7 requires exactly seven binary digits: {bits!r}")

    def glyph(self, bits: str, layout: str) -> str | None:
        self._checked_bits(bits)
        if bits not in self.roles:
            raise D7CodecError(f"D7:{bits} is not owner-admitted")
        if layout not in self.forward:
            raise D7CodecError(f"unknown D7 surface {layout!r}")
        return self.forward[layout].get(bits)

    def render_tokens(self, codes: tuple[str, ...] | list[str], layout: str) -> tuple[str, ...]:
        return tuple(self._required_glyph(word, layout) for word in codes)

    def _required_glyph(self, bits: str, layout: str) -> str:
        glyph = self.glyph(bits, layout)
        if glyph is None:
            raise D7CodecError(f"D7:{bits} has no {layout} glyph")
        return glyph

    def encode_tokens(self, tokens: tuple[str, ...] | list[str], layout: str) -> tuple[str, ...]:
        if layout not in self.reverse:
            raise D7CodecError(f"unknown D7 surface {layout!r}")
        inverse = self.reverse[layout]
        out = []
        for token in tokens:
            if token not in inverse:
                raise D7CodecError(f"{layout}: unknown or ambiguous token {token!r}")
            out.append(inverse[token])
        return tuple(out)

    def encode_text(self, text: str, layout: str) -> tuple[str, ...]:
        """Donor UPC7Text longest-match tokenizer with strict unknown rejection."""
        if not isinstance(text, str):
            raise D7CodecError("text must be a Unicode string")
        if layout not in self.reverse:
            raise D7CodecError(f"unknown D7 surface {layout!r}")
        inverse = self.reverse[layout]
        choices = sorted(inverse, key=lambda glyph: (-len(glyph), glyph))
        result: list[str] = []
        offset = 0
        while offset < len(text):
            for glyph in choices:
                if text.startswith(glyph, offset):
                    result.append(inverse[glyph])
                    offset += len(glyph)
                    break
            else:
                raise D7CodecError(f"{layout}: no glyph at offset {offset}: {text[offset:offset+8]!r}")
        return tuple(result)

    def render_text(self, codes: tuple[str, ...] | list[str], layout: str) -> str:
        """Reject any concatenation which would lose exact cell boundaries."""
        words = tuple(codes)
        displayed = "".join(self.render_tokens(words, layout))
        if self.encode_text(displayed, layout) != words:
            raise D7CodecError(f"{layout}: ambiguous concatenation; use render_tokens")
        return displayed

    def switch_surface(self, text: str, source: str, target: str) -> str:
        """Same exact D7 words; fail if target script has no faithful spelling."""
        return self.render_text(self.encode_text(text, source), target)


@lru_cache(maxsize=1)
def current_codec() -> D7SymbolCodec:
    return D7SymbolCodec()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--surface", required=True, choices=tuple(LAYOUTS))
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--code", help="render a single D7 word (7 bits)")
    action.add_argument("--text", help="encode text into a sequence of D7 words")
    action.add_argument("--words", nargs="+", help="render a sequence of D7 words")
    parser.add_argument("--target", choices=tuple(LAYOUTS), help="switch a text input")
    args = parser.parse_args()
    try:
        codec = current_codec()
        if args.code is not None:
            result = {"coordinate": args.code, "surface": args.surface,
                      "symbol": codec.glyph(args.code, args.surface)}
        elif args.words is not None:
            result = {"words": args.words, "surface": args.surface,
                      "text": codec.render_text(args.words, args.surface)}
        else:
            words = codec.encode_text(args.text, args.surface)
            result = {"words": words, "surface": args.surface,
                      "text": codec.render_text(words, args.surface)}
            if args.target:
                result["target_surface"] = args.target
                result["target_text"] = codec.render_text(words, args.target)
    except D7CodecError as exc:
        parser.exit(2, f"BLOCKED: {exc}\n")
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
