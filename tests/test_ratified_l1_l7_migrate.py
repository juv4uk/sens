#!/usr/bin/env python3
"""Pure/fail-closed regressions for the owner's ratified L1–L7 gate."""
from __future__ import annotations

import contextlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "scripts" / "ratified_l1_l7_migrate.py"
spec = importlib.util.spec_from_file_location("_ratified_l1_l7_under_test", SOURCE)
assert spec and spec.loader
import sys
sys.modules[spec.name] = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sys.modules[spec.name])
m = sys.modules[spec.name]


class Ratification(unittest.TestCase):
    def try_source(self, text, *, era="auto"):
        ctx = m.Context(source_era=era)
        payload, typed = m.migrate(text, ctx)
        self.assertTrue(payload)
        self.assertEqual(len(typed), 64)
        return ctx

    def blocked(self, text, rule):
        with self.assertRaises(m.Block) as c:
            self.try_source(text)
        self.assertEqual(c.exception.rule, rule)

    def test_l1_exact_predicate(self):
        ctx = self.try_source("(110 ((010 000) (001 1)))")
        self.assertIn("L1", [x["rule"] for x in ctx.events])

    def test_l1_truthiness_fails_closed(self):
        self.blocked("(110 ((100 000) (001 1)))", "L1")

    def test_l1_three_part_no_silent_polarity_loss(self):
        self.blocked("(110 ((010 000) 0 (001 1)))", "L1")

    def test_l2_t_only_in_clause(self):
        ctx = self.try_source("(110 (t (001 1)))")
        self.assertIn("L2", [x["rule"] for x in ctx.events])
        self.blocked("(t 000)", "L2")

    def test_l3_no_invented_coordinate(self):
        ctx = m.Context()
        with self.assertRaises(m.Block) as exc:
            m.migrate("(function-without-coordinate 000)", ctx)
        self.assertEqual(exc.exception.rule, "L3")
        self.assertIn("function-without-coordinate", ctx.proposals)

    def test_l4_current_d8_equal(self):
        ctx = self.try_source("(equal? 000 000)")
        self.assertIn("L4", [x["rule"] for x in ctx.events])
        self.assertIn("D8:11110111", [x["detail"].split(" -> ")[-1] for x in ctx.events])

    def test_l4_no_manual_d3_null_guess(self):
        self.blocked("(null 000)", "L4")

    def test_l5_retired_form_blocked(self):
        self.blocked("(structural-kind 000)", "L5")
        self.blocked("(identity-relation 000)", "L5")

    def test_l7_bad_form_kept_out(self):
        self.blocked("(110 (t (001 1))", "L7")

    def test_l6_fixture_blocks_without_touching(self):
        with tempfile.TemporaryDirectory() as tmp:
            original = Path(tmp) / "fixtures" / "old.lisp"
            original.parent.mkdir()
            original.write_text("(110 (t (001 1)))", encoding="utf-8")
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                code = m.main([str(original)])
            self.assertEqual(code, 4)
            self.assertEqual(original.read_text(), "(110 (t (001 1)))")
            record = json.loads(out.getvalue())["results"][0]
            self.assertEqual(record["blocked_rule"], "L6")

    def test_apply_needs_oracle(self):
        with tempfile.TemporaryDirectory() as tmp:
            original = Path(tmp) / "x.lisp"
            original.write_text("(110 (t (001 1)))")
            with contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit):
                    m.main([str(original), "--apply", "--out", str(Path(tmp) / "out")])
            self.assertFalse((Path(tmp) / "out").exists())


    def test_forged_equal_semantic_digests_cannot_approve_apply(self):
        """An executable printing constant matching SHA strings is not an oracle."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source.lisp"
            source.write_text("(110 (t (001 1)))", encoding="utf-8")
            candidate = root / "candidate.sens"
            candidate.write_bytes(m.encode_projection("1\n"))
            fake = root / "fake-oracle"
            fake.write_text(
                "#!/usr/bin/env python3\n"
                "import json\n"
                "print(json.dumps({'source_semantic_sha256': 'a'*64, "
                "'candidate_semantic_sha256': 'a'*64}))\n",
                encoding="utf-8",
            )
            fake.chmod(0o755)
            with self.assertRaises(m.Block) as caught:
                m.run_oracle(fake, source, candidate)
            self.assertEqual(caught.exception.rule, "ORACLE")
            self.assertIn("content-pinned", caught.exception.detail)

if __name__ == "__main__":
    unittest.main()
