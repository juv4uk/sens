"""Red must speak — the daily 24h escalation has to fire for named quarantines too."""
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


class Escalation24h(unittest.TestCase):
    def audit(self, first_seen_hours, expires_days=6):
        case = {
            "test_id": "named-red", "stamp": "TRANSITIONAL", "owner": "worker",
            "first_seen_at": hours_ago(first_seen_hours),
            "expires_at": days_from_now(expires_days),
            "ticket": "#5029", "reason": "probe", "investigation": "issue 5029",
        }
        path = pathlib.Path(tempfile.mkdtemp()) / "quarantine.json"
        path.write_text(json.dumps({"schema": "sens-red-v1", "cases": [case]}))
        return subprocess.run(
            [sys.executable, str(SCRIPT), "audit", "--manifest", str(path)],
            cwd=ROOT, capture_output=True, text=True)

    def test_named_quarantine_escalates_after_24h(self):
        result = self.audit(30)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("::error::named-red:ESCALATION-24H", result.stdout)

    def test_fresh_named_quarantine_passes(self):
        result = self.audit(2)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("PASS named red registry", result.stdout)

    def test_expired_quarantine_still_fails(self):
        result = self.audit(2, expires_days=-1)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("EXPIRED_QUARANTINE", result.stdout)


if __name__ == "__main__":
    unittest.main()
