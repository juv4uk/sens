"""Synthetic FAIR evidence integrity cases, no real measurements."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

import validate_manifest as audit

SHA = "c" * 40

class ArtifactIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.work = tempfile.TemporaryDirectory()
        self.addCleanup(self.work.cleanup)
        self.root = Path(self.work.name)
        self.files = {
            "raw_samples": [
                {"language": lang, "block": 1, "pair": pair, "order": order,
                 "wall_time_ns": 100, "peak_rss_kib": 1000, "energy_uj": None,
                 "time_boundary": "host_wrapper_includes_subprocess"}
                for candidate, flip in (("c", 0), ("python", 1))
                for pair in range(1, 5)
                for order in ("AB" if (pair + flip) % 2 == 0 else "BA",)
                for lang in (("rust", candidate) if order == "AB"
                             else (candidate, "rust"))
            ],
            "provenance": {"git_sha": SHA, "language_semantics": "NOT_TESTED",
                           "energy_sensor": "RAPL_UNAVAILABLE"},
            "paired_report": {
                candidate: {
                    "wall_time_ns": {"status": "INCONCLUSIVE", "pairs": 4},
                    "peak_rss_kib": {"status": "INCONCLUSIVE", "pairs": 4},
                    "energy_uj": {"status": "ENERGY_NOT_MEASURED"},
                } for candidate in ("c", "python")
            },
            "summary": "No joules; physical source copy only.\n",
        }
        self.write()

    def write(self):
        entries = {}
        for key, filename in audit.REQUIRED_FILES.items():
            payload = self.files[key]
            data = (payload if isinstance(payload, str)
                    else json.dumps(payload, ensure_ascii=False))
            (self.root / filename).write_text(data, encoding="utf-8")
            entries[key] = {"path": filename,
                            "sha256": hashlib.sha256(data.encode()).hexdigest()}
        self.manifest = {"schema": audit.SCHEMA, "source_sha": SHA,
                         "energy_status": "ENERGY_NOT_MEASURED",
                         "independent_reproduction": "NOT_REPRODUCED", "files": entries}
        (self.root / "manifest.json").write_text(json.dumps(self.manifest))

    def check(self):
        return audit.verify(self.root / "manifest.json")

    def test_valid_no_sensor_records_missing_energy(self):
        self.assertEqual(self.check()["energy_status"], "ENERGY_NOT_MEASURED")

    def test_tampered_raw_bytes_rejected(self):
        (self.root / "raw-samples.json").write_text("[]")
        with self.assertRaisesRegex(audit.InvalidArtifact, "tampered"):
            self.check()

    def test_traversal_or_symlink_rejected(self):
        self.manifest["files"]["raw_samples"]["path"] = "../raw-samples.json"
        (self.root / "manifest.json").write_text(json.dumps(self.manifest))
        with self.assertRaises(audit.InvalidArtifact):
            self.check()

    def test_source_sha_mismatch_rejected(self):
        self.files["provenance"]["git_sha"] = "d" * 40
        self.write()
        with self.assertRaisesRegex(audit.InvalidArtifact, "source SHA"):
            self.check()

    def test_no_sensor_with_fabricated_joules_rejected(self):
        self.files["raw_samples"][0]["energy_uj"] = 100
        self.write()
        with self.assertRaisesRegex(audit.InvalidArtifact, "fabricated energy"):
            self.check()

    def test_no_sensor_with_numeric_report_rejected(self):
        self.files["paired_report"]["c"]["energy_uj"]["ratio"] = 1.2
        self.write()
        with self.assertRaisesRegex(audit.InvalidArtifact, "numeric energy"):
            self.check()

    def test_missing_peak_rss_rejected(self):
        self.files["raw_samples"][0]["peak_rss_kib"] = 0
        self.write()
        with self.assertRaisesRegex(audit.InvalidArtifact, "RSS invalid"):
            self.check()

    def test_false_reproduction_status_rejected(self):
        self.manifest["independent_reproduction"] = "REPRODUCED"
        (self.root / "manifest.json").write_text(json.dumps(self.manifest))
        with self.assertRaisesRegex(audit.InvalidArtifact, "third-party"):
            self.check()

    def test_measured_without_package_scope_rejected(self):
        self.manifest["energy_status"] = "MEASURED"
        self.files["provenance"]["energy_sensor"] = "RAPL_AVAILABLE"
        self.files["raw_samples"][0]["energy_uj"] = 1000
        self.write()
        self.manifest["energy_status"] = "MEASURED"
        (self.root / "manifest.json").write_text(json.dumps(self.manifest))
        with self.assertRaisesRegex(audit.InvalidArtifact, "meter boundary"):
            self.check()

    def test_numeric_wrap_flag_is_not_a_boolean(self):
        self.files["provenance"]["energy_sensor"] = "RAPL_AVAILABLE"
        self.files["raw_samples"][0].update(
            energy_uj=1000, scope="whole_package_not_process",
            time_boundary="RAPL_meter_wraps_usr_bin_time", wrapped_once=1,
            counter="/sys/class/powercap/intel-rapl:0/energy_uj")
        for language in ("python", "c"):
            self.files["paired_report"][language]["energy_uj"] = {"status": "INCONCLUSIVE"}
        self.write()
        self.manifest["energy_status"] = "MEASURED"
        (self.root / "manifest.json").write_text(json.dumps(self.manifest))
        with self.assertRaisesRegex(audit.InvalidArtifact, "counter provenance"):
            self.check()

    def test_unpaired_raw_launch_rejected(self):
        self.files["raw_samples"].pop()
        self.write()
        with self.assertRaisesRegex(audit.InvalidArtifact, "unpaired raw launch"):
            self.check()

    def test_swapped_ab_launch_order_rejected(self):
        rows = self.files["raw_samples"]
        rows[0], rows[1] = rows[1], rows[0]
        self.write()
        with self.assertRaisesRegex(audit.InvalidArtifact, "order contradicts launches"):
            self.check()

    def test_skipped_candidate_launch_rejected(self):
        self.files["raw_samples"] = [
            row for row in self.files["raw_samples"] if row["language"] != "python"]
        self.write()
        with self.assertRaises(audit.InvalidArtifact):
            self.check()

    def test_corrupt_pair_number_rejected(self):
        self.files["raw_samples"][0]["pair"] = 7
        self.write()
        with self.assertRaisesRegex(audit.InvalidArtifact, "mismatched block/pair"):
            self.check()

    def test_report_pair_count_drift_rejected(self):
        self.files["paired_report"]["c"]["wall_time_ns"]["pairs"] = 5
        self.write()
        with self.assertRaisesRegex(audit.InvalidArtifact, "does not match raw paired launches"):
            self.check()

    def test_missing_report_metric_rejected(self):
        del self.files["paired_report"]["python"]["peak_rss_kib"]
        self.write()
        with self.assertRaisesRegex(audit.InvalidArtifact, "does not match raw paired launches"):
            self.check()

    def test_valid_measured_scope_without_claiming_reproduction(self):
        self.files["provenance"]["energy_sensor"] = "RAPL_AVAILABLE"
        for sample in self.files["raw_samples"]:
            sample.update(
                energy_uj=50000, scope="whole_package_not_process",
                time_boundary="RAPL_meter_wraps_usr_bin_time", wrapped_once=False,
                counter="/sys/class/powercap/intel-rapl:0/energy_uj")
        for language in ("python", "c"):
            self.files["paired_report"][language]["energy_uj"] = {"status": "INCONCLUSIVE"}
        self.write()
        self.manifest["energy_status"] = "MEASURED"
        (self.root / "manifest.json").write_text(json.dumps(self.manifest))
        self.assertEqual(self.check()["independent_reproduction"], "NOT_REPRODUCED")

if __name__ == "__main__":
    unittest.main()
