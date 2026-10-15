"""Nonsemantic, structural guard for the REPL Zig-only physical corridor."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ReplPhysicalPrerquisites(unittest.TestCase):
    def test_repl_preserves_three_sources_exclusively_through_zig(self):
        files = {name: (ROOT / path).read_text(encoding="utf-8") for name, path in (
            ("repl", "crates/sens-cli/src/repl.rs"),
            ("rust", "crates/sens-cli/src/zig_transport.rs"),
            ("ffi", "crates/sens-cli/src/zig_transport_assets.rs"),
            ("zig", "zig_transport_root.zig"),
        )}
        self.assertNotRegex(files["repl"], r"\binclude_(?:str|bytes)!\s*\(")
        self.assertIn("surface_prerequisite_sources()?", files["repl"])
        self.assertIn("prerequisite_sources.iter()", files["repl"])
        for key, filename in (("persistent_vector", "persistent-vector.lisp"),
                              ("time", "time.lisp"),
                              ("epistemic", "epistemic.lisp")):
            with self.subTest(asset=key):
                symbol = f"sens_zig_repl_{key}_bytes_copy"
                self.assertIn(f'@embedFile("lib/{filename}")', files["zig"])
                self.assertIn(f"pub export fn {symbol}", files["zig"])
                self.assertIn(f"pub(super) fn {symbol}", files["ffi"])
                self.assertIn(f"asset_ffi::{symbol}", files["rust"])
                self.assertIn(f'"{filename}"', files["repl"])
                self.assertIn(f'test "REPL {key} exact bytes and untouched short buffer"', files["zig"])
