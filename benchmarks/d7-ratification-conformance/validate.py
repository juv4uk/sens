#!/usr/bin/env python3
"""Current D7 v2 conformance: exact W7 text, no phonetic v1/ordinal fallback."""
from __future__ import annotations
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from d7_symbol_codec import D7CodecError, current_codec

def require(condition: bool, label: str) -> None:
    if not condition:
        raise ValueError(label)

def main() -> None:
    norm = json.loads((ROOT / "knowledge/d7-keyboard-v2-ratified.json").read_text(encoding="utf-8"))
    require((norm["schema"], norm["status"], norm["width"], norm["occupancy"]) ==
            ("sens.d7.keyboard/v2", "owner-ratified", 7, 128), "authority")
    codec = current_codec()
    words = [f"{i:07b}" for i in range(128)]
    for surface in ("ук", "san", "en"):
        text = codec.render_text(words, surface)
        require(len(text) == 128, f"{surface} scalar count")
        require(len(set(text)) == 128, f"{surface} bijection")
        require(list(codec.encode_text(text, surface)) == words, f"{surface} exact roundtrip")
    require(codec.glyph("0100001", "ук") == "!", "v1 reserved ! still blocked")
    require(codec.glyph("0101010", "ук") == "*", "v1 reserved * still blocked")
    require(codec.glyph("1100001", "ук") == "ф", "v1 duplicate still blocked")
    require(codec.glyph("0100111", "ук") == "'", "apostrophe mapping drift")
    for invalid in ("0", "00000000", "11x0101"):
        try:
            codec.glyph(invalid, "ук")
        except D7CodecError:
            pass
        else:
            raise ValueError("D7 width/error gate bypassed")
    for legacy in ("slp1", "iast", "en-ipa"):
        try:
            codec.render_text(["0000000"], legacy)
        except D7CodecError:
            pass
        else:
            raise ValueError("historical D7 projection unexpectedly admitted")
    print("D7-CURRENT-CONFORMANCE: PASS 128/128 W7 data; no phonetic D7 v1 roles")
    print("D7-CALLABILITY=NOT-AUTHORIZED-BY-TEXT-PROJECTION")
    print("D7-NUMBER=NOT-AUTHORIZED-BY-TEXT-PROJECTION")
    print("D7-WIDTH=7")

if __name__ == "__main__":
    main()
