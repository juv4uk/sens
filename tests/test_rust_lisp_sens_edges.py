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

    def test_live_repo_has_no_production_lisp_or_sens_embeds(self) -> None:
        """The production Rust boundary is Zig-only; test fixtures are separate."""
        data = self.mod.inventory(ROOT)
        self.assertEqual(data["forbidden_edge_count"], 0, data["edges"])
        self.assertEqual(data["verdict"], "EDGES_OK")
        self.assertEqual(self.mod.main(["--root", str(ROOT)]), 0)

    def test_literal_concat_embeds_are_exact_direct_rust_sens_edges(self) -> None:
        """Compiler expands concat! before embed; split paths must stay RED."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            crate = root / "crates/demo/src"
            crate.mkdir(parents=True)
            (root / "lib").mkdir()
            (root / "lib/core.lisp").write_text("(001)\n", encoding="utf-8")
            (root / "lib/packed.sens").write_bytes(b"\x00")
            source = crate / "lib.rs"
            source.write_text(
                'const A: &str = include_str!(concat!("../../../lib/", "core.lisp"));\n'
                'const B: &[u8] = include_bytes!(concat!("../../../lib/", "packed.sens"));\n'
                'const C: &str = include_str!(concat!("../../../README", ".md"));\n'
                'const D: &str = include_str!("../../../lib/core.lisp");\n',
                encoding="utf-8",
            )
            edges = self.mod.scan_file(source, root)
            self.assertEqual(len(edges), 3, edges)
            self.assertEqual(
                [(edge["kind"], edge["target"], edge["line"]) for edge in edges],
                [
                    ("include_str", "lib/core.lisp", 1),
                    ("include_bytes", "lib/packed.sens", 2),
                    ("include_str", "lib/core.lisp", 4),
                ],
            )
            self.assertTrue(all(edge["exists"] for edge in edges))
            self.assertTrue(all(edge["status"] == "RED" for edge in edges))
            self.assertTrue(all(edge["violation"] == "DIRECT_RUST_PROJECT_EMBED"
                                for edge in edges))

    def test_concat_non_sens_asset_remains_unblocked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            crate = root / "crates/demo/src"
            crate.mkdir(parents=True)
            source = crate / "lib.rs"
            source.write_text(
                'const TEXT: &str = include_str!(concat!("../../../README", ".md"));\n',
                encoding="utf-8",
            )
            self.assertEqual(self.mod.scan_file(source, root), [])

    def test_cfg_test_and_literal_ghosts_cannot_change_live_production_edges(self) -> None:
        """Test-only includes are not production; live includes never disappear."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            crate = root / "crates/demo/src"
            crate.mkdir(parents=True)
            (root / "lib").mkdir()
            (root / "lib/core.lisp").write_text("(001)\n", encoding="utf-8")
            source = crate / "lib.rs"
            source.write_text(
                'const BEFORE: &str = include_str!("../../../lib/core.lisp");\n'
                '// #[cfg(test)] mod fake { include_str!("../../../lib/core.lisp"); }\n'
                'const GHOST: &str = r##"#[cfg(test)] mod fake { include_str!("../../../lib/core.lisp"); }"##;\n'
                '#[cfg(test)] mod tests {\n'
                '    fn nested() { let _ = { include_str!("../../../lib/core.lisp") }; }\n'
                '    fn more() { let _ = include_bytes!(concat!("../../../lib/", "core.lisp")); }\n'
                '}\n'
                'const AFTER: &str = include_str!("../../../lib/core.lisp");\n',
                encoding="utf-8",
            )
            edges = self.mod.scan_file(source, root)
            self.assertEqual(
                [(item["kind"], item["target"], item["line"]) for item in edges],
                [
                    ("include_str", "lib/core.lisp", 1),
                    ("include_str", "lib/core.lisp", 8),
                ],
                edges,
            )

    def test_cfg_condition_not_proven_test_only_remains_red(self) -> None:
        """An unknown cfg(feature/test) branch may compile in production."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            crate = root / "crates/demo/src"
            crate.mkdir(parents=True)
            (root / "lib").mkdir()
            (root / "lib/core.lisp").write_text("(001)\n", encoding="utf-8")
            file = crate / "lib.rs"
            file.write_text(
                '#[cfg(any(test, feature = "host"))] mod uncertain {\n'
                '    const BAD: &str = include_str!("../../../../lib/core.lisp");\n'
                '}\n',
                encoding="utf-8",
            )
            edges = self.mod.scan_file(file, root)
            self.assertEqual(len(edges), 1, edges)
            self.assertEqual(edges[0]["status"], "RED")

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

    def test_uncompiled_staged_out_snapshot_is_not_a_production_edge(self) -> None:
        """Parked Rust snapshots are not compiled by Cargo and must not block isolation."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            parked = root / "crates/demo/src/staged-out"
            parked.mkdir(parents=True)
            (root / "lib").mkdir()
            (root / "lib/core.lisp").write_text("(001)\n", encoding="utf-8")
            path = parked / "old.rs"
            path.write_text(
                'const OLD: &str = include_str!("../../../../lib/core.lisp");\n',
                encoding="utf-8",
            )
            real_git = self.mod.git_tracked
            self.mod.git_tracked = lambda _root: {
                "crates/demo/src/staged-out/old.rs",
                "lib/core.lisp",
            }  # type: ignore[assignment]
            try:
                data = self.mod.inventory(root)
            finally:
                self.mod.git_tracked = real_git  # type: ignore[assignment]
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
