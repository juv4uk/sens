#!/usr/bin/env python3
"""Тести конкретних локальних slot для оригінальної програми machine-block."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import prove_lexical_locals as proof

ORIGINAL = ROOT / "lib/machine/block.lisp"
NAMES = (
    "machine-block", "machine-block-empty", "machine-block-one",
    "machine-block-append", "machine-block-concat", "machine-block-forms",
)


def locals_in(node):
    if isinstance(node, dict):
        if node.get("kind") == "Local":
            return [(node["depth"], node["index"])]
        return [item for value in node.values() for item in locals_in(value)]
    if isinstance(node, list):
        return [item for value in node for item in locals_in(value)]
    return []


class OriginalLocalCoordinates(unittest.TestCase):
    def original(self):
        raw = ORIGINAL.read_bytes()
        self.assertEqual(proof.git_blob(raw), proof.HISTORICAL_MACHINE_BLOB)
        data = proof.lower_definitions(raw.decode("utf-8"), expected_names=NAMES)
        self.assertEqual(data["status"], "LEXICAL_COORDINATES_PROVEN__PHYSICAL_NOT_ADMITTED")
        return raw, data

    def test_actual_unchanged_original_six_definitions_seven_local_references(self):
        raw, data = self.original()
        self.assertEqual(len(data["definitions"]), 6)
        bodies = [item["local_coordinate_body"] for item in data["definitions"]]
        self.assertEqual([locals_in(body) for body in bodies], [
            [(0, 0)], [], [(0, 0)], [(0, 0), (0, 1)],
            [(0, 0), (0, 1)], [(0, 0)],
        ])
        self.assertEqual(sum(len(locals_in(body)) for body in bodies), 7)
        self.assertEqual(bodies[0]["arity"], 1)
        self.assertEqual(bodies[1]["arity"], 0)
        self.assertEqual(bodies[3]["arity"], 2)
        self.assertEqual(data["original_executable_migrations_admitted"], 0)
        self.assertFalse(data["global_names_encoded"])
        self.assertFalse(data["d2_or_d7_framing_defined"])
        self.assertEqual(ORIGINAL.read_bytes(), raw)

    def test_historical_w8_function_identity_not_promoted_to_current_d8(self):
        _, data = self.original()
        rows = json.dumps(data["definitions"], ensure_ascii=False)
        self.assertIn('"historical_w8": "00100111"', rows)
        self.assertIn('"historical_w8": "00101001"', rows)
        self.assertIn('"kind": "historical-call-not-current-domain"', rows)
        self.assertNotIn('"kind": "DomainIdentity"', rows)

    def test_nested_lambda_nonlocal_depth_exact(self):
        form = "(00001001 example (00001000 (x) (00001000 (y) (00100111 x y))))"
        result = proof.lower_definitions(form)
        self.assertEqual(locals_in(result["definitions"][0]), [(1, 0), (0, 0)])

    def test_alpha_renaming_changes_no_numeric_local_machine_payload(self):
        first = "(00001001 example (00001000 (x) (00001000 (y) (00100111 x y))))"
        renamed = "(00001001 example (00001000 (a) (00001000 (b) (00100111 a b))))"
        self.assertEqual(proof.lower_definitions(first), proof.lower_definitions(renamed))

    def test_lexical_shadowing_uses_nearest_zero_depth(self):
        form = "(00001001 example (00001000 (x) (00001000 (x) x)))"
        result = proof.lower_definitions(form)
        self.assertEqual(locals_in(result["definitions"][0]), [(0, 0)])

    def test_second_param_has_exact_zero_based_index(self):
        form = "(00001001 example (00001000 (x y) (00100111 y x)))"
        result = proof.lower_definitions(form)
        self.assertEqual(locals_in(result["definitions"][0]), [(0, 1), (0, 0)])

    def test_empty_quote_stays_data_and_not_variable_reference(self):
        source = "(00001001 e (00001000 () (00000001 ())))"
        result = proof.lower_definitions(source)
        body = result["definitions"][0]["local_coordinate_body"]["body"]
        self.assertEqual(body, {"kind": "quote-empty-historical-w8", "datum": "D3:000"})
        self.assertEqual(locals_in(body), [])

    def test_duplicate_params_fail_closed(self):
        source = "(00001001 e (00001000 (x x) x))"
        with self.assertRaisesRegex(proof.BindingBlocked, "duplicate"):
            proof.lower_definitions(source)

    def test_unknown_local_does_not_fall_back_to_name_lookup(self):
        source = "(00001001 e (00001000 (x) free))"
        with self.assertRaisesRegex(proof.BindingBlocked, "unresolved free variable"):
            proof.lower_definitions(source)

    def test_unsupported_named_callable_fails_closed(self):
        source = "(00001001 e (00001000 (x) (some-global x)))"
        with self.assertRaisesRegex(proof.BindingBlocked, "global callable"):
            proof.lower_definitions(source)

    def test_other_legacy_head_or_data_unsupported(self):
        source = "(00001001 e (00001000 (x) (00000101 x)))"
        with self.assertRaisesRegex(proof.BindingBlocked, "unknown historical"):
            proof.lower_definitions(source)

    def test_quote_of_named_data_requires_a_data_framing_law(self):
        source = "(00001001 e (00001000 () (00000001 (named-symbol))))"
        with self.assertRaisesRegex(proof.BindingBlocked, "only QUOTE"):
            proof.lower_definitions(source)

    def test_ambiguous_global_and_local_names_not_encoded_as_domain_bits(self):
        source = "(00001001 000 (00001000 (x) x))"
        with self.assertRaises(proof.BindingBlocked):
            proof.lower_definitions(source)

    def test_multiple_definitions_cannot_reuse_global_name(self):
        source = "(00001001 e (00001000 (x) x))\n(00001001 e (00001000 (y) y))"
        with self.assertRaisesRegex(proof.BindingBlocked, "duplicate top-level"):
            proof.lower_definitions(source)

    def test_malformed_unclosed_source_blocked_not_repaired(self):
        source = "(00001001 e (00001000 (x) x)"
        with self.assertRaises(proof.parser.MigrationError):
            proof.lower_definitions(source)

    def test_cli_real_original_provenance_and_zero_physical_admission(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts/prove_lexical_locals.py"),
             "--source", str(ORIGINAL), "--require-machine-block-provenance"],
            cwd=ROOT, capture_output=True, text=True, timeout=45,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        self.assertEqual(data["source_git_blob_sha"], proof.HISTORICAL_MACHINE_BLOB)
        self.assertEqual(data["definition_count"], 6)
        self.assertEqual(data["original_executable_migrations_admitted"], 0)
        self.assertNotIn("physical_output", data)
        self.assertFalse((ROOT / "lib/machine/block.sens").exists())


if __name__ == "__main__":
    unittest.main()
