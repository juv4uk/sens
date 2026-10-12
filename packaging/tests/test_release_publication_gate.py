"""Fail-closed regression guards for SENS's one-shot release publication.

Replays the actual asset verifier embedded in .github/workflows/release.yml
on synthetic files. No tags or releases are created. It does not replace
exact-SHA hosted release evidence.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import textwrap
import unittest

WORKFLOW = Path(__file__).resolve().parents[2] / ".github/workflows/release.yml"
TAG = "l0.42.0"
SHA = "a" * 40


def required_assets(tag: str) -> set[str]:
    version = tag.removeprefix("l")
    return {
        f"sens-cli_{version}_linux_amd64",
        f"sens-cli_{version}_windows_x64.exe",
        f"sens-cli_{version}_windows_x64.msi",
        f"sens-cli_{version}_macos_x64",
        f"sens-cli_{version}_macos_arm64",
        "sens-cli-web.html",
        "islands-manifest-v1.json",
        "install.sh",
    }


def release_job(workflow: str) -> str:
    match = re.search(r"^  release-publish:\s*$", workflow, re.MULTILINE)
    if not match:
        raise ValueError("RELEASE_BLOCKED: final publication job missing")
    end = re.search(r"^  [a-zA-Z][\w-]*:\s*$", workflow[match.end():], re.MULTILINE)
    return workflow[match.start():match.end() + end.start() if end else len(workflow)]


def check_release_workflow(workflow: str) -> None:
    job = release_job(workflow)
    mandatory = (
        "needs: [test, publish-island-manifest, build-cli, build-msi, build-web]",
        "RELEASE_GO_SHA: $" + "{{ vars.SENS_RELEASE_GO_SHA }}",
        "RELEASE_GO_TAG: $" + "{{ vars.SENS_RELEASE_GO_TAG }}",
        'test "$(git rev-parse FETCH_HEAD)" = "$GITHUB_SHA"',
        "actions/download-artifact@v4",
        "merge-multiple: true",
        'gh release create "$GITHUB_REF_NAME" dist/*',
        "--draft --verify-tag",
        "RELEASE_DRAFT_REPLAY_PASS",
        "sha256sum --check SHA256SUMS",
        'gh release edit "$GITHUB_REF_NAME" --draft=false',
    )
    for marker in mandatory:
        if marker not in job:
            raise ValueError("RELEASE_BLOCKED: missing release safety requirement: " + marker)
    if not (job.index('gh release create "$GITHUB_REF_NAME" dist/*')
            < job.index("RELEASE_DRAFT_REPLAY_PASS")
            < job.index('gh release edit "$GITHUB_REF_NAME" --draft=false')):
        raise ValueError("RELEASE_BLOCKED: release publication order changed")


def embedded_asset_verifier(workflow: str) -> str:
    job = release_job(workflow)
    step = "      - name: Reject missing, extra or empty assets; produce exact SHA-256 manifest"
    if step not in job:
        raise ValueError("RELEASE_BLOCKED: asset preflight step missing")
    after = job.split(step, 1)[1]
    start = "          python3 - <<'PY'\n"
    if start not in after:
        raise ValueError("RELEASE_BLOCKED: missing executable asset verifier")
    code = after.split(start, 1)[1].split("\n          PY", 1)
    if len(code) != 2:
        raise ValueError("RELEASE_BLOCKED: unterminated asset verifier")
    return textwrap.dedent(code[0])


class PublicationGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.workflow = WORKFLOW.read_text(encoding="utf-8")
        cls.verifier = embedded_asset_verifier(cls.workflow)

    def test_release_flow_is_draft_first_and_exact_sha(self):
        check_release_workflow(self.workflow)

    def test_removed_safety_barriers_are_rejected(self):
        for removed in (
            "--draft --verify-tag",
            "needs: [test, publish-island-manifest, build-cli, build-msi, build-web]",
            "RELEASE_GO_SHA: $" + "{{ vars.SENS_RELEASE_GO_SHA }}",
            'gh release edit "$GITHUB_REF_NAME" --draft=false',
        ):
            with self.subTest(removed=removed):
                self.assertIn(removed, self.workflow)
                with self.assertRaisesRegex(ValueError, "RELEASE_BLOCKED"):
                    check_release_workflow(self.workflow.replace(removed, "", 1))

    def stage(self, root: Path):
        dist = root / "dist"
        dist.mkdir()
        for name in required_assets(TAG):
            (dist / name).write_bytes(("dummy test-only artifact: " + name).encode())
        return dist

    def invoke(self, root: Path, *, tag: str = TAG, sha: str = SHA):
        return subprocess.run(
            [sys.executable, "-c", self.verifier], cwd=root,
            env={**os.environ, "GITHUB_REF_NAME": tag, "GITHUB_SHA": sha},
            capture_output=True, text=True, timeout=15,
        )

    def test_complete_asset_set_produces_replayable_checksums(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            dist = self.stage(root)
            result = self.invoke(root)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("RELEASE_STAGED", result.stdout)
            manifest = json.loads((dist / "release-provenance.json").read_text())
            self.assertEqual(manifest["commit"], SHA)
            self.assertEqual(manifest["tag"], TAG)
            self.assertEqual({a["name"] for a in manifest["assets"]}, required_assets(TAG))
            checks = (dist / "SHA256SUMS").read_text().splitlines()
            self.assertEqual(len(checks), len(required_assets(TAG)) + 1)
            for line in checks:
                digest, name = line.split("  ", 1)
                self.assertEqual(hashlib.sha256((dist / name).read_bytes()).hexdigest(), digest)

    def test_missing_extra_empty_and_symlink_assets_block(self):
        for defect in ("missing-msi", "unexpected-file", "empty-file", "symlink"):
            with self.subTest(defect=defect), tempfile.TemporaryDirectory() as d:
                root = Path(d)
                dist = self.stage(root)
                msi = dist / f"sens-cli_{TAG[1:]}_windows_x64.msi"
                if defect == "missing-msi":
                    msi.unlink()
                elif defect == "unexpected-file":
                    (dist / "unexpected.bin").write_bytes(b"X")
                elif defect == "empty-file":
                    msi.write_bytes(b"")
                else:
                    msi.unlink()
                    msi.symlink_to(dist / "install.sh")
                result = self.invoke(root)
                self.assertNotEqual(result.returncode, 0, f"{defect} admitted")
                self.assertIn("RELEASE_BLOCKED", result.stderr)
                self.assertFalse((dist / "SHA256SUMS").exists())

    def test_unapproved_sha_or_tag_blocks(self):
        for tag, sha in (("v0.42.0", SHA), (TAG, "bad-sha")):
            with self.subTest(tag=tag, sha=sha), tempfile.TemporaryDirectory() as d:
                root = Path(d)
                self.stage(root)
                result = self.invoke(root, tag=tag, sha=sha)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("RELEASE_BLOCKED", result.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
