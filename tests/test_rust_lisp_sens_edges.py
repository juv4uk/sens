#!/usr/bin/env python3
"""Red until Rust has ZERO compile-time project-source embeds.

No Rust -> .lisp/.sens/.fasl edge is allowed, including historical bootstrap.
Only the Zig corridor may bridge physical bytes. This test deliberately fails
on the currently populated repository; the negative fixture tests stay green.
"""
from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "rust_lisp_sens_edges.py"


def load_module():
    spec = importlib.util.spec_from_file_location("rust_lisp_sens_edges", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


class RustLispSensEdgesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.mod = load_module()

    def test_repository_has_zero_direct_rust_project_edges(self) -> None:
        data = self.mod.inventory(ROOT)
        examples = [
            f"{edge['rust']}:{edge['line']} -> {edge['target']}"
            for edge in data["forbidden_edges"][:20]
        ]
        self.assertEqual(
            data["forbidden_edge_count"],
            0,
            f"RUST_ZIG_ONLY_RED: {data['forbidden_edge_count']} forbidden Rust->SENS "
            f"embeds; first examples={examples}; "
            "repro: python3 scripts/rust_lisp_sens_edges.py --by-rust",
        )
        self.assertEqual(data["verdict"], "EDGES_OK")

    def test_every_detected_embed_is_red_without_exemptions(self) -> None:
        data = self.mod.inventory(ROOT)
        self.assertEqual(data["forbidden_edge_count"], len(data["edges"]))
        self.assertEqual(data["forbidden_edges"], data["edges"])
        for edge in data["edges"]:
            self.assertEqual(edge["status"], "RED")
            self.assertEqual(edge["violation"], "DIRECT_RUST_PROJECT_EMBED")
            self.assertIn(edge["target"], data["by_rust"][edge["rust"]])

    def test_existing_tracked_embed_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "crates/demo/src").mkdir(parents=True)
            (root / "lib").mkdir()
            (root / "lib/core.lisp").write_text("(001 000)\n", encoding="utf-8")
            (root / "crates/demo/src/lib.rs").write_text(
                'const X: &str = include_str!("../../../lib/core.lisp");\n',
                encoding="utf-8",
            )
            original = self.mod.git_tracked
            self.mod.git_tracked = lambda _: {
                "crates/demo/src/lib.rs", "lib/core.lisp"
            }
            try:
                data = self.mod.inventory(root)
            finally:
                self.mod.git_tracked = original
            self.assertEqual(data["verdict"], "EDGES_BLOCKED")
            self.assertEqual(data["forbidden_edge_count"], 1)
            self.assertFalse(data["missing"])
            self.assertFalse(data["untracked_targets"])

    def test_missing_include_is_also_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "crates/demo/src").mkdir(parents=True)
            (root / "crates/demo/src/lib.rs").write_text(
                'const X: &str = include_bytes!("../../../lib/absent.sens");\n',
                encoding="utf-8",
            )
            original = self.mod.git_tracked
            self.mod.git_tracked = lambda _: {
                "crates/demo/src/lib.rs", "lib/absent.sens"
            }
            try:
                data = self.mod.inventory(root)
            finally:
                self.mod.git_tracked = original
            self.assertEqual(data["verdict"], "EDGES_BLOCKED")
            self.assertEqual(data["forbidden_edge_count"], 1)
            self.assertTrue(data["missing"])

    def test_empty_source_tree_has_no_direct_embeds(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            original = self.mod.git_tracked
            self.mod.git_tracked = lambda _: set()
            try:
                data = self.mod.inventory(root)
            finally:
                self.mod.git_tracked = original
            self.assertEqual(data["verdict"], "EDGES_OK")
            self.assertEqual(data["forbidden_edge_count"], 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
