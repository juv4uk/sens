#!/usr/bin/env python3
"""Інструментальні тести генератора D11; семантику SENS перевіряють окремі Lisp-свідки."""
from __future__ import annotations

import contextlib
import importlib.util
import io
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "derive_d11_coordinate", ROOT / "scripts" / "derive-d11-coordinate.py"
)
assert SPEC and SPEC.loader
MOD = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MOD
SPEC.loader.exec_module(MOD)

PARENT = "0110000000"
PARENT_LISP = "CDAAAAAAAR"
SEED = {
    "01100000000": "CDAAAAAAAAR",
    "01100000001": "CDAAAAAAADR",
}


class DeriveD11CoordinateTests(unittest.TestCase):
    def test_suffix_zero_appends_car_before_final_r(self) -> None:
        result = MOD.derive(PARENT, "0", PARENT_LISP, SEED)
        self.assertEqual(result["coordinate"], "01100000000")
        self.assertEqual(result["lisp"], "CDAAAAAAAAR")
        self.assertEqual(result["en"], "cdaaaaaaaar")

    def test_suffix_one_appends_cdr_before_final_r(self) -> None:
        result = MOD.derive(PARENT, "1", PARENT_LISP, SEED)
        self.assertEqual(result["coordinate"], "01100000001")
        self.assertEqual(result["lisp"], "CDAAAAAAADR")

    def test_nonselector_parent_cannot_claim_new_d11_coordinate(self) -> None:
        with self.assertRaisesRegex(SystemExit, "NO_EXTENSION"):
            MOD.derive("0000000000", "0", "MISSING-CAPABILITY", SEED)

    def test_parent_name_must_agree_with_seed(self) -> None:
        with self.assertRaisesRegex(SystemExit, "SEED_MISMATCH"):
            MOD.derive(PARENT, "0", "CAAAAAAAAR", SEED)

    def test_invalid_parent_shape_is_rejected(self) -> None:
        with self.assertRaisesRegex(SystemExit, "INVALID_PARENT_SELECTOR"):
            MOD.derive(PARENT, "0", "FILTER", SEED)

    def test_main_checks_seed_instead_of_silently_replacing_wrong_name(self) -> None:
        output = io.StringIO()
        with patch.object(MOD, "_rows", return_value=SEED):
            with patch.object(MOD, "_d10_by_lisp", return_value={PARENT_LISP: PARENT}):
                with contextlib.redirect_stdout(output):
                    self.assertEqual(MOD.main([PARENT, "0", "--check"]), 0)
        self.assertIn("CDAAAAAAAAR", output.getvalue())
        self.assertIn("точний збіг із сідом", output.getvalue())

    def test_from_lisp_accepts_existing_derived_name_via_parent(self) -> None:
        output = io.StringIO()
        with patch.object(MOD, "_rows", return_value=SEED):
            with patch.object(MOD, "_d10_by_lisp", return_value={PARENT_LISP: PARENT}):
                with contextlib.redirect_stdout(output):
                    self.assertEqual(MOD.main(["--from-lisp", SEED["01100000000"]]), 0)
        self.assertIn("D11-КООРДИНАТА: 01100000000", output.getvalue())


if __name__ == "__main__":
    unittest.main()
