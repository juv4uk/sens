"""RED metadata transport: 24h classification and named quarantine expiry differ."""
import datetime as dt
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/ci_failure_contract.py"


def hours_ago(hours):
    return (dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=hours)).isoformat()


def days_from_now(days):
    return (dt.datetime.now(dt.timezone.utc) + dt.timedelta(days=days)).isoformat()


class ClassificationVsExpiry(unittest.TestCase):
    def audit(self, stamp, first_seen_hours, expires_days):
        case = {
            "test_id": "red-quarantine-classification-vs-expiry",
            "stamp": stamp, "owner": "worker",
            "first_seen_at": hours_ago(first_seen_hours),
            "reason": "metadata classification or expiry evidence",
        }
        if stamp in {"TRANSITIONAL", "FLAKE"}:
            case.update({
                "expires_at": days_from_now(expires_days),
                "ticket": "#5029", "investigation": "issue 5029",
            })
        with tempfile.TemporaryDirectory() as tmp:
            manifest = pathlib.Path(tmp) / "quarantine.json"
            manifest.write_text(json.dumps({"schema": "sens-red-v1", "cases": [case]}))
            return subprocess.run(
                [sys.executable, str(SCRIPT), "audit", "--manifest", str(manifest)],
                cwd=ROOT, capture_output=True, text=True, check=False)

    def test_red_quarantine_classification_vs_expiry(self):
        controls = [
            # One policy invariant, three counterexamples / witnesses.
            ("UNCLASSIFIED", 25, 6, 1, "ESCALATE_24H_UNCLASSIFIED"),
            ("TRANSITIONAL", 30, 6, 0, "PASS named red registry"),
            ("TRANSITIONAL", 60, -1, 1, "EXPIRED_QUARANTINE"),
        ]
        for stamp, age, expiry, exit_code, evidence in controls:
            with self.subTest(stamp=stamp, age=age, expiry=expiry):
                result = self.audit(stamp, age, expiry)
                self.assertEqual(result.returncode, exit_code, result.stdout + result.stderr)
                self.assertIn(evidence, result.stdout)


if __name__ == "__main__":
    unittest.main()
