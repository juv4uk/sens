#!/usr/bin/env python3
"""Zig isolation ratchet: production Rust embeds of SENS sources are RED.

Mechanism tests stay green. The live repository is expected to report a
non-zero forbidden production edge count until cutover; the SCRIPT exit
code is the RED signal for CI. Zero production embeds is the goal
(RUST_ZIG_ONLY / sterile Zig corridor #5777/#5779).
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

    def test_scope_is_production_only(self) -> None:
        data = self.mod.inventory(ROOT)
        self.assertEqual(data["scope"], "production-rust-only")
        for edge in data["edges"]:
            self.assertNotIn("/tests/", f"/{edge['rust']}/")
            self.assertNotIn("/examples/", f"/{edge['rust']}/")

    def test_every_detected_production_embed_is_red(self) -> None:
        data = self.mod.inventory(ROOT)
        self.assertEqual(data["forbidden_edge_count"], len(data["edges"]))
        self.assertEqual(data["forbidden_edges"], data["edges"])
        for edge in data["edges"]:
            self.assertEqual(edge["status"], "RED")
            self.assertEqual(edge["violation"], "DIRECT_RUST_PROJECT_EMBED")

    def test_live_repo_reports_red_debt_until_cutover(self) -> None:
        """Honest RED: debt is visible, not greenwashed."""
        data = self.mod.inventory(ROOT)
        self.assertGreater(
            data["forbidden_edge_count"],
            0,
            "expected production embeds still present as RED isolation debt",
        )
        self.assertEqual(data["verdict"], "EDGES_BLOCKED")
        self.assertEqual(self.mod.main(["--root", str(ROOT)]), 1)

    def test_empty_production_tree_is_ok(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "crates/demo/src").mkdir(parents=True)
            (root / "crates/demo/src/lib.rs").write_text(
                '// isolated: only Zig\nextern "C" { fn sens_zig_t5_encode_be3(); }\n',
                encoding="utf-8",
            )
            real_git = self.mod.git_tracked

            def fake_git(r: Path) -> set[str]:
                return {"crates/demo/src/lib.rs"}

            self.mod.git_tracked = fake_git  # type: ignore
            try:
                data = self.mod.inventory(root)
            finally:
                self.mod.git_tracked = real_git  # type: ignore
            self.assertEqual(data["forbidden_edge_count"], 0)
            self.assertEqual(data["verdict"], "EDGES_OK")

    def test_production_embed_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "crates/demo/src").mkdir(parents=True)
            (root / "lib").mkdir()
            (root / "lib/core.lisp").write_text("(001)\n", encoding="utf-8")
            (root / "crates/demo/src/lib.rs").write_text(
                'const X: &str = include_str!("../../../lib/core.lisp");\n',
                encoding="utf-8",
            )
            real_git = self.mod.git_tracked

            def fake_git(r: Path) -> set[str]:
                return {
                    "crates/demo/src/lib.rs",
                    "lib/core.lisp",
                }

            self.mod.git_tracked = fake_git  # type: ignore
            try:
                data = self.mod.inventory(root)
            finally:
                self.mod.git_tracked = real_git  # type: ignore
            self.assertEqual(data["verdict"], "EDGES_BLOCKED")
            self.assertEqual(data["forbidden_edge_count"], 1)
            self.assertEqual(data["edges"][0]["status"], "RED")


if __name__ == "__main__":
    unittest.main(verbosity=2)
