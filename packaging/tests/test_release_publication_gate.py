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
        for workflow in ('"ci.yml"', '"ci-hosted.yml"', '"release-preflight.yml"'):
            with self.subTest(workflow=workflow):
                self.assertIn(workflow, driver)
                self.assertIn('"--limit" "1"', driver)
        self.assertIn('"SENS_RELEASE_GO_SHA"', driver)
        self.assertIn('"SENS_RELEASE_GO_TAG"', driver)
        self.assertIn('"variable" "get"', driver)

    def test_local_tag_driver_is_not_satisfied_by_any_old_green_run(self):
        driver = (ROOT / "scripts" / "release.lisp").read_text(encoding="utf-8")
        self.assertNotIn('"--workflow" "CI"', driver)
        self.assertNotIn('"--limit" "20"', driver)


if __name__ == "__main__":
    unittest.main()
