"""Negative gates for asset completeness, integrity and provenance."""

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from verify_release_assets import _expected, prepare, verify_replay

TAG = "l0.42.0"
SHA = "a" * 40


class ReleaseAssetsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.dist = self.root / "dist"
        self.dist.mkdir()
        for name in _expected(TAG):
            (self.dist / name).write_bytes(b"fake test fixture for " + name.encode())

    def replay(self):
        target = self.root / "downloaded"
        shutil.copytree(self.dist, target)
        return target

    def test_complete_success(self):
        prepare(self.dist, TAG, SHA)
        self.assertEqual(verify_replay(self.dist, self.replay(), TAG, SHA), 8)

    def test_missing_msi_rejected(self):
        (self.dist / "sens-cli_0.42.0_windows_x64.msi").unlink()
        with self.assertRaisesRegex(ValueError, "missing"):
            prepare(self.dist, TAG, SHA)

    def test_extra_artifact_rejected(self):
        (self.dist / "unknown.exe").write_bytes(b"bad")
        with self.assertRaisesRegex(ValueError, "extra"):
            prepare(self.dist, TAG, SHA)

    def test_empty_artifact_rejected(self):
        (self.dist / "sens-cli-web.html").write_bytes(b"")
        with self.assertRaisesRegex(ValueError, "empty"):
            prepare(self.dist, TAG, SHA)

    def test_bad_downloaded_checksum_rejected(self):
        prepare(self.dist, TAG, SHA)
        replay = self.replay()
        (replay / "sens-cli-web.html").write_bytes(b"corrupt")
        with self.assertRaisesRegex(ValueError, "digest/size mismatch"):
            verify_replay(self.dist, replay, TAG, SHA)

    def test_tampered_both_checksums_rejected(self):
        prepare(self.dist, TAG, SHA)
        replay = self.replay()
        for root in (self.dist, replay):
            (root / "SHA256SUMS").write_text("bad\n", encoding="ascii")
        with self.assertRaisesRegex(ValueError, "SHA256SUMS mismatch"):
            verify_replay(self.dist, replay, TAG, SHA)

    def test_wrong_candidate_sha_rejected(self):
        prepare(self.dist, TAG, SHA)
        with self.assertRaisesRegex(ValueError, "identity mismatch"):
            verify_replay(self.dist, self.replay(), TAG, "b" * 40)

    def test_wrong_tag_rejected(self):
        with self.assertRaisesRegex(ValueError, "malformed release tag"):
            prepare(self.dist, "main", SHA)

    def test_symlink_rejected(self):
        target = self.dist / "sens-cli-web.html"
        target.unlink()
        target.symlink_to(self.dist / "install.sh")
        with self.assertRaisesRegex(ValueError, "invalid"):
            prepare(self.dist, TAG, SHA)


class ReleaseWorkflowOrderingTest(unittest.TestCase):
    """Keep the workflow's last-moment SHA/owner-authorization barrier covered."""

    def test_main_sha_and_owner_go_are_rechecked_after_replay_before_publish(self):
        root = Path(__file__).resolve().parents[1]
        workflow = (root / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8")

        replay = workflow.rfind("python3 scripts/verify_release_assets.py replay")
        publish = workflow.rfind('gh release edit "$GITHUB_REF_NAME" --draft=false')
        last_fetch = workflow.rfind("git fetch --no-tags --depth=1 origin main")
        last_compare = workflow.rfind('test "$(git rev-parse FETCH_HEAD)" = "$GITHUB_SHA"')

        self.assertGreaterEqual(replay, 0, "draft replay verifier is required")
        self.assertGreater(last_fetch, replay, "main must be refetched after byte replay")
        self.assertGreater(last_compare, last_fetch, "fresh main ref must be compared to tagged SHA")
        self.assertGreater(publish, last_compare, "nothing may publish before the final SHA guard")
        final_guard = workflow[last_fetch:publish]
        self.assertIn("RELEASE_GO_SHA", final_guard)
        self.assertIn("RELEASE_GO_TAG", final_guard)
        self.assertIn("RELEASE_BLOCKED", final_guard)




class TaggedReleaseVersionGuardTests(unittest.TestCase):
    """Exercise the real release.yml tag/version gate, including Python -O."""

    def test_tag_guard_has_positive_and_negative_optimized_receipts(self):
        import os
        import re
        import subprocess
        import textwrap
        import tomllib

        root = Path(__file__).resolve().parents[1]
        workflow = (root / ".github" / "workflows" / "release.yml").read_text(
            encoding="utf-8"
        )
        # Test the same inline Python snippet executed by the tagged workflow;
        # a stale test-specific rewrite must not mask a weakened production gate.
        match = re.search(
            r"^          python3 - <<'PY'\n(.*?)^          PY$",
            workflow,
            flags=re.MULTILINE | re.DOTALL,
        )
        self.assertIsNotNone(match, "RELEASE_BLOCKED: tag preflight missing")
        code = textwrap.dedent(match.group(1))
        version = tomllib.loads(
            (root / "crates/sens-cli/Cargo.toml").read_text(encoding="utf-8")
        )["package"]["version"]
        cases = (
            ("l" + version, True),
            ("v" + version, False),
            ("l0.0.0", False),
        )
        for tag, should_pass in cases:
            with self.subTest(tag=tag):
                result = subprocess.run(
                    [sys.executable, "-O", "-c", code],
                    cwd=root,
                    env={**os.environ, "RELEASE_TAG": tag},
                    text=True,
                    capture_output=True,
                    timeout=10,
                )
                if should_pass:
                    self.assertEqual(result.returncode, 0, result.stderr)
                else:
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn("RELEASE_BLOCKED", result.stderr)

if __name__ == "__main__":
    unittest.main()
