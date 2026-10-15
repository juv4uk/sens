#!/usr/bin/env python3
"""Negative controls for the axiom-coverage guard (G1-G8, S1-S3)."""
from __future__ import annotations

import importlib.util
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "scripts" / "check_axiom_coverage.py"
DOC = "docs/language-core-axioms.md"
CONF = "tests/fixtures/conformance.lisp"


def load_checker():
    spec = importlib.util.spec_from_file_location("sens_axiom_coverage", CHECKER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def mirror(dst: Path) -> None:
    for rel in (DOC, CONF):
        target = dst / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / rel, target)


class AxiomCoverageTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        mirror(self.root)
        self.module = load_checker()

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_real_coverage_is_complete(self) -> None:
        self.assertEqual(self.module.check(self.root), [])

    def test_invented_axiom_tag_is_blocked(self) -> None:
        path = self.root / CONF
        path.write_text(path.read_text(encoding="utf-8") + "\n((expr . \"x\") (expected . \"y\") (tier . 1) (axioms . (G99)))\n", encoding="utf-8")
        self.assertTrue(self.module.check(self.root))

    def test_uncovered_declared_axiom_is_blocked(self) -> None:
        # declare a new axiom in the doc that no fixture evidences
        doc = self.root / DOC
        doc.write_text(doc.read_text(encoding="utf-8") + "\n### S4 — a new axiom with no fixture\n", encoding="utf-8")
        self.assertTrue(self.module.check(self.root))

    def test_no_fixtures_is_blocked(self) -> None:
        (self.root / CONF).write_text("; empty\n", encoding="utf-8")
        self.assertTrue(self.module.check(self.root))


if __name__ == "__main__":
    unittest.main()
