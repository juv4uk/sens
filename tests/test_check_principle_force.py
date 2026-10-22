#!/usr/bin/env python3
"""Negative controls for the principle-force guard (P1-P5, focus on P5)."""
from __future__ import annotations

import importlib.util
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "scripts" / "check_principle_force.py"
REGISTRY = "research/principle-evidence.json"
DOC = "docs/language-core-axioms.md"
CONST = "my-lisp-constitution.lisp"
CONF = "tests/fixtures/conformance.lisp"
ARTIFACTS = (
    "lib/core.lisp", "lib/unify.lisp", "lib/reason.lisp",
    "lib/clips-import.lisp", "lib/understand.lisp", "lib/narrate.lisp",
    "lib/axioms-d1-principle-five.lisp",
)


def load_checker():
    spec = importlib.util.spec_from_file_location("sens_principle_force", CHECKER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def mirror(dst: Path) -> None:
    for rel in (REGISTRY, DOC, CONST, CONF, *ARTIFACTS):
        target = dst / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / rel, target)


def edit_registry(root: Path, mutate) -> None:
    path = root / REGISTRY
    data = json.loads(path.read_text(encoding="utf-8"))
    mutate(data)
    path.write_text(json.dumps(data), encoding="utf-8")


class PrincipleForceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        mirror(self.root)
        self.module = load_checker()

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_real_principles_are_evidenced(self) -> None:
        self.assertEqual(self.module.check(self.root), [])

    def test_p5_missing_artifact_is_blocked(self) -> None:
        (self.root / "lib/clips-import.lisp").unlink()
        self.assertTrue(self.module.check(self.root))

    def test_p5_missing_reversible_is_blocked(self) -> None:
        def drop_reversible(d):
            for b in d["bindings"]:
                if b.get("principle") == 5:
                    b["evidence"] = [e for e in b["evidence"] if e.get("kind") != "reversible"]
        edit_registry(self.root, drop_reversible)
        problems = self.module.check(self.root)
        self.assertTrue(any("reversible" in p for p in problems), problems)

    def test_unbound_principle_is_blocked(self) -> None:
        edit_registry(self.root, lambda d: d["bindings"].pop())
        self.assertTrue(self.module.check(self.root))

    def test_empty_evidence_is_blocked(self) -> None:
        edit_registry(self.root, lambda d: d["bindings"][-1].update({"evidence": []}))
        self.assertTrue(self.module.check(self.root))

    def test_missing_fixture_is_blocked(self) -> None:
        edit_registry(self.root, lambda d: d["bindings"][-1]["evidence"].append(
            {"kind": "fixture", "expr": "(this-fixture-does-not-exist)"}))
        self.assertTrue(self.module.check(self.root))


if __name__ == "__main__":
    unittest.main()
