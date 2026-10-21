"""Regression tests for the read-only D1–D10 candidate discovery tool."""
from __future__ import annotations

import contextlib
import csv
import importlib.util
import io
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "discover_domain_function_candidates.py"
SPEC = importlib.util.spec_from_file_location("discover_domain_function_candidates", SCRIPT)
assert SPEC and SPEC.loader
MOD = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MOD
SPEC.loader.exec_module(MOD)


def write_fixture_repo(root: Path) -> Path:
    """Build the complete 2046-cell shape with a few named candidate rows."""
    (root / "lib" / "domains").mkdir(parents=True)
    for domain in range(1, 11):
        path = root / "lib" / "domains" / f"d{domain}.lisp"
        lines = ["(domain-table-1"]
        for value in range(1 << domain):
            bits = format(value, f"0{domain}b")
            en = f"D{domain}-CELL-{bits}"
            lisp = en
            if domain == 3 and bits == "000":
                uk = ukr = san = en = lisp = sym = "()"
            elif domain == 6 and bits == "000000":
                uk = ukr = san = en = lisp = sym = "()"
            elif domain == 6 and bits == "001011":
                en = lisp = "COMPOSE"
                uk = ukr = "скласти-функції"
                san = "phalana-saṃyojana"
                sym = "оо"
            elif domain == 7:
                uk = ukr = san = en = lisp = "DATA"
                sym = '"x"'
            else:
                uk = ukr = f"uk-{domain}-{bits}"
                san = f"san-{domain}-{bits}"
                sym = f"sym-{domain}-{bits}"
            lines.append(
                f"  ({bits} (ук {uk}) (укр {ukr}) (san {san}) "
                f"(en {en}) (LISP {lisp}) (sym {sym}))"
            )
        lines.append(")")
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    source = root / "lib" / "definitions.lisp"
    source.write_text(
        "(0011 compose (0010 (f g) f))\n"
        "; (0011 fake-comment (0010 () ()))\n"
        '"(0011 fake-string (0010 () ()))"\n'
        "'(0011 fake-quoted (0010 () ()))\n"
        "(outer (0011 fake-nested (0010 () ())))\n",
        encoding="utf-8",
    )
    research = root / "docs" / "research"
    research.mkdir(parents=True)
    (research / "compose.md").write_text(
        "Archived law candidate COMPOSE has a positive example and a separate falsifier.\n",
        encoding="utf-8",
    )
    witness = root / "tests" / "semantic"
    witness.mkdir(parents=True)
    (witness / "compose-law.lisp").write_text(
        "(list (compose first rest) (not? (compose first rest)))\\n",
        encoding="utf-8",
    )
    return root


class CandidateDiscoveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._temp = tempfile.TemporaryDirectory(prefix="sens-function-candidates-")
        cls.root = write_fixture_repo(Path(cls._temp.name))

    @classmethod
    def tearDownClass(cls):
        cls._temp.cleanup()

    def test_all_ten_maps_have_exact_width_and_complete_unique_spaces(self):
        maps = MOD.load_domain_tables(self.root)
        self.assertEqual(sum(len(rows) for rows in maps.values()), 2046)
        for domain in range(1, 11):
            rows = maps[domain]
            self.assertEqual(len(rows), 1 << domain)
            self.assertEqual({row["bits"] for row in rows},
                             {format(value, f"0{domain}b") for value in range(1 << domain)})

    def test_d1_d2_d7_never_become_function_candidates(self):
        report = MOD.discover(self.root, scan_research=False)
        by_identity = {row["identity"]: row for row in report}
        self.assertFalse(by_identity["D1:1"]["function_candidate"])
        self.assertEqual(by_identity["D1:1"]["object_kind"], "predicate-bit-not-a-function-table")
        self.assertFalse(by_identity["D2:10"]["function_candidate"])
        self.assertFalse(by_identity["D7:0000000"]["function_candidate"])
        self.assertEqual(by_identity["D7:0000000"]["callability"], "NOT_ASSERTED")

    def test_empty_d3_coordinate_is_structural_not_a_function(self):
        report = MOD.discover(self.root, scan_research=False)
        empty = next(row for row in report if row["identity"] == "D3:000")
        self.assertEqual(empty["lisp"], "()")
        self.assertEqual(empty["object_kind"], "structural-empty-not-a-function")
        self.assertFalse(empty["function_candidate"])

    def test_definition_source_is_not_inferred_from_comment_string_or_nested_form(self):
        definitions = MOD.find_active_sens_definitions(self.root)
        self.assertIn("compose", definitions)
        for fake in ("fake-comment", "fake-string", "fake-quoted", "fake-nested"):
            self.assertNotIn(fake, definitions)

    def test_research_mention_and_source_definition_never_assert_callability(self):
        report = MOD.discover(self.root, scan_research=True)
        compose = next(row for row in report if row["identity"] == "D6:001011")
        self.assertTrue(compose["function_candidate"])
        self.assertEqual(compose["source_definition_paths"], ["lib/definitions.lisp"])
        self.assertEqual(compose["research_mention_files"], 1)
        self.assertEqual(compose["research_paths"], ["docs/research/compose.md"])
        self.assertEqual(compose["witness_reference_files"], 1)
        self.assertEqual(compose["witness_reference_paths"], ["tests/semantic/compose-law.lisp"])
        self.assertFalse(compose["witness_references_are_proofs"])
        self.assertEqual(compose["callability"], "NOT_ASSERTED")
        self.assertIn("native SENS witnesses", compose["next_step"])

    def test_duplicate_and_missing_coordinates_fail_closed(self):
        table = self.root / "lib" / "domains" / "d3.lisp"
        original = table.read_text(encoding="utf-8")
        duplicate = original.replace(
            "  (000 (ук ()) (укр ()) (san ()) (en ()) (LISP ()) (sym ()))",
            "  (001 (ук ()) (укр ()) (san ()) (en ()) (LISP ()) (sym ()))",
            1,
        )
        table.write_text(duplicate, encoding="utf-8")
        try:
            with self.assertRaises(MOD.AuditError):
                MOD.load_domain_tables(self.root)
        finally:
            table.write_text(original, encoding="utf-8")

    def test_batch_cli_limits_rows_and_keeps_domain_qualified_bits(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            status = MOD.main([
                "--root", str(self.root), "--domain", "D6", "--limit", "1",
                "--format", "tsv", "--no-research-scan",
            ])
        self.assertEqual(status, 0)
        parsed = list(csv.DictReader(io.StringIO(out.getvalue()), delimiter="\t"))
        self.assertEqual(len(parsed), 1)
        self.assertEqual(parsed[0]["identity"], "D6:000000")
        self.assertEqual(parsed[0]["width"], "6")
        self.assertEqual(parsed[0]["callability"], "NOT_ASSERTED")

    def test_candidates_only_filters_before_batch_limit(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            status = MOD.main([
                "--root", str(self.root), "--domain", "D6", "--limit", "1",
                "--format", "tsv", "--no-research-scan", "--candidates-only",
            ])
        self.assertEqual(status, 0)
        parsed = list(csv.DictReader(io.StringIO(out.getvalue()), delimiter="\t"))
        self.assertEqual(len(parsed), 1)
        self.assertEqual(parsed[0]["identity"], "D6:000001")
        self.assertEqual(parsed[0]["function_candidate"], "True")
        self.assertEqual(parsed[0]["callability"], "NOT_ASSERTED")

    def test_evidence_first_batch_prefers_existing_definition_and_witness_reference(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            status = MOD.main([
                "--root", str(self.root), "--domain", "D6", "--limit", "1",
                "--format", "tsv", "--no-research-scan", "--candidates-only",
                "--evidence-first",
            ])
        self.assertEqual(status, 0)
        parsed = list(csv.DictReader(io.StringIO(out.getvalue()), delimiter="\t"))
        self.assertEqual(len(parsed), 1)
        self.assertEqual(parsed[0]["identity"], "D6:001011")
        self.assertEqual(parsed[0]["source_definition_paths"], "lib/definitions.lisp")
        self.assertEqual(parsed[0]["witness_reference_paths"], "tests/semantic/compose-law.lisp")
        self.assertEqual(parsed[0]["witness_references_are_proofs"], "False")
        self.assertEqual(parsed[0]["callability"], "NOT_ASSERTED")

    @unittest.skipUnless((ROOT / "lib" / "domains" / "d1.lisp").is_file(),
                         "repository tables are only available in the full checkout")
    def test_real_repository_shape_smoke(self):
        maps = MOD.load_domain_tables(ROOT)
        self.assertEqual(sum(len(rows) for rows in maps.values()), 2046)
        self.assertEqual(next(row for row in maps[3] if row["bits"] == "000")["LISP"], "()")
        self.assertEqual(next(row for row in maps[10] if row["bits"] == "0000000000")["domain"], 10)


if __name__ == "__main__":
    unittest.main(verbosity=2)
