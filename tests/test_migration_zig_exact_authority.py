#!/usr/bin/env python3
"""Migration→Zig preflight: exact width and safe historical donor provenance."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "migration-zig-gate.py"
SPEC = importlib.util.spec_from_file_location("migration_zig_exact_authority", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
gate = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gate)


def word(domain, bits, label):
    return SimpleNamespace(domain=domain, bits=bits, label=label)


class MigrationExactAuthority(unittest.TestCase):
    def setUp(self):
        self.surface = {"quote": word("D3", "001", "QUOTE"),
                        "lambda": word("D4", "0001", "LAMBDA")}
        self.legacy = {"00000001": word("D3", "001", "QUOTE")}
        self.safe = {("D3", "QUOTE"), ("D4", "LAMBDA")}

    def checked(self):
        gate.validate_migration_identities(self.surface, self.legacy, self.safe)

    def assert_blocked(self, diagnostic):
        with self.assertRaisesRegex(ValueError, diagnostic):
            self.checked()

    def test_valid_owner_qualified_d3_d4_surfaces_and_donor(self):
        self.checked()

    def test_surface_domain_prefix_must_be_ratified(self):
        self.surface["quote"] = word("X3", "001", "QUOTE")
        self.assert_blocked("unexpected-domain")

    def test_surface_wrong_width_is_rejected(self):
        self.surface["quote"] = word("D3", "01", "QUOTE")
        self.assert_blocked("invalid-exact-bits")

    def test_surface_nonbinary_bits_are_rejected(self):
        self.surface["quote"] = word("D3", "0A1", "QUOTE")
        self.assert_blocked("invalid-exact-bits")

    def test_legacy_donor_wrong_width_is_rejected(self):
        self.legacy["00000001"] = word("D3", "0001", "QUOTE")
        self.assert_blocked("invalid-exact-bits")

    def test_legacy_donor_wrong_historical_code_is_rejected(self):
        self.legacy = {"001": word("D3", "001", "QUOTE")}
        self.assert_blocked("invalid-8bit-donor-provenance")

    def test_legacy_donor_unratified_label_is_rejected(self):
        self.legacy["00000001"] = word("D3", "001", "UNRATIFIED")
        self.assert_blocked("unratified-donor")

    def test_legacy_d8_identity_not_promoted_to_callable_d3(self):
        self.legacy["00000001"] = word("D8", "00000001", "QUOTE")
        self.assert_blocked("unexpected-domain")

    def test_surfaces_do_not_admit_d24_arithmetic_as_call(self):
        self.surface["quote"] = word("D24", "0" * 24, "QUOTE")
        self.assert_blocked("unexpected-domain")

    def test_non_mapping_donor_set_rejected(self):
        self.legacy = []
        self.assert_blocked("expected=mapping")


if __name__ == "__main__":
    unittest.main()
