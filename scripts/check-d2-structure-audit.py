#!/usr/bin/env python3
import json
from pathlib import Path

root=Path(__file__).resolve().parents[1]
audit=json.loads((root/"knowledge/d2-structure-audit.json").read_text(encoding="utf-8"))

assert audit["schema"]=="d2-structure-audit/v1"
assert audit["authority"]=="#4160"
assert audit["parent"]=="#4157"
assert audit["invariant"]["language_structure_owner"]=="D2 only"
assert audit["invariant"]["d2_roles"]=={
    "00":"SEPARATOR",
    "01":"CLOSE",
    "10":"OPEN",
    "11":"DOT",
}
assert audit["summary"]["debt_unowned"]==0
assert audit["summary"]["blocking_semantic_conflict"]==0

rows={row["path"]:row for row in audit["paths"]}
assert len(rows)==6

reader=(root/"crates/sens/src/canonical_reader.rs").read_text(encoding="utf-8")
for literal in [
    "const D2_SEPARATOR: u8 = 0b00;",
    "const D2_CLOSE: u8 = 0b01;",
    "const D2_OPEN: u8 = 0b10;",
    "const D2_DOT: u8 = 0b11;",
    "BinarySourceWord::W2(word)",
    "D2 separator word 00 cannot stand in expression position",
]:
    assert literal in reader, literal
assert "W3..W9 word carry exact ratified domain identity" in reader
assert rows["crates/sens/src/canonical_reader.rs"]["status"]=="PASS"

source=(root/"crates/sens/src/source_words.rs").read_text(encoding="utf-8")
for variant in ("W1(Bit1)","W2(Bit2)","W3(Bit3)","W4(Bit4)","W5(Bit5)","W6(Bit6)","W7(Bit7)","W8(Bit8)","W9(Bit9)"):
    assert variant in source
assert "Structural roles remain language-owned; width is the only fact here." in source
assert rows["crates/sens/src/source_words.rs"]["status"]=="PASS"

migrate=(root/"scripts/migrate-three-pass.py").read_text(encoding="utf-8")
for literal in [
    'D2_SEP="00"',
    'D2_CLOSE="01"',
    'D2_OPEN="10"',
    'D2_DOT="11"',
    "D2 word {t} is structural control only; it cannot be an executable head",
    "D2 word {t} is structural control only; it cannot be ordinary data",
]:
    assert literal in migrate, literal
assert rows["scripts/migrate-three-pass.py"]["status"]=="PASS"

translator=(root/"scripts/translate-domain-program.py").read_text(encoding="utf-8")
assert "D2 labels and D3 EMPTY are descriptive only." in translator
assert 'assert "open" not in translation_map("en", "uk")' in translator
assert rows["scripts/translate-domain-program.py"]["status"]=="PASS"

packing=(root/"crates/sens/src/source_packing.rs").read_text(encoding="utf-8")
for literal in [
    "grammar/EOS/container framing is a separate protocol",
    "structural_bit_patterns_are_packed_as_payload_not_transport_delimiters",
    "Standalone self-description belongs to",
    "the framing layer.",
]:
    assert literal in packing, literal
assert rows["crates/sens/src/source_packing.rs"]["status"]=="PASS"

framing=(root/"crates/sens/src/binary_framing.rs").read_text(encoding="utf-8")
debt=rows["crates/sens/src/binary_framing.rs"]
assert debt["owner"]=="#4164"
old_tags=("const CONTROL_SPACE", "const CONTROL_CLOSE", "const CONTROL_OPEN", "const CONTROL_ESCAPE")
new_tags=("const WIRE_SPACE_TAG", "const WIRE_CLOSE_TAG", "const WIRE_OPEN_TAG", "const WIRE_ESCAPE_TAG")
old_present=any(tag in framing for tag in old_tags)
new_present=all(tag in framing for tag in new_tags)
stale_claim="canonical Control2" in framing

# Current main may still carry the owned #4164 debt. Once #4164 lands, the
# exact same guard recognizes the resolved transport-only state without
# weakening the D2 language-structure invariant.
if old_present or stale_claim:
    assert debt["status"]=="DEBT-OWNED"
    assert "#4164" in debt["owner"]
    assert "standalone framing/decoder mechanism" in framing
    assert "not** the canonical" in framing
    print("binary_framing=DEBT-OWNED:#4164")
else:
    assert new_present, "framing debt disappeared without WIRE_* replacement"
    assert "Private tags of this standalone transport framing" in framing
    assert "current D2:11, whose language meaning is DOT" in framing
    print("binary_framing=PASS-RESOLVED-BY-4164")

print("D2-STRUCTURE-AUDIT=PASS")
print("language-structure-owner=D2 only")
print("unowned-debt=0 blocking-semantic-conflict=0")
