#!/usr/bin/env python3
"""SENS D7 v2: exact reversible W7 keyboard *data* projection.

Normative data: knowledge/d7-keyboard-v2-ratified.json.
Do not import phonetic D7 v1, phonological aliases, or legacy reserved cells.
Only the enclosing text value selects a projection. No cell creates a function.
"""
from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "knowledge/d7-keyboard-v2-ratified.json"
BITS7 = re.compile(r"[01]{7}\Z")
LAYOUTS = {
    "ук": "uk", "укр": "uk", "uk": "uk", "sym": "uk",
    "san": "san", "sa-deva": "san", "en": "ascii",
}


class D7CodecError(ValueError):
    """Unratified table, wrong width, missing glyph or unsupported projection."""


class D7SymbolCodec:
    def __init__(self, authority: dict | None = None) -> None:
        doc = json.loads(SOURCE.read_text(encoding="utf-8")) if authority is None else authority
        if (doc.get("schema"), doc.get("status"), doc.get("width"),
                doc.get("capacity"), doc.get("occupancy")) != (
                "sens.d7.keyboard/v2", "owner-ratified", 7, 128, 128):
            raise D7CodecError("D7 v2 owner authority mismatch")
        table = doc.get("table")
        if not isinstance(table, list) or len(table) != 128:
            raise D7CodecError("D7 v2 requires 128 exact W7 cells")
        self.forward: dict[str, dict[str, str]] = {}
        self.reverse: dict[str, dict[str, str]] = {}
        for surface in ("uk", "san", "ascii"):
            values = [entry.get(surface) for entry in table]
            if any(not isinstance(v, str) or len(v) != 1 for v in values):
                raise D7CodecError(f"D7 v2 non-scalar {surface} cell")
            if len(set(values)) != 128:
                raise D7CodecError(f"D7 v2 non-injective {surface} projection")
            self.forward[surface] = {}
            self.reverse[surface] = {}
        for index, entry in enumerate(table):
            bits = f"{index:07b}"
            if not isinstance(entry, dict) or entry.get("bits") != bits or entry.get("ascii") != chr(index):
                raise D7CodecError(f"D7 v2 coordinate drift at {bits}")
            for surface in self.forward:
                glyph = entry[surface]
                self.forward[surface][bits] = glyph
                self.reverse[surface][glyph] = bits

    def _layout(self, surface: str) -> str:
        if surface not in LAYOUTS:
            raise D7CodecError(f"unsupported current D7 v2 projection: {surface!r}")
        return LAYOUTS[surface]

    def glyph(self, bits: str, surface: str) -> str:
        if not isinstance(bits, str) or BITS7.fullmatch(bits) is None:
            raise D7CodecError("D7 requires an exact seven-bit word")
        return self.forward[self._layout(surface)][bits]

    def encode_text(self, text: str, surface: str) -> tuple[str, ...]:
        if not isinstance(text, str):
            raise D7CodecError("D7 text input must be Unicode")
        inverse = self.reverse[self._layout(surface)]
        try:
            return tuple(inverse[character] for character in text)
        except KeyError as exc:
            raise D7CodecError(f"unassigned D7 v2 keyboard character: {exc.args[0]!r}") from exc

    def render_text(self, words: list[str] | tuple[str, ...], surface: str) -> str:
        return "".join(self.glyph(word, surface) for word in words)

    def switch_surface(self, text: str, source: str, target: str) -> str:
        return self.render_text(self.encode_text(text, source), target)


@lru_cache(maxsize=1)
def current_codec() -> D7SymbolCodec:
    return D7SymbolCodec()


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--surface", choices=tuple(LAYOUTS), required=True)
    ap.add_argument("--text", required=True)
    args = ap.parse_args()
    print(" ".join(current_codec().encode_text(args.text, args.surface)))
