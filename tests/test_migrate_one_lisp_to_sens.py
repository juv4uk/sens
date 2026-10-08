#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import tempfile
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "migrate-one-lisp-to-sens.py"
SOURCE = ROOT / "lib" / "machine" / "block.lisp"

spec = importlib.util.spec_from_file_location("one_lisp", SCRIPT)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


class OneFileMigrationTests(unittest.TestCase):
    def test_existing_machine_block_is_a_real_migration(self):
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "block.sens"
            result = mod.migrate_one(SOURCE, target, check_only=False)

            self.assertEqual(result["status"], "written")
            self.assertEqual(result["source"], "lib/machine/block.lisp")
            self.assertEqual(result["target"], str(target.relative_to(ROOT)) if target.is_relative_to(ROOT) else str(target))
            self.assertGreater(result["semantic_word_count"], 200)
            self.assertGreater(result["physical_bytes"], 200)
            self.assertEqual(len(result["resolved_heads"]), 17)
            self.assertTrue(target.is_file())
            self.assertFalse((target.parent / "block").exists())

            codec = mod.mod if hasattr(mod, "mod") else None
            physical = target.read_bytes()
            self.assertTrue(all(byte < 243 for byte in physical))
            from sens_t5_codec import decode_bytes
            self.assertEqual(len(decode_bytes(physical)), result["semantic_word_count"])

            source_sha = result["source_sha256"]
            self.assertEqual(source_sha, mod.sha256(SOURCE.read_bytes()).hexdigest())

    def test_check_mode_does_not_write(self):
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "block.sens"
            result = mod.migrate_one(SOURCE, target, check_only=True)
            self.assertEqual(result["status"], "check")
            self.assertFalse(target.exists())

    def test_existing_target_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "block.sens"
            target.write_bytes(b"sentinel")
            with self.assertRaises(SystemExit):
                mod.migrate_one(SOURCE, target, check_only=False)
            self.assertEqual(target.read_bytes(), b"sentinel")


if __name__ == "__main__":
    unittest.main()
