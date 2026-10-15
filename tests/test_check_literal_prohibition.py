#!/usr/bin/env python3
"""Negative controls for the literal-prohibition guard (owner forbade #…:)."""
from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "scripts" / "check_literal_prohibition.py"
REGISTRY = "research/literal-prohibition.json"


def load_checker():
    spec = importlib.util.spec_from_file_location("sens_literal_prohibition", CHECKER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def write_registry(root: Path) -> None:
    path = root / REGISTRY
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({
        "owner_rule": "literals forbidden",
        "canonical_d1": "bare 0/1",
        "ratified_roles": [
            {"prefix": "d1", "status": "debt"},
            {"prefix": "d", "status": "ratified"},
            {"prefix": "b", "status": "ratified"},
            {"prefix": "q2", "status": "ratified"},
            {"prefix": "t7", "status": "ratified"},
            {"prefix": "f32", "status": "ratified"},
        ],
        "scan": {"lib_glob": "lib/**/*.lisp"},
    }), encoding="utf-8")


def write_lib(root: Path, body: str) -> None:
    d = root / "lib"
    d.mkdir(parents=True, exist_ok=True)
    (d / "x.lisp").write_text(body, encoding="utf-8")


class LiteralProhibitionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        write_registry(self.root)
        self.module = load_checker()

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_named_roles_pass(self) -> None:
        write_lib(self.root, "(f #d1:0 #b1010 #q2:1/2 #d24:000000000000000000000001)")
        self.assertEqual(self.module.check(self.root), [])

    def test_new_unratified_prefix_is_blocked(self) -> None:
        write_lib(self.root, "(f #d2:01)")
        self.assertTrue(self.module.check(self.root))

    def test_arbitrary_hash_prefix_is_blocked(self) -> None:
        write_lib(self.root, "(f #foo:bar)")
        self.assertTrue(self.module.check(self.root))

    def test_non_d24_width_is_blocked(self) -> None:
        write_lib(self.root, "(f #d10:0000000000)")
        self.assertTrue(self.module.check(self.root))

    def test_missing_owner_rule_is_blocked(self) -> None:
        (self.root / REGISTRY).write_text(json.dumps({"ratified_roles": []}), encoding="utf-8")
        write_lib(self.root, "(f #d1:0)")
        self.assertTrue(self.module.check(self.root))


if __name__ == "__main__":
    unittest.main()
