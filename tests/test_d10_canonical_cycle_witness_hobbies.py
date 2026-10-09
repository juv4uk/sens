#!/usr/bin/env python3
"""Independent edge-case and negative tests for D10 directed-cycle research."""
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
source = ROOT / "scripts/check_d10_cycle_witness_hobbies.py"
spec = importlib.util.spec_from_file_location("d10_cycle_witness_proof", source)
proof = importlib.util.module_from_spec(spec)
spec.loader.exec_module(proof)


class DirectedWitnessTests(unittest.TestCase):
    def test_acyclic_chain_returns_none(self):
        self.assertIsNone(proof.dfs_reference([0,1,2], [(0,1),(1,2)]))

    def test_self_loop_is_valid_singleton(self):
        self.assertEqual(proof.dfs_reference([0,1,2], [(1,1),(0,1)]), (1,))

    def test_scc_without_explicit_path_is_not_enough(self):
        edges = [(0,1),(1,0),(0,2),(2,0)]
        self.assertEqual(proof.dfs_reference([0,1,2], edges), (0,1))

    def test_directed_reverse_not_equivalent(self):
        edges = [(2,0),(0,1),(1,2)]
        self.assertEqual(proof.dfs_reference([2,0,1], edges), (0,1,2))
        self.assertIsNone(proof.dfs_reference([0,1,2], [(2,0),(1,0),(2,1)]))

    def test_tie_policy_is_lexicographic_not_shortest(self):
        # (0,1,2) precedes (0,2), despite being longer.
        e = [(0,1),(1,2),(2,0),(0,2)]
        self.assertEqual(proof.dfs_reference([0,1,2], e), (0,1,2))

    def test_duplicate_edges_do_not_multiply_witness(self):
        edges = [(0,1),(0,1),(1,0)]
        self.assertEqual(proof.dfs_reference([1,0], edges), (0,1))

    def test_invalid_endpoints_fail_closed(self):
        for vertices, edges in [([0,1],[(0,2)]),([0,0],[]),([-1],[])]:
            with self.subTest(v=vertices,e=edges), self.assertRaises(proof.ProofFailure):
                proof.permutation_oracle(vertices, edges)

    def test_oracles_agree_on_adversarial_graph(self):
        edges = [(0,0),(0,1),(1,2),(2,3),(3,0),(3,1),(2,2)]
        self.assertEqual(proof.dfs_reference(range(4), edges),
                         proof.permutation_oracle(range(4), edges))

    def test_quoted_graph_has_explicit_original_ownership(self):
        import json
        dossier = json.loads((ROOT / "knowledge/d10-canonical-directed-cycle-witness-research-v1.json").read_text())
        inv = json.loads((ROOT / "knowledge/d10-v1-semantic-inventory.json").read_text())
        self.assertTrue(proof.verify_dossier(dossier,inv))
        self.assertEqual(dossier["identity"]["status"], "HOLD-CORE-LIBRARY-DERIVABILITY")

if __name__ == "__main__":
    unittest.main(verbosity=2)
