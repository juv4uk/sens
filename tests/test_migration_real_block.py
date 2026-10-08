#!/usr/bin/env python3
"""Regression guard for the real historical machine-block physical witness.

The paired .sens is admitted only through the proof-carrying release gate:
source SHA + physical/typed digests + real Rust D2 + current pure-SENS runtime +
independent historical/current oracle parity. This unit test validates the
immutable source/fixture side without becoming a semantic authority itself.
"""
from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "lib/machine/block.lisp"
SENS = ROOT / "lib/machine/block.sens"
SOURCE_GIT_BLOB = "200201b741787c4e144ad4194848acf51d7b439e"
PHYSICAL_SHA256 = "1540c7e9a69c7dcb953713469a2c6ac803ae5aebfc40e2cd1ab529e66f0271"
EXPECTED_BYTES = 343


class RealBlockProofFixtureTests(unittest.TestCase):
    def test_source_is_immutable_and_physical_pair_is_real_binary(self):
        self.assertTrue(SOURCE.is_file())
        self.assertTrue(SENS.is_file())
        source_blob = subprocess.run(
            ["git", "hash-object", "lib/machine/block.lisp"],
            cwd=ROOT, capture_output=True, text=True, check=True,
        ).stdout.strip()
        self.assertEqual(source_blob, SOURCE_GIT_BLOB)
        payload = SENS.read_bytes()
        self.assertEqual(len(payload), EXPECTED_BYTES)
        self.assertEqual(hashlib.sha256(payload).hexdigest(), PHYSICAL_SHA256)
        self.assertNotRegex(payload.decode("utf-8", "ignore"), r"^[012\\s]+$")


if __name__ == "__main__":
    unittest.main()
