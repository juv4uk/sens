"""Regression checks for the #2019 H-NIL archaeology audit on Contract 11.8."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "experiments/research-2019-h-nil-corpus.py"
spec = importlib.util.spec_from_file_location("h_nil_2019_current_witness", MODULE)
assert spec and spec.loader
h_nil = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = h_nil
spec.loader.exec_module(h_nil)


class HNilContract118Tests(unittest.TestCase):
    def test_current_owner_ratified_domain_law_separates_d3_empty_from_d8_zero(self):
        mechanism, separated = h_nil.route_evidence()
        self.assertTrue(separated, "do not fall back to retired Contract 10 word matching")
        self.assertFalse(mechanism, "no implicit native mechanism for D8 zero")

    def test_domain_table_is_metadata_but_actual_calls_remain_detected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "lib/domains").mkdir(parents=True)
            (root / "lib/domains/d8.lisp").write_text(
                "(domain-table/1 (00000000 (ук символ-за-кодом)))\n", encoding="utf-8"
            )
            (root / "lib/active.lisp").write_text(
                "(NIL 1)\n(00000000 1)\n", encoding="utf-8"
            )
            with patch.object(h_nil, "ROOT", root):
                nil_heads, zero_heads, zero_tokens, _ = h_nil.scan_active_lisp()
            self.assertEqual([str(p) for p, _ in nil_heads], ["lib/active.lisp"])
            self.assertEqual([str(p) for p, _ in zero_heads], ["lib/active.lisp"])
            self.assertEqual([str(p) for p, _ in zero_tokens], ["lib/active.lisp"])

    def test_contract_absence_still_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "lib").mkdir()
            (root / "knowledge").mkdir()
            (root / "lib/function-table-mechanisms.lisp").write_text("()\n", encoding="utf-8")
            # Only the historic two English Contract 10 phrases: not normative.
            (root / "language-contract.lisp").write_text(
                "function 00000000 is not the empty-list value\n"
                "() is represented as a structural empty value outside the function space\n",
                encoding="utf-8",
            )
            (root / "knowledge/d1-d9-foundation.json").write_text(
                json.dumps({"status": "owner-ratified", "domains": {
                    "D3": {"width": 3, "residents": {"000": "EMPTY"}},
                    "D8": {"width": 8, "residents": {"00000000": "CODE-CHAR"}},
                }}), encoding="utf-8",
            )
            with patch.object(h_nil, "ROOT", root):
                _, separated = h_nil.route_evidence()
            self.assertFalse(separated)


if __name__ == "__main__":
    unittest.main()
