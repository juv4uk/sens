"""Focused conformance tests for the D7 v1/v2 authority boundary.

D7 v1 retains a 126/128 Sound7 occupancy witness with two pinned coordinates.
D7 v2 is a full 128/128 keyboard text/data projection. These facts coexist but
must not be merged into one generic occupancy table.
"""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "generate-domain-owner-registry.py"
SPEC = importlib.util.spec_from_file_location("domain_owner_registry", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
GENERATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GENERATOR)

D7_V1 = json.loads((ROOT / "knowledge/d7-ratified.json").read_text(encoding="utf-8"))
D7_V2 = json.loads((ROOT / "knowledge/d7-keyboard-v2-ratified.json").read_text(encoding="utf-8"))
RESERVED = {"0100001", "0101010"}
FULL_W7 = {f"{number:07b}" for number in range(128)}


class D7DualAuthorityTests(unittest.TestCase):
    def test_current_maps_have_distinct_exact_scopes(self) -> None:
        v1_words = GENERATOR.validate_d7_dual_authority(D7_V1, D7_V2)
        v2_words = {row["bits"] for row in D7_V2["table"]}

        self.assertEqual(len(v1_words), 126)
        self.assertFalse(set(v1_words) & RESERVED)
        self.assertEqual(set(v1_words) | RESERVED, FULL_W7)
        self.assertEqual(len(v2_words), 128)
        self.assertEqual(v2_words, FULL_W7)
        self.assertTrue(RESERVED <= v2_words)

        # The generated owner bitmap must retain only the role-specific v1
        # Sound7 occupancy. Text/Data surface availability does not fill holes.
        generated_d7 = {bits for width, bits, _source in GENERATOR.owner_rows() if width == 7}
        self.assertEqual(generated_d7, set(v1_words))
        self.assertEqual(len(GENERATOR.owner_rows()), 243)

    def test_historical_v1_cannot_claim_current_owner_status(self) -> None:
        mutant = deepcopy(D7_V1)
        mutant["status"] = "owner-ratified"
        with self.assertRaisesRegex(ValueError, "D7 v1 historical Sound7 authority"):
            GENERATOR.validate_d7_dual_authority(mutant, D7_V2)

    def test_v1_reserved_coordinate_cannot_become_an_occupant(self) -> None:
        mutant = deepcopy(D7_V1)
        mutant["residents"]["0100001"] = "unauthorized.resident"
        with self.assertRaisesRegex(ValueError, "D7 v1"):
            GENERATOR.validate_d7_dual_authority(mutant, D7_V2)

    def test_v2_missing_or_duplicate_coordinate_is_rejected(self) -> None:
        missing = deepcopy(D7_V2)
        missing["table"].pop()
        with self.assertRaisesRegex(ValueError, "D7 v2 keyboard authority shape"):
            GENERATOR.validate_d7_dual_authority(D7_V1, missing)

        duplicate = deepcopy(D7_V2)
        duplicate["table"][-1]["bits"] = duplicate["table"][0]["bits"]
        with self.assertRaisesRegex(ValueError, "complete exact W7 domain"):
            GENERATOR.validate_d7_dual_authority(D7_V1, duplicate)

    def test_v2_projections_must_be_bijective_and_ascii_coordinate_exact(self) -> None:
        for field in ("uk", "san"):
            with self.subTest(field=field):
                mutant = deepcopy(D7_V2)
                mutant["table"][1][field] = mutant["table"][0][field]
                with self.assertRaisesRegex(ValueError, f"D7 v2 {field} projection"):
                    GENERATOR.validate_d7_dual_authority(D7_V1, mutant)

        wrong_ascii = deepcopy(D7_V2)
        wrong_ascii["table"][0]["ascii"] = wrong_ascii["table"][1]["ascii"]
        with self.assertRaisesRegex(ValueError, "ASCII projection"):
            GENERATOR.validate_d7_dual_authority(D7_V1, wrong_ascii)


if __name__ == "__main__":
    unittest.main()
