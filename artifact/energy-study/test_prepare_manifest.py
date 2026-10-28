"""Synthetic packaging controls only: never evidence of measured energy or reproduction."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import prepare_manifest as package
import validate_manifest as audit

SHA = "a" * 40


class PackageTests(unittest.TestCase):
    def setUp(self):
        self.work = tempfile.TemporaryDirectory()
        self.addCleanup(self.work.cleanup)
        self.root = Path(self.work.name)
        self.raw = [
            {"language": language, "block": 1, "pair": pair, "order": order,
             "wall_time_ns": 150, "peak_rss_kib": 1000, "energy_uj": None,
             "time_boundary": "host_wrapper_includes_subprocess"}
            for candidate in ("python", "c")
            for pair in range(1, 5)
            for order in ("AB" if pair % 2 else "BA",)
            for language in (("rust", candidate) if order == "AB"
                             else (candidate, "rust"))
        ]
        self.provenance = {"git_sha": SHA, "energy_sensor": "RAPL_UNAVAILABLE",
                           "language_semantics": "NOT_TESTED"}
        self.report = {
            candidate: {"wall_time_ns": {"pairs": 4, "status": "INCONCLUSIVE"},
                        "peak_rss_kib": {"pairs": 4, "status": "INCONCLUSIVE"},
                        "energy_uj": {"status": "ENERGY_NOT_MEASURED"}}
            for candidate in ("c", "python")
        }
        self.write()

    def write(self):
        for filename, payload in (("raw-samples.json", self.raw),
                                  ("provenance.json", self.provenance),
                                  ("paired-report.json", self.report)):
            (self.root / filename).write_text(json.dumps(payload) + "\n", encoding="utf-8")
        (self.root / "summary.md").write_text("SYNTHETIC; no language ranking.\n")

    def assert_blocked(self, match: str):
        with self.assertRaisesRegex(audit.InvalidArtifact, match):
            package.prepare(self.root, SHA)
        self.assertFalse((self.root / "manifest.json").exists())
        self.assertEqual(list(self.root.glob(".manifest-check-*")), [])

    def test_packs_valid_no_sensor_and_checks_sha256(self):
        result = package.prepare(self.root, SHA)
        manifest_path = self.root / "manifest.json"
        manifest = json.loads(manifest_path.read_text())
        self.assertEqual(result["raw_samples"], 16)
        self.assertEqual(result["energy_status"], "ENERGY_NOT_MEASURED")
        self.assertEqual(manifest["independent_reproduction"], "NOT_REPRODUCED")
        for key, path in audit.REQUIRED_FILES.items():
            self.assertEqual(manifest["files"][key]["sha256"],
                             hashlib.sha256((self.root / path).read_bytes()).hexdigest())
        self.assertEqual(audit.verify(manifest_path)["source_sha"], SHA)
        self.assertEqual(list(self.root.glob(".manifest-check-*")), [])

    def test_measured_packet_is_still_not_reproduced(self):
        self.provenance["energy_sensor"] = "RAPL_AVAILABLE"
        for item in self.raw:
            item.update(energy_uj=12345, scope="whole_package_not_process",
                        counter="/sys/class/powercap/intel-rapl:0/energy_uj",
                        wrapped_once=False,
                        time_boundary="RAPL_meter_wraps_usr_bin_time")
        for report in self.report.values():
            report["energy_uj"] = {"status": "INCONCLUSIVE"}
        self.write()
        self.assertEqual(package.prepare(self.root, SHA)["energy_status"], "MEASURED")
        self.assertEqual(audit.verify(self.root / "manifest.json")
                         ["independent_reproduction"], "NOT_REPRODUCED")

    def test_rejects_missing_expected_sha(self):
        for bad in ("a" * 39, "Z" * 40, "a" * 40 + "b"):
            with self.subTest(bad=bad), self.assertRaisesRegex(
                    audit.InvalidArtifact, "expected Git SHA"):
                package.prepare(self.root, bad)
        self.assertFalse((self.root / "manifest.json").exists())

    def test_rejects_expected_sha_different_from_provenance(self):
        self.provenance["git_sha"] = "b" * 40
        self.write()
        self.assert_blocked("provenance Git SHA")

    def test_rejects_legacy_pilot_without_time_boundary(self):
        self.raw[0].pop("time_boundary")
        self.write()
        self.assert_blocked("time boundary invalid")

    def test_rejects_old_not_measured_report_without_masking_it(self):
        self.report["c"]["energy_uj"] = {"status": "NOT_MEASURED"}
        self.write()
        self.assert_blocked("numeric energy claim")

    def test_rejects_pseudojoules_without_sensor(self):
        self.raw[0]["energy_uj"] = 2
        self.write()
        self.assert_blocked("fabricated energy")

    def test_rejects_unknown_sensor_status(self):
        self.provenance["energy_sensor"] = "RAPL_MAYBE"
        self.write()
        self.assert_blocked("unrecognized energy sensor")

    def test_rejects_missing_raw_file(self):
        (self.root / "raw-samples.json").unlink()
        self.assert_blocked("missing, linked or escaping evidence")

    def test_rejects_symlink_file(self):
        raw = self.root / "raw-samples.json"
        raw.rename(self.root / "real-raw.json")
        raw.symlink_to(self.root / "real-raw.json")
        self.assert_blocked("missing, linked or escaping evidence")

    def test_rejects_report_pair_count_drift(self):
        self.report["python"]["wall_time_ns"]["pairs"] = 6
        self.write()
        self.assert_blocked("does not match raw paired launches")

    def test_rejects_invalid_provenance_json(self):
        (self.root / "provenance.json").write_text("not json", encoding="utf-8")
        self.assert_blocked("unreadable JSON")

    def test_does_not_overwrite_existing_manifest(self):
        dest = self.root / "manifest.json"
        dest.write_text("owner existing data", encoding="utf-8")
        with self.assertRaisesRegex(audit.InvalidArtifact, "already exists"):
            package.prepare(self.root, SHA)
        self.assertEqual(dest.read_text(), "owner existing data")

    def test_atomic_link_rejects_race_and_cleans_temp(self):
        with mock.patch.object(package.os, "link", side_effect=FileExistsError("race")):
            with self.assertRaises(FileExistsError):
                package.prepare(self.root, SHA)
        self.assertFalse((self.root / "manifest.json").exists())
        self.assertEqual(list(self.root.glob(".manifest-check-*")), [])

    def test_rejects_linked_directory(self):
        link = self.root.parent / (self.root.name + "-alias")
        link.symlink_to(self.root, target_is_directory=True)
        self.addCleanup(link.unlink)
        with self.assertRaisesRegex(audit.InvalidArtifact, "directory missing or linked"):
            package.prepare(link, SHA)

    def test_sha256_detects_evidence_changed_after_packaging(self):
        package.prepare(self.root, SHA)
        (self.root / "summary.md").write_text("TAMPERED\n")
        with self.assertRaisesRegex(audit.InvalidArtifact, "tampered evidence"):
            audit.verify(self.root / "manifest.json")


if __name__ == "__main__":
    unittest.main()
