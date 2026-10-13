"""D7 v2 / SLP1 boundary: exact 128-key authority, QUOTE data, fail-closed.

SLP1 is historical Sanskrit phonetic notation. Active SENS D7 v2 is a
7-bit keyboard-coordinate profile: en=ASCII, uk/san positional projections.
A textual glyph never mints an executable function.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))
SCRIPT = SCRIPTS / "migrate-to-sens-codes.py"
SPEC = importlib.util.spec_from_file_location("sens_d7_slp1_boundary", SCRIPT)
assert SPEC and SPEC.loader
migration = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = migration
SPEC.loader.exec_module(migration)
from sens_source_resolver import build_resolver

OWNER = ROOT / "knowledge/d7-keyboard-v2-ratified.json"
RETIRED = ROOT / "crates/sens/src/text7_projection_generated.rs"
FOUNDATION = ROOT / "knowledge/d1-d9-foundation.json"
REGISTRY = ROOT / "lib/surface/semantic-registry.lisp"
HISTORICAL = ROOT / "contracts/core1-historical-sid-map.lisp"
DOMAINS = [ROOT / f"lib/domains/d{width}.lisp" for width in range(1, 10)]


def setup():
    data, _ = migration.load_foundation(FOUNDATION)
    current = migration.build_text7_encoder(data, OWNER)
    code_map = migration.build_map(data, ["D3", "D4", "D5", "D6"])
    code_map = migration.augment_code_map_with_domain_surfaces(code_map, DOMAINS)
    code_map = migration.augment_code_map_with_registry_aliases(code_map, REGISTRY)
    sid8 = migration.build_legacy_sid_map(REGISTRY, code_map)
    surfaces = migration.build_registry_surface_sid_map(REGISTRY)
    resolver = build_resolver(
        historical_map=HISTORICAL,
        foundation=FOUNDATION,
        registry=REGISTRY,
        domain_surfaces=DOMAINS,
    )
    return current, code_map, sid8, surfaces, resolver


class ExactD7QuotedBoundary(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        (cls.current, cls.code_map, cls.sid8,
         cls.surfaces, cls.resolver) = setup()

    def rewrite(self, source):
        return migration.binary_rewrite(
            source, self.code_map, self.current,
            self.sid8, self.surfaces, self.resolver
        )[0].split()

    def test_all_128_positions_are_exactly_seven_bits_in_three_views(self):
        owner = json.loads(OWNER.read_text(encoding="utf-8"))
        self.assertEqual(
            (owner["schema"], owner["status"], owner["width"],
             owner["capacity"], owner["occupancy"]),
            ("sens.d7.keyboard/v2", "owner-ratified", 7, 128, 128)
        )
        self.assertEqual(len(owner["table"]), 128)
        views = self.current["d7-keyboard/v2"]
        for mode, field in (("en", "ascii"), ("uk", "uk"), ("san", "san")):
            self.assertEqual(len(views[mode]), 128)
            self.assertEqual(len(set(views[mode].values())), 128)
            for n, row in enumerate(owner["table"]):
                with self.subTest(mode=mode, code=n):
                    bits = f"{n:07b}"
                    self.assertEqual(row["bits"], bits)
                    self.assertEqual(views[mode][row[field]], bits)
                    self.assertEqual(len(bits), 7)
                    self.assertEqual(len(row[field]), 1)

    def test_slp1_phonemes_are_not_new_machine_coordinates(self):
        # The old phonetic 'K' = ख at v1 cell 0000001. Under keyboard/v2
        # the exact English keyboard coordinate for 'K' is ASCII 75.
        self.assertEqual(self.current["d7-keyboard/v2"]["en"]["K"], "1001011")
        self.assertEqual(
            migration.encode_text7_spelling("K", self.current), ["1001011"]
        )
        self.assertNotEqual("1001011", "0000001")

    def test_quoted_binary_is_data_not_executable_slp1(self):
        got = self.rewrite("(001 binary)\n")
        payload = [f"{ord(ch):07b}" for ch in "binary"]
        framed = ["10"]
        for index, code in enumerate(payload):
            if index:
                framed.append("00")
            framed.append(code)
        framed.append("01")
        self.assertEqual(got, ["10", "001", "00"] + framed + ["01"])
        self.assertNotIn("SA_SLP1_ENCODE", " ".join(got))

    def test_negative_unbound_executable_name_remains_blocked(self):
        with self.assertRaisesRegex(
            migration.BinaryMigrationError, "unresolved executable head"
        ):
            self.rewrite("(binary (001 ()))\n")
        with self.assertRaisesRegex(
            migration.BinaryMigrationError, "UNADMITTED_TEXT7_CONTEXT"
        ):
            self.rewrite("(111 binary (001 ()))\n")

    def test_negative_string_law_remains_explicitly_blocked(self):
        with self.assertRaisesRegex(
            migration.BinaryMigrationError, "UNADMITTED_STRING_VALUE"
        ):
            self.rewrite('(001 "binary")\n')

    def test_negative_authority_capacity_127_cannot_masquerade_as_128(self):
        authority = json.loads(OWNER.read_text(encoding="utf-8"))
        authority["capacity"] = 127
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "tampered-v2.json"
            path.write_text(json.dumps(authority, ensure_ascii=False), encoding="utf-8")
            with self.assertRaisesRegex(
                migration.BinaryMigrationError,
                "D7 keyboard/v2 owner authority invalid",
            ):
                migration.build_text7_encoder(None, path)

    def test_retired_generated_donor_has_no_slp1_encode_table(self):
        source = RETIRED.read_text(encoding="utf-8")
        self.assertIn("UPC7_SOURCE_REVISION", source)
        self.assertNotIn("pub(crate) const SA_SLP1_ENCODE", source)
        self.assertNotIn("pub(crate) const UK_ENCODE", source)
        with self.assertRaisesRegex(
            migration.BinaryMigrationError, "HISTORICAL_D7_DISABLED",
        ):
            migration.build_text7_encoder(None, RETIRED)


if __name__ == "__main__":
    unittest.main()
