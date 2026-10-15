#!/usr/bin/env python3
"""Negative controls for the corridor axiom-binding guard (#5777/#5779)."""
from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "scripts" / "check_corridor_axiom_binding.py"
BINDING = "research/zig-codecs/corridor_axioms.json"
AXIOMS_DOC = "docs/language-core-axioms.md"


def load_checker():
    spec = importlib.util.spec_from_file_location("sens_corridor_axiom_binding", CHECKER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def mirror(dst: Path) -> None:
    for rel in (BINDING, AXIOMS_DOC):
        target = dst / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text((ROOT / rel).read_text(encoding="utf-8"), encoding="utf-8")
    # guard files named by bindings must exist
    for guard in ("scripts/check_rust_sens_zig_corridor.py",
                  "scripts/check_sterile_zig_corridor.py",
                  "scripts/check_rust_sens_corridor_coverage.py"):
        p = dst / guard
        p.parent.mkdir(parents=True, exist_ok=True)
        if not p.exists():
            p.write_text("# stub\n", encoding="utf-8")


def edit_binding(root: Path, mutate) -> None:
    path = root / BINDING
    data = json.loads(path.read_text(encoding="utf-8"))
    mutate(data)
    path.write_text(json.dumps(data), encoding="utf-8")


class AxiomBindingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        mirror(self.root)
        self.module = load_checker()

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_real_binding_is_ok(self) -> None:
        self.assertEqual(self.module.check(self.root), [])

    def test_unbound_rule_is_blocked(self) -> None:
        edit_binding(self.root, lambda d: d["bindings"].pop())
        self.assertTrue(self.module.check(self.root))

    def test_unknown_axiom_is_blocked(self) -> None:
        edit_binding(self.root, lambda d: d["bindings"][0].update({"axioms": ["G99"]}))
        self.assertTrue(self.module.check(self.root))

    def test_empty_derivation_is_blocked(self) -> None:
        edit_binding(self.root, lambda d: d["bindings"][0].update({"derivation": ""}))
        self.assertTrue(self.module.check(self.root))

    def test_missing_guard_file_is_blocked(self) -> None:
        edit_binding(self.root, lambda d: d["bindings"][0].update({"guard": "scripts/nope.py"}))
        self.assertTrue(self.module.check(self.root))


if __name__ == "__main__":
    unittest.main()
