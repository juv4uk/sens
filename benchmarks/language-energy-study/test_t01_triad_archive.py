#!/usr/bin/env python3
"""FAIR offline guard for actual T01 triad GitHub-job-log transcriptions.

This checks *provenance* and empirical observation formatting, not SENS laws.
The files were transcribed from the published job log; no ZIP was retrieved.
"""
from __future__ import annotations

import csv
import hashlib
import io
from pathlib import Path
import sys
import unittest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from t01_clock_floor import InvalidPhysicalEvidence, audit  # noqa: E402

ARCHIVE = HERE.parents[1] / "artifact/energy-study/observations/t01-triad"
SAMPLES = ARCHIVE / "samples.log-transcribed.tsv"
ENV = ARCHIVE / "environment.log-transcribed.tsv"
SAMPLES_SHA256 = "f3c37fc90af183c837f861cbe50cb7e02ffceeb71c975d0a9d76f6144ede0980"
ENV_SHA256 = "d81f733b4bb200d162eef6eb004b4fce086e2f4654b8dcec8cfe59d173b6795f"
RUN_SHA = "6a27d38494a76eb03840e0110a76b1712ff94546"


def immutable_read(path: Path, expected_sha: str) -> bytes:
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected_sha:
        raise InvalidPhysicalEvidence("ARCHIVED_JOB_TRANSCRIPT_SHA_MISMATCH")
    return raw


def audit_environment(raw: bytes) -> dict[str, str]:
    try:
        content = raw.decode("utf-8")
        rows = list(csv.reader(io.StringIO(content, newline=""), delimiter="\t", strict=True))
    except (UnicodeError, csv.Error) as exc:
        raise InvalidPhysicalEvidence("ENVIRONMENT_INVALID_TSV") from exc
    keys = (
        "source_sha", "machine", "cpu", "sens_version", "node_version",
        "compiler", "source_c", "source_js", "source_sens", "functional_unit",
        "phase", "energy", "admission",
    )
    if len(rows) != len(keys) or any(len(x) != 2 or x[0] != keys[i]
                                    for i, x in enumerate(rows)):
        raise InvalidPhysicalEvidence("ENVIRONMENT_FIELDS_CHANGED")
    values = dict(rows)
    if (values["source_sha"] != RUN_SHA
            or values["sens_version"] != "sens 0.42.3"
            or values["cpu"] != "Intel(R) Xeon(R) 6973P-C"
            or "Linux 7.0.0-1017-azure" not in values["machine"]
            or values["functional_unit"] != "T01 naive fib(12), stdout 144"
            or "SENS debug" not in values["phase"]
            or values["energy"] != "ENERGY_NOT_MEASURED"
            or not values["admission"].startswith("EXPLORATORY;")):
        raise InvalidPhysicalEvidence("ENVIRONMENT_PROVENANCE_INVALID")
    return values


class HostedT01TriadArchive(unittest.TestCase):
    def test_exact_transcript_sha_and_metadata(self):
        raw = immutable_read(SAMPLES, SAMPLES_SHA256)
        self.assertGreater(len(raw), 200)
        self.assertTrue(raw.endswith(b"\n"))
        metadata = audit_environment(immutable_read(ENV, ENV_SHA256))
        self.assertEqual(len(metadata), 13)
        self.assertEqual(metadata["source_sha"], RUN_SHA)

    def test_real_physical_samples_are_descriptive_only(self):
        report = audit(immutable_read(SAMPLES, SAMPLES_SHA256))
        self.assertEqual(report["samples"], 9)
        self.assertEqual(report["clock_admission"], "BLOCKED_BELOW_RESOLUTION")
        self.assertEqual([(row["round"], row["language"]) for row in
                          report["zero_rounded_samples"]],
                         [(1, "C"), (2, "C"), (3, "C")])
        self.assertFalse(report["inference_admitted"])
        self.assertIsNone(report["speed_ratios"])
        self.assertIsNone(report["confidence_intervals"])
        self.assertIsNone(report["energy_joules"])
        self.assertEqual(report["energy_status"], "ENERGY_NOT_MEASURED")

    def test_transcript_mutation_is_detected_before_analysis(self):
        raw = immutable_read(SAMPLES, SAMPLES_SHA256)
        for modified in (
            raw.replace(b"1\tC\t0.00", b"1\tC\t0.01"),
            raw.replace(b"3\tJS\t0.02", b"3\tJS\t0.00"),
            raw.replace(b"1\tSENS\t0.01\t25088\t0\t144", b"1\tSENS\t0.01\t25088\t0\t143"),
        ):
            with self.assertRaisesRegex(InvalidPhysicalEvidence, "SHA_MISMATCH"):
                immutable_read_bytes(modified, SAMPLES_SHA256)

    def test_negative_parity_and_missing_record_block_inference(self):
        raw = immutable_read(SAMPLES, SAMPLES_SHA256)
        with self.assertRaisesRegex(InvalidPhysicalEvidence, "RESULT_OR_EXIT"):
            audit(raw.replace(b"2\tJS\t0.02\t43772\t0\t144",
                              b"2\tJS\t0.02\t43772\t1\t144"))
        with self.assertRaisesRegex(InvalidPhysicalEvidence, "EXACTLY_9"):
            audit(raw.rsplit(b"\n", 2)[0] + b"\n")

    def test_wrong_environment_or_fabricated_energy_rejected(self):
        raw = immutable_read(ENV, ENV_SHA256)
        for modified in (
            raw.replace(b"ENERGY_NOT_MEASURED", b"42.0 J"),
            raw.replace(b"Intel(R) Xeon(R) 6973P-C", b"CPU unspecified"),
            raw.replace(RUN_SHA.encode("ascii"), b"0" * 40),
        ):
            with self.assertRaises(InvalidPhysicalEvidence):
                audit_environment(modified)


def immutable_read_bytes(raw: bytes, sha: str) -> bytes:
    if hashlib.sha256(raw).hexdigest() != sha:
        raise InvalidPhysicalEvidence("ARCHIVED_JOB_TRANSCRIPT_SHA_MISMATCH")
    return raw


if __name__ == "__main__":
    unittest.main()
