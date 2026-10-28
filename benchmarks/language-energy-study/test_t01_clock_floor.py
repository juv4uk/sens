#!/usr/bin/env python3
"""Mechanical negative/positive tests for T01 clock admission; NOT SENS laws.

Observed values below come from actual hosted GitHub Actions run 40730987210,
job 122966914730, PR head d5ef7c0938abeb0a4af59b1af221d2e812af0b1f.
The test fixture is a transcription of the published nine-row job-log output,
not a second physical measurement or independent replication.
"""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

SCRIPT = Path(__file__).with_name("t01_clock_floor.py")
spec = importlib.util.spec_from_file_location("sens_t01_clock_floor", SCRIPT)
assert spec is not None and spec.loader is not None
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

HEADER = "round\tlanguage\twall_seconds\tpeak_rss_kib\tchild_exit\tstdout"
ROWS = [
    "1\tC\t0.00\t1700\t0\t144",
    "1\tJS\t0.10\t43092\t0\t144",
    "1\tSENS\t0.01\t25088\t0\t144",
    "2\tJS\t0.02\t43772\t0\t144",
    "2\tSENS\t0.01\t25212\t0\t144",
    "2\tC\t0.00\t1700\t0\t144",
    "3\tSENS\t0.01\t24924\t0\t144",
    "3\tC\t0.00\t1764\t0\t144",
    "3\tJS\t0.02\t43736\t0\t144",
]


def table(rows=ROWS, header=HEADER):
    return (header + "\n" + "\n".join(rows) + "\n").encode("utf-8")


class T01ClockTests(unittest.TestCase):
    def test_actual_hosted_transcription_is_clock_blocked(self):
        data = table()
        out = mod.audit(data)
        self.assertEqual(out["raw_sha256"], hashlib.sha256(data).hexdigest())
        self.assertEqual(out["status"], "DESCRIPTIVE_ONLY_NO_INFERENCE")
        self.assertEqual(out["clock_admission"], "BLOCKED_BELOW_RESOLUTION")
        self.assertEqual([(z["round"], z["language"]) for z in out["zero_rounded_samples"]],
                         [(1, "C"), (2, "C"), (3, "C")])
        self.assertIsNone(out["speed_ratios"])
        self.assertIsNone(out["confidence_intervals"])
        self.assertIsNone(out["energy_joules"])
        self.assertEqual(out["energy_status"], "ENERGY_NOT_MEASURED")
        self.assertFalse(out["inference_admitted"])

    def test_nonzero_clock_still_not_inferential(self):
        changed = [line.replace("\t0.00\t", "\t0.03\t") for line in ROWS]
        out = mod.audit(table(changed))
        self.assertEqual(out["clock_admission"], "REPORTED_PRECISION_ONLY")
        self.assertEqual(out["zero_rounded_samples"], [])
        self.assertEqual(out["inference_blockers"],
                         ["NO_INDEPENDENT_SESSION_EVIDENCE_IN_TSV"])
        self.assertFalse(out["inference_admitted"])

    def test_incorrect_output_rejected(self):
        changed = [line.replace("\t144", "\t143") if i == 2 else line
                   for i, line in enumerate(ROWS)]
        with self.assertRaisesRegex(mod.InvalidPhysicalEvidence, "RESULT_OR_EXIT"):
            mod.audit(table(changed))

    def test_bad_exit_rejected(self):
        changed = [line.replace("\t0\t144", "\t2\t144") if i == 5 else line
                   for i, line in enumerate(ROWS)]
        with self.assertRaisesRegex(mod.InvalidPhysicalEvidence, "RESULT_OR_EXIT"):
            mod.audit(table(changed))

    def test_duplicate_or_unbalanced_round_rejected(self):
        changed = ROWS.copy()
        changed[3] = changed[4]
        with self.assertRaisesRegex(mod.InvalidPhysicalEvidence, "ORDER"):
            mod.audit(table(changed))

    def test_missing_sample_rejected(self):
        with self.assertRaisesRegex(mod.InvalidPhysicalEvidence, "EXACTLY_9"):
            mod.audit(table(ROWS[:-1]))

    def test_bad_header_and_extra_column_rejected(self):
        with self.assertRaisesRegex(mod.InvalidPhysicalEvidence, "HEADER"):
            mod.audit(table(header=HEADER + "\tclock"))
        changed = ROWS.copy()
        changed[-1] += "\textra"
        with self.assertRaisesRegex(mod.InvalidPhysicalEvidence, "FIELD_COUNT"):
            mod.audit(table(changed))

    def test_zero_rss_and_negative_wall_rejected(self):
        for index, value in [(0, "0"), (3, "0")]:
            changed = ROWS.copy()
            parts = changed[index].split("\t")
            parts[3] = value
            changed[index] = "\t".join(parts)
            with self.assertRaisesRegex(mod.InvalidPhysicalEvidence, "RSS_INVALID"):
                mod.audit(table(changed))
        changed = ROWS.copy()
        changed[0] = changed[0].replace("0.00", "-0.01")
        with self.assertRaisesRegex(mod.InvalidPhysicalEvidence, "WALL_NOT"):
            mod.audit(table(changed))

    def test_nan_and_malformed_precision_rejected(self):
        for val in ("nan", "inf", "1e-9", "0.001", "00.01", ""):
            changed = ROWS.copy()
            changed[1] = changed[1].replace("0.10", val)
            with self.subTest(val=val), self.assertRaisesRegex(
                    mod.InvalidPhysicalEvidence, "WALL_NOT"):
                mod.audit(table(changed))

    def test_non_utf8_and_empty_rejected(self):
        for data in (b"\xff", b""):
            with self.assertRaises(mod.InvalidPhysicalEvidence):
                mod.audit(data)

    def test_cli_emits_fail_closed_json_without_fabricating_joules(self):
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            source = base / "samples.tsv"
            out = base / "audit.json"
            source.write_bytes(table())
            self.assertEqual(mod.main(["--samples", str(source), "--out", str(out)]), 0)
            report = json.loads(out.read_text(encoding="utf-8"))
            self.assertIsNone(report["energy_joules"])
            self.assertEqual(len(report["zero_rounded_samples"]), 3)
            source.write_bytes(table(ROWS[:3]))
            self.assertEqual(mod.main(["--samples", str(source), "--out", str(out)]), 2)


if __name__ == "__main__":
    unittest.main()
