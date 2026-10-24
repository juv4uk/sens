"""Negative controls for the independent release CI admission gate."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from verify_release_ci import REQUIRED_CHECKS, verify_check_runs

SHA = "a" * 40


def good_run(name, rid):
    return {"name": name, "id": rid, "head_sha": SHA,
            "status": "completed", "conclusion": "success",
            "app": {"slug": "github-actions"},
            "details_url": f"https://github.com/juv4uk/sens/actions/runs/{rid}/job/{rid}"}


class ReleaseCIChecks(unittest.TestCase):
    def setUp(self):
        self.runs = [good_run(name, i + 1) for i, name in enumerate(REQUIRED_CHECKS)]

    def test_all_required_green_pass(self):
        self.assertEqual(len(verify_check_runs({"check_runs": self.runs}, SHA)), len(REQUIRED_CHECKS))

    def test_paged_results_are_merged(self):
        pages = [{"check_runs": self.runs[:3]}, {"check_runs": self.runs[3:]}]
        self.assertEqual(len(verify_check_runs(pages, SHA)), len(REQUIRED_CHECKS))

    def test_missing_required_check_blocks(self):
        with self.assertRaisesRegex(ValueError, "missing exact-SHA check"):
            verify_check_runs({"check_runs": self.runs[:-1]}, SHA)

    def test_explicit_failure_blocks(self):
        self.runs[0]["conclusion"] = "failure"
        with self.assertRaisesRegex(ValueError, "not green"):
            verify_check_runs({"check_runs": self.runs}, SHA)

    def test_queued_blocks(self):
        self.runs[1].update(status="queued", conclusion=None)
        with self.assertRaisesRegex(ValueError, "not green"):
            verify_check_runs({"check_runs": self.runs}, SHA)

    def test_stale_sha_blocks(self):
        self.runs[0]["head_sha"] = "b" * 40
        with self.assertRaisesRegex(ValueError, "wrong check-run SHA"):
            verify_check_runs({"check_runs": self.runs}, SHA)

    def test_newer_red_rerun_overrides_old_green(self):
        newer = dict(self.runs[0], id=999999, conclusion="cancelled")
        with self.assertRaisesRegex(ValueError, "not green"):
            verify_check_runs({"check_runs": [*self.runs, newer]}, SHA)

    def test_newer_green_rerun_can_recover_prior_red(self):
        self.runs[0]["conclusion"] = "failure"
        newer = dict(self.runs[0], id=999999, conclusion="success")
        self.assertEqual(len(verify_check_runs({"check_runs": [*self.runs, newer]}, SHA)), len(REQUIRED_CHECKS))

    def test_untrusted_external_check_provider_blocks(self):
        self.runs[0]["app"] = {"slug": "external"}
        with self.assertRaisesRegex(ValueError, "untrusted check provider"):
            verify_check_runs({"check_runs": self.runs}, SHA)

    def test_bad_api_shape_blocks(self):
        for data in ([], {}, {"check_runs": "wrong"}, {"check_runs": [None]}):
            with self.subTest(data=data), self.assertRaisesRegex(ValueError, "RELEASE_BLOCKED"):
                verify_check_runs(data, SHA)

    def test_missing_or_invalid_check_run_id_blocks(self):
        self.runs[0]["id"] = False
        with self.assertRaisesRegex(ValueError, "invalid check-run ID"):
            verify_check_runs({"check_runs": self.runs}, SHA)


def verify_publish_wiring(workflow):
    """Keep exact-SHA CI admission on both sides of draft creation."""
    # Першопричина: job release-publish винесено з release.yml у делегований
    # release-publish.yml (workflow_call). Приймаємо або весь файл, або job.
    if "\n  release-publish:\n" in workflow:
        job = workflow.split("\n  release-publish:\n", 1)[1]
    else:
        job = workflow
    required = "python3 scripts/verify_release_ci.py"
    if job.count(required) != 2:
        raise ValueError("RELEASE_BLOCKED: two live CI rechecks required")
    first = job.index(required)
    draft = job.index('gh release create "$GITHUB_REF_NAME"')
    replay = job.index("scripts/verify_release_assets.py replay")
    final = job.rindex(required)
    publish = job.index('gh release edit "$GITHUB_REF_NAME" --draft=false')
    if not (first < draft < replay < final < publish):
        raise ValueError("RELEASE_BLOCKED: CI guards must straddle draft verification")
    if "checks: read" not in job:
        raise ValueError("RELEASE_BLOCKED: live check-read token permission missing")


class ReleaseCIWorkflowWiring(unittest.TestCase):
    def setUp(self):
        # Першопричина: послідовність публікації живе у делегованому
        # release-publish.yml, а не в release.yml.
        self.workflow = (
            Path(__file__).resolve().parents[2] / ".github" / "workflows" / "release-publish.yml"
        ).read_text(encoding="utf-8")

    def test_live_ci_gate_before_draft_and_after_replay(self):
        verify_publish_wiring(self.workflow)

    def test_bypassing_either_ci_gate_is_rejected(self):
        pattern = "python3 scripts/verify_release_ci.py"
        for first in (True, False):
            with self.subTest(remove_first=first):
                if first:
                    broken = self.workflow.replace(pattern, "true # bypass", 1)
                else:
                    prefix, suffix = self.workflow.rsplit(pattern, 1)
                    broken = prefix + "true # bypass" + suffix
                with self.assertRaisesRegex(ValueError, "RELEASE_BLOCKED"):
                    verify_publish_wiring(broken)


if __name__ == "__main__":
    unittest.main()
