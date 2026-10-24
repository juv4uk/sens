"""Structural regression for the final exact-SHA publication guard.

The guard must execute after the draft has been downloaded and replay-verified,
because main can advance while platform artifacts are being built or uploaded.
"""

import importlib.util
import re
import shutil
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github" / "workflows" / "release.yml"
PUBLISH_JOB = "  release-publish:"
FINAL_GUARD = "# Revalidate authorization and main immediately before publication:"
PUBLISH_COMMAND = 'gh release edit "$GITHUB_REF_NAME" --draft=false'
CI_COMMAND = 'python3 scripts/verify_release_ci.py "$GITHUB_SHA" "$GITHUB_REPOSITORY"'
DRAFT_COMMAND = 'gh release create "$GITHUB_REF_NAME" dist/*'


def resolved_publish_job() -> str:
    """Тіло job `release-publish`, з переходом за `uses:` у викликаний workflow.

    Першопричина: раніше цей job містив усю послідовність inline у release.yml.
    Тепер його винесено у release-publish.yml (workflow_call), тож структурні
    тести, що читали лише release.yml, згнили й блокували релізний preflight.
    Тепер вони перевіряють САМЕ той workflow, який справді публікує.
    """
    source = WORKFLOW.read_text(encoding="utf-8")
    if PUBLISH_JOB not in source:
        raise AssertionError("release-publish job is missing")
    job = source[source.index(PUBLISH_JOB) :]
    match = re.search(r"uses:\s*\./\.github/workflows/([\w.\-]+)", job)
    if match:
        called = ROOT / ".github" / "workflows" / match.group(1)
        if not called.is_file():
            raise AssertionError(f"delegated publish workflow is missing: {match.group(1)}")
        return called.read_text(encoding="utf-8")
    return job


def require_final_publication_guard(job: str) -> None:
    """Fail unless replay, checksum, fresh main/GO checks precede public publish."""
    if FINAL_GUARD not in job:
        raise AssertionError("release-publish job is missing the final publication guard")
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

    # A successful pre-draft CI check is insufficient: a check can be
    # rerun or invalidated while artifacts are staged and replayed.
    # Require an independent exact-SHA check immediately before publication.
    first_ci_at = job.find(CI_COMMAND)
    final_ci_at = job.rfind(CI_COMMAND, 0, publish_at)
    draft_at = job.find(DRAFT_COMMAND)
    if (
        first_ci_at < 0
        or draft_at < 0
        or final_ci_at == first_ci_at
        or not (
            first_ci_at < draft_at < replay_at < checksum_at
            < final_guard_at < final_fetch_at < final_compare_at
            < final_go_at < final_ci_at < publish_at
        )
    ):
        raise AssertionError(
            "final exact-SHA release CI recheck must follow draft replay, "
            "fresh main and owner GO, directly before public publication"
        )


def require_pinned_artifact_download(job: str) -> None:
    """Reject floating action tags and truncated hashes before publication."""
    pinned = re.search(
        r"(?m)^\s+uses:\s+actions/download-artifact@[0-9a-f]{40}\s+# v\d+\s*$",
        job,
    )
    if pinned is None:
        raise AssertionError(
            "release-publish must use full immutable SHA for actions/download-artifact"
        )


