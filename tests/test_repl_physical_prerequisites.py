"""Nonsemantic, structural guard for the REPL Zig-only physical corridor."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


def check_repl_time_source_ingress(repl: str, core: str) -> None:
    """Reject a REPL that fetches Zig bytes but executes a Rust-embedded copy."""
    expected = (
        ('sens::load_time_library_from_source(&mut session, source)', repl),
        ('pub fn load_time_library_from_source(', core),
        ('parse_mixed_exact_domain_time_source("lib/time.lisp", source)?', core),
    )
    for value, text in expected:
        if value not in text:
            raise ValueError(f"RUST_ZIG_ONLY_TIME_INGRESS missing={value}")
    if 'sens::load_time_library(&mut session)' in repl:
        raise ValueError("RUST_ZIG_ONLY_TIME_INGRESS legacy_time_loader")


class ReplPhysicalPrerquisites(unittest.TestCase):
    def test_repl_time_executes_zig_transported_bytes_via_exact_domain_reader(self):
        repl = (ROOT / "crates/sens-cli/src/repl.rs").read_text(encoding="utf-8")
        core = (ROOT / "crates/sens/src/lib.rs").read_text(encoding="utf-8")
        check_repl_time_source_ingress(repl, core)
        wrong_repl = repl.replace(
            "sens::load_time_library_from_source(&mut session, source)",
            "sens::load_time_library(&mut session)", 1,
        )
        wrong_core = core.replace(
            'parse_mixed_exact_domain_time_source("lib/time.lisp", source)?',
            'parse_mixed_exact_domain_time_source("lib/time.lisp", TIME_LIBRARY_SOURCE)?', 1,
        )
        with self.assertRaisesRegex(ValueError, "RUST_ZIG_ONLY_TIME_INGRESS"):
            check_repl_time_source_ingress(wrong_repl, core)
        with self.assertRaisesRegex(ValueError, "RUST_ZIG_ONLY_TIME_INGRESS"):
            check_repl_time_source_ingress(repl, wrong_core)

    def test_repl_preserves_three_sources_exclusively_through_zig(self):
        files = {name: (ROOT / path).read_text(encoding="utf-8") for name, path in (
            ("repl", "crates/sens-cli/src/repl.rs"),
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
                self.assertIn(f"fn {symbol}(", files["repl"])
                self.assertIn(f'"{filename}"', files["repl"])
                self.assertIn(f'test "REPL {key} exact bytes and untouched short buffer"', files["zig"])
