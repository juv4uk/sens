"""Безпечність двоетапного українського мігратора D1–D11."""
from __future__ import annotations

import importlib.util
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "uk_projection_migration", ROOT / "scripts/audit_ukrainian_domain_projections.py"
)
assert SPEC and SPEC.loader
import sys
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def row(bits: str, uk: str = "так", ukr: str = "так") -> str:
    return (
        f"  ({bits} (ук {uk}) (укр {ukr}) "
        '(san "śānti") (en "latin") (LISP LATIN) (sym ()))\n'
    )


class DomainProjectionMigrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "lib/domains").mkdir(parents=True)
        (self.root / "knowledge").mkdir()
        for width in range(1, 12):
            bits = "0" * width
            value = row(bits, "()" if width == 7 else "так",
                        "()" if width == 7 else "так")
            (self.root / f"lib/domains/d{width}.lisp").write_text(
                "(domain-table/1\n" + value + ")\n", encoding="utf-8"
            )
        table = [{"bits": format(i, "07b"), "uk": chr(i) if i < 32 or i == 127 else "а"}
                 for i in range(128)]
        (self.root / "knowledge/d7-keyboard-v2-ratified.json").write_text(
            json.dumps({"status": "owner-ratified", "width": 7, "table": table},
                       ensure_ascii=False), encoding="utf-8"
        )
        self.d9 = self.root / "lib/domains/d9.lisp"
        self.d9.write_text(
            "(domain-table/1\n" + row("000000000", "json-розібрати") + ")\n",
            encoding="utf-8"
        )
        self.mapping = self.root / "authority.json"
        self.write_mapping([{
            "domain": "D9", "bits": "000000000", "column": "ук",
            "before": "json-розібрати", "after": "розібрати-обмін-даними",
            "authority": "contracts/d9-ratification.lisp + donor semantics"
        }])

    def write_mapping(self, replacements):
        self.mapping.write_text(json.dumps({
            "schema": "ukrainian-projection-authority/1", "replacements": replacements
        }, ensure_ascii=False), encoding="utf-8")

    def run_audit(self, apply=False, use_mapping=True):
        output = io.StringIO()
        with redirect_stdout(output):
            changes = MODULE.execute(
                self.root, self.mapping if use_mapping else None, apply=apply
            )
        return changes, output.getvalue()

    def test_dry_run_reports_coordinate_and_never_writes(self):
        before = {p: p.read_bytes() for p in (self.root / "lib/domains").glob("*.lisp")}
        changes, output = self.run_audit()
        self.assertEqual(len(changes), 1)
        self.assertIn("lib/domains/d9.lisp D9:000000000 column=ук", output)
        self.assertIn("after='розібрати-обмін-даними'", output)
        self.assertIn("DRY_RUN", output)
        self.assertEqual(before, {p: p.read_bytes() for p in before})

    def test_only_selected_columns_and_no_other_files(self):
        outside = self.root / "lib" / "non_domain.lisp"
        outside.write_text("(0011 json-виклик)\n", encoding="utf-8")
        extra = self.root / "lib/domains/d12.lisp"
        extra.write_text(row("0" * 12, "latin"), encoding="utf-8")
        before = self.d9.read_text(encoding="utf-8")
        changes, output = self.run_audit(apply=True)
        self.assertEqual(len(changes), 1)
        after = self.d9.read_text(encoding="utf-8")
        self.assertIn("(ук розібрати-обмін-даними)", after)
        self.assertEqual(
            before.replace("(ук json-розібрати)", "(ук розібрати-обмін-даними)"),
            after,
        )
        self.assertIn('(san "śānti") (en "latin") (LISP LATIN)', after)
        self.assertEqual(outside.read_text(encoding="utf-8"), "(0011 json-виклик)\n")
        self.assertEqual(extra.read_text(encoding="utf-8"), row("0" * 12, "latin"))
        self.assertIn("rewritten_files=1", output)

    def test_idempotent_second_apply(self):
        self.run_audit(apply=True)
        first = self.d9.read_bytes()
        changes, output = self.run_audit(apply=True)
        self.assertEqual(changes, [])
        self.assertIn("findings=0", output)
        self.assertEqual(self.d9.read_bytes(), first)

    def test_ambiguous_manifest_refuses_before_any_write(self):
        item = json.loads(self.mapping.read_text(encoding="utf-8"))["replacements"][0]
        self.write_mapping([item, dict(item, after="інші-дані")])
        before = self.d9.read_bytes()
        with self.assertRaisesRegex(ValueError, "неоднозначна"):
            self.run_audit(apply=True)
        self.assertEqual(self.d9.read_bytes(), before)

    def test_unresolved_replacement_refuses_without_writes(self):
        before = self.d9.read_bytes()
        changes, output = self.run_audit(use_mapping=False)
        self.assertEqual(len(changes), 1)
        self.assertIn("after=None", output)
        with self.assertRaisesRegex(ValueError, "неоднозначних"):
            self.run_audit(apply=True, use_mapping=False)
        self.assertEqual(self.d9.read_bytes(), before)

    def test_stale_manifest_refuses_other_value(self):
        self.d9.write_text(
            "(domain-table/1\n" + row("000000000", "неочікуване-зовнішнє") + ")\n",
            encoding="utf-8"
        )
        before = self.d9.read_bytes()
        with self.assertRaisesRegex(ValueError, "застаріла"):
            self.run_audit(apply=True)
        self.assertEqual(self.d9.read_bytes(), before)

    def test_d7_uses_only_exact_ratified_bits(self):
        d7 = self.root / "lib/domains/d7.lisp"
        d7.write_text(
            "(domain-table/1\n"
            + row("0000000", "()", "()")
            + row("1101101", '"&"', '"&"').replace("(sym ())", '(sym "&")')
            + ")\n", encoding="utf-8"
        )
        table = json.loads(
            (self.root / "knowledge/d7-keyboard-v2-ratified.json").read_text()
        )
        table["table"][int("1101101", 2)]["uk"] = "ь"
        (self.root / "knowledge/d7-keyboard-v2-ratified.json").write_text(
            json.dumps(table, ensure_ascii=False), encoding="utf-8"
        )
        changes, _output = self.run_audit(apply=True)
        self.assertEqual(len([c for c in changes if c.file.endswith("d7.lisp")]), 3)
        self.assertIn('(1101101 (ук "ь") (укр "ь")', d7.read_text(encoding="utf-8"))
        self.assertIn('(sym "ь")', d7.read_text(encoding="utf-8"))


    def test_valid_but_different_d7_glyph_requires_review(self):
        d7 = self.root / "lib/domains/d7.lisp"
        d7.write_text(
            "(domain-table/1\n" + row("0000000", "()", "()")
            + row("1101101", '"а"', '"а"') + ")\n", encoding="utf-8"
        )
        table = json.loads(
            (self.root / "knowledge/d7-keyboard-v2-ratified.json").read_text()
        )
        table["table"][int("1101101", 2)]["uk"] = "ь"
        (self.root / "knowledge/d7-keyboard-v2-ratified.json").write_text(
            json.dumps(table, ensure_ascii=False), encoding="utf-8"
        )
        before = d7.read_bytes()
        changes, output = self.run_audit()
        self.assertTrue(any(c.after is None and c.coordinate == "D7:1101101"
                            for c in changes))
        self.assertIn("потрібне уточнення власника", output)
        with self.assertRaisesRegex(ValueError, "неоднозначних"):
            self.run_audit(apply=True)
        self.assertEqual(d7.read_bytes(), before)

    def test_apply_preserves_original_file_mode(self):
        import stat
        self.d9.chmod(0o644)
        self.run_audit(apply=True)
        self.assertEqual(stat.S_IMODE(self.d9.stat().st_mode), 0o644)

    def test_target_symlink_outside_root_refused(self):
        external = self.root.parent / f"{self.root.name}-out-of-scope.lisp"
        external.write_text("(external text)\n", encoding="utf-8")
        self.addCleanup(external.unlink)
        d5 = self.root / "lib/domains/d5.lisp"
        d5.unlink()
        d5.symlink_to(external)
        before = external.read_bytes()
        with self.assertRaisesRegex(ValueError, "виходить за --root"):
            self.run_audit(apply=True)
        self.assertEqual(external.read_bytes(), before)



if __name__ == "__main__":
    unittest.main(verbosity=2)
