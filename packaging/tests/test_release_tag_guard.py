"""Regression suite for optimization-resistant release tag checks."""

import subprocess
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from verify_release_tag import verify_release_tag


class ReleaseTagGuardTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        manifest = self.root / "crates" / "sens-cli" / "Cargo.toml"
        manifest.parent.mkdir(parents=True)
        manifest.write_text(
            '[package]\nname = "sens-cli"\nversion = "0.42.0"\n', encoding="utf-8"
        )

    def test_exact_tag_accepted(self):
        self.assertEqual(verify_release_tag("s0.42.0", self.root), "0.42.0")

    def test_other_tag_rejected(self):
        with self.assertRaisesRegex(ValueError, "RELEASE_BLOCKED"):
            verify_release_tag("s0.41.0", self.root)

    def test_malformed_tag_rejected(self):
        for tag in ("v0.42.0", "l0.42.0", "s0.42", "s00.42.0", "s0.42.0-dev", ""):
            with self.subTest(tag=tag), self.assertRaisesRegex(ValueError, "RELEASE_BLOCKED"):
                verify_release_tag(tag, self.root)

    def test_python_optimized_does_not_bypass_negative_guard(self):
        script = ROOT / "scripts" / "verify_release_tag.py"
        result = subprocess.run(
            [sys.executable, "-O", str(script), "s999.999.999"],
            capture_output=True, text=True, check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("RELEASE_BLOCKED", result.stderr)

    def test_python_optimized_accepts_current_matching_tag(self):
        current = tomllib.loads(
            (ROOT / "crates" / "sens-cli" / "Cargo.toml").read_text(encoding="utf-8")
        )
        script = ROOT / "scripts" / "verify_release_tag.py"
        result = subprocess.run(
            [sys.executable, "-O", str(script), "s" + current["package"]["version"]],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("RELEASE_TAG_VERSION_PASS", result.stdout)


if __name__ == "__main__":
    unittest.main()
