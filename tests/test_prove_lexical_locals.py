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

    def test_real_six_exported_names_have_source_only_slots_zero_to_five(self):
        raw, data = self.original()
        self.assertEqual(proof.git_blob(raw), proof.HISTORICAL_MACHINE_BLOB)
        self.assertTrue(data["global_declaration_order_source_only_proven"])
        self.assertEqual(data["global_declaration_count"], 6)
        self.assertEqual(
            [d["global_declaration_ordinal_source_only"]
             for d in data["definitions"]], list(range(6))
        )
        self.assertEqual(
            [d["source_global_name_provenance_only"]
             for d in data["definitions"]], list(NAMES)
        )
        self.assertEqual(data["source_global_export_manifest"], [
            {"ordinal_source_only": i,
             "source_name_provenance_only": name,
             "runtime_binding_admitted": False}
            for i, name in enumerate(NAMES)
        ])
        for declaration in data["definitions"]:
            self.assertFalse(declaration["global_binding_runtime_admitted"])
        self.assertFalse(data["global_binding_runtime_admitted"])
        self.assertFalse(data["global_names_encoded"])
        self.assertFalse(data["d2_or_d7_framing_defined"])
        self.assertEqual(data["original_executable_migrations_admitted"], 0)

    def test_global_call_uses_declaration_order_without_invented_d7_id(self):
        # Forward global reference must resolve source-order manifest,
        # not legacy W8 or current D8 callable resident.
        text = (
            "(00001001 alpha (00001000 (x) (beta x)))\n"
            "(00001001 beta (00001000 (y) y))\n"
        )
        rows = proof.lower_definitions(text)
        call = rows["definitions"][0]["local_coordinate_body"]["body"]
        self.assertEqual(call["kind"], "GlobalCallCandidate")
        self.assertEqual(call["declaration_ordinal_source_only"], 1)
        self.assertEqual(call["source_name_provenance_only"], "beta")
        self.assertEqual(call["arguments"], [{"kind": "Local", "depth": 0, "index": 0}])
        self.assertFalse(call["runtime_binding_admitted"])
        self.assertEqual(rows["original_executable_migrations_admitted"], 0)

    def test_global_value_reference_remains_source_only_candidate(self):
        text = (
            "(00001001 alpha (00001000 (x) beta))\n"
            "(00001001 beta (00001000 (y) y))\n"
        )
        rows = proof.lower_definitions(text)
        value = rows["definitions"][0]["local_coordinate_body"]["body"]
        self.assertEqual(value["kind"], "GlobalReferenceCandidate")
        self.assertEqual(value["declaration_ordinal_source_only"], 1)
        self.assertFalse(value["runtime_binding_admitted"])

    def test_lexical_shadow_of_global_callable_blocks_not_dispatches(self):
        text = (
            "(00001001 alpha (00001000 (beta) (beta beta)))\n"
            "(00001001 beta (00001000 (y) y))\n"
        )
        with self.assertRaisesRegex(proof.BindingBlocked, "shadowed global callable"):
            proof.lower_definitions(text)

    def test_shadowed_global_value_resolves_local_first(self):
        text = (
            "(00001001 alpha (00001000 (beta) beta))\n"
            "(00001001 beta (00001000 (y) y))\n"
        )
        rows = proof.lower_definitions(text)
        local = rows["definitions"][0]["local_coordinate_body"]["body"]
        self.assertEqual(local, {"kind": "Local", "depth": 0, "index": 0})

    def test_ordinal_changes_under_definition_reordering_not_semantic_law(self):
        source = (
            "(00001001 alpha (00001000 (x) (beta x)))\n"
            "(00001001 beta (00001000 (y) y))\n"
        )
        permuted = (
            "(00001001 beta (00001000 (y) y))\n"
            "(00001001 alpha (00001000 (x) (beta x)))\n"
        )
        a, b = proof.lower_definitions(source), proof.lower_definitions(permuted)
        self.assertEqual(
            a["definitions"][0]["local_coordinate_body"]["body"][
                "declaration_ordinal_source_only"], 1
        )
        self.assertEqual(
            b["definitions"][1]["local_coordinate_body"]["body"][
                "declaration_ordinal_source_only"], 0
        )
        self.assertNotEqual(a["source_global_export_manifest"],
                            b["source_global_export_manifest"])
        for data in (a, b):
            self.assertFalse(data["global_binding_runtime_admitted"])
            self.assertEqual(data["original_executable_migrations_admitted"], 0)

    def test_historical_w8_function_identity_not_promoted_to_current_d8(self):
        _, data = self.original()
        rows = json.dumps(data["definitions"], ensure_ascii=False)
        self.assertIn('"historical_w8": "00100111"', rows)
        self.assertIn('"historical_w8": "00101001"', rows)
        self.assertIn('"kind": "historical-call-proven-current-head-not-admitted"', rows)
        self.assertIn('"current_domain": "D4"', rows)
        self.assertIn('"current_exact_word": "1110"', rows)
        self.assertIn('"current_exact_word": "1111"', rows)
        self.assertNotIn('"kind": "DomainIdentity"', rows)

    def test_all_seventeen_real_old_heads_have_only_audited_current_successors(self):
        _, data = self.original()
        expected = {
            "00001001": ("D4", "0011", 6),  # DEFINE
            "00001000": ("D4", "0010", 6),  # LAMBDA
            "00000001": ("D3", "001", 1),   # QUOTE
            "00100111": ("D4", "1110", 2),  # LIST
            "00101001": ("D4", "1111", 2),  # APPEND
        }
        self.assertTrue(data["historical_head_successors_proven"])
        witness = data["historical_head_successors"]
        counts = {key: 0 for key in expected}

        def walk(node):
            if isinstance(node, dict):
                for key in ("historical_head_successor", "historical_define_successor"):
                    successor = node.get(key)
                    if successor is not None:
                        counts[successor["old_w8"]] += 1
                        self.assertFalse(successor["current_runtime_admitted_by_this_proof"])
                for key, value in node.items():
                    if key not in ("historical_head_successor", "historical_define_successor"):
                        walk(value)
            elif isinstance(node, list):
                for value in node:
                    walk(value)

        walk(data["definitions"])
        self.assertEqual(sum(counts.values()), 17)
        for old_w8, (domain, word, n) in expected.items():
            self.assertEqual(counts[old_w8], n)
            self.assertEqual(witness[old_w8]["current_domain"], domain)
            self.assertEqual(witness[old_w8]["current_exact_word"], word)
            self.assertEqual(len(word), int(domain[1:]))
        self.assertFalse(data["current_callable_domain_identity_proven"])
        self.assertEqual(data["original_executable_migrations_admitted"], 0)

    def test_audited_successor_not_guessed_from_historical_w8_bits(self):
        self.assertEqual(proof.audited_current_head("00100111")["current_exact_word"], "1110")
        self.assertEqual(proof.audited_current_head("00101001")["current_exact_word"], "1111")
        self.assertNotEqual("00100111", "1110")
        with self.assertRaises(proof.BindingBlocked):
            proof.audited_current_head("11111111")

    def test_audited_successor_corrupt_registry_blocks(self):
        from unittest.mock import patch
        for corrupt in (
            {"00100111": None},
            {"00100111": ("111", "D3", "forged")},
            {"00100111": ("11100000", "D8", "forged")},
        ):
            with self.subTest(corrupt=corrupt):
                with patch.object(proof, "historical_successor_registry", return_value=corrupt):
                    with self.assertRaises(proof.BindingBlocked):
                        proof.audited_current_head("00100111")

    def test_historical_w8_cannot_be_interpreted_as_current_d8_in_auto(self):
        registry = proof.historical_successor_registry()
        resolver = proof.parser.Resolver(registry, {}, {}, source_era="auto")
        with self.assertRaisesRegex(proof.parser.MigrationError, "ambiguous W8"):
            resolver.head(proof.parser.Tok("ATOM", "00100111", 0))

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
        self.assertEqual(body["kind"], "quote-empty-historical-w8")
        self.assertEqual(body["datum"], "D3:000")
        self.assertEqual(body["historical_head_successor"]["current_domain"], "D3")
        self.assertEqual(body["historical_head_successor"]["current_exact_word"], "001")
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
