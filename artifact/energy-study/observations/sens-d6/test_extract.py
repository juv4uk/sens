import unittest
from extract import InvalidEvidence, extract

SHA = "979f09772fd370c1374468f665b875f0c4a60bef"
LOG = """2026-10-28T15:42:55.3588902Z shell: /usr/bin/bash --noprofile --norc -e -o pipefail {0}
2026-10-28T15:42:55.3671254Z === три повтори, /usr/bin/time -v ===
2026-10-28T15:42:55.3671599Z --- повтор 1 ---
2026-10-28T15:42:56.4808997Z \tElapsed (wall clock) time (h:mm:ss or m:ss): 0:01.11
2026-10-28T15:42:56.4809607Z \tMaximum resident set size (kbytes): 46668
2026-10-28T15:42:56.4811110Z --- повтор 2 ---
2026-10-28T15:42:57.5756275Z \tElapsed (wall clock) time (h:mm:ss or m:ss): 0:01.09
2026-10-28T15:42:57.5756684Z \tMaximum resident set size (kbytes): 48668
2026-10-28T15:42:57.5759456Z --- повтор 3 ---
2026-10-28T15:42:58.6823164Z \tElapsed (wall clock) time (h:mm:ss or m:ss): 0:01.10
2026-10-28T15:42:58.6823835Z \tMaximum resident set size (kbytes): 48168
"""


def parsed(log=LOG, **kw):
    args = {"commit_sha": SHA, "run_id": 40718451952, "job_id": 122922468383}
    args.update(kw)
    return extract(log, **args)


class EvidenceTests(unittest.TestCase):
    def test_real_ci_excerpt_preserves_exact_observations(self):
        report = parsed()
        self.assertEqual([r["wall_seconds"] for r in report["samples"]], [1.11, 1.09, 1.10])
        self.assertEqual([r["peak_rss_kib"] for r in report["samples"]], [46668, 48668, 48168])
        self.assertEqual(report["status"], "EXPLORATORY_NOT_ADMITTED")
        self.assertEqual(report["energy_status"], "ENERGY_NOT_MEASURED")
        self.assertIsNone(report["energy_j"])
        self.assertEqual(report["output_parity"], "NOT_VERIFIED")

    def test_no_pipefail_cannot_claim_exit_propagation(self):
        with self.assertRaises(InvalidEvidence):
            parsed(LOG.replace("-e -o pipefail", "-e"))

    def test_missing_sample_is_blocked(self):
        with self.assertRaises(InvalidEvidence):
            parsed(LOG[:LOG.index("--- повтор 3 ---")])

    def test_duplicate_round_is_blocked(self):
        with self.assertRaises(InvalidEvidence):
            parsed(LOG.replace("--- повтор 2 ---", "--- повтор 1 ---"))

    def test_zero_rss_is_blocked(self):
        with self.assertRaises(InvalidEvidence):
            parsed(LOG.replace("46668", "0"))

    def test_wrong_sha_or_failed_job_is_blocked(self):
        with self.assertRaises(InvalidEvidence):
            parsed(commit_sha="short")
        with self.assertRaises(InvalidEvidence):
            parsed(conclusion="failure")


if __name__ == "__main__":
    unittest.main()
