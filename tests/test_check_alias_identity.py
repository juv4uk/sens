#!/usr/bin/env python3
"""Controls for the alias-identity guard (#5609)."""
from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "scripts" / "check_alias_identity.py"


def load():
    spec = importlib.util.spec_from_file_location("sens_alias_identity", CHECKER)
    assert spec is not None and spec.loader is not None
    m = importlib.util.module_from_spec(spec); sys.modules[spec.name] = m
    spec.loader.exec_module(m); return m


class AliasIdentityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "lib/surface").mkdir(parents=True, exist_ok=True)
        self.m = load()

    def tearDown(self):
        self.tmp.cleanup()

    def _write(self, body: str) -> None:
        (self.root / "lib/surface/semantic-registry.lisp").write_text(body, encoding="utf-8")

    def test_unique_aliases_pass(self) -> None:
        self._write("(\n  (00000001 (en quote) (ук як-є) (укр як-є) (sa svarupa) (sym '))\n"
                    "  (00000010 (en atom?) (ук атом?) (укр атом?) (sa anu) (sym .?))\n)\n")
        self.assertEqual(self.m.check(self.root), [])

    def test_ambiguous_human_alias_fails(self) -> None:
        self._write("(\n  (00000001 (en quote) (ук спільне) (укр x) (sa a) (sym '))\n"
                    "  (00000010 (en atom?) (ук спільне) (укр y) (sa b) (sym .?))\n)\n")
        self.assertTrue(self.m.check(self.root))

    def test_duplicate_en_name_fails(self) -> None:
        self._write("(\n  (00000001 (en car) (ук перше) (укр перше) (sa a) (sym :п))\n"
                    "  (00000010 (en car) (ук інше) (укр інше) (sa b) (sym :і))\n)\n")
        self.assertTrue(self.m.check(self.root))

    def test_empty_slots_are_not_aliases(self) -> None:
        self._write("(\n  (00000000 (en ()) (ук ()) (укр ()) (sa ()) (sym ()))\n"
                    "  (00000001 (en quote) (ук як-є) (укр як-є) (sa svarupa) (sym '))\n)\n")
        self.assertEqual(self.m.check(self.root), [])


if __name__ == "__main__":
    unittest.main()
