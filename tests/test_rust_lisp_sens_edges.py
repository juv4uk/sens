#!/usr/bin/env python3
"""Fail-closed: compile-time Rust → Lisp/SENS edges must stay resolved.

Owner rule: embedded .lisp/.sens/.fasl paths are a named dependency graph.
A deleted or untracked target is an unnamed break (S2). No semantic admission.
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

    def test_repo_edges_ok(self) -> None:
        data = self.mod.inventory(ROOT)
        self.assertEqual(
            data["verdict"],
            "EDGES_OK",
            f"missing={data['missing']} untracked={data['untracked_targets']} "
            f"critical={data['critical_missing']}",
        )
        self.assertGreater(data["edge_count"], 10)
        self.assertGreater(data["rust_files_with_edges"], 3)

    def test_critical_bootstrap_edges_present(self) -> None:
        data = self.mod.inventory(ROOT)
        pairs = {(e["rust"], e["target"]) for e in data["edges"]}
        for rust, target in self.mod.CRITICAL_EDGES:
            self.assertIn(
                (rust, target),
                pairs,
                f"critical embed lost: {rust} → {target}",
            )

    def test_by_rust_lists_sens_cli_repl_libs(self) -> None:
        data = self.mod.inventory(ROOT)
        repl = data["by_rust"].get("crates/sens-cli/src/repl.rs", [])
        self.assertIn("lib/unify.lisp", repl)
        self.assertIn("lib/epistemic.lisp", repl)

    def test_negative_missing_include_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "crates" / "demo" / "src").mkdir(parents=True)
            rs = root / "crates" / "demo" / "src" / "lib.rs"
            rs.write_text(
                'const X: &str = include_str!("../../../lib/does-not-exist.lisp");\n',
                encoding="utf-8",
            )
            real_git = self.mod.git_tracked

            def fake_git(r: Path) -> set[str]:
                return {
                    "crates/demo/src/lib.rs",
                    "lib/does-not-exist.lisp",
                }

            self.mod.git_tracked = fake_git  # type: ignore
            try:
                data = self.mod.inventory(root)
            finally:
                self.mod.git_tracked = real_git  # type: ignore
            self.assertEqual(data["verdict"], "EDGES_BLOCKED")
            self.assertTrue(data["missing"])

    def test_main_exit_zero_on_real_repo(self) -> None:
        code = self.mod.main(["--root", str(ROOT)])
        self.assertEqual(code, 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
