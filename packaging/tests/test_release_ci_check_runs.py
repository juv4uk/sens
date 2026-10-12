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


if __name__ == "__main__":
    unittest.main()
