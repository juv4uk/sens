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
                  "scripts/check_rust_sens_corridor_coverage.py",
                  "scripts/check_migration_zig_only_path.py"):
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

    def test_real_migration_zig_guard_missing_fails_closed(self) -> None:
        # Missing real M1 must fail, not turn the original broken mirror into
        # false evidence that the canonical axiom binding itself is defective.
        guard = self.root / "scripts/check_migration_zig_only_path.py"
        guard.unlink()
        self.assertTrue(any(
            "M1-migration-zig-only-path" in msg and "does not exist" in msg
            for msg in self.module.check(self.root)
        ))


    def test_duplicate_rule_is_blocked(self) -> None:
        edit_binding(self.root, lambda d: d["bindings"].append(dict(d["bindings"][0])))
        self.assertTrue(any("duplicate bindings" in p for p in self.module.check(self.root)))

    def test_unknown_rule_is_blocked(self) -> None:
        edit_binding(self.root, lambda d: d["bindings"].append({
            "rule": "R6-fictitious", "guard": "scripts/check_sterile_zig_corridor.py",
            "axioms": ["G6"], "derivation": "improper extra guard"
        }))
        self.assertTrue(any("unknown corridor rule" in p for p in self.module.check(self.root)))

    def test_rule_cannot_point_to_another_existing_guard(self) -> None:
        # R1's real owner is check_sterile_zig_corridor.py. Mutate to a
        # DIFFERENT existing owner; a no-op cannot be a negative witness.
        edit_binding(self.root, lambda d: d["bindings"][0].update({
            "guard": "scripts/check_rust_sens_zig_corridor.py"
        }))
        self.assertTrue(any("must use its actual guard" in p for p in self.module.check(self.root)))

    def test_empty_guard_is_blocked(self) -> None:
        edit_binding(self.root, lambda d: d["bindings"][0].update({"guard": ""}))
        self.assertTrue(any("must use its actual guard" in p for p in self.module.check(self.root)))

    def test_axiom_source_cannot_be_swapped(self) -> None:
        edit_binding(self.root, lambda d: d.update({"axioms_doc": "docs/substitute.md"}))
        (self.root / "docs/substitute.md").write_text("### G6 spoofed\n", encoding="utf-8")
        self.assertTrue(any("source must be pinned" in p for p in self.module.check(self.root)))

    def test_schema_drift_is_blocked(self) -> None:
        edit_binding(self.root, lambda d: d.update({"schema": "unstable-fake-schema"}))
        self.assertTrue(any("schema is not" in p for p in self.module.check(self.root)))

    def test_malformed_bindings_are_blocked(self) -> None:
        edit_binding(self.root, lambda d: d.update({"bindings": None}))
        self.assertTrue(any("must be a list" in p for p in self.module.check(self.root)))

    def test_duplicate_root_axiom_source_is_blocked(self) -> None:
        # Even if the last key names the ratified source, the record has two
        # competing meanings and must not become an axiom provenance receipt.
        path = self.root / BINDING
        raw = path.read_text(encoding="utf-8")
        self.assertIn('"axioms_doc":', raw)
        path.write_text(
            raw.replace('"axioms_doc":', '"axioms_doc": "docs/fake.md", "axioms_doc":', 1),
            encoding="utf-8",
        )
        with self.assertRaisesRegex(ValueError, "duplicate JSON key 'axioms_doc'"):
            self.module.check(self.root)

    def test_duplicate_nested_guard_is_blocked_with_named_cli_diagnostic(self) -> None:
        import subprocess

        path = self.root / BINDING
        raw = path.read_text(encoding="utf-8")
        self.assertIn('"guard":', raw)
        path.write_text(
            raw.replace('"guard":', '"guard": "scripts/fake.py", "guard":', 1),
            encoding="utf-8",
        )
        with self.assertRaisesRegex(ValueError, "duplicate JSON key 'guard'"):
            self.module.check(self.root)
        completed = subprocess.run(
            [sys.executable, str(CHECKER), str(self.root)],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(completed.returncode, 1)
        self.assertIn("AXIOM_BINDING_BLOCKED malformed input", completed.stdout)
        self.assertIn("duplicate JSON key 'guard'", completed.stdout)

    def test_malformed_json_fails_with_named_diagnostic(self) -> None:
        (self.root / BINDING).write_text("{", encoding="utf-8")
        # CLI exception handling rather than an uncontrolled traceback.
        import subprocess
        result = subprocess.run([sys.executable, str(CHECKER), str(self.root)],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertIn("AXIOM_BINDING_BLOCKED malformed input", result.stdout)



if __name__ == "__main__":
    unittest.main()
