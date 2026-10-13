"""Mechanical perf evidence tests; SENS owns semantics."""
import importlib.util
from pathlib import Path
import unittest

P = Path(__file__).resolve().parents[1] / "scripts/perf_budget_gate.py"
spec = importlib.util.spec_from_file_location("perf_budget_gate", P)
g = importlib.util.module_from_spec(spec)
spec.loader.exec_module(g)
ENV = {"git_sha": "a"*40, "rustc": "rustc pinned", "valgrind": "valgrind pinned",
       "machine": "x86_64", "iterations": 10000, "reps": 3,
       "contract_version": "11.8", "semantic_generation": "contract-11-8-exact-d1-d9"}
ROW = {"case": "d5", "iterations": "10000", "reps": "3",
       "net_i_refs_per_iteration": "120.0", "spread_pct": "0",
       "contract_version": "11.8", "semantic_generation": "contract-11-8-exact-d1-d9"}
POLICY = {"schema": g.SCHEMA,
          "baseline": {"source_sha": "b"*40, "evidence_sha256": "c"*64, "ratification_issue": "#4134"},
          "environment": {k: ENV[k] for k in
                          ("rustc", "valgrind", "machine", "iterations", "reps",
                           "contract_version", "semantic_generation")},
          "budgets": [{"case": "d5", "layer": "transport", "max_net_irefs_per_iteration": 115.0}]}

class RatchetEvidenceTests(unittest.TestCase):
    def check(self, policy=None, env=None, row=None):
        return g.evaluate(POLICY if policy is None else policy,
                          ENV if env is None else env,
                          {"d5": ROW if row is None else row},
                          env_sha="e"*64, result_sha="f"*64)

    def test_named_overage(self):
        failures, verdict = self.check()
        self.assertIn("PERF-BUDGET-EXCEEDED case=d5", failures[0])
        self.assertEqual(verdict["excess_total_ir_per_op"], 5.0)

    def test_pass_below_limit(self):
        failures, verdict = self.check(row=dict(ROW, net_i_refs_per_iteration="114.0"))
        self.assertEqual(failures, [])
        self.assertEqual(verdict["status"], "PASS")

    def test_no_fake_uncalibrated_green(self):
        with self.assertRaisesRegex(g.BudgetError, "PERF-BUDGET-UNCALIBRATED"):
            self.check(policy=dict(POLICY, budgets=[]))

    def test_environment_mismatch(self):
        with self.assertRaisesRegex(g.BudgetError, "PERF-ENVIRONMENT-MISMATCH"):
            self.check(env=dict(ENV, rustc="different"))

    def test_unregistered_case(self):
        with self.assertRaisesRegex(g.BudgetError, "PERF-EVIDENCE-INCOMPLETE"):
            self.check(policy=dict(POLICY, budgets=[dict(POLICY["budgets"][0], case="d7")]))

    def test_negative_net_not_clamped(self):
        with self.assertRaisesRegex(g.BudgetError, "PERF-EVIDENCE-INCOMPLETE"):
            self.check(row=dict(ROW, net_i_refs_per_iteration="-0.5"))

    def test_duplicate_budget(self):
        with self.assertRaisesRegex(g.BudgetError, "PERF-BUDGET-BAD-CONTRACT"):
            self.check(policy=dict(POLICY, budgets=POLICY["budgets"] * 2))

if __name__ == "__main__":
    unittest.main()
