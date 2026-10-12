"""Structural regression for the final exact-SHA publication guard.

The guard must execute after the draft has been downloaded and replay-verified,
because main can advance while platform artifacts are being built or uploaded.
"""

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github" / "workflows" / "release.yml"
PUBLISH_JOB = "  release-publish:"
FINAL_GUARD = "# Revalidate authorization and main immediately before publication:"
PUBLISH_COMMAND = 'gh release edit "$GITHUB_REF_NAME" --draft=false'


def require_final_publication_guard(source: str) -> None:
    """Fail unless replay, checksum, fresh main/GO checks precede public publish."""
    if PUBLISH_JOB not in source:
        raise AssertionError("release-publish job is missing")
    job = source[source.index(PUBLISH_JOB) :]
    publish_at = job.index(PUBLISH_COMMAND)
    replay_at = job.rfind("scripts/verify_release_assets.py replay", 0, publish_at)
    checksum_at = job.rfind("sha256sum --check SHA256SUMS", 0, publish_at)
    final_fetch_at = job.rfind("git fetch --no-tags --depth=1 origin main", 0, publish_at)
    final_compare_at = job.rfind(
        'test "$(git rev-parse FETCH_HEAD)" = "$GITHUB_SHA"', 0, publish_at
    )
    final_go_at = job.rfind(
        'if [[ -z "$RELEASE_GO_SHA" || -z "$RELEASE_GO_TAG"', 0, publish_at
    )
    final_guard_at = job.rfind(FINAL_GUARD, 0, publish_at)

    if replay_at < 0 or checksum_at < 0:
        raise AssertionError("draft replay and SHA256 verification must precede publication")
    if not (
        replay_at < checksum_at < final_guard_at < final_fetch_at
        < final_compare_at < final_go_at < publish_at
    ):
        raise AssertionError(
            "fresh main-SHA and owner-GO checks must occur after replay/checksum "
            "and immediately before public publication"
        )
    if job.count("git fetch --no-tags --depth=1 origin main") < 2:
        raise AssertionError("both initial and final main-SHA checks are required")


class ReleasePublicationGateTest(unittest.TestCase):
    def setUp(self):
        self.source = WORKFLOW.read_text(encoding="utf-8")

    def test_workflow_rechecks_main_after_replay_and_before_publish(self):
        require_final_publication_guard(self.source)

    def test_workflow_without_final_guard_is_rejected(self):
        job_start = self.source.index(PUBLISH_JOB)
        job = self.source[job_start:]
        guard_at = job.index(FINAL_GUARD)
        publish_at = job.index(PUBLISH_COMMAND, guard_at)
        mutated = self.source[:job_start] + job[:guard_at] + job[publish_at:]
        with self.assertRaisesRegex(AssertionError, "fresh main-SHA"):
            require_final_publication_guard(mutated)

    def test_local_tag_driver_requires_every_exact_sha_workflow_and_owner_go(self):
        driver = (ROOT / "scripts" / "release.lisp").read_text(encoding="utf-8")
        for workflow in ('"ci-hosted.yml"', '"release-preflight.yml"'):
            with self.subTest(workflow=workflow):
                self.assertIn(workflow, driver)
                self.assertIn('"--limit" "1"', driver)
        self.assertIn('"SENS_RELEASE_GO_SHA"', driver)
        self.assertIn('"SENS_RELEASE_GO_TAG"', driver)
        self.assertIn('"variable" "get"', driver)

    def test_local_tag_driver_is_not_satisfied_by_any_old_green_run(self):
        driver = (ROOT / "scripts" / "release.lisp").read_text(encoding="utf-8")
        self.assertNotIn('"--workflow" "CI"', driver)
        self.assertNotIn('"--workflow" "ci.yml"', driver)
        self.assertNotIn('"--limit" "20"', driver)

    def test_publisher_waits_for_all_assets_and_replays_exact_bytes(self):
        workflow = WORKFLOW.read_text(encoding="utf-8")
        publish_at = workflow.index("  release-publish:")
        job = workflow[publish_at:]
        self.assertIn(
            "needs: [test, publish-island-manifest, build-cli, build-msi, build-web]",
            job,
        )
        self.assertIn("actions/download-artifact@v4", job)
        self.assertIn("python3 scripts/verify_release_assets.py replay", job)
        self.assertIn("sha256sum --check SHA256SUMS", job)
        self.assertIn("RELEASE_GO_SHA: ${{ vars.SENS_RELEASE_GO_SHA }}", job)
        self.assertIn("RELEASE_GO_TAG: ${{ vars.SENS_RELEASE_GO_TAG }}", job)
        self.assertIn('gh release edit "$GITHUB_REF_NAME" --draft=false', job)
        self.assertIn("--draft --verify-tag", job)

    def test_preflight_runs_workspace_test_clippy_and_triggers_on_release_docs(self):
        preflight = (ROOT / ".github" / "workflows" / "release-preflight.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn("cargo test --locked --workspace", preflight)
        self.assertIn(
            "cargo clippy --locked --workspace --all-targets -- -D warnings",
            preflight,
        )
        push = preflight.split("  push:", 1)[1].split("  pull_request:", 1)[0]
        pull_request = preflight.split("  pull_request:", 1)[1].split("  workflow_dispatch:", 1)[0]
        for path in (
            "RELEASE.md",
            "RELEASE-EVIDENCE.md",
            "docs/release-readiness-contract-11-9-2026-10-12.uk.md",
            "scripts/release.lisp",
            "rust-toolchain.toml",
        ):
            with self.subTest(path=path):
                self.assertIn(f'- "{path}"', push)
                self.assertIn(f'- "{path}"', pull_request)


if __name__ == "__main__":
    unittest.main()
