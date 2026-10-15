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

# a real guard with a passing negative control
GUARD_OK = """import sys
def check(root):
    return [] if (root / 'ok').exists() else ['bad input rejected']
if __name__ == '__main__':
    raise SystemExit(0 if not check(__import__('pathlib').Path('.')) else 1)
"""
TEST_OK = """import unittest
class T(unittest.TestCase):
    def test_negative(self):
        self.assertTrue(True)
"""


def load():
    spec = importlib.util.spec_from_file_location("sens_unguarding", CHECKER)
    assert spec is not None and spec.loader is not None
    m = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = m
    spec.loader.exec_module(m)
    return m


class UnguardingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "scripts").mkdir(parents=True, exist_ok=True)
        (self.root / "tests").mkdir(parents=True, exist_ok=True)
        self.m = load()

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _guard(self, name: str, body: str, test_body: str | None = TEST_OK) -> None:
        (self.root / "scripts" / name).write_text(body, encoding="utf-8")
        if test_body is not None:
            (self.root / "tests" / f"test_{name}").write_text(test_body, encoding="utf-8")

    def test_real_guard_passes(self) -> None:
        self._guard("check_real.py", GUARD_OK)
        self.assertEqual(self.m.check(self.root), [])

    def test_placeholder_guard_is_unguarding(self) -> None:
        self._guard("check_dummy.py", "# PLACEHOLDER\nimport sys\nsys.exit(0)\n")
        self.assertTrue(self.m.check(self.root))

    def test_guard_without_test_is_unguarding(self) -> None:
        self._guard("check_notest.py", GUARD_OK, test_body=None)
        self.assertTrue(self.m.check(self.root))

    def test_guard_with_failing_controls_is_unguarding(self) -> None:
        self._guard("check_badctl.py", GUARD_OK,
                    test_body="import unittest\nclass T(unittest.TestCase):\n"
                              "    def test_x(self):\n        self.assertTrue(False)\n")
        self.assertTrue(self.m.check(self.root))


if __name__ == "__main__":
    unittest.main()
