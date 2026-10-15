#!/usr/bin/env python3
"""Controls for the UNGUARDING ratchet (#5777)."""
from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "scripts" / "check_guards_are_real.py"


def load():
    spec = importlib.util.spec_from_file_location("check_guards_are_real", CHECKER)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


class GuardsAreRealTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "scripts").mkdir()
        (self.root / "tests").mkdir()
        self.m = load()

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_placeholder_file_is_unguarding(self) -> None:
        (self.root / "scripts" / "migration-zig-gate.py").write_text(
            "PLACEHOLDER\n", encoding="utf-8")
        problems = self.m.check(self.root)
        self.assertTrue(any("PLACEHOLDER" in p or "stub" in p for p in problems))

    def test_sole_placeholder_chunk_is_unguarding(self) -> None:
        (self.root / "scripts" / "_mg_chunk_1.b64").write_text(
            "PLACEHOLDER1\n", encoding="utf-8")
        problems = self.m.check(self.root)
        self.assertTrue(any("_mg_chunk_1" in p for p in problems))

    def test_thin_base64_loader_is_unguarding(self) -> None:
        (self.root / "scripts" / "migration-zig-gate.py").write_text(
            "import base64\nfrom pathlib import Path\n"
            "code = base64.b64decode(Path('_mg_chunk_0.b64').read_text())\n"
            "exec(code)\n",
            encoding="utf-8",
        )
        problems = self.m.check(self.root)
        self.assertTrue(any("migration-zig-gate" in p for p in problems))

    def test_stub_body_marker_is_unguarding(self) -> None:
        (self.root / "scripts" / "migration-zig-gate.py").write_text(
            '#!/usr/bin/env python3\n'
            'raise SystemExit("MIGRATION_ZIG_GATE_PLACEHOLDER_RESTORE_PENDING")\n',
            encoding="utf-8",
        )
        problems = self.m.check(self.root)
        self.assertTrue(any("stub" in p or "PLACEHOLDER" in p for p in problems))


if __name__ == "__main__":
    unittest.main(verbosity=2)
