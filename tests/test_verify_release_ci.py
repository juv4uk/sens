"""Negative controls for the exact-SHA, independent release-check verifier.

These tests use synthetic API responses. They never create a tag or contact
GitHub, and do not pronounce any real SENS commit release-ready.
"""
from __future__ import annotations

import copy
import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "verify_release_ci.py"
SPEC = importlib.util.spec_from_file_location("sens_verify_release_ci_test", SCRIPT)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("release CI verifier cannot be loaded")
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)

SHA = "a" * 40


def check(name: str, number: int) -> dict:
    return {
        "id": number,
        "name": name,
        "head_sha": SHA,
        "status": "completed",
        "conclusion": "success",
        "app": {"slug": "github-actions"},
        "details_url": f"https://github.com/juv4uk/sens/actions/runs/{number}",
    }


def complete_payload() -> dict:
    return {
        "check_runs": [
            check(name, 100 + i)
            for i, name in enumerate(MODULE.REQUIRED_CHECKS)
        ]
    }


class ExactReleaseChecksTest(unittest.TestCase):
    def test_all_required_independent_checks_pass_with_receipt(self):
        receipt = MODULE.verify_check_runs(complete_payload(), SHA)
        self.assertEqual(len(receipt), len(MODULE.REQUIRED_CHECKS))
        self.assertEqual([x["name"] for x in receipt], list(MODULE.REQUIRED_CHECKS))
        self.assertTrue(all(x["sha"] == SHA and x["status"] == "success"
                            for x in receipt))

    def test_release_requires_exact_sha_native_lisp_t5m_job(self):
        # Exact check name in ci.yml; a skipped, missing or red native gate
        # must never be treated as a passed SENS release witness.
        central = "Українська проєкція та заборона сирих літералів"
        self.assertIn(central, MODULE.REQUIRED_CHECKS)
        payload = complete_payload()
        self.assertEqual(len(MODULE.verify_check_runs(payload, SHA)),
                         len(MODULE.REQUIRED_CHECKS))

        missing = copy.deepcopy(payload)
        missing["check_runs"] = [
            row for row in missing["check_runs"] if row["name"] != central
        ]
        with self.assertRaisesRegex(ValueError, "missing exact-SHA check"):
            MODULE.verify_check_runs(missing, SHA, "juv4uk/sens")

        for change, expected in (
            ({"conclusion": "failure"}, "not green"),
            ({"status": "in_progress", "conclusion": None}, "not green"),
            ({"head_sha": "b" * 40}, "wrong check-run SHA"),
        ):
            with self.subTest(change=change):
                mutant = copy.deepcopy(payload)
                row = next(r for r in mutant["check_runs"] if r["name"] == central)
                row.update(change)
                with self.assertRaisesRegex(ValueError, expected):
                    MODULE.verify_check_runs(mutant, SHA, "juv4uk/sens")

    def test_missing_required_check_is_rejected(self):
        payload = complete_payload()
        missing = MODULE.REQUIRED_CHECKS[0]
        payload["check_runs"] = [r for r in payload["check_runs"] if r["name"] != missing]
        with self.assertRaisesRegex(ValueError, "missing exact-SHA check"):
            MODULE.verify_check_runs(payload, SHA)

    def test_pending_failed_skipped_and_cancelled_are_rejected(self):
        for status, conclusion in (
            ("queued", None), ("in_progress", None), ("completed", "failure"),
            ("completed", "skipped"), ("completed", "cancelled"),
        ):
            with self.subTest(status=status, conclusion=conclusion):
                payload = complete_payload()
                payload["check_runs"][0].update(status=status, conclusion=conclusion)
                with self.assertRaisesRegex(ValueError, "not green"):
                    MODULE.verify_check_runs(payload, SHA)

    def test_newer_red_run_supersedes_earlier_green_even_across_pages(self):
        green = complete_payload()
        name = MODULE.REQUIRED_CHECKS[0]
        new_failure = check(name, 10000)
        new_failure["conclusion"] = "failure"
        for pages in ([green, {"check_runs": [new_failure]}],
                      [{"check_runs": [new_failure]}, green]):
            with self.subTest(page_order=pages[0] is green):
                with self.assertRaisesRegex(ValueError, "not green"):
                    MODULE.verify_check_runs(pages, SHA)

    def test_newer_green_replaces_old_failure_not_vice_versa(self):
        payload = complete_payload()
        old_failure = check(MODULE.REQUIRED_CHECKS[0], 1)
        old_failure["conclusion"] = "failure"
        payload["check_runs"].append(old_failure)
        self.assertEqual(len(MODULE.verify_check_runs(payload, SHA)),
                         len(MODULE.REQUIRED_CHECKS))

    def test_wrong_sha_is_rejected_even_when_status_is_green(self):
        payload = complete_payload()
        payload["check_runs"][0]["head_sha"] = "b" * 40
        with self.assertRaisesRegex(ValueError, "wrong check-run SHA"):
            MODULE.verify_check_runs(payload, SHA)
        with self.assertRaisesRegex(ValueError, "invalid exact source SHA"):
            MODULE.verify_check_runs(complete_payload(), "abc")

    def test_untrusted_provider_and_missing_actions_url_are_rejected(self):
        for field, value in (("app", {"slug": "other"}),
                             ("details_url", "https://example.com/fake/pass")):
            with self.subTest(field=field):
                payload = complete_payload()
                payload["check_runs"][0][field] = value
                with self.assertRaisesRegex(ValueError, "untrusted check provider"):
                    MODULE.verify_check_runs(payload, SHA)

    def test_reject_untrusted_actions_urls_and_cross_repo_runs(self):
        # A provider slug does not authorize a foreign host or repository.
        invalid_urls = (
            "https://attacker.example/juv4uk/sens/actions/runs/100",
            "https://github.com/juv4uk/other/actions/runs/100",
            "http://github.com/juv4uk/sens/actions/runs/100",
            "https://github.com.evil.example/juv4uk/sens/actions/runs/100",
            "https://github.com/juv4uk/sens/actions/runs/100/../other",
        )
        for url in invalid_urls:
            with self.subTest(url=url):
                payload = complete_payload()
                payload["check_runs"][0]["details_url"] = url
                with self.assertRaisesRegex(ValueError, "untrusted check provider"):
                    MODULE.verify_check_runs(payload, SHA, "juv4uk/sens")

        valid = complete_payload()
        valid["check_runs"][0]["details_url"] = (
            "https://github.com/juv4uk/sens/actions/runs/100/job/200"
        )
        self.assertEqual(
            len(MODULE.verify_check_runs(valid, SHA, "juv4uk/sens")),
            len(MODULE.REQUIRED_CHECKS),
        )

    def test_malformed_responses_and_bad_ids_fail_closed(self):
        for payload in ([], {}, {"check_runs": None}, {"check_runs": [None]}):
            with self.subTest(payload=payload):
                with self.assertRaises(ValueError):
                    MODULE.verify_check_runs(payload, SHA)
        for invalid in (0, -1, True, "10", None):
            with self.subTest(id=invalid):
                payload = complete_payload()
                payload["check_runs"][0]["id"] = invalid
                with self.assertRaisesRegex(ValueError, "invalid check-run ID"):
                    MODULE.verify_check_runs(payload, SHA)

    def test_tag_workflow_requires_release_ci_before_staging_and_publication(self):
        # Першопричина: job release-publish винесено з release.yml у делегований
        # release-publish.yml (workflow_call). Тест мусить читати САМЕ той файл,
        # який публікує, інакше він згниває й блокує релізний preflight.
        tag = (ROOT / ".github/workflows/release.yml").read_text(encoding="utf-8")
        publish = (ROOT / ".github/workflows/release-publish.yml").read_text(encoding="utf-8")
        self.assertIn("uses: ./.github/workflows/release-publish.yml", tag)
        self.assertGreaterEqual(
            publish.count('python3 scripts/verify_release_ci.py "$GITHUB_SHA" "$GITHUB_REPOSITORY"'),
            2,
            "exact-SHA verifier must run before staging and again before publication",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