class ReleasePublicationGateTest(unittest.TestCase):
    def setUp(self):
        self.source = WORKFLOW.read_text(encoding="utf-8")
        self.job = resolved_publish_job()

    def test_workflow_rechecks_main_after_replay_and_before_publish(self):
        require_final_publication_guard(self.job)

    def test_workflow_without_final_guard_is_rejected(self):
        job = self.job
        guard_at = job.index(FINAL_GUARD)
        publish_at = job.index(PUBLISH_COMMAND, guard_at)
        mutated = job[:guard_at] + job[publish_at:]
        with self.assertRaisesRegex(AssertionError, "final publication guard"):
            require_final_publication_guard(mutated)

    def test_missing_final_exact_sha_ci_recheck_is_rejected(self):
        job = self.job
        last_ci_at = job.rfind(CI_COMMAND)
        self.assertGreater(last_ci_at, job.index(FINAL_GUARD))
        broken_job = job[:last_ci_at] + job[last_ci_at:].replace(CI_COMMAND, "", 1)
        with self.assertRaisesRegex(AssertionError, "final exact-SHA release CI recheck"):
            require_final_publication_guard(broken_job)

    def test_ci_recheck_moved_to_before_draft_is_rejected(self):
        job = self.job
        last_ci_at = job.rfind(CI_COMMAND)
        self.assertGreater(last_ci_at, job.index(FINAL_GUARD))
        broken_job = job[:last_ci_at] + job[last_ci_at:].replace(CI_COMMAND, "", 1)
        broken_job = broken_job.replace(
            DRAFT_COMMAND, CI_COMMAND + "\n          " + DRAFT_COMMAND, 1
        )
        with self.assertRaisesRegex(AssertionError, "final exact-SHA release CI recheck"):
            require_final_publication_guard(broken_job)

    def test_missing_pre_draft_ci_check_is_rejected(self):
        job = self.job
        broken_job = job.replace(CI_COMMAND, "", 1)
        with self.assertRaisesRegex(AssertionError, "final exact-SHA release CI recheck"):
            require_final_publication_guard(broken_job)

    def test_local_tag_driver_requires_every_exact_sha_workflow_and_owner_go(self):
        # Першопричина: локальний tag-driver (scripts/release.lisp) виведено з
        # ужитку, а тест усе ще шукав його рядки. Живий owner-GO бар'єр тепер у
        # release-publish.yml і задокументований у RELEASE.md — перевіряємо його.
        publish = (ROOT / ".github" / "workflows" /
                   "release-publish.yml").read_text(encoding="utf-8")
        for marker in ("SENS_RELEASE_GO_SHA", "SENS_RELEASE_GO_TAG",
                       "RELEASE_GO_SHA", "RELEASE_GO_TAG",
                       "verify_release_ci.py"):
            with self.subTest(marker=marker):
                self.assertIn(marker, publish)
        doc = (ROOT / "RELEASE.md").read_text(encoding="utf-8")
        self.assertIn("SENS_RELEASE_GO_SHA", doc)
        self.assertIn("SENS_RELEASE_GO_TAG", doc)

    def test_local_tag_driver_is_not_satisfied_by_any_old_green_run(self):
        # Точний SHA перевіряє verify_release_ci.py, прив'язуючись до GITHUB_SHA,
        # а не до «будь-якого старого зеленого прогону».
        ci = (ROOT / "scripts" / "verify_release_ci.py").read_text(encoding="utf-8")
        self.assertIn("REQUIRED_CHECKS", ci)
        publish = (ROOT / ".github" / "workflows" /
                   "release-publish.yml").read_text(encoding="utf-8")
        self.assertIn(
            'verify_release_ci.py "$GITHUB_SHA" "$GITHUB_REPOSITORY"', publish
        )

    def test_publisher_waits_for_all_assets_and_replays_exact_bytes(self):
        workflow = WORKFLOW.read_text(encoding="utf-8")
        publish_at = workflow.index("  release-publish:")
        self.assertIn(
            "needs: [test, publish-island-manifest, build-cli, build-msi, build-web]",
            workflow[publish_at:],
        )
        job = self.job
        require_pinned_artifact_download(job)
        self.assertIn("python3 scripts/verify_release_assets.py replay", job)
        self.assertIn("sha256sum --check SHA256SUMS", job)
        self.assertIn("RELEASE_GO_SHA: ${{ vars.SENS_RELEASE_GO_SHA }}", job)
        self.assertIn("RELEASE_GO_TAG: ${{ vars.SENS_RELEASE_GO_TAG }}", job)
        self.assertIn('gh release edit "$GITHUB_REF_NAME" --draft=false', job)
        self.assertIn("--draft --verify-tag", job)

    def test_download_artifact_pin_is_not_satisfied_by_floating_tag_or_short_hash(self):
        job = self.job
        require_pinned_artifact_download(job)
        pin = re.search(
            r"actions/download-artifact@[0-9a-f]{40} # v\d+",
            job,
        )
        self.assertIsNotNone(pin)
        for broken in (
            "actions/download-artifact@v4",
            "actions/download-artifact@1234567 # v4",
            "actions/upload-artifact@1234567890123456789012345678901234567890 # v4",
        ):
            with self.subTest(broken=broken), self.assertRaisesRegex(
                AssertionError, "full immutable SHA"
            ):
                require_pinned_artifact_download(job.replace(pin.group(), broken))

    def test_release_replay_rejects_self_comparison_and_accepts_downloaded_bytes(self):
        # Real filesystem fixture: staged==downloaded must never attest replay.
        # Standalone test lives here because another writer owns
        # tests/test_verify_release_assets.py at this time.
        script = ROOT / "scripts" / "verify_release_assets.py"
        spec = importlib.util.spec_from_file_location(
            "sens_release_assets_independent_replay", script
        )
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        tag, sha = "l0.42.0", "a" * 40

        with tempfile.TemporaryDirectory() as tmp:
            staging = Path(tmp) / "staged"
            staging.mkdir()
            for name in module._expected(tag):
                (staging / name).write_bytes(b"release-test-asset:" + name.encode())
            # Existing release contract requires identical canonical/alias HTML.
            (staging / "my-lisp-cli-web.html").write_bytes(
                (staging / "sens-cli-web.html").read_bytes()
            )
            module.prepare(staging, tag, sha)

            with self.assertRaisesRegex(ValueError, "independent download directory"):
                module.verify_replay(staging, staging, tag, sha)
            with self.assertRaisesRegex(ValueError, "independent download directory"):
                module.verify_replay(staging, staging / ".." / "staged", tag, sha)

            downloaded = Path(tmp) / "downloaded"
            shutil.copytree(staging, downloaded)
            self.assertEqual(
                module.verify_replay(staging, downloaded, tag, sha),
                len(module._expected(tag)),
            )
            # A *distinct* directory must still refuse corrupted bytes.
            (downloaded / "install.sh").write_bytes(b"corrupted download")
            with self.assertRaisesRegex(ValueError, "digest/size mismatch"):
                module.verify_replay(staging, downloaded, tag, sha)

    def test_preflight_is_manual_only_and_keeps_strict_workspace_gates(self):
        preflight = (
            ROOT / ".github" / "workflows" / "release-preflight.yml"
        ).read_text(encoding="utf-8")

        # Only the central ci.yml is automatic under the ratified
        # single-workflow budget; preflight remains an explicit release gate.
        self.assertIn("on:\n  workflow_dispatch:\n", preflight)
        self.assertIsNone(
            re.search(r"(?m)^  (push|pull_request|schedule):", preflight),
            "release-preflight must not introduce a second automatic workflow",
        )
        self.assertIn("cargo test --locked --workspace", preflight)
        self.assertIn(
            "cargo clippy --locked --workspace --all-targets -- -D warnings",
            preflight,
        )


if __name__ == "__main__":
    unittest.main()
